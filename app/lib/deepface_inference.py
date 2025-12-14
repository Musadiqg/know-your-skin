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
    try:
        from deepface import DeepFace
        
        # Analyze the image for age
        # enforce_detection=False allows partial faces
        result = DeepFace.analyze(
            img_path=image_path,
            actions=['age'],
            enforce_detection=False,
            silent=True
        )
        
        # DeepFace returns a list if multiple faces, or dict if single
        if isinstance(result, list):
            # Take the first face detected
            if len(result) > 0:
                age = result[0].get('age')
            else:
                return {
                    "estimated_age": None,
                    "success": False,
                    "error": "No face detected in image"
                }
        else:
            age = result.get('age')
        
        if age is not None:
            return {
                "estimated_age": int(age),
                "success": True,
                "error": None
            }
        else:
            return {
                "estimated_age": None,
                "success": False,
                "error": "Could not determine age"
            }
            
    except ImportError:
        logger.warning("DeepFace not installed. Age estimation unavailable.")
        return {
            "estimated_age": None,
            "success": False,
            "error": "DeepFace library not installed"
        }
    except Exception as e:
        logger.warning(f"DeepFace age estimation failed: {e}")
        return {
            "estimated_age": None,
            "success": False,
            "error": str(e)
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

