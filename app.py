# app.py (Clean endpoint architecture)
import os
import json
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import google.generativeai as genai
import cloudinary
from pathlib import Path
import tempfile

# Import pipelines
from image_pipeline import generate_images
from ad_pipeline import generate_product_video
from config import ENABLE_PROMPT_VIEW, PROMPT_DISPLAY_FILE

load_dotenv()
app = Flask(__name__)
CORS(app)

# --- Configuration ---
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


@app.route('/api/generate', methods=['POST'])
def generate_images_endpoint():
    """
    Image generation endpoint - calls image_pipeline module
    """
    image_files = request.files.getlist('images')
    product_type = request.form.get('product_type', 'default_product')
    guidelines = request.form.get('guidelines', '')
    marketing_copy = request.form.get('marketing_copy', '')

    if not image_files:
        return jsonify({"error": "At least one product image is required."}), 400

    try:
        user_images_bytes_list = [img.read() for img in image_files]
        
        # Call image pipeline
        result = generate_images(
            product_type=product_type,
            guidelines=guidelines,
            marketing_copy=marketing_copy,
            user_images_bytes_list=user_images_bytes_list
        )
        
        if result["success"]:
            return jsonify({
                "status": "success",
                "message": result["message"],
                "generated_image_urls": result["generated_image_urls"]
            })
        else:
            return jsonify({"error": "Image generation failed"}), 500

    except Exception as e:
        print(f"Error in image generation endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route('/api/generate-video', methods=['POST'])
def generate_video_endpoint():
    """
    Video generation endpoint - calls ad_pipeline module
    """
    temp_dir = None
    try:
        # Get uploaded images
        image_files = request.files.getlist('images')
        if not image_files:
            return jsonify({"error": "At least one product image is required."}), 400
        
        # Get text inputs
        product_overview = request.form.get('product_overview', '')
        brand_guidelines = request.form.get('brand_guidelines', '')
        
        if not product_overview:
            return jsonify({"error": "Product overview is required."}), 400
        
        # Save uploaded images temporarily
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='product_images_')
        image_paths = []
        
        for i, img_file in enumerate(image_files):
            temp_path = os.path.join(temp_dir, f"product_image_{i}.png")
            img_file.save(temp_path)
            image_paths.append(temp_path)
        
        print(f"Saved {len(image_paths)} images to temporary directory: {temp_dir}")
        
        # Call video generation pipeline
        result = generate_product_video(
            image_paths=image_paths,
            product_overview=product_overview,
            brand_guidelines=brand_guidelines
        )
        
        if result["success"]:
            response_data = {
                "status": "success",
                "video_url": result.get("final_video_url"),
                "request_id": result.get("request_id"),
                "duration": result.get("duration"),
                "segment_count": result.get("segment_count")
            }
            
            # Include prompt data if available
            if ENABLE_PROMPT_VIEW and result.get("mode") != "prompt_only":
                response_data["prompt_available"] = True
            
            return jsonify(response_data)
        else:
            return jsonify({"error": result.get("error", "Video generation failed")}), 500
            
    except Exception as e:
        print(f"Error in video generation endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
    finally:
        # CRITICAL: Always cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"🗑️ Cleaned up temp directory: {temp_dir}")


@app.route('/api/get-prompt', methods=['GET'])
def get_prompt_endpoint():
    """
    Retrieve the latest generated prompt from JSON file
    Controlled by ENABLE_PROMPT_VIEW flag in config
    """
    if not ENABLE_PROMPT_VIEW:
        return jsonify({"error": "Prompt viewing is disabled"}), 403
    
    try:
        prompt_file_path = Path(PROMPT_DISPLAY_FILE)
        
        if not prompt_file_path.exists():
            return jsonify({"error": "No prompts available yet"}), 404
        
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        
        return jsonify({
            "status": "success",
            "prompt_data": prompt_data
        })
        
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid prompt file format"}), 500
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        return jsonify({"error": "Failed to retrieve prompt"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "Product Creative Generator",
        "features": {
            "image_generation": True,
            "video_generation": True,
            "prompt_view": ENABLE_PROMPT_VIEW
        }
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)