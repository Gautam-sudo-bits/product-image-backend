import os
import cloudinary
import cloudinary.uploader
import requests
from dotenv import load_dotenv

# Load Cloudinary credentials securely
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY_2"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET_2")
)

def convert_webp_to_png(input_dir, output_dir):
    """
    Converts all .webp images in input_dir to .png using Cloudinary.
    Saves the PNGs to output_dir.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".webp"):
            local_path = os.path.join(input_dir, filename)
            print(f"Uploading and converting: {filename}")

            try:
                # Upload image to Cloudinary (without auto format)
                upload_result = cloudinary.uploader.upload(local_path, resource_type="image")

                # Get public_id to use for transformation
                public_id = upload_result['public_id']

                # Generate PNG URL using Cloudinary transformation
                png_url = cloudinary.CloudinaryImage(public_id).build_url(format="png")

                # Download the transformed PNG image
                response = requests.get(png_url)
                if response.status_code == 200:
                    output_path = os.path.join(output_dir, os.path.splitext(filename)[0] + ".png")
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    print(f"✅ Saved converted image: {output_path}")
                else:
                    print(f"❌ Failed to download converted image for {filename}")

            except Exception as e:
                print(f"⚠️ Error processing {filename}: {e}")

if __name__ == "__main__":
    # Example usage
    input_folder = r"C:\Users\furry\Downloads\www.watchstationindia.com-1760251861381"   
    output_folder = r"E:\product-image-backend\brand_assets\images"
    convert_webp_to_png(input_folder, output_folder)
