"""
Veo Video Generator - JSON String Passthrough
Converts structured JSON dict to formatted string for Veo API
"""
import time
import json
from google import genai
from google.genai import types
from config import VIDEO_MODEL, ALLOW_PEOPLE_IN_VIDEO, GENERATE_AUDIO, VIDEO_RESOLUTION


class VeoVideoGenerator:
    """Generates videos using structured prompts (as strings)"""
    
    def __init__(self, model=VIDEO_MODEL, gcs_manager=None):
        self.client = genai.Client()
        self.model = model
        self.gcs_manager = gcs_manager
    
    def generate_segments(self, prompts, image_gcs_uris):
        """
        Generate video segments from structured JSON prompts.
        
        Args:
            prompts: List of JSON prompt objects (dicts)
            image_gcs_uris: List of uploaded image URIs
        
        Returns:
            List of generated video URIs
        """
        if not prompts:
            print("❌ No prompts provided")
            return None
        
        video_gcs_uris = []
        primary_image_uri = image_gcs_uris[0]
        
        for prompt_obj in prompts:
            if not isinstance(prompt_obj, dict):
                print(f"⚠️ Skipping non-dict prompt: {type(prompt_obj)}")
                continue
            
            seg_num = prompt_obj.get('segment_number', len(video_gcs_uris) + 1)
            duration = prompt_obj.get('duration', 8)
            
            # Calculate times
            start_time = (seg_num - 1) * duration
            end_time = start_time + duration
            
            print(f"\n{'=' * 70}")
            print(f"🎬 SEGMENT {seg_num}/{len(prompts)}: {start_time}-{end_time}s")
            print(f"{'=' * 70}")
            
            # ========== CONVERT STRUCTURED JSON TO STRING ==========
            # Remove our internal metadata
            veo_prompt_dict = prompt_obj.copy()
            veo_prompt_dict.pop('segment_number', None)
            veo_prompt_dict.pop('duration', None)
            veo_prompt_dict.pop('veo_prompt', None)  # Remove generic fallback
            veo_prompt_dict.pop('style', None)  # Remove generic style
            
            # Option 1: JSON string (preserves exact structure)
            veo_prompt_string = json.dumps(veo_prompt_dict, indent=2, ensure_ascii=False)
            
            # Option 2: If you want natural language instead, uncomment this:
            # veo_prompt_string = self._flatten_to_natural_language(veo_prompt_dict)
            
            print(f"\n{'🚨 FINAL STRING → VEO API '.center(70, '=')}")
            print(f"Format: JSON string")
            print(f"Length: {len(veo_prompt_string)} chars")
            print(f"\nFirst 400 chars:\n{veo_prompt_string[:400]}...")
            print(f"\nLast 200 chars:\n...{veo_prompt_string[-200:]}")
            print("="*70 + "\n")
            
            if not veo_prompt_string or len(veo_prompt_string) < 10:
                print(f"❌ Empty prompt for segment {seg_num}, skipping")
                continue
            # ========== END PROMPT CONVERSION ==========
            
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
                    
                    # ========== VEO API CALL WITH STRING ==========
                    person_gen = "disabled" if not ALLOW_PEOPLE_IN_VIDEO else "allow_adult"
                    
                    operation = self.client.models.generate_videos(
                        model=self.model,
                        prompt=veo_prompt_string,  # ← String (not dict)
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
                    # ========== END VEO CALL ==========
                    
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
    
    def _flatten_to_natural_language(self, prompt_dict):
        """
        ALTERNATIVE: Convert structured JSON to detailed natural language.
        Preserves all precision but in prose form.
        Uncomment the call to this in generate_segments if JSON strings don't work well.
        """
        parts = []
        
        # Global header
        if 'global_header' in prompt_dict:
            parts.append(str(prompt_dict['global_header']))
        
        # Global style
        if 'global_style' in prompt_dict:
            gs = prompt_dict['global_style']
            if isinstance(gs, dict):
                parts.append(f"Aspect ratio: {gs.get('aspect_ratio', '16:9')}.")
                parts.append(f"Resolution: {gs.get('resolution', '4K')} at {gs.get('fps', 24)} fps.")
                parts.append(f"Look: {gs.get('look', '')}.")
                parts.append(f"Set: {gs.get('set_environment', '')}.")
                parts.append(f"Lighting: {gs.get('lighting_mood', '')}.")
                parts.append(f"Music: {gs.get('music_style', '')}.")
                parts.append(f"SFX: {gs.get('audio_sfx', '')}.")
        
        # Scene plan
        if 'scene_plan' in prompt_dict:
            sp = prompt_dict['scene_plan']
            if isinstance(sp, dict):
                parts.append(f"Scene purpose: {sp.get('scene_purpose', '')}.")
                parts.append(f"Camera: {sp.get('camera_lens', '')}.")
                parts.append(f"Motion: {sp.get('motion_plan', '')}.")
                parts.append(f"Speed: {sp.get('motion_speed', '')}.")
                parts.append(f"Composition: {sp.get('composition', '')}.")
                parts.append(f"Transition: {sp.get('transition_out', '')}.")
                
                # Overlay
                if 'overlay' in sp:
                    ov = sp['overlay']
                    if isinstance(ov, dict):
                        parts.append(f"Text overlay: '{ov.get('text', '')}' appears at {ov.get('timecode_on', '')} and disappears at {ov.get('timecode_off', '')}, positioned in {ov.get('position', '')}.")
        
        # Hard negatives
        if 'hard_negatives' in prompt_dict:
            parts.append(f"Critical constraints: {prompt_dict['hard_negatives']}")
        
        return " ".join(parts)
    
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