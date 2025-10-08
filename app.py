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
            "objective": "Generate an ultra-realistic full-body e-commerce photo showing the product from image 1(product only image) being worn by a human model.",
            "composition": "Centered, full-body long shot with the model standing naturally.",
            "environment": "Bright and elegant lifestyle background such as a modern city street, minimalist indoor studio, or upscale cafe setting. Maintan real world object proportions.",
            "lighting": "Soft, natural daylight with even exposure across the frame.",
            "camera": "Shot with a DSLR camera using a 50mm lens, aperture f/2.8, ISO 100.",
            "style": "ultra-realistic, 4k, professional e-commerce photography, high-detail, clean, premium",
            "constraints": [
            "The product shirt/t-shirt/fabric must appear perfectly smooth and evenly textured. Remove all wrinkles, fold, and creases completely while preserving the natural fabric texture.",
            "Ensure the entire product is visible in the frame.",
            "Avoid cropping of the main product or model.",
            "Maintain realistic body and fabric proportions.",
            "Preserve maximum product features, colors and patterns, folds, and stitching details."
            ]
        }
        })
            jobs.append({"type": "human_close_up", "prompt_json": {
                "objective": "Create a high-detail close-up of the product from image 1(product only image) being worn by the model human on the second image(only if second human image is provided).",
                "composition": "If the product in the image is clothing apparel, then create a Waist-up shot emphasizing fabric quality, fit, and product texture. Clear human model face. If the product is an accessory like a hat, scarf, purse, shoe, or jewelry, etc., then create a tight close-up focusing on the product details and craftsmanship. Create a natural pose of the human model(e.g., two shoes can be placed on the floor, one shoe can be slightly forward to show depth).",
                "environment": "Clean, neutral, and minimally distracting background.",
                "lighting": "Softbox studio lighting setup with subtle shadow gradients for depth.",
                "camera": "Captured with a Canon EOS R5, 85mm lens, f/3.2 aperture.",
                "style": "ultra-realistic, 4k, professional e-commerce photography, high-detail, clean, premium",
                "constraints":["Keep the product fully visible and in sharp focus.",
                "The product shirt/t-shirt/fabric must appear perfectly smooth and evenly textured. Remove all wrinkles, fold, and creases completely while preserving the natural fabric texture.",
                "Preserve maximum product features, colors and patterns, folds, and stitching details.",
                "Avoid reflections or overexposed areas.",
                "No heavy post-processing or artificial effects."]
            }})
        if options.get('mannequin'):
            jobs.append({"type": "mannequin", "prompt_json": {
                "objective": "Generate a clean, studio-style e-commerce photo displaying the product from image 1 on a mannequin.",
                "composition": "Centered, head-on view with the full mannequin body visible. Mannequin should be neutral in color (white, gray) to avoid distractions.",
                "environment": "Solid light-gray or white seamless studio background.",
                "lighting": "Even, bright studio lighting with soft shadows to highlight product contours.",
                "camera": "Shot on tripod, 70mm focal length for accurate proportions.",
                "style": "ultra-realistic, 4k, professional e-commerce photography, high-detail, clean, premium",
                "constraints": [
                "Ensure the full product is shown without cropping.",
                "The product shirt/t-shirt/fabric must appear perfectly smooth and evenly textured. Remove all wrinkles, fold, and creases completely while preserving the natural fabric texture.",
                "Maintain true-to-life proportions and folds.",
                "Preserve maximum product features, colors and patterns, folds, and stitching details.",
                "Avoid reflective or glossy mannequin surfaces.",
                "Keep focus strictly on the product."
                ]
            }})
        if options.get('creative'):
            jobs.append({"type": "creative_fashion", "prompt_json": {
                "objective": "Design a vibrant, eye-catching fashion, social-media marketing image for the product from image 1(product only image), that focuses only on the product image.",
                "composition": "Dynamic composition where the product is the central focus. The fabric should be neatly ironed with no creases, folds and wrinkles",
                "environment": "Abstract or colorful backdrop with stylish graphic overlays. The backdrop colors and style should complement the color palette of the fabric/product.",
                "visuals": "Add creative design elements such as colorful frames, shapes, overlays, or graphic accents that enhance the advertisement's appeal. Incorporate bold typography inside creative design elements like frames or shapes, that reads '50% OFF – Limited Time!' with clean layout balance, integrated naturaly into the design(not just pasted on the image). Include any one: 'Buy Now!',or 'Click the link in Bio!',or 'Link in Bio!' or 'Shop Now' texts, resembling social media posts.",
                "style": "high-energy, commercial, advertisement, modern, premium aesthetic",
                "constraints": [
                "The product shirt/t-shirt/fabric must appear perfectly smooth and evenly textured. Remove all wrinkles, fold, and creases completely while preserving the natural fabric texture.",
                "The product should remain clearly visible and unobstructed.",
                "Typography should not overlap key product details.",
                "Image should look like a high-quality e-commerce or fashion sale ad designed for Instagram, facenook or pinterest.",
                "Preserve maximum product features, colors and patterns, folds, and stitching details."
                ]
            }})

    elif category == 'Home Decor':
        if options.get('lifestyle'):
            """jobs.append({"type": "lifestyle_angle2", "prompt_json": {
                "task": "Place the product from image 1 into a suitable, high-end home lifestyle scene.",
                "composition": "Shot from a 45-degree high angle, eye-level perspective to the product.",
                "environment": "A beautifully decorated living room or study that complements the product.",
                "lighting": "Warm, natural light from a window.", "style": base_style, "constraints": base_constraints
            }})"""
            jobs.append({"type": "lifestyle_angle1", "prompt_json": {
                "objective": "Generate a lifestyle photo of the product from image in a clean home interior. The scene should be naturally lit and the product should be the main focus, resembling as such a real e-commerce product photo.",
                "composition": "Direct front-facing eye-level shot focusing on the product’s shape and material. If the product is a lighting fixture, it should be turned on to showcase its effect(e.g., floor lamps, table lamps)-no outdoor window lighting. The product should be the only main item - no duplicates or unrelated objects in the scene. The setting should look logical and context-appropriate for the product type(e.g., a sofa in a neat living room, shoes in a stylish entryway).Focus entirely on the product.",
                "environment": "Minimalist bedroom, home office with coordinated decor tones, living room with appropriate product placement in the room, or any scene suitable for the main product. Table products can have suitable creative elements like books, vases, or plants, etc., on the table. Avoid cluttered or overly busy backgrounds.",
                "lighting": "Soft, ambient indoor lighting with gentle contrast.",
                "camera": "50mm lens, ISO 100, balanced exposure.",
                "style": "ultra-realistic, 4k, professional e-commerce photography, high-detail, clean, premium",
                "constraints": [
                "Keep full visibility of the product.",
                "No cropping or reflections.",
                "Preserve maximum product features, colors and patterns, folds, and stitching details.",
                "Maintain accurate shape, typography, texture, features, and proportions as such from the original image."
                ]
            }})
        if options.get('studio'):
            jobs.append({"type": "studio", "prompt_json": {
                "objective": "Generate a clean e-commerce product listing image for the product from image 1.",
                "composition": "Centered and isolated product on a plain background.",
                "environment": "Seamless, solid white or light-gray backdrop.",
                "lighting": "Bright, balanced studio lighting with soft shadows for realism.",
                "camera": "Canon 5D Mark IV, 70mm lens, aperture f/5.6.",
                "style": "ultra-realistic, 4k, professional e-commerce photography, high-detail, clean, premium",
                "constraints": [
                "Show the entire product clearly without any cropping.",
                "Maintain accurate shape, typography, texture, features, and proportions as such from the original image.",
                "Avoid glare, overexposure, or reflections."
                ]
            }})
        if options.get('creative'):
            jobs.append({"type": "creative_decor", "prompt_json": {
                "objective": "Create a visually engaging marketing image for the home decor product from image 1.",
                "composition": "Hero-style composition emphasizing the product as the central subject.",
                "environment": "Elegant backdrop with decorative elements that enhance but don’t distract.",
                "visuals": "Overlay refined text, Incorporating bold typography inside creative design elements like frames or shapes, that reads 'SALE – UP TO 70% OFF!' in a premium, minimalist font.",
                "style": "advertisement, elegant, promotional, lifestyle-inspired",
                "constraints": [
                "Product must remain unobstructed and clearly visible.",
                "Image should look like a high-quality e-commerce or fashion sale ad designed for Instagram, facenook or pinterest.",
                "Text should complement, not overpower, the visual.",
                "Maintain high photorealism and premium aesthetic.",
                "Preserve maximum product features, colors and patterns, folds, and stitching details."
                ]
            }})

    return jobs

def generate_and_upload_image(job_details):
    """
    Receives a job with RAW IMAGE BYTES, creates its own image objects,
    calls Gemini, and uploads the result. This is now thread-safe.
    """
    prompt_json = job_details['prompt_json']
    # This now receives raw bytes, not PIL.Image objects
    input_images_bytes = job_details['images_bytes_list']
    base_public_id = job_details['base_public_id']
    job_type = job_details['type']
    job_index = job_details['index']

    try:
        print(f"Starting job {job_index} ({job_type})...")
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        
        plain_text_prompt = flatten_prompt_json(prompt_json)

        input_images_for_this_thread = []
        for img_bytes in input_images_bytes:
            input_images_for_this_thread.append(Image.open(BytesIO(img_bytes)))

        contents = [plain_text_prompt] + input_images_for_this_thread
        
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
        # Upload ALL user images and prepare them for Gemini
        input_image_bytes_list = [] 
        base_public_id = None
        for i, image_file in enumerate(image_files):
            print(f"Uploading input image {i+1}...")
            upload_result = cloudinary.uploader.upload(image_file, folder="product-image-inputs")
            if i == 0:
                base_public_id = upload_result['public_id']
            
            image_response = requests.get(upload_result['secure_url'])
            image_response.raise_for_status()
            input_image_bytes_list.append(image_response.content)

        # Get the list of prompt jobs
        prompt_jobs = create_prompt_jobs(form_data)
        if not prompt_jobs:
            return jsonify({"error": "No generation options selected."}), 400
        print(f"Created {len(prompt_jobs)} generation jobs.")

        # Prepare jobs for the parallel executor
        jobs_with_context = [{
            'prompt_json': job['prompt_json'],
            'images_bytes_list': input_image_bytes_list,
            'base_public_id': base_public_id,
            'type': job['type'], 'index': i
        } for i, job in enumerate(prompt_jobs)]

        #  Execute jobs in parallel
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