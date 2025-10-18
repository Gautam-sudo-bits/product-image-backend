# ingest_assets.py
import os
import json
import shutil
import pickle
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, KEYWORD, BOOLEAN
from whoosh.qparser import QueryParser
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

print("--- Starting Advanced Asset Ingestion Script ---")

# --- 1. CONFIGURATION ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

ASSET_FOLDER = "./brand_assets/images"
INDEX_DIR = "./whoosh_index"
TFIDF_MODEL_PATH = "./tfidf_data.pkl"

# --- 2. DEFINE THE SEARCH SCHEMA for Whoosh (BM25) ---
# This schema defines the fields we can search against.
schema = Schema(
    # The 'path' will be the unique ID and points to the local file
    path=ID(stored=True, unique=True),
    title=TEXT(stored=True, field_boost=1.5),
    product_type=KEYWORD(stored=True, field_boost=3.0, scorable=True),
    description=TEXT(stored=True, field_boost=1.0),
    tags=KEYWORD(stored=True, field_boost=2.0, scorable=True, commas=True),
    background_style=TEXT(stored=True, field_boost=1.5),
    contains_human=BOOLEAN(stored=True)
)

# --- 3. SETUP INDEX DIRECTORY ---
# Clear out the old index to ensure a fresh build every time
if os.path.exists(INDEX_DIR):
    shutil.rmtree(INDEX_DIR)
os.makedirs(INDEX_DIR)
ix = create_in(INDEX_DIR, schema)
writer = ix.writer()
print(f"Whoosh index created at: {INDEX_DIR}")

# --- 4. PREPARE for TF-IDF ---
# We will collect all text data to train the TF-IDF model at the end
all_documents_text = []
all_document_paths = []

# --- 5. METADATA GENERATION PROMPT ---
metadata_prompt = """
You are an expert cataloger for a high-end e-commerce platform. Analyze the provided image and generate a structured JSON object containing the following fields:
- "title": A short, compelling, SEO-friendly title for the product (max 10 words).
- "product_type": A concise category for the item (e.g., 'running shoe', 'armchair', 'summer dress').
- "description": A one or two-sentence descriptive summary of the image's content and style.
- "tags": A comma-separated string of 10-15 highly relevant keywords (include objects, colors, materials, mood, and style).
- "background_style": A short description of the background (e.g., 'solid white studio', 'warm lifestyle living room', 'abstract gradient', 'materialistic background', and so on).
- "contains_human": A boolean value (true or false) indicating if a human is present in the image.
Ensure the output is only the raw JSON object.
"""
metadata_model = genai.GenerativeModel('gemini-2.5-pro')

# --- 6. PROCESSING LOOP ---
print(f"Processing images from: {ASSET_FOLDER}")
for filename in os.listdir(ASSET_FOLDER):
    file_path = os.path.join(ASSET_FOLDER, filename)
    if not os.path.isfile(file_path):
        continue

    print(f"\n--- Processing: {filename} ---")
    try:
        # a. Generate structured metadata using Gemini Pro
        print("Step 1/3: Generating structured metadata...")
        local_image = Image.open(file_path)
        response = metadata_model.generate_content([metadata_prompt, local_image])
        metadata = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        print("-> Success. Metadata generated.")

        # b. Add the document to the Whoosh (BM25) index writer
        print("Step 2/3: Indexing with Whoosh (BM25)...")
        writer.add_document(
            path=file_path,
            title=metadata.get('title'),
            product_type=metadata.get('product_type'),
            description=metadata.get('description'),
            tags=metadata.get('tags'),
            background_style=metadata.get('background_style'),
            contains_human=metadata.get('contains_human')
        )
        print("-> Success. Document added to BM25 index.")

        # c. Collect text for TF-IDF model training
        combined_text = " ".join([
            str(metadata.get('title', '')),
            str(metadata.get('product_type', '')),
            str(metadata.get('description', '')),
            str(metadata.get('tags', '')),
            str(metadata.get('background_style', ''))
        ])
        all_documents_text.append(combined_text)
        all_document_paths.append(file_path)
        print("Step 3/3: Text prepared for TF-IDF training.")

    except Exception as e:
        print(f"[ERROR] Failed to process {filename}: {e}")

# --- 7. COMMIT THE WHOOSH INDEX ---
print("\nCommitting all documents to the Whoosh index...")
writer.commit()
print("-> Success. Whoosh index is ready.")

# --- 8. TRAIN and SAVE THE TF-IDF MODEL ---
print("Training and saving the TF-IDF model...")
try:
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(all_documents_text)

    # Save the vectorizer and the matrix for fast retrieval later
    with open(TFIDF_MODEL_PATH, 'wb') as f:
        pickle.dump({
            'vectorizer': vectorizer,
            'matrix': tfidf_matrix,
            'paths': all_document_paths
        }, f)
    print(f"-> Success. TF-IDF model and data saved to: {TFIDF_MODEL_PATH}")
except Exception as e:
    print(f"[ERROR] Failed to train TF-IDF model: {e}")

print("\n--- Advanced Asset Ingestion Complete ---")