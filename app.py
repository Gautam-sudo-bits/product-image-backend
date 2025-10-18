# app.py (New Architecture)
import os
import json
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import prompt_instruction_templates
import cloudinary
import cloudinary.uploader
from PIL import Image
from io import BytesIO
import requests
import concurrent.futures

load_dotenv()
app = Flask(__name__)
CORS(app)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    
def plan_prompt(instruction_template, user_product_type, user_guidelines, user_marketing_copy):
    """
    Uses Gemini Pro (The Planner) to convert user inputs into a structured prompt
    for Nano Banana (The Artist).
    """
    print("--- Step 1: Planning Prompt ---")
    
    # We construct a detailed meta-prompt for the planner LLM
    meta_prompt = f"""
    {instruction_template}

    **USER-PROVIDED INPUTS FOLLOW:**
    ---
    - Product Type: "{user_product_type}"
    - Brand/Theme Guidelines: "{user_guidelines}"
    - Marketing Copy: "{user_marketing_copy}"
    ---
    Based on all the information above, generate the structured but Descriptive prompt for the image generator. Be creative and logical in product usage depiction.
    """
    
    try:
        # For this planning step, we use a standard text-generation model
        planner_model = genai.GenerativeModel('gemini-2.5-pro')
        response = planner_model.generate_content(meta_prompt)
        
        # The raw response might be plain text, or wrapped in markdown backticks
        planned_prompt_text = response.text.strip().replace('```json', '').replace('```', '')
        
        print(f"Successfully planned prompt:\n{planned_prompt_text}")
        
        # We return the clean text, ready to be passed to the artist model
        return planned_prompt_text

    except Exception as e:
        print(f"Error during prompt planning: {e}")
        raise

def execute_generation(planned_prompt, user_images):
    """
    Uses Nano Banana to generate an image. This version includes robust error handling
    and logs the full API response on failure to help debug safety filter issues.
    """
    print("--- Step 2: Executing Image Generation ---")
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        contents = [planned_prompt] + user_images
        
        response = model.generate_content(contents)
        print("Received response from Nano Banana.")
        
        generated_image_bytes = None
        
        # --- ROBUSTNESS FIX: Loop through all parts to find the image ---
        # Don't assume the image is always the first part.
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                # Defensively copy the data into a stable bytes object
                image_stream = BytesIO(part.inline_data.data)
                generated_image_bytes = image_stream.getvalue()
                print("Successfully extracted and copied generated image bytes.")
                break # Exit the loop once we find our image

        # --- DEBUGGING FIX: Check if we found an image and log if we didn't ---
        if generated_image_bytes:
            return generated_image_bytes
        else:
            # This is the critical part. We need to see the "black box" response.
            print("--- !!! FAILED TO FIND IMAGE DATA IN RESPONSE !!! ---")
            print(f"Full Gemini Response: {response}")
            raise ValueError("No inline_data found in any part of the Gemini response.")

    except Exception as e:
        print(f"Error during image generation execution: {e}")
        # Also log the full response if available, in case of other errors
        if 'response' in locals():
            print(f"Full Gemini Response at time of error: {response}")
        raise

def run_generation_pipeline(job_type, user_product_type, user_guidelines, user_marketing_copy, user_images):
    """
    Runs the full two-step pipeline for a single generation task and uploads the result.
    """
    print(f"\n--- Starting Generation Pipeline for Job: {job_type.upper()} ---")
    
    try:
        if job_type == 'solid_background':
            instruction = prompt_instruction_templates.SOLID_BACKGROUND_INSTRUCTION
        elif job_type == 'lifestyle':
            instruction = prompt_instruction_templates.LIFESTYLE_INSTRUCTION
        else: # 'marketing_creative'
            instruction = prompt_instruction_templates.MARKETING_CREATIVE_INSTRUCTION
            
        planned_prompt = plan_prompt(instruction, user_product_type, user_guidelines, user_marketing_copy)
        
        generated_image_bytes = execute_generation(planned_prompt, user_images)
        
        print(f"Uploading final '{job_type}' image to Cloudinary...")
        product_slug = user_product_type.replace(" ", "-").lower()
        public_id = f"{product_slug}_{job_type}"

        file_to_upload = BytesIO(generated_image_bytes)
        
        upload_result = cloudinary.uploader.upload(
            file_to_upload,
            folder="test_version_2/outputs",
            public_id=public_id
        )
        final_url = upload_result['secure_url']
        print(f"Successfully uploaded. Final URL: {final_url}")
        
        return final_url

    except Exception as e:
        # --- THE CRITICAL FIX IS HERE ---
        # We now print the actual error message for proper debugging.
        print(f"--- Pipeline for Job '{job_type.upper()}' FAILED ---")
        print(f"REASON: {e}") 
        return None

# app.py (replace ONLY this function)

@app.route('/api/test-pipeline', methods=['POST'])
def test_pipeline_endpoint():
    """
    Tests the entire single-threaded generation pipeline with a real image.
    """
    image_files = request.files.getlist('images')
    product_type = request.form.get('product_type', 'default_product')
    guidelines = request.form.get('guidelines', '')
    marketing_copy = request.form.get('marketing_copy', '')

    if not image_files:
        return jsonify({"error": "No image file provided"}), 400

    try:
        print("--- Uploading Input Image for Test ---")
        input_filename = os.path.splitext(image_files[0].filename)[0]
        
        upload_result = cloudinary.uploader.upload(
            image_files[0],
            folder="test_version_2/inputs",
            public_id=f"input_{input_filename}"
        )
        print(f"Input image uploaded to: {upload_result['secure_url']}")

        # --- THE CRITICAL FIX IS HERE ---
        # "Rewind" the file stream's cursor to the beginning after the first read.
        image_files[0].seek(0)
        
        # Now, the second read will get the full, correct data.
        image_bytes = image_files[0].read()
        user_images_for_ai = [Image.open(BytesIO(image_bytes))]
        
        final_image_url = run_generation_pipeline(
            job_type='lifestyle',
            user_product_type=product_type,
            user_guidelines=guidelines,
            user_marketing_copy=marketing_copy,
            user_images=user_images_for_ai
        )
        
        if not final_image_url:
            raise Exception("The generation pipeline failed to return a URL.")

        return jsonify({
            "status": "success",
            "message": "Full pipeline test successful.",
            "final_generated_image_url": final_image_url
        })
        
    except Exception as e:
        # This will now provide a more informative error if something else goes wrong.
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-planner', methods=['GET'])
def test_planner_endpoint():
    """
    A dedicated endpoint to test the plan_prompt function in isolation.
    """
    try:
        # --- 1. Define Example User Inputs (as requested) ---
        example_product_type = "Running shoes"
        example_guidelines = "Brand colors: black & red; product-human interaction- human wearing the shoe; Snow theme, Should cover the poduct 45-degree view; format: 1080x1080 for Instagram."
        example_marketing_copy = "Brand: StrideX — Limited-time 50% off this weekend! Christmas-themed ad targeting Gen Z shoppers."

        # --- 2. Choose one of our master templates to test with ---
        # We'll use the MARKETING_CREATIVE instruction for a complex test.
        #test_instruction_template = prompt_instruction_templates.MARKETING_CREATIVE_INSTRUCTION
        test_instruction_template = prompt_instruction_templates.LIFESTYLE_INSTRUCTION
        #test_instruction_template = prompt_instruction_templates.SOLID_BACKGROUND_INSTRUCTION

        # --- 3. Call our new planner function ---
        planned_prompt = plan_prompt(
            instruction_template=test_instruction_template,
            user_product_type=example_product_type,
            user_guidelines=example_guidelines,
            user_marketing_copy=example_marketing_copy
        )
        
        # --- 4. Return the result for verification ---
        return jsonify({
            "status": "success",
            "message": "Prompt planning was successful.",
            "planned_prompt_from_gemini_pro": planned_prompt
        })

    except Exception as e:
        print(f"Error in test planner endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_endpoint():
    """
    Receives user inputs, runs three generation pipelines in parallel,
    and returns the list of final image URLs.
    """
    # 1. Get user inputs from the request
    # This now expects the final frontend data structure
    image_files = request.files.getlist('images')
    product_type = request.form.get('product_type', 'default_product')
    guidelines = request.form.get('guidelines', '')
    marketing_copy = request.form.get('marketing_copy', '')

    if not image_files:
        return jsonify({"error": "At least one product image is required."}), 400

    try:
        # 2. Prepare the input images for AI (read them into memory once)
        # This list of PIL.Image objects will be shared with all threads.
        user_images_for_ai = []
        for image_file in image_files:
            image_bytes = image_file.read()
            user_images_for_ai.append(Image.open(BytesIO(image_bytes)))
            # No need to seek() as we are creating new objects for each pipeline call now

        # 3. Define the three jobs we need to run
        job_types = ['solid_background', 'lifestyle', 'marketing_creative']

        # 4. Prepare the arguments for each parallel pipeline run
        # We create a list of tuples, where each tuple contains all arguments for one pipeline call.
        job_args = []
        for job_type in job_types:
            job_args.append(
                (job_type, product_type, guidelines, marketing_copy, user_images_for_ai)
            )
            
        print(f"--- Preparing to run {len(job_types)} pipelines in parallel ---")
        
        # 5. Execute all three pipelines concurrently using ThreadPoolExecutor
        generated_urls = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # executor.map is good for a single argument. For multiple arguments,
            # we use executor.submit and a loop to get more control.
            
            # Create a future for each pipeline run
            futures = [executor.submit(run_generation_pipeline, *args) for args in job_args]
            
            # Wait for each future to complete and collect the results
            for future in concurrent.futures.as_completed(futures):
                result_url = future.result()
                if result_url: # Only add successful results
                    generated_urls.append(result_url)
        
        print(f"--- All pipelines finished. Successfully generated {len(generated_urls)} images. ---")

        # 6. Return the final list of URLs to the frontend
        return jsonify({
            "status": "success",
            "message": f"Successfully generated {len(generated_urls)} images.",
            "generated_image_urls": generated_urls
        })

    except Exception as e:
        print(f"A critical error occurred in the main generate endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)