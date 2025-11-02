"""
Veo Video Generator - Generic Prompt Passthrough
Passes LLM-generated prompts to Veo API without assumptions about structure
"""
import time
import json
from google import genai
from google.genai import types
from config import VIDEO_MODEL, ALLOW_PEOPLE_IN_VIDEO, GENERATE_AUDIO, VIDEO_RESOLUTION


class VeoVideoGenerator:
    """Generates videos using LLM prompts (any format)"""
    
    def __init__(self, model=VIDEO_MODEL, gcs_manager=None):
        self.client = genai.Client()
        self.model = model
        self.gcs_manager = gcs_manager
    
    def _prepare_prompt_for_veo(self, prompt_obj, context=""):
        """
        Generic prompt preparation - NO assumptions about LLM output structure
        
        Only removes pipeline metadata (segment_number, duration).
        Keeps ALL LLM-generated content intact.
        
        Args:
            prompt_obj: LLM output (string, dict, or any format)
            context: Label for logging (e.g., "Segment 1", "Base Video")
        
        Returns:
            String prompt ready for Veo API, or None if invalid
        """
        print(f"\n{'🔍 PROMPT PREP: ' + context + ' '.ljust(70, '=')}")
        print(f"📥 Input type: {type(prompt_obj).__name__}")
        
        # Case 1: Already a string (LLM returned plain text)
        if isinstance(prompt_obj, str):
            veo_prompt = prompt_obj
            print(f"✓ Plain text prompt, using as-is")
        
        # Case 2: Dictionary (LLM returned structured JSON)
        elif isinstance(prompt_obj, dict):
            # Copy to avoid modifying original
            prompt_dict = prompt_obj.copy()
            
            # ONLY remove our pipeline metadata (not LLM keys!)
            pipeline_metadata = ['segment_number', 'duration']
            removed = []
            
            for key in pipeline_metadata:
                if key in prompt_dict:
                    prompt_dict.pop(key)
                    removed.append(key)
            
            if removed:
                print(f"✓ Removed pipeline metadata: {removed}")
            else:
                print(f"✓ No pipeline metadata found (clean LLM output)")
            
            # Keep everything else and convert to JSON string
            veo_prompt = json.dumps(prompt_dict, indent=2, ensure_ascii=False)
            print(f"✓ Converted to JSON string ({len(prompt_dict)} LLM keys preserved)")
        
        # Case 3: Unexpected type (fallback)
        else:
            veo_prompt = str(prompt_obj)
            print(f"⚠️ Unexpected type, converting to string")
        
        # Validation
        if not veo_prompt or len(veo_prompt) < 10:
            print(f"❌ ERROR: Prompt too short or empty ({len(veo_prompt)} chars)")
            print(f"="*70)
            return None
        
        # ========== CRITICAL: LOG EXACT PROMPT SENT TO VEO ==========
        print(f"\n{'🚨 FINAL PROMPT → VEO API 🚨'.center(70, '=')}")
        print(f"Context: {context}")
        print(f"Length: {len(veo_prompt)} characters")
        print(f"Format: {'Plain text' if isinstance(prompt_obj, str) else 'Structured JSON'}")
        print(f"\n{'-'*70}")
        print(f"COMPLETE PROMPT (exactly as sent to Veo):")
        print(f"{'-'*70}\n")
        print(veo_prompt)  # ← Full prompt, no truncation
        print(f"\n{'-'*70}")
        print(f"END OF PROMPT")
        print(f"{'='*70}\n")
        # ========== END LOGGING ==========
        
        return veo_prompt
    
    def generate_segments(self, prompts, image_gcs_uris):
        """
        Generate video segments from LLM prompts (any format)
        
        Args:
            prompts: List of LLM prompt objects (any structure)
            image_gcs_uris: List of uploaded image URIs
        
        Returns:
            List of generated video URIs
        """
        if not prompts:
            print("❌ No prompts provided")
            return None
        
        video_gcs_uris = []
        primary_image_uri = image_gcs_uris[0]
        
        for idx, prompt_obj in enumerate(prompts):
            # Extract metadata if present (for logging/organization)
            if isinstance(prompt_obj, dict):
                seg_num = prompt_obj.get('segment_number', idx + 1)
                duration = prompt_obj.get('duration', 8)
            else:
                seg_num = idx + 1
                duration = 8
            
            start_time = (seg_num - 1) * duration
            end_time = start_time + duration
            
            print(f"\n{'=' * 70}")
            print(f"🎬 SEGMENT {seg_num}/{len(prompts)}: {start_time}-{end_time}s")
            print(f"{'=' * 70}")
            
            # Prepare prompt (generic - no assumptions)
            veo_prompt_string = self._prepare_prompt_for_veo(
                prompt_obj, 
                context=f"Segment {seg_num}"
            )
            
            if not veo_prompt_string:
                print(f"❌ Invalid prompt for segment {seg_num}, skipping")
                continue
            
            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    output_gcs_uri = self.gcs_manager.get_segment_output_uri(
                        seg_num, start_time, end_time
                    )
                    
                    print(f"📍 Output URI: {output_gcs_uri}")
                    
                    # Select image
                    image_uri = (
                        image_gcs_uris[seg_num % len(image_gcs_uris)] 
                        if len(image_gcs_uris) > 1 
                        else primary_image_uri
                    )
                    
                    if attempt > 0:
                        print(f"🔄 Retry {attempt}/{max_retries - 1}...")
                    
                    print(f"🎥 Calling Veo API...")
                    
                    # VEO API CALL
                    person_gen = "disabled" if not ALLOW_PEOPLE_IN_VIDEO else "allow_adult"
                    
                    operation = self.client.models.generate_videos(
                        model=self.model,
                        prompt=veo_prompt_string,  # ← Generic prompt
                        image=types.Image(
                            gcs_uri=image_uri,
                            mime_type="image/png",
                        ),
                        config=types.GenerateVideosConfig(
                            aspect_ratio="16:9",
                            duration_seconds=duration,
                            resolution=VIDEO_RESOLUTION,
                            person_generation=person_gen,
                            generate_audio=GENERATE_AUDIO,
                            output_gcs_uri=output_gcs_uri,
                        ),
                    )
                    
                    print(f"✓ Operation submitted: {operation.name}")
                    
                    video_uri = self._wait_for_completion(operation, seg_num, len(prompts))
                    
                    if video_uri:
                        video_gcs_uris.append(video_uri)
                        print(f"✅ Segment {seg_num} succeeded")
                        break
                    else:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 10
                            print(f"⏰ Waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                        else:
                            print(f"❌ Segment {seg_num} failed after {max_retries} attempts")
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Attempt {attempt + 1} error: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(10)
                    else:
                        import traceback
                        traceback.print_exc()
                        break
        
        return video_gcs_uris if len(video_gcs_uris) > 0 else None

    def generate_with_extension(self, prompt_obj, image_gcs_uri, base_duration, extension_count, extension_increment):
        """
        Generate video using cumulative extension (EXACT Reddit method)
        
        CRITICAL: Extension API is simpler than base generation!
        - NO config parameter
        - NO duration_seconds (auto-extends by 7s)
        - NO output_gcs_uri (auto-generates)
        """
        from config import get_extension_model, ALLOW_PEOPLE_IN_VIDEO, GENERATE_AUDIO, VIDEO_RESOLUTION
        
        model = get_extension_model()
        
        print("\n" + "=" * 70)
        print("🔬 EXTENSION MODE - EXACT REDDIT METHOD")
        print("=" * 70)
        print(f"📐 Base duration: {base_duration}s")
        print(f"🔄 Extensions: {extension_count} × {extension_increment}s each")
        print(f"⏱️ Target duration: {base_duration + (extension_count * extension_increment)}s")
        print(f"🤖 Model: {model}")
        print("=" * 70)
        
        # Prepare prompt
        veo_prompt_string = self._prepare_prompt_for_veo(
            prompt_obj, 
            context="Base Video"
        )
        
        if not veo_prompt_string:
            print("❌ Invalid prompt")
            return None
        
        # ============================================================
        # STEP 1: Generate base video (WITH config - normal generation)
        # ============================================================
        print("\n" + "🎬 STEP 1: GENERATING BASE VIDEO ".ljust(70, "="))
        
        try:
            person_gen = "disabled" if not ALLOW_PEOPLE_IN_VIDEO else "allow_adult"
            
            print(f"⏳ Generating {base_duration}s base video...")
            print(f"📍 Using config (normal generation)")
            
            # Base generation DOES use config (normal API)
            base_operation = self.client.models.generate_videos(
                model=model,
                prompt=veo_prompt_string,
                image=types.Image(
                    gcs_uri=image_gcs_uri,
                    mime_type="image/png",
                ),
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                    duration_seconds=base_duration,
                    resolution=VIDEO_RESOLUTION,
                    person_generation=person_gen,
                    generate_audio=GENERATE_AUDIO,
                ),
            )
            
            print(f"✓ Base operation submitted: {base_operation.name}")
            
            # Wait using Reddit's polling pattern
            print(f"⏳ Polling for completion (Reddit method)...")
            while not base_operation.done:
                time.sleep(10)  # Reddit uses 10s intervals
                base_operation = self.client.operations.get(base_operation)
            
            print(f"✅ Base operation complete!")
            
            # Check for errors
            if base_operation.error:
                print(f"❌ Base generation error: {base_operation.error}")
                return None
            
            # REDDIT METHOD: Use .response (not .result)
            if not hasattr(base_operation, 'response') or not base_operation.response:
                print(f"❌ No response in operation")
                print(f"   Available attributes: {dir(base_operation)}")
                # Fallback to .result if .response doesn't exist
                if hasattr(base_operation, 'result') and base_operation.result:
                    print(f"   Using .result instead of .response")
                    base_video = base_operation.result.generated_videos[0]
                else:
                    return None
            else:
                # Use .response like Reddit user
                base_video = base_operation.response.generated_videos[0]
            
            base_video_uri = base_video.video.uri
            print(f"✅ Base video: {base_video_uri}")
            
        except Exception as e:
            print(f"❌ Base generation error: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # ============================================================
        # STEP 2: Extend the video (NO config - extension API!)
        # ============================================================
        current_video = base_video
        current_duration = base_duration
        
        for ext_num in range(1, extension_count + 1):
            print("\n" + f"🔄 EXTENSION {ext_num}/{extension_count} ".ljust(70, "="))
            print(f"⏳ Extending from {current_duration}s...")
            
            try:
                # REDDIT METHOD: Minimal API call
                print(f"\n{'🚨 EXTENSION API CALL (REDDIT METHOD) 🚨'.center(70, '=')}")
                print(f"Model: {model}")
                print(f"Source: Video object from previous generation")
                print(f"Config: NONE (auto-extends by 7s)")
                print(f"{'='*70}\n")
                
                # THIS IS THE KEY: Minimal extension call, just like Reddit
                extension_operation = self.client.models.generate_videos(
                    model=model,
                    source=current_video,  # Just source, NOTHING ELSE!
                )
                
                print(f"✓ Extension submitted: {extension_operation.name}")
                
                # Poll using Reddit method
                print(f"⏳ Polling for completion...")
                while not extension_operation.done:
                    time.sleep(10)
                    extension_operation = self.client.operations.get(extension_operation)
                
                print(f"✅ Extension {ext_num} complete!")
                
                # Check for errors
                if extension_operation.error:
                    print(f"❌ Extension error: {extension_operation.error}")
                    print(f"⚠️ Returning last successful video ({current_duration}s)")
                    return current_video.video.uri
                
                # Get extended video (use .response like Reddit)
                if not hasattr(extension_operation, 'response') or not extension_operation.response:
                    print(f"❌ No response in extension operation")
                    # Fallback
                    if hasattr(extension_operation, 'result') and extension_operation.result:
                        print(f"   Using .result instead")
                        extended_video = extension_operation.result.generated_videos[0]
                    else:
                        print(f"⚠️ Returning last successful video")
                        return current_video.video.uri
                else:
                    extended_video = extension_operation.response.generated_videos[0]
                
                extended_video_uri = extended_video.video.uri
                new_duration = current_duration + extension_increment
                
                print(f"✅ Extended to ~{new_duration}s: {extended_video_uri}")
                
                # Update for next iteration
                current_video = extended_video
                current_duration = new_duration
                
            except Exception as e:
                print(f"❌ Extension {ext_num} failed: {e}")
                import traceback
                traceback.print_exc()
                print(f"⚠️ Returning last successful video ({current_duration}s)")
                return current_video.video.uri
        
        # Return final extended video
        final_uri = current_video.video.uri
        
        print("\n" + "=" * 70)
        print(f"🎉 EXTENSION COMPLETE!")
        print(f"📹 Final video (~{current_duration}s): {final_uri}")
        print("=" * 70)
        
        return final_uri
    
    def _wait_for_completion(self, operation, segment_num, total_segments):
        """Poll operation until complete"""
        print(f"⏳ Waiting for Veo generation...")
        
        poll_count = 0
        max_polls = 60
        
        while not operation.done and poll_count < max_polls:
            time.sleep(15)
            poll_count += 1
            
            if poll_count % 4 == 0:
                elapsed = poll_count * 15
                print(f"   {elapsed}s elapsed...")
            
            try:
                operation = self.client.operations.get(operation)
            except Exception as e:
                print(f"⚠️ Polling error: {e}")
                time.sleep(5)
                continue
        
        if poll_count >= max_polls:
            print(f"⏱️ Timeout after {max_polls * 15}s")
            return None
        
        print(f"✅ Segment {segment_num}/{total_segments} complete!")
        
        if operation.error:
            error_code = operation.error.get('code', 'Unknown')
            error_msg = operation.error.get('message', 'No message')
            print(f"❌ Veo error {error_code}: {error_msg}")
            return None
        
        try:
            if operation.response:
                video_uri = operation.result.generated_videos[0].video.uri
                print(f"📹 Video: {video_uri}")
                return video_uri
            else:
                print(f"❌ No response")
                return None
        except Exception as e:
            print(f"❌ URI extraction error: {e}")
            import traceback
            traceback.print_exc()
            return None