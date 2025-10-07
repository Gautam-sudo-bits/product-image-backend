import os
import json
import concurrent.futures
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import requests
from flask_cors import CORS

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

# app.py (add this new function)

def flatten_prompt_json(prompt_json):
    """Converts our structured prompt JSON into a single, detailed string."""
    lines = []
    for key, value in prompt_json.items():
        # Format constraints as a list for better readability
        if key == 'constraints' and isinstance(value, list):
            constraints_str = ", ".join(value)
            lines.append(f"- {key}: {constraints_str}")
        else:
            lines.append(f"- {key}: {value}")
    return "Execute the following instructions for the provided images:\n" + "\n".join(lines)
    
# --- NEW: Production-Grade JSON Prompt Factory ---
def create_prompt_jobs(form_data):
    jobs = []
    category = form_data.get('category')
    options = form_data.get('selectedOptions', {})

    # Base prompt elements to ensure consistency
    base_style = "ultra-realistic, 4k, professional e-commerce photography, high-detail, clean, premium"
    base_constraints = ["ensure the entire product is visible in the frame", "no cropping of the main product", "maintain realistic proportions","Preserve maximum product details and textures"]

    if category == 'Fashion':
        if options.get('humanModel'):
            jobs.append({"type": "human_long_shot", "prompt_json": {
                "task": "Place the product from image 1 onto a human model, similar to the context in image 2 if provided.",
                "composition": "Full-body long shot, model centered.",
                "environment": "A bright, elegant lifestyle setting like a modern city street or upscale cafe.",
                "lighting": "Soft, natural daylight.", "style": base_style, "constraints": base_constraints
            }})
            jobs.append({"type": "human_close_up", "prompt_json": {
                "task": "Create a close-up shot of the product from image 1 being worn by a human model.",
                "composition": "Waist-up shot, focusing on the product's texture and details.",
                "environment": "Clean, minimally distracting background.",
                "lighting": "Professional studio softbox lighting.", "style": base_style, "constraints": base_constraints
            }})
        if options.get('mannequin'):
            jobs.append({"type": "mannequin", "prompt_json": {
                "task": "Display the product from image 1 on a featureless, abstract mannequin.",
                "composition": "Centered, three-quarter view of the mannequin.",
                "environment": "Solid light-grey or white studio background.",
                "lighting": "Even, bright studio lighting.", "style": base_style, "constraints": base_constraints
            }})
        if options.get('creative'):
            jobs.append({"type": "creative_fashion", "prompt_json": {
                "task": "Create a vibrant marketing banner for the product in image 1.",
                "composition": "Dynamic, eye-catching layout.",
                "visuals": "Incorporate abstract graphic elements and bold colors. Superimpose flashy text that reads '50% OFF - Limited Time!'",
                "style": "commercial, advertisement, high-energy"
            }})

    elif category == 'Home Decor':
        if options.get('lifestyle'):
            jobs.append({"type": "lifestyle_angle1", "prompt_json": {
                "task": "Place the product from image 1 into a suitable, high-end home lifestyle scene.",
                "composition": "Shot from a 45-degree high angle, eye-level perspective to the product.",
                "environment": "A beautifully decorated living room or study that complements the product.",
                "lighting": "Warm, natural light from a window.", "style": base_style, "constraints": base_constraints
            }})
            jobs.append({"type": "lifestyle_angle2", "prompt_json": {
                "task": "Place the product from image 1 into a different lifestyle scene.",
                "composition": "Direct, eye-level front view, showing the product's proportions accurately.",
                "environment": "A calm, minimalist bedroom or office setting.",
                "lighting": "Soft, ambient indoor lighting.", "style": base_style, "constraints": base_constraints
            }})
        if options.get('studio'):
            jobs.append({"type": "studio", "prompt_json": {
                "task": "Create a clean, e-commerce listing photo for the product in image 1.",
                "composition": "Product centered perfectly.",
                "environment": "Seamless, solid white background.",
                "lighting": "Flawless, bright studio lighting with no harsh shadows.", "style": base_style, "constraints": base_constraints
            }})
        if options.get('creative'):
            jobs.append({"type": "creative_decor", "prompt_json": {
                "task": "Create an engaging marketing image for the home decor product in image 1.",
                "composition": "Product as the hero element.",
                "visuals": "Surround with elegant design elements. Overlay text that says 'SALE - UP TO 70% OFF!' in a stylish font.",
                "style": "advertisement, elegant, promotional"
            }})

    return jobs

def generate_and_upload_image(job_details):
    # This function is now designed to take a list of input images
    prompt_json = job_details['prompt_json']
    input_images = job_details['images_list']
    base_public_id = job_details['base_public_id']
    job_type = job_details['type']
    job_index = job_details['index']

    try:
        print(f"Starting job {job_index} ({job_type})...")
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        
        # The 'contents' list now includes the JSON prompt and ALL input images
        contents = [json.dumps(prompt_json)] + input_images
        
        response = model.generate_content(contents)
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

@app.route('/api/generate', methods=['POST'])
def generate_endpoint():
    if 'images' not in request.files or 'generationSettings' not in request.form:
        return jsonify({"error": "Missing images or generation settings"}), 400

    image_files = request.files.getlist('images')
    form_data = json.loads(request.form['generationSettings'])

    try:
        # 1. Upload ALL user images and prepare them for Gemini
        input_images_for_gemini = []
        base_public_id = None
        for i, image_file in enumerate(image_files):
            print(f"Uploading input image {i+1}...")
            upload_result = cloudinary.uploader.upload(image_file, folder="product-image-inputs")
            if i == 0: # Use the first image's ID for naming outputs
                base_public_id = upload_result['public_id']
            
            image_response = requests.get(upload_result['secure_url'])
            image_response.raise_for_status()
            input_images_for_gemini.append(Image.open(BytesIO(image_response.content)))

        # 2. Get the list of prompt jobs
        prompt_jobs = create_prompt_jobs(form_data)
        if not prompt_jobs:
            return jsonify({"error": "No generation options selected."}), 400
        print(f"Created {len(prompt_jobs)} generation jobs.")

        # 3. Prepare jobs for the parallel executor
        jobs_with_context = [{
            'prompt_json': job['prompt_json'],
            'images_list': input_images_for_gemini,
            'base_public_id': base_public_id,
            'type': job['type'], 'index': i
        } for i, job in enumerate(prompt_jobs)]

        # 4. Execute jobs in parallel
        generated_urls = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(generate_and_upload_image, jobs_with_context)
            for url in results:
                if url: generated_urls.append(url)
        
        print(f"All jobs finished. Successfully generated {len(generated_urls)} images.")
        
        return jsonify({
            "status": "success",
            "message": f"Generated {len(generated_urls)} images.",
            "generated_image_urls": generated_urls
        })

    except Exception as e:
        print(f"A critical error occurred in the main endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)