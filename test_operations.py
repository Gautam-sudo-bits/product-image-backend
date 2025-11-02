"""
Automated Operation Testing Script - TWO STAGE PROCESS
Stage 1: Download images only (preview before testing)
Stage 2: Run API tests on validated images (costs API credits)
"""
import os
import sys
import time
import requests
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from operations_config import OPERATIONS, get_test_image_type
from config import UNSPLASH_ACCESS_KEY, TEST_IMAGES_FOLDER, TEST_OUTPUTS_FOLDER, USE_UNSPLASH_FALLBACK

# ===========================
# CONFIGURATION
# ===========================

TEST_IMAGES_DIR = TEST_IMAGES_FOLDER
TEST_OUTPUTS_DIR = TEST_OUTPUTS_FOLDER
IMAGE_PREVIEW_REPORT = "downloaded_images_report.txt"
FINAL_TEST_REPORT = "test_report.txt"
API_ENDPOINT = "http://localhost:5001/api/edit-image"

# Fallback hardcoded images (used only if Unsplash fails)
HARDCODED_IMAGES = {
    "product_tool": "https://images.pexels.com/photos/1249611/pexels-photo-1249611.jpeg?auto=compress&cs=tinysrgb&w=1260",
    "furniture_chair": "https://images.pexels.com/photos/116910/pexels-photo-116910.jpeg?auto=compress&cs=tinysrgb&w=1260",
    "electronics_laptop": "https://images.pexels.com/photos/18105/pexels-photo.jpg?auto=compress&cs=tinysrgb&w=1260",
    "apparel_tshirt": "https://images.pexels.com/photos/8532616/pexels-photo-8532616.jpeg?auto=compress&cs=tinysrgb&w=1260",
    "beauty_bottle": "https://images.pexels.com/photos/3685523/pexels-photo-3685523.jpeg?auto=compress&cs=tinysrgb&w=1260",
    "product_snowblower": "https://images.pexels.com/photos/209224/pexels-photo-209224.jpeg?auto=compress&cs=tinysrgb&w=1260",
    "product_generic": "https://images.pexels.com/photos/90946/pexels-photo-90946.jpeg?auto=compress&cs=tinysrgb&w=1260"
}

# Improved Unsplash queries for better product images
UNSPLASH_QUERIES = {
    "product_tool": "power drill product photography white background",
    "furniture_chair": "modern chair product studio photography",
    "electronics_laptop": "laptop computer product white background",
    "apparel_tshirt": "white tshirt product flat lay",
    "beauty_bottle": "cosmetic bottle product photography",
    "product_snowblower": "snow blower product photography",
    "product_generic": "product photography white background studio"
}

# ===========================
# IMAGE DOWNLOAD FUNCTIONS
# ===========================

def download_image_from_url(url, save_path):
    """Download image from URL"""
    try:
        print(f"   📥 Downloading from URL...")
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            # Verify it's a valid image
            from PIL import Image
            try:
                img = Image.open(save_path)
                img.verify()
                print(f"   ✅ Saved: {os.path.basename(save_path)} ({img.size[0]}x{img.size[1]})")
                return True
            except:
                os.remove(save_path)
                print(f"   ❌ Invalid image file")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def download_from_unsplash(image_type, save_path):
    """Download from Unsplash API with better query"""
    if not UNSPLASH_ACCESS_KEY:
        print(f"   ⚠️ No Unsplash API key configured in .env")
        print(f"      Add: UNSPLASH_ACCESS_KEY=your_key_here")
        return False
    
    query = UNSPLASH_QUERIES.get(image_type, "product photography")
    
    try:
        print(f"   🔍 Searching Unsplash: '{query}'...")
        
        # Use search endpoint for better results
        url = f"https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        params = {
            "query": query,
            "per_page": 5,  # Get multiple options
            "orientation": "landscape"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                print(f"   ⚠️ No results for query: {query}")
                return False
            
            # Try the first result
            image_url = results[0]['urls']['regular']
            photographer = results[0]['user']['name']
            
            print(f"   📷 Found image by {photographer}")
            
            # Download the image
            img_response = requests.get(image_url, timeout=15)
            if img_response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(img_response.content)
                
                # Verify it's valid
                from PIL import Image
                try:
                    img = Image.open(save_path)
                    img.verify()
                    print(f"   ✅ Downloaded: {os.path.basename(save_path)} ({img.size[0]}x{img.size[1]})")
                    return True
                except:
                    os.remove(save_path)
                    print(f"   ❌ Invalid image")
                    return False
        
        print(f"   ❌ Unsplash API error: {response.status_code}")
        if response.status_code == 403:
            print(f"      Check your API key is correct")
        return False
        
    except Exception as e:
        print(f"   ❌ Unsplash error: {e}")
        return False

def download_image_for_operation(image_type, operation_id):
    """Download image for a specific operation"""
    filename = f"op{operation_id:02d}_{image_type}.jpg"
    filepath = os.path.join(TEST_IMAGES_DIR, filename)
    
    # If already exists, skip
    if os.path.exists(filepath):
        print(f"   ✓ Already exists: {filename}")
        return filepath
    
    success = False
    
    # Primary source based on flag
    if USE_UNSPLASH_FALLBACK and UNSPLASH_ACCESS_KEY:
        # Try Unsplash FIRST
        print(f"   Primary: Unsplash (USE_UNSPLASH_FALLBACK=True)")
        success = download_from_unsplash(image_type, filepath)
        
        # Fallback to hardcoded if Unsplash fails
        if not success and image_type in HARDCODED_IMAGES:
            print(f"   🔄 Falling back to hardcoded URL...")
            url = HARDCODED_IMAGES[image_type]
            success = download_image_from_url(url, filepath)
    else:
        # Try hardcoded FIRST
        print(f"   Primary: Hardcoded URLs (USE_UNSPLASH_FALLBACK=False)")
        if image_type in HARDCODED_IMAGES:
            url = HARDCODED_IMAGES[image_type]
            success = download_image_from_url(url, filepath)
        
        # Fallback to Unsplash if hardcoded fails
        if not success and UNSPLASH_ACCESS_KEY:
            print(f"   🔄 Falling back to Unsplash...")
            success = download_from_unsplash(image_type, filepath)
    
    if success:
        return filepath
    else:
        print(f"   ❌ Failed to download image for {image_type}")
        return None

# ===========================
# STAGE 1: DOWNLOAD IMAGES
# ===========================

def download_all_images():
    """Stage 1: Download all test images"""
    print("\n" + "=" * 80)
    print("📥 STAGE 1: DOWNLOADING TEST IMAGES")
    print("=" * 80)
    print("This will download images for all 38 operations.")
    print("NO API CALLS will be made to your backend (no cost).")
    
    if USE_UNSPLASH_FALLBACK:
        print("🔍 Primary source: Unsplash API (better quality)")
        if not UNSPLASH_ACCESS_KEY:
            print("⚠️  WARNING: No Unsplash API key found!")
            print("   Will try hardcoded URLs only.")
            print("   Add UNSPLASH_ACCESS_KEY to .env for better images.")
    else:
        print("📦 Primary source: Hardcoded URLs")
    
    print("=" * 80 + "\n")
    
    os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
    
    downloaded = []
    failed = []
    
    # Track unique image types needed
    image_types_needed = {}
    for op_id, operation in OPERATIONS.items():
        img_type = get_test_image_type(op_id)
        if img_type not in image_types_needed:
            image_types_needed[img_type] = []
        image_types_needed[img_type].append(op_id)
    
    print(f"📊 Unique image types needed: {len(image_types_needed)}")
    print(f"📋 Total operations: 38")
    print(f"💡 Smart downloading: Same image reused for multiple operations\n")
    
    # Download unique images only
    downloaded_types = set()
    
    for op_id in sorted(OPERATIONS.keys()):
        operation = OPERATIONS[op_id]
        image_type = get_test_image_type(op_id)
        
        print(f"[{op_id:02d}] {operation['name']}")
        print(f"     Image type: {image_type}")
        
        # Skip if we already downloaded this image type
        if image_type in downloaded_types:
            filename = f"op{op_id:02d}_{image_type}.jpg"
            filepath = os.path.join(TEST_IMAGES_DIR, filename)
            
            # Find the source file (first operation with this type)
            source_op_id = image_types_needed[image_type][0]
            source_filename = f"op{source_op_id:02d}_{image_type}.jpg"
            source_filepath = os.path.join(TEST_IMAGES_DIR, source_filename)
            
            if os.path.exists(source_filepath):
                # Create symbolic link or copy
                import shutil
                try:
                    shutil.copy(source_filepath, filepath)
                    print(f"   ✓ Reusing: {source_filename}")
                    downloaded.append((op_id, filepath))
                except:
                    print(f"   ⚠️ Failed to copy, will download separately")
                    filepath = download_image_for_operation(image_type, op_id)
                    if filepath:
                        downloaded.append((op_id, filepath))
                    else:
                        failed.append(op_id)
            else:
                filepath = download_image_for_operation(image_type, op_id)
                if filepath:
                    downloaded.append((op_id, filepath))
                else:
                    failed.append(op_id)
        else:
            # Download new image
            filepath = download_image_for_operation(image_type, op_id)
            
            if filepath:
                downloaded.append((op_id, filepath))
                downloaded_types.add(image_type)
            else:
                failed.append(op_id)
        
        print()  # Blank line
        time.sleep(0.5)  # Small delay to avoid rate limits
    
    # Generate preview report
    generate_image_preview_report(downloaded, failed, image_types_needed)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ STAGE 1 COMPLETE - IMAGE DOWNLOAD")
    print("=" * 80)
    print(f"Successfully downloaded: {len(downloaded)}/38")
    print(f"Failed: {len(failed)}/38")
    print(f"Unique images downloaded: {len(downloaded_types)}")
    print(f"\nImages saved in: {TEST_IMAGES_DIR}/")
    print(f"\nNEXT STEPS:")
    print(f"1. Open folder: {TEST_IMAGES_DIR}/")
    print(f"2. Preview each image to ensure quality")
    print(f"3. If any image is unsuitable:")
    print(f"   - Delete it")
    print(f"   - Download better one manually")
    print(f"   - Keep same filename (e.g., op01_product_tool.jpg)")
    print(f"4. When satisfied, run: python test_operations.py test")
    print("=" * 80 + "\n")

def generate_image_preview_report(downloaded, failed, image_types_needed):
    """Generate report of downloaded images"""
    lines = []
    lines.append("=" * 80)
    lines.append("DOWNLOADED IMAGES PREVIEW REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")
    lines.append("INSTRUCTIONS:")
    lines.append(f"1. Open the '{TEST_IMAGES_DIR}/' folder")
    lines.append("2. Preview each image for quality and relevance")
    lines.append("3. If unsuitable:")
    lines.append("   - Delete the bad image")
    lines.append("   - Download a better one manually")
    lines.append("   - Save with EXACT same filename")
    lines.append("4. When ready, run: python test_operations.py test")
    lines.append("")
    lines.append("=" * 80)
    lines.append("IMAGE MAPPING (Which operations use which images)")
    lines.append("=" * 80)
    lines.append("")
    
    for img_type, op_ids in sorted(image_types_needed.items()):
        lines.append(f"Image Type: {img_type}")
        lines.append(f"Used by {len(op_ids)} operation(s): {', '.join(str(x) for x in op_ids)}")
        
        # Find the file
        sample_op = op_ids[0]
        filename = f"op{sample_op:02d}_{img_type}.jpg"
        filepath = os.path.join(TEST_IMAGES_DIR, filename)
        
        if os.path.exists(filepath):
            # Get image dimensions
            try:
                from PIL import Image
                img = Image.open(filepath)
                dimensions = f"{img.size[0]}x{img.size[1]}"
                lines.append(f"File: {filename} ✅ ({dimensions})")
            except:
                lines.append(f"File: {filename} ✅")
        else:
            lines.append(f"File: {filename} ❌ MISSING - needs manual download")
        
        lines.append("")
    
    if failed:
        lines.append("=" * 80)
        lines.append("⚠️  FAILED DOWNLOADS - Manual Action Required")
        lines.append("=" * 80)
        lines.append("These images failed to download. Please download manually:")
        lines.append("")
        for op_id in failed:
            operation = OPERATIONS[op_id]
            img_type = get_test_image_type(op_id)
            filename = f"op{op_id:02d}_{img_type}.jpg"
            lines.append(f"[{op_id:02d}] {operation['name']}")
            lines.append(f"      Filename: {filename}")
            lines.append(f"      Type: {img_type}")
            lines.append("")
    
    lines.append("=" * 80)
    
    with open(IMAGE_PREVIEW_REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n✅ Preview report saved: {IMAGE_PREVIEW_REPORT}")

# ===========================
# STAGE 2: RUN API TESTS
# ===========================

def test_single_operation(operation_id):
    """Test one operation using API"""
    operation = OPERATIONS.get(operation_id)
    if not operation:
        return {"status": "ERROR", "error": "Operation not found"}
    
    # Check if test image exists
    image_type = get_test_image_type(operation_id)
    filename = f"op{operation_id:02d}_{image_type}.jpg"
    image_path = os.path.join(TEST_IMAGES_DIR, filename)
    
    if not os.path.exists(image_path):
        return {
            "status": "ERROR",
            "error": f"Test image not found: {filename}",
            "image_path": None
        }
    
    print(f"   📷 Using: {filename}")
    
    try:
        print(f"   📤 Calling API...")
        
        with open(image_path, 'rb') as img_file:
            files = {'image': img_file}
            data = {'operation_id': operation_id}
            
            response = requests.post(
                API_ENDPOINT,
                files=files,
                data=data,
                timeout=120
            )
        
        if response.status_code == 200:
            result = response.json()
            edited_url = result.get('edited_image_url')
            
            # Download result
            output_filename = f"op{operation_id:02d}_output.jpg"
            output_path = os.path.join(TEST_OUTPUTS_DIR, output_filename)
            
            print(f"   📥 Downloading result...")
            img_response = requests.get(edited_url, timeout=30)
            
            if img_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                
                print(f"   ✅ Success: {output_filename}")
                
                return {
                    "status": "SUCCESS",
                    "output_path": output_path,
                    "image_path": image_path
                }
            else:
                return {
                    "status": "ERROR",
                    "error": "Failed to download result",
                    "image_path": image_path
                }
        else:
            error_msg = response.json().get('error', 'Unknown error')
            print(f"   ❌ API Error: {error_msg}")
            return {
                "status": "ERROR",
                "error": error_msg,
                "image_path": image_path
            }
    
    except requests.exceptions.Timeout:
        print(f"   ⏱️ Timeout")
        return {"status": "ERROR", "error": "Timeout", "image_path": image_path}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"status": "ERROR", "error": str(e), "image_path": image_path}

def run_api_tests():
    """Stage 2: Run API tests on downloaded images"""
    print("\n" + "=" * 80)
    print("🧪 STAGE 2: RUNNING API TESTS")
    print("=" * 80)
    print("This will test all 38 operations using the downloaded images.")
    print("⚠️  WARNING: This will use API credits and cost money!")
    print("Estimated time: 8-15 minutes")
    print("=" * 80 + "\n")
    
    # Check if images exist
    if not os.path.exists(TEST_IMAGES_DIR):
        print("❌ No test images found!")
        print(f"   Run first: python test_operations.py download")
        return
    
    # Count available images
    image_count = len([f for f in os.listdir(TEST_IMAGES_DIR) if f.endswith('.jpg')])
    print(f"📊 Found {image_count} test images in {TEST_IMAGES_DIR}/")
    
    if image_count < 38:
        print(f"⚠️  Warning: Expected 38 images, found {image_count}")
        response = input("Continue anyway? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Cancelled")
            return
    
    # Check backend
    try:
        health_response = requests.get("http://localhost:5001/health", timeout=5)
        if health_response.status_code != 200:
            raise Exception("Backend not healthy")
        print("✅ Backend is running\n")
    except:
        print("❌ Backend not running!")
        print("   Start it first: python app.py")
        return
    
    # Confirm before proceeding
    print("=" * 80)
    response = input("⚠️  Proceed with API testing? This will cost money! (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Cancelled")
        return
    
    os.makedirs(TEST_OUTPUTS_DIR, exist_ok=True)
    
    results = {}
    successful = 0
    failed = 0
    
    start_time = time.time()
    
    print("\n" + "=" * 80)
    print("Starting tests...")
    print("=" * 80 + "\n")
    
    # Test each operation
    for op_id in sorted(OPERATIONS.keys()):
        operation = OPERATIONS[op_id]
        print(f"[{op_id:02d}] {operation['name']}")
        
        result = test_single_operation(op_id)
        results[op_id] = result
        
        if result['status'] == 'SUCCESS':
            successful += 1
        else:
            failed += 1
        
        print()  # Blank line
        time.sleep(2)  # Rate limiting
    
    elapsed = time.time() - start_time
    
    # Generate validation report
    generate_validation_report(results)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ STAGE 2 COMPLETE - API TESTING")
    print("=" * 80)
    print(f"Total Time: {elapsed/60:.1f} minutes")
    print(f"Successfully Generated: {successful}/38")
    print(f"Failed/Errors: {failed}/38")
    print("")
    print("NEXT STEPS:")
    print(f"1. Open '{FINAL_TEST_REPORT}' in text editor")
    print(f"2. Review output images in '{TEST_OUTPUTS_DIR}/'")
    print("3. Compare each output with its input")
    print("4. Fill in PASS or FAIL for each operation")
    print("5. Save the file")
    print("6. Run: python update_frontend_operations.py test_report.txt")
    print("=" * 80 + "\n")

def generate_validation_report(results):
    """Generate report for manual validation"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = []
    lines.append("=" * 80)
    lines.append("NANO BANANA OPERATION TEST REPORT")
    lines.append(f"Generated: {timestamp}")
    lines.append("=" * 80)
    lines.append("")
    lines.append("VALIDATION INSTRUCTIONS:")
    lines.append("1. Open each output image in test_outputs/")
    lines.append("2. Compare with original in test_images/")
    lines.append("3. Did the operation work as expected?")
    lines.append("4. Enter PASS or FAIL in the [STATUS] field below")
    lines.append("5. Save this file when done")
    lines.append("6. Run: python update_frontend_operations.py test_report.txt")
    lines.append("")
    lines.append(f"Test Images: {TEST_IMAGES_DIR}/")
    lines.append(f"Output Images: {TEST_OUTPUTS_DIR}/")
    lines.append("")
    lines.append("=" * 80)
    lines.append("TEST RESULTS - FILL IN STATUS FOR EACH")
    lines.append("=" * 80)
    lines.append("")
    
    for op_id in sorted(OPERATIONS.keys()):
        operation = OPERATIONS[op_id]
        result = results.get(op_id, {"status": "NOT_TESTED"})
        
        lines.append(f"[{op_id:02d}] {operation['name']}")
        
        if result['status'] == 'SUCCESS':
            lines.append(f"      Input: {result.get('image_path', 'N/A')}")
            lines.append(f"      Output: {result.get('output_path', 'N/A')}")
            lines.append(f"      STATUS: [        ]  ← Enter PASS or FAIL here")
        else:
            error = result.get('error', 'Unknown')
            lines.append(f"      ❌ Test Error: {error}")
            lines.append(f"      STATUS: [  SKIP  ]  ← Test failed to run")
        
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("SUMMARY (Auto-calculated when you run update script)")
    lines.append("=" * 80)
    lines.append("")
    
    with open(FINAL_TEST_REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n✅ Validation report saved: {FINAL_TEST_REPORT}")

# ===========================
# MAIN
# ===========================

def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("\n" + "=" * 80)
        print("NANO BANANA OPERATION TESTING - TWO-STAGE PROCESS")
        print("=" * 80)
        print("")
        print("USAGE:")
        print("  python test_operations.py download   ← Stage 1: Download test images")
        print("  python test_operations.py test       ← Stage 2: Run API tests (costs $)")
        print("")
        print("CONFIGURATION:")
        print(f"  Primary source: {'Unsplash' if USE_UNSPLASH_FALLBACK else 'Hardcoded URLs'}")
        if USE_UNSPLASH_FALLBACK:
            if UNSPLASH_ACCESS_KEY:
                print(f"  Unsplash API: ✅ Configured")
            else:
                print(f"  Unsplash API: ❌ Not configured (add to .env)")
        print("")
        print("=" * 80 + "\n")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'download':
        download_all_images()
    elif command == 'test':
        run_api_tests()
    else:
        print(f"❌ Unknown command: {command}")
        print("   Use: download or test")

if __name__ == "__main__":
    main()

# Stage 1: Download images (no cost)
#python test_operations.py download

# Stage 2: Test with API (costs money)
#python app.py                    # Terminal 1
#python test_operations.py test

# Stage 3: Update frontend
#python update_frontend_operations.py test_report.txt