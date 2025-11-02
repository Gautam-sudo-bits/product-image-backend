"""
Image Edit Pipeline - Direct Operation Flow
Simplified: operation_id → template → prompt generation → execution
Skips operation selection LLM call
"""
import time
import json
import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from datetime import datetime
import cloudinary.uploader

from operations_config import get_operation_by_id, get_operation_template


class ImageEditPipeline:
    """Handles image editing with direct operation selection"""
    
    def __init__(self):
        self.client = genai.Client()
        self.prompt_generator_model = "gemini-2.5-pro"  # For prompt generation
        self.editor_model = "gemini-2.5-flash-image"     # Nano Banana for editing
    
    def generate_nano_banana_prompt(self, operation_id, user_details, user_image, unique_id):
        """
        Generate hyper-specific Nano Banana prompt using operation template
        
        Args:
            operation_id: ID of the operation (1-38)
            user_details: Optional user specifications
            user_image: PIL Image object
            unique_id: Request identifier
        
        Returns:
            str: Generated Nano Banana prompt
        """
        print(f"\n--- Step 1: Generating Nano Banana Prompt (ID: {unique_id}) ---")
        
        # Get operation config
        operation = get_operation_by_id(operation_id)
        if not operation:
            raise ValueError(f"Invalid operation_id: {operation_id}")
        
        print(f"✓ Operation: {operation['name']}")
        print(f"✓ Category: {operation['category']}")
        
        # Get instruction template with user details merged
        instruction_template = get_operation_template(operation_id, user_details)
        
        print(f"✓ Template loaded ({len(instruction_template)} chars)")
        if user_details:
            print(f"✓ User details provided: {user_details[:100]}...")
        else:
            print(f"✓ No user details - using defaults")
        
        # Build the prompt for Gemini 2.5 Pro
        prompt_instruction = f"""
You are an expert at creating hyper-specific image editing instructions for Nano Banana AI.

Based on the operation template and guidelines below, generate a SINGLE, DETAILED, DESCRIPTIVE editing instruction.

{instruction_template}

IMPORTANT OUTPUT FORMAT:
- Return ONLY the descriptive editing instruction
- Do NOT include JSON, markdown, code blocks, or explanations
- The output should be a clean paragraph of editing instructions
- Be hyper-specific with measurements, colors, positions, and effects
- The instruction should be ready to send directly to Nano Banana

Generate the instruction now.
"""
        
        # Multimodal content: instruction + image
        contents = [prompt_instruction, user_image]
        
        try:
            print(f"📤 Sending to {self.prompt_generator_model}...")
            
            response = self.client.models.generate_content(
                model=self.prompt_generator_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower for more consistent technical output
                )
            )
            
            # Extract the generated prompt
            nano_banana_prompt = response.text.strip()
            
            # Remove any markdown formatting if present
            nano_banana_prompt = nano_banana_prompt.replace('```', '').strip()
            
            print(f"\n✅ Nano Banana Prompt Generated:")
            print(f"{'='*70}")
            print(f"{nano_banana_prompt[:300]}...")
            print(f"{'='*70}\n")
            
            time.sleep(1)  # Rate limiting
            return nano_banana_prompt
            
        except Exception as e:
            print(f"❌ Prompt generation error: {e}")
            raise
    
    def execute_edit(self, nano_banana_prompt, user_image, unique_id):
        """
        Execute edit using Nano Banana (Gemini 2.5 Flash Image)
        
        Args:
            nano_banana_prompt: Generated editing instruction
            user_image: PIL Image object
            unique_id: Request identifier
        
        Returns:
            bytes: Edited image data
        """
        print(f"\n--- Step 2: Executing Edit with Nano Banana (ID: {unique_id}) ---")
        
        try:
            print(f"📤 Sending to {self.editor_model}...")
            print(f"   Prompt: {nano_banana_prompt[:150]}...")
            
            # Construct editing request
            contents = [nano_banana_prompt, user_image]
            
            response = self.client.models.generate_content(
                model=self.editor_model,
                contents=contents
            )
            
            # Extract edited image bytes
            edited_image_bytes = None
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_stream = BytesIO(part.inline_data.data)
                    edited_image_bytes = image_stream.getvalue()
                    print("✅ Edited image received")
                    break
            
            if edited_image_bytes:
                time.sleep(1)  # Rate limiting
                return edited_image_bytes
            else:
                raise ValueError("No image data in Nano Banana response")
        
        except Exception as e:
            print(f"❌ Nano Banana edit error: {e}")
            raise
    
    def run_edit_pipeline(self, image_bytes, operation_id, user_details, timestamp_str):
        """
        Complete edit pipeline: load operation → generate prompt → execute
        
        Args:
            image_bytes: Image file bytes
            operation_id: Operation ID (1-38)
            user_details: Optional user specifications
            timestamp_str: Timestamp for unique IDs
        
        Returns:
            tuple: (cloudinary_url, operation_name) or (None, None) on failure
        """
        pipeline_unique_id = f"{timestamp_str}_op{operation_id}"
        
        print(f"\n{'='*70}")
        print(f"🎨 IMAGE EDIT PIPELINE (ID: {pipeline_unique_id})")
        print(f"{'='*70}")
        
        try:
            # Load image
            user_image = Image.open(BytesIO(image_bytes))
            print(f"✅ Image loaded: {user_image.size[0]}x{user_image.size[1]} px")
            
            # Get operation info
            operation = get_operation_by_id(operation_id)
            operation_name = operation['name']
            
            # STEP 1: Generate Nano Banana prompt (using template + Gemini 2.5 Pro)
            nano_banana_prompt = self.generate_nano_banana_prompt(
                operation_id=operation_id,
                user_details=user_details,
                user_image=user_image,
                unique_id=pipeline_unique_id
            )
            
            # STEP 2: Execute edit with Nano Banana
            edited_image_bytes = self.execute_edit(
                nano_banana_prompt=nano_banana_prompt,
                user_image=user_image,
                unique_id=pipeline_unique_id
            )
            
            # STEP 3: Upload to Cloudinary
            print(f"\n--- Step 3: Uploading to Cloudinary ---")
            
            # Sanitize operation name for public_id
            import re
            operation_slug = operation_name.lower()
            operation_slug = re.sub(r'[^a-z0-9-_]', '-', operation_slug)
            operation_slug = re.sub(r'-+', '-', operation_slug)
            operation_slug = operation_slug.strip('-')
            
            public_id = f"edit_{operation_slug}_{timestamp_str}"
            
            upload_result = cloudinary.uploader.upload(
                BytesIO(edited_image_bytes),
                folder="product_edits",
                public_id=public_id
            )
            
            final_url = upload_result['secure_url']
            print(f"✅ Uploaded: {final_url}")
            
            print(f"\n{'='*70}")
            print(f"🎉 EDIT COMPLETE (ID: {pipeline_unique_id})")
            print(f"{'='*70}\n")
            
            return (final_url, operation_name)
        
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"❌ PIPELINE FAILED (ID: {pipeline_unique_id})")
            print(f"❌ ERROR: {e}")
            print(f"{'='*70}\n")
            import traceback
            traceback.print_exc()
            return (None, None)


def edit_product_image(image_bytes, operation_id, operation_details=None):
    """
    Main entry point for image editing
    
    Args:
        image_bytes: Image file bytes
        operation_id: Operation ID (1-38)
        operation_details: Optional user specifications
    
    Returns:
        dict: {
            "success": bool,
            "edited_image_url": str,
            "operation_name": str,
            "error": str (if failed)
        }
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'#'*70}")
    print(f"# IMAGE EDIT REQUEST")
    print(f"# Timestamp: {timestamp_str}")
    print(f"# Operation ID: {operation_id}")
    if operation_details:
        print(f"# User Details: {operation_details[:100]}...")
    print(f"{'#'*70}\n")
    
    try:
        pipeline = ImageEditPipeline()
        
        result_url, operation_name = pipeline.run_edit_pipeline(
            image_bytes=image_bytes,
            operation_id=operation_id,
            user_details=operation_details or "",
            timestamp_str=timestamp_str
        )
        
        if result_url:
            return {
                "success": True,
                "edited_image_url": result_url,
                "operation_name": operation_name
            }
        else:
            return {
                "success": False,
                "error": "Edit execution failed"
            }
    
    except Exception as e:
        print(f"❌ Pipeline exception: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }