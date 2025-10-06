# app.py
import os
import json
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import requests
from flask_cors import CORS
import concurrent.futures

# --- Configuration ---
load_dotenv()
app = Flask(__name__)
CORS(app)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def create_prompt_jobs(form_data):
    """Generates a list of prompt "jobs" based on user selections."""
    jobs = []
    category = form_data.get('category')
    options = form_data.get('selectedOptions', {})
    ethnicity = form_data.get('ethnicity')

    if category == 'Fashion':
        if options.get('humanModel'):
            jobs.append({'type': 'human', 'prompt': f"Full-shot of a {ethnicity} model wearing the product, professional studio lighting, captured from a front angle."})
            jobs.append({'type': 'human', 'prompt': f"Waist-up shot of a {ethnicity} model wearing the product, dynamic pose, outdoor natural lighting, from a 45-degree angle."})
            jobs.append({'type': 'human', 'prompt': f"Detailed close-up shot focusing on the product's texture and fit on a {ethnicity} model, soft lighting."})
        if options.get('mannequin'):
            jobs.append({'type': 'mannequin', 'prompt': "Product displayed on a sleek, featureless white mannequin, clean studio background, perfect for a product listing."})
        if options.get('creative'):
            jobs.append({'type': 'creative', 'prompt': "A high-fashion, artistic marketing image featuring the product. Use bold colors, abstract background, and a sense of luxury. Include text overlay saying 'New Collection'."})

    elif category == 'Home Decor':
        if options.get('lifestyle'):
            jobs.append({'type': 'lifestyle', 'prompt': "Product placed in a beautifully decorated, realistic home lifestyle setting that complements its style. Soft, natural light from a window."})
        if options.get('studio'):
            jobs.append({'type': 'studio', 'prompt': "Product against a solid, neutral-colored seamless background, crisp studio lighting, shot from a direct front angle."})
            jobs.append({'type': 'studio', 'prompt': "Product against a solid background, shot from a high 45-degree angle to show the top surface and details."})
            jobs.append({'type': 'studio', 'prompt': "A close-up, detailed shot of the product's material and craftsmanship against a solid background."})
        if options.get('creative'):
            jobs.append({'type': 'creative', 'prompt': "An eye-catching marketing banner for a home decor sale. The product is the centerpiece, with elegant graphic elements and text saying 'Limited Time Offer'."})

    return jobs

def generate_and_upload_image(job_details):
    """
    Receives a job, calls Gemini, and uploads the result to Cloudinary.
    This function is designed to be run in a separate thread.
    """
    prompt = job_details['prompt']
    input_image_for_gemini = job_details['image_object']
    base_public_id = job_details['base_public_id']
    job_type = job_details['type']
    job_index = job_details['index']

    try:
        print(f"Starting job {job_index} ({job_type})...")
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        response = model.generate_content([prompt, input_image_for_gemini])

        generated_image_bytes = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                generated_image_bytes = part.inline_data.data
                break
        
        if generated_image_bytes is None:
            print(f"Job {job_index} ({job_type}) failed: No image data from Gemini.")
            return None

        # Upload the generated image bytes to Cloudinary
        upload_result = cloudinary.uploader.upload(
            generated_image_bytes,
            folder="product-image-outputs",
            public_id=f"gen_{base_public_id}_{job_type}_{job_index}"
        )
        print(f"Finished job {job_index} ({job_type}). URL: {upload_result['secure_url']}")
        return upload_result['secure_url']

    except Exception as e:
        print(f"Error in job {job_index} ({job_type}): {e}")
        return None

# app.py (replace the old endpoint with this)

@app.route('/api/generate', methods=['POST'])
def generate_endpoint():
    # We now expect 'images' (plural) and 'generationSettings'
    if 'images' not in request.files or 'generationSettings' not in request.form:
        return jsonify({"error": "Missing images or generation settings"}), 400

    # Note: We are using the first uploaded image for now.
    # A more advanced version could blend features from multiple images.
    image_file = request.files.getlist('images')[0]
    form_data = json.loads(request.form['generationSettings'])

    try:
        # 1. Upload the primary user image once
        print("Uploading user's input image to Cloudinary...")
        upload_result = cloudinary.uploader.upload(image_file, folder="product-image-inputs")
        input_image_url = upload_result['secure_url']
        base_public_id = upload_result['public_id']
        print(f"Input image ready: {input_image_url}")

        # 2. Prepare the input image object for Gemini (download it once)
        image_response = requests.get(input_image_url)
        image_response.raise_for_status()
        input_image_for_gemini = Image.open(BytesIO(image_response.content))
        
        # 3. Use our factory to get the list of prompts/jobs to run
        prompt_jobs = create_prompt_jobs(form_data)
        if not prompt_jobs:
            return jsonify({"error": "No generation options selected."}), 400

        print(f"Created {len(prompt_jobs)} generation jobs.")

        # 4. Prepare the job details for the parallel executor
        jobs_with_context = []
        for i, job in enumerate(prompt_jobs):
            jobs_with_context.append({
                'prompt': job['prompt'],
                'image_object': input_image_for_gemini,
                'base_public_id': base_public_id,
                'type': job['type'],
                'index': i
            })
        
        # 5. Execute jobs in parallel using ThreadPoolExecutor
        generated_urls = []
        # The 'with' statement ensures threads are cleaned up properly
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 'map' runs the function for each item in the list in a separate thread
            results = executor.map(generate_and_upload_image, jobs_with_context)
            
            for url in results:
                if url: # Only add successful results
                    generated_urls.append(url)
        
        print(f"All jobs finished. Successfully generated {len(generated_urls)} images.")

        # 6. Send the list of URLs back to the frontend
        return jsonify({
            "status": "success",
            "message": f"Generated {len(generated_urls)} images.",
            "generated_image_urls": generated_urls # The key is now plural
        })

    except Exception as e:
        print(f"A critical error occurred in the main endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)