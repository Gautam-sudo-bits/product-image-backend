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

# --- Configuration ---
load_dotenv()
app = Flask(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/api/generate', methods=['POST'])
def generate_endpoint():
    if 'image' not in request.files or 'formData' not in request.form:
        return jsonify({"error": "Missing image or form data"}), 400

    image_file = request.files['image']
    form_data = json.loads(request.form['formData'])

    try:
        # 1. Upload USER'S input image to Cloudinary
        print("Uploading user's input image to Cloudinary...")
        upload_result = cloudinary.uploader.upload(image_file, folder="product-image-inputs")
        input_image_url = upload_result['secure_url']
        print(f"Input image URL: {input_image_url}")

        # 2. Create the detailed text prompt
        prompt = f"""
        Analyze the user-provided product image. Then, create a new, professional, ultra-realistic e-commerce photograph for this '{form_data['category']}' product.
        Desired composition: '{form_data['composition']}'. Background: '{form_data['background']}'.
        Lighting: '{form_data['lighting']}'. Camera angle: '{form_data['angle']}'.
        Additional creative direction: '{form_data['details']}'.
        The final image must be clean, high-resolution (4K), photorealistic, and ready for an e-commerce listing.
        """
        print(f"Generated Prompt: {prompt}")

        # --- NEW & CORRECTED GEMINI LOGIC ---

        # 3. Fetch the input image from Cloudinary to create a local copy in memory
        print("Fetching image from Cloudinary URL for Gemini...")
        image_response = requests.get(input_image_url)
        # Ensure the request was successful
        image_response.raise_for_status() 
        # Open the image from the raw byte content
        input_image_for_gemini = Image.open(BytesIO(image_response.content))
        print("Successfully prepared input image for the model.")

        # 4. Initialize the correct model and prepare the contents list
        # Using the standard genai.GenerativeModel approach
        model = genai.GenerativeModel('gemini-2.5-flash-image')
        
        # The 'contents' list must contain the prompt and the image object, in order.
        contents = [prompt, input_image_for_gemini]

        # 5. Call the Gemini API with the correct contents structure
        print("Calling Gemini API...")
        response = model.generate_content(contents)
        print("Received response from Gemini API.")
        
        # 6. Process the response exactly as in the official documentation
        # This loop finds the part of the response that contains the generated image data
        generated_image_bytes = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                generated_image_bytes = part.inline_data.data
                break # Exit the loop once we find the image
        
        if generated_image_bytes is None:
            raise ValueError("No image data received from Gemini API.")
        
        print("Extracted generated image bytes from response.")

        # 7. Upload the GENERATED image bytes to Cloudinary
        print("Uploading generated image to Cloudinary...")
        generated_upload_result = cloudinary.uploader.upload(
            generated_image_bytes,
            folder="product-image-outputs",
            public_id=f"gen_{upload_result['public_id']}"
        )
        generated_image_url = generated_upload_result['secure_url']
        print(f"Successfully uploaded generated image. Final URL: {generated_image_url}")
        
        # 8. Send the final URL back to the frontend
        return jsonify({
            "status": "success",
            "message": "Image generated and stored successfully.",
            "generated_image_url": generated_image_url
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An internal server error occurred while generating the image."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)