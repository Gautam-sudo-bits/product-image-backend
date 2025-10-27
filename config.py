"""
Configuration file for product video generation pipeline
UPDATED: Testing flags and cost controls
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ===========================
# Vertex AI Configuration
# ===========================
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "True")

# Set environment variables for SDK
os.environ["GOOGLE_CLOUD_PROJECT"] = GOOGLE_CLOUD_PROJECT
os.environ["GOOGLE_CLOUD_LOCATION"] = GOOGLE_CLOUD_LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = GOOGLE_GENAI_USE_VERTEXAI

# Optional: Service account credentials
if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# ===========================
# GCS Configuration
# ===========================
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_OUTPUT_PREFIX = "veo-product-videos"

# ===========================
# Model Configuration
# ===========================
TEXT_MODEL = "gemini-2.5-pro"
VIDEO_MODEL = "veo-3.1-generate-preview"

# ===========================
# TESTING & COST CONTROL FLAGS
# ===========================

# NOTE: Temp files are ALWAYS deleted for deployment (ignoring this flag for cleanup)
TESTING_MODE = True  # Set to False for production deployment

ENABLE_PROMPT_VIEW = True  # Allow frontend to view generated prompts
PROMPT_DISPLAY_FILE = "veo_generated_prompts_vertex.json"  # File to read prompts from

PROMPT_ONLY_MODE = True  # Set to True to skip video generation (just test prompts)
SAVE_PROMPTS_TO_FILE = True  # Save generated prompts to JSON

GENERATE_AUDIO = False  # Disable audio to save credits
USE_LOWER_RESOLUTION = True  # Set to True for "720p" (saves ~30% credits)

# ===========================
# Video Configuration
# ===========================
# Cost-optimized durations
DEFAULT_TOTAL_DURATION = 16  # Reduced from 40s (60% cost savings)
DEFAULT_SEGMENT_DURATION = 8  # 2 segments instead of 5

# Alternative configurations (uncomment to use)
# DEFAULT_TOTAL_DURATION = 24  # 3 segments
# DEFAULT_SEGMENT_DURATION = 8

DEFAULT_TRANSITION_DURATION = 1.0  # Reduced from 1.5s

# ===========================
# Video Generation Limits
# ===========================
MAX_IMAGES = 3
MIN_SEGMENT_DURATION = 6
MAX_SEGMENT_DURATION = 10

# ===========================
# Video Quality Settings
# ===========================
VIDEO_ASPECT_RATIO = "16:9"
VIDEO_RESOLUTION = "720p" if USE_LOWER_RESOLUTION else "1080p"  # Dynamic based on flag
VIDEO_FPS = 24
VIDEO_CODEC = "libx264"
VIDEO_PRESET = "medium"

# ===========================
# E-Commerce Video Rules
# ===========================
ALLOW_PEOPLE_IN_VIDEO = False
PRODUCT_OPERATION_MODE = False
COMMERCIAL_STYLE_ONLY = True

# Veo 3.1 Prompt Limits
MAX_PROMPT_LENGTH = 500  # Concise prompts work better
OPTIMAL_PROMPT_LENGTH = 400  # Target length

# ===========================
# Cost Tracking (Optional)
# ===========================
# Approximate Veo 3.1 costs (as of 2024)
COST_PER_SECOND_1080P = 0.10  # $0.10 per second
COST_PER_SECOND_720P = 0.07   # $0.07 per second

def estimate_generation_cost():
    """Calculate estimated cost for current configuration"""
    resolution_cost = COST_PER_SECOND_720P if USE_LOWER_RESOLUTION else COST_PER_SECOND_1080P
    total_cost = DEFAULT_TOTAL_DURATION * resolution_cost
    
    print(f"\n💰 ESTIMATED COST:")
    print(f"   Duration: {DEFAULT_TOTAL_DURATION}s")
    print(f"   Resolution: {VIDEO_RESOLUTION}")
    print(f"   Audio: {'Yes' if GENERATE_AUDIO else 'No (savings!)'}")
    print(f"   Estimated: ${total_cost:.2f} per video")
    print(f"   (Actual cost may vary)\n")
    
    return total_cost