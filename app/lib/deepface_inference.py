"""
DeepFace Age Estimation Module.

Provides age estimation using DeepFace library.
Handles face detection failures gracefully for partial face images.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def estimate_age(image_path: str) -> Dict[str, Any]:
    """
    Estimate age from a face image using DeepFace.
    
    NOTE: DeepFace is temporarily disabled due to dependency issues.
    This function returns a placeholder response.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        {
            "estimated_age": 32,
            "success": True,
            "error": None
        }
        
        On failure:
        {
            "estimated_age": None,
            "success": False,
            "error": "Face not detected"
        }
    """
    # TEMPORARILY DISABLED - DeepFace has dependency issues with OpenCV/TensorFlow
    # TODO: Re-enable when DeepFace dependencies are resolved
    logger.info("DeepFace age estimation temporarily disabled")
    return {
        "estimated_age": None,
        "success": False,
        "error": "Age estimation temporarily unavailable"
    }


def get_age_assessment(estimated_age: Optional[int], primary_concern: str) -> str:
    """
    Generate a human-readable age assessment message.
    
    Args:
        estimated_age: Estimated biological age from DeepFace
        primary_concern: Primary aging concern detected
        
    Returns:
        A descriptive assessment string
    """
    concern_descriptions = {
        "dark_spots": "signs of hyperpigmentation",
        "puffy_eyes": "puffiness around the eyes",
        "wrinkles": "fine lines and wrinkles"
    }
    
    concern_text = concern_descriptions.get(primary_concern, primary_concern.replace("_", " "))
    
    if estimated_age is not None:
        return f"Based on your image, your skin appears to be around {estimated_age} years old with {concern_text} as your primary aging concern."
    else:
        return f"Your primary aging concern appears to be {concern_text}."

