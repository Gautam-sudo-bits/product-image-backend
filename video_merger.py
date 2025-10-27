"""
Video merging with MoviePy - OPTIMIZED FOR RENDER FREE TIER
- Forces temp file deletion regardless of TESTING_MODE
- Minimized memory footprint
- Immediate cleanup after use
"""
import os
import gc
from config import VIDEO_FPS, VIDEO_CODEC, VIDEO_PRESET, TESTING_MODE

class VideoMerger:
    """Merges video segments with aggressive resource cleanup"""
    
    def __init__(self, gcs_manager=None):
        self.gcs_manager = gcs_manager
    
    def merge_with_transitions(self, video_gcs_uris, output_filename, 
                           transition_duration=None):
        """Download and merge videos with minimal memory usage"""
        if not video_gcs_uris or len(video_gcs_uris) == 0:
            print("⚠️ No videos to merge")
            return None
        
        if len(video_gcs_uris) == 1:
            return self._handle_single_video(video_gcs_uris[0])
        
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        
        print(f"\n{'=' * 70}")
        print(f"🎬 MERGING {len(video_gcs_uris)} SEGMENTS")
        print(f"{'=' * 70}")
        
        temp_files = []
        clips = []
        final_video = None
        
        try:
            # Download and load clips
            for i, video_uri in enumerate(video_gcs_uris):
                temp_file = f"temp_segment_{i+1}.mp4"
                self.gcs_manager.download_video(video_uri, temp_file)
                temp_files.append(temp_file)
                
                print(f"   Loading segment {i+1}/{len(video_gcs_uris)}...")
                clip = VideoFileClip(temp_file, audio=True, target_resolution=None)
                clips.append(clip)
            
            print(f"\n🔗 Concatenating segments...")
            
            # Simple concatenation without transitions (saves memory)
            final_video = concatenate_videoclips(clips, method="compose")
            
            print(f"\n💾 Rendering: {output_filename}")
            print(f"   Codec: {VIDEO_CODEC} | FPS: {VIDEO_FPS}")
            
            # Write with optimized settings for low memory
            final_video.write_videofile(
                output_filename,
                codec=VIDEO_CODEC,
                audio_codec='aac',
                fps=VIDEO_FPS,
                preset=VIDEO_PRESET,
                threads=2,
                bitrate="2000k",
                logger=None,
                temp_audiofile='temp_audio.m4a',
                remove_temp=True
            )
            
            print(f"✅ Merge complete!")
            
            # CRITICAL: Close and cleanup MoviePy resources
            self._cleanup_clips(clips, final_video)
            
            # Delete segment temp files IMMEDIATELY (always delete these)
            self._delete_temp_files(temp_files)
            
            # Upload final video to GCS
            print(f"\n📤 Uploading final video to GCS...")
            final_video_info = self.gcs_manager.upload_final_video(output_filename)
            
            # ========== RESPECT TESTING_MODE FOR FINAL VIDEO ==========
            if TESTING_MODE:
                print(f"🧪 TESTING_MODE: Keeping local file: {output_filename}")
            else:
                # Production: delete local copy after GCS upload
                if os.path.exists(output_filename):
                    os.remove(output_filename)
                    print(f"🗑️ Production mode: Deleted local file: {output_filename}")
            # ===========================================================
            
            # Force garbage collection
            import gc
            gc.collect()
            
            return final_video_info
            
        except Exception as e:
            print(f"\n❌ Merge failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Ensure cleanup even on error
            self._cleanup_clips(clips, final_video)
            self._delete_temp_files(temp_files)
            
            # Delete partial output if exists (regardless of mode - it's broken)
            if os.path.exists(output_filename):
                os.remove(output_filename)
                print(f"🗑️ Deleted partial/corrupted file: {output_filename}")
            
            import gc
            gc.collect()
            return None
    
    def _handle_single_video(self, video_uri):
        """Download single video and upload as final"""
        temp_file = "temp_single_video.mp4"
        final_file = "final_product_video_single.mp4"
        
        try:
            # Download from GCS
            self.gcs_manager.download_video(video_uri, temp_file)
            
            # Rename to final (or copy if you want to keep temp)
            import shutil
            shutil.move(temp_file, final_file)
            
            # Upload to GCS
            result = self.gcs_manager.upload_final_video(final_file)
            
            # Respect TESTING_MODE
            if TESTING_MODE:
                print(f"🧪 TESTING_MODE: Keeping local file: {final_file}")
            else:
                if os.path.exists(final_file):
                    os.remove(final_file)
                    print(f"🗑️ Production mode: Deleted local file: {final_file}")
            
            return result
            
        except Exception as e:
            print(f"❌ Single video handling failed: {e}")
            return None
        finally:
            # Always cleanup the temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _cleanup_clips(self, clips, final_video):
        """Aggressively close all MoviePy clips to free memory"""
        try:
            # Close individual clips
            for clip in clips:
                if clip:
                    clip.close()
            
            # Close final video
            if final_video:
                final_video.close()
            
            print("✓ MoviePy clips closed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    
    def _delete_temp_files(self, temp_files):
        """Delete all temporary segment files"""
        deleted_count = 0
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    deleted_count += 1
            except Exception as e:
                print(f"⚠️ Could not delete {temp_file}: {e}")
        
        if deleted_count > 0:
            print(f"🗑️ Deleted {deleted_count} temp segment(s)")
        
        # Also check for any orphaned temp files
        self._cleanup_orphaned_temps()
    
    def _cleanup_orphaned_temps(self):
        """Remove any leftover temp files from failed runs"""
        orphans = []
        
        # Check for common temp file patterns
        for filename in os.listdir('.'):
            if (filename.startswith('temp_segment_') or 
                filename.startswith('temp_single_') or
                filename.startswith('temp_audio')):
                orphans.append(filename)
        
        for orphan in orphans:
            try:
                os.remove(orphan)
                print(f"🗑️ Cleaned orphan: {orphan}")
            except:
                pass