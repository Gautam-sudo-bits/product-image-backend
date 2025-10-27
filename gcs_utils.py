"""
Google Cloud Storage utility - FIXED for Veo output paths
"""
import os
import time
import uuid
from pathlib import Path
from google.cloud import storage
from config import GCS_BUCKET_NAME, GCS_OUTPUT_PREFIX, TESTING_MODE


class GCSManager:
    """Manages GCS operations with proper file paths for Veo"""
    
    def __init__(self, bucket_name=None):
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name or GCS_BUCKET_NAME
        self.bucket = self.storage_client.bucket(self.bucket_name)
        
        # Generate unique folder for this run
        timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:8]
        self.request_id = f"{timestamp}_{unique_id}"
        self.request_folder = f"{GCS_OUTPUT_PREFIX}/{self.request_id}"
        
        # Subfolders
        self.input_folder = f"{self.request_folder}/input_images"
        self.segments_folder = f"{self.request_folder}/segments"
        
        print(f"\n{'=' * 70}")
        print(f"📁 GCS FOLDER: {self.request_folder}")
        print(f"{'=' * 70}\n")
    
    def upload_image(self, local_path):
        """Upload image to input_images folder"""
        filename = Path(local_path).name
        blob_name = f"{self.input_folder}/{filename}"
        blob = self.bucket.blob(blob_name)
        
        print(f"📤 Uploading {filename}...")
        blob.upload_from_filename(local_path)
        
        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
        return gcs_uri
    
    def get_segment_output_uri(self, segment_number, start_time, end_time):
        """
        CRITICAL FIX: Return full file path with .mp4 extension
        This prevents Veo from creating nested folders
        """
        # Include .mp4 extension to specify it's a file, not a folder
        filename = f"segment_{segment_number:02d}_{start_time:02d}-{end_time:02d}s.mp4"
        blob_path = f"{self.segments_folder}/{filename}"
        
        # Return full path including .mp4
        return f"gs://{self.bucket_name}/{blob_path}"
    
    def upload_final_video(self, local_path):
        """Upload final video to GCS and return public-accessible info"""
        blob = self.bucket.blob(f"{self.request_folder}/final_merged_video.mp4")
        
        print(f"📤 Uploading final video...")
        blob.upload_from_filename(local_path)
        
        # Make blob publicly readable (if your bucket allows)
        # Uncomment if you want direct public URLs:
        # blob.make_public()
        
        gcs_uri = f"gs://{self.bucket_name}/{blob.name}"
        
        # Generate a signed URL for temporary access (24 hours)
        # This works without making bucket public
        from datetime import timedelta
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=24),
            method="GET"
        )
        
        print(f"✅ Final video uploaded")
        print(f"   GCS URI: {gcs_uri}")
        print(f"   Signed URL generated (24h expiry)")
        
        return {
            "gcs_uri": gcs_uri,
            "public_url": signed_url,  # Use signed URL instead of GCS URI
            "blob_name": blob.name
        }
        
    def download_video(self, gcs_uri, local_filename):
        """Download video from GCS"""
        parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ""
        
        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        display_name = Path(blob_name).name
        print(f"📥 Downloading {display_name}...")
        
        blob.download_to_filename(local_filename)
        return local_filename
    
    def list_segment_videos(self):
        """List all MP4 files in segments folder"""
        prefix = f"{self.segments_folder}/"
        blobs = self.bucket.list_blobs(prefix=prefix)
        
        video_uris = []
        for blob in blobs:
            if blob.name.endswith('.mp4'):
                video_uris.append(f"gs://{self.bucket_name}/{blob.name}")
        
        return sorted(video_uris)