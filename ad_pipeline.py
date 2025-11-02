"""
Main pipeline - WITH PROMPT TESTING MODE
OPTIMIZED: Forces cleanup of temp files
"""
import json
import os
import shutil
from config import (
    DEFAULT_TOTAL_DURATION, 
    DEFAULT_SEGMENT_DURATION, 
    MAX_IMAGES,
    PROMPT_ONLY_MODE,
    estimate_generation_cost
)
from gcs_utils import GCSManager
from prompt_generator_for_video import VeoPromptGenerator
from video_generator import VeoVideoGenerator
from video_merger import VideoMerger


def generate_product_video(
    image_paths, 
    product_overview, 
    brand_guidelines="", 
    total_duration=DEFAULT_TOTAL_DURATION,
    segment_duration=DEFAULT_SEGMENT_DURATION,
    prompt_only=PROMPT_ONLY_MODE
):
    """
    Generate professional E-Commerce product video
    
    Args:
        prompt_only: If True, only generate prompts (skip video generation)
    """
    # Validation
    if not image_paths or len(image_paths) == 0:
        return {"success": False, "error": "No images provided"}
    
    if len(image_paths) > MAX_IMAGES:
        return {"success": False, "error": f"Max {MAX_IMAGES} images"}
    
    print("\n" + "=" * 70)
    print("🎥 PRODUCT VIDEO GENERATION PIPELINE")
    print("=" * 70)
    print(f"📸 Images: {len(image_paths)}")
    print(f"⏱️ Duration: {total_duration}s ({total_duration//segment_duration} segments)")
    
    if prompt_only:
        print(f"🧪 MODE: PROMPT TESTING ONLY (no video generation)")
    else:
        print(f"🎬 MODE: FULL GENERATION")
        estimate_generation_cost()
    
    print("=" * 70)
    
    try:
        # STEP 1: Generate prompts
        print("\n" + "=" * 70)
        print("STEP 1: GENERATING TIMESTAMP PROMPTS")
        print("=" * 70)
        
        prompt_generator = VeoPromptGenerator()
        
        simple_prompts = prompt_generator.generate_simple_prompts(
            image_paths=image_paths,
            product_overview=product_overview,
            brand_guidelines=brand_guidelines,
            total_duration=total_duration,
            segment_duration=segment_duration
        )

        if not simple_prompts:
            return {"success": False, "error": "Prompt generation failed"}

        # Check if we should stop after prompt generation
        if prompt_only:
            print("\n✅ Prompt generation complete (prompt-only mode)")
            return {
                "success": True,
                "mode": "prompt_only",
                "prompts": simple_prompts,
                "prompt_count": len(simple_prompts),
            }

        # FULL GENERATION MODE - Continue to video generation
        print("\n🎬 Continuing to video generation...")
        
        # Initialize managers
        gcs_manager = GCSManager()
        video_generator = VeoVideoGenerator(gcs_manager=gcs_manager)
        video_merger = VideoMerger(gcs_manager=gcs_manager)
        
        # STEP 2: Upload images
        print("\n" + "=" * 70)
        print("STEP 2: UPLOADING IMAGES")
        print("=" * 70)
        
        image_gcs_uris = [gcs_manager.upload_image(img) for img in image_paths]
        
        # ===== EXTENSION MODE FORK =====
        from config import ENABLE_VIDEO_EXTENSION, EXTENSION_BASE_DURATION, EXTENSION_COUNT, EXTENSION_INCREMENT
        
        if ENABLE_VIDEO_EXTENSION:
            # EXTENSION MODE: Single video with cumulative extensions
            print("\n" + "=" * 70)
            print("STEP 3: GENERATING VIDEO WITH EXTENSIONS (REDDIT METHOD)")
            print("=" * 70)
            print("⚠️ Extension mode: Bypassing multi-segment pipeline")
            print("📌 Using first image and first prompt only")
            
            final_video_uri = video_generator.generate_with_extension(
                prompt_obj=simple_prompts[0],  # Use first prompt
                image_gcs_uri=image_gcs_uris[0],  # Use first image
                base_duration=EXTENSION_BASE_DURATION,
                extension_count=EXTENSION_COUNT,
                extension_increment=EXTENSION_INCREMENT
            )
            
            if not final_video_uri:
                return {"success": False, "error": "Extension mode generation failed"}
            
            print(f"\n✅ Extended video ready: {final_video_uri}")
            
            # No merging needed - we have one extended video
            from config import get_effective_duration
            final_duration = get_effective_duration()
            
            # Upload to final location (optional - already in GCS)
            final_video_info = {
                "gcs_uri": final_video_uri,
                "public_url": final_video_uri,  # or generate signed URL
                "duration": final_duration
            }
            
        else:
            # NORMAL MODE: Multi-segment generation + merge
            print("\n" + "=" * 70)
            print("STEP 3: GENERATING VIDEO SEGMENTS")
            print("=" * 70)
            
            video_gcs_uris = video_generator.generate_segments(
                prompts=simple_prompts,
                image_gcs_uris=image_gcs_uris
            )
            
            if not video_gcs_uris:
                return {"success": False, "error": "No segments generated"}
            
            print(f"\n✅ {len(video_gcs_uris)}/{len(simple_prompts)} segments ready")
            
            # STEP 4: Merge
            print("\n" + "=" * 70)
            print("STEP 4: MERGING SEGMENTS")
            print("=" * 70)
            
            final_video_info = video_merger.merge_with_transitions(
                video_gcs_uris=video_gcs_uris,
                output_filename=f"final_product_video_{total_duration}s.mp4"
            )
            
            if not final_video_info:
                return {"success": False, "error": "Merge failed"}
        
        # ===== END FORK =====
        
        # CRITICAL: Force cleanup of any remaining temp files
        _force_cleanup_temp_files()

        print("\n" + "=" * 70)
        print("🎉 VIDEO GENERATION COMPLETE")
        print("=" * 70)
        
        mode_label = "EXTENSION" if ENABLE_VIDEO_EXTENSION else "MULTI-SEGMENT"
        print(f"🎬 Mode: {mode_label}")
        
        if not ENABLE_VIDEO_EXTENSION:
            print(f"📁 All files organized in: {gcs_manager.request_folder}")
            print(f"🎬 Segments folder: {gcs_manager.segments_folder}")
        
        print(f"📹 Final video: {final_video_info['public_url']}")
        print("=" * 70)

        return {
            "success": True,
            "mode": "extension" if ENABLE_VIDEO_EXTENSION else "full_generation",
            "final_video_url": final_video_info["public_url"],
            "gcs_uri": final_video_info["gcs_uri"],
            "request_folder": gcs_manager.request_folder if not ENABLE_VIDEO_EXTENSION else "N/A",
            "request_id": gcs_manager.request_id,
            "segments_folder": gcs_manager.segments_folder if not ENABLE_VIDEO_EXTENSION else "N/A",
            "segment_count": 1 if ENABLE_VIDEO_EXTENSION else len(video_gcs_uris),
            "duration": final_video_info.get("duration", total_duration),
        }
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Ensure cleanup even on error
        _force_cleanup_temp_files()
        
        return {"success": False, "error": str(e)}


def _force_cleanup_temp_files():
    """
    Delete temporary files, respecting TESTING_MODE for final videos.
    ALWAYS deletes: temp segments, temp audio
    CONDITIONALLY deletes: final merged videos (only in production)
    NEVER deletes: prompt logs (.txt, .json)
    """
    from config import TESTING_MODE
    import glob
    
    # Always delete these (intermediate files)
    always_delete_patterns = [
        'temp_segment_*.mp4',
        'temp_single_*.mp4',
        'temp_audio*.m4a',
    ]
    
    # Only delete in production
    conditional_delete_patterns = [
        'final_product_video_*.mp4'
    ]
    
    deleted = []
    
    # Always delete temp files
    for pattern in always_delete_patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                deleted.append(file)
            except:
                pass
    
    # Conditionally delete final videos
    if not TESTING_MODE:
        for pattern in conditional_delete_patterns:
            for file in glob.glob(pattern):
                try:
                    os.remove(file)
                    deleted.append(file)
                except:
                    pass
    
    if deleted:
        print(f"\n🗑️ Force cleanup: Deleted {len(deleted)} temp file(s)")
    
    if TESTING_MODE:
        kept_finals = glob.glob('final_product_video_*.mp4')
        if kept_finals:
            print(f"🧪 TESTING_MODE: Kept {len(kept_finals)} final video(s) locally")

if __name__ == "__main__":
    test_image_paths = [r"E:\product-image-backend\test_images\faucet_plantex.png"]
    #r"E:\product-image-backend\test_images\snow_blower_1.png",
    #r"E:\product-image-backend\test_images\snow_blower_2.png"]
    
    test_product_overview = """
𝐏𝐢𝐥𝐥𝐚𝐫 𝐓𝐚𝐩𝐬: 𝐄𝐚𝐬𝐲 𝐔𝐬𝐞: Pillar taps are ideal for use with both wash basins and sinks, offering flexibility in bathroom and kitchen designs. Their installation on the countertop provides easy access and convenient water control, enhancing the overall user experience.
𝐆𝐞𝐫𝐦𝐚𝐧 𝐀𝐞𝐫𝐚𝐭𝐨𝐫: The German aerator in this washbasin tap provides splash-free water. It is also easily removable for cleaning. The aerator helps to save water, which can lower your water bill.
𝐅𝐨𝐚𝐦 𝐅𝐥𝐨𝐰 - The foam flow in this basin tap ensures a smooth and streamlined flow of water. This makes the tap more efficient and helps to prevent splashing. The silver finish of the tap adds a– modern touch to your bathroom.
𝐒𝐩𝐢𝐧𝐝𝐥𝐞: This washbasin faucet features a Brass spindle that prevents leaks and resists wear. The exterior finish is also corrosion-resistant, ideal for tough water conditions. This double defense ensures long life and saves on future plumbing costs.
𝐏𝐚𝐜𝐤𝐚𝐠𝐞 𝐂𝐨𝐧𝐭𝐚𝐢𝐧𝐬 : The package includes 1-piece pillar cock tap (Short Body-Quarter Turn Tap), free Teflon tape.
𝐄𝐟𝐟𝐨𝐫𝐭𝐥𝐞𝐬𝐬 𝐌𝐚𝐢𝐧𝐭𝐞𝐧𝐚𝐧𝐜𝐞: This pillar tap for wash basin is easy to clean. Simply wipe it with a clean towel; no detergent is needed. These taps are designed for a stress-free experience.
𝐏𝐥𝐚𝐧𝐭𝐞𝐱: 𝐃𝐞𝐝𝐢𝐜𝐚𝐭𝐞𝐝 𝐭𝐨 𝐲𝐨𝐮𝐫 𝐡𝐚𝐩𝐩𝐢𝐧𝐞𝐬𝐬: At Plantex, we prioritize your complete contentment. Our products are designed to ensure that you have the best experience possible when it comes to upgrading your home. For any questions or assistance, please feel free to contact us.
"""
    """
    Winter is no match for the Toro 60v Power Max e24 two stage snow blower. We combine our no compromises steel built construction with up to three ports to give you the muscle to power through the toughest snow. Big driveway no worries. We can easily clear up to 24 car spaces on one charge and with a third battery slot, you can add another 4 to 15 car spaces. With our 24 inches wide clearing width and 20 inch intake height, you will make quick work of even the deepest snow. The innovative quick stick control allows you to change the steel chute direction and chute deflector with a single, smooth motion. Convenient one hand operation levers allow single handed use, freeing the other hand to change speeds or the chute control without stopping. The exclusive anti clogging system monitors snow intake to reduce clogging and maximize clearing efficiency. Toro uses bolts that are 2x stronger than the competition's shear pins. The blower is also equipped with hardened gears in your auger gearbox, in other words, no shear pins to replace. Ideal for concrete, asphalt and gravel surfaces.
    Identical to the gas two stage in every way, except the gas
    Night Vision have a brighter and broader view with the panoramic LED lighting
    Clears up to 20 car spaces in up to 10 inches of snow with the included 10.0Ah battery.
    Quickly and easily cut through snow with total speed control, 6 speeds forward and 2 speeds reverse
    Minimizes clogging and routes heavy snow away from chute and back into the auger
    With Toros quick stick chute control, you can aim for the exact spot where you want to put snow while keeping it from blowing into your face
    """
    
    test_brand_guidelines = "Brand colors: Toro red, black, metallic gray. Modern. Add These Features as text: 'Toughened Steel Body', '10.0Ah Battery' "
    
    result = generate_product_video(
        image_paths=test_image_paths,
        product_overview=test_product_overview,
        brand_guidelines=test_brand_guidelines
    )
    
    if result["success"]:
        print("\n✅ PIPELINE COMPLETE!")
        if result.get("mode") == "prompt_only":
            print(f"📝 Prompts generated and saved")
        else:
            print(f"🔗 Video URL: {result['final_video_url']}")
    else:
        print(f"\n❌ FAILED: {result['error']}")