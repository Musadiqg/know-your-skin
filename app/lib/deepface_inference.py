"""
Age Estimation Module using OpenCV DNN.

Uses lightweight Caffe models for face detection and age estimation.
No TensorFlow required - just OpenCV.
Models are downloaded during Docker build.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Model directory
MODELS_DIR = Path(__file__).parent.parent / "models" / "age"

# Age buckets from the Levi-Hassner model
AGE_BUCKETS = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']

# Approximate center age for each bucket (for numeric output)
AGE_CENTERS = [1, 5, 10, 17, 28, 40, 50, 70]

# Mean values for face preprocessing
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)

# Cache for loaded models
_face_net = None
_age_net = None
_models_loaded = False
_models_available = None


def _check_models_exist() -> bool:
    """Check if all required model files exist."""
    required_files = [
        "age_deploy.prototxt",
        "age_net.caffemodel",
        "face_deploy.prototxt",
        "face_net.caffemodel",
    ]
    for f in required_files:
        filepath = MODELS_DIR / f
        if not filepath.exists():
            logger.warning(f"Missing model file: {filepath}")
            return False
        # Check file is not empty
        if filepath.stat().st_size < 100:
            logger.warning(f"Model file appears empty or corrupted: {filepath}")
            return False
    return True


def _load_models():
    """
    Load the face detector and age estimator models.
    Returns (face_net, age_net) or (None, None) on failure.
    Uses caching to avoid reloading.
    """
    global _face_net, _age_net, _models_loaded, _models_available
    
    # Return cached result
    if _models_loaded:
        return _face_net, _age_net
    
    _models_loaded = True
    
    try:
        import cv2
    except ImportError:
        logger.error("OpenCV not installed")
        _models_available = False
        return None, None
    
    if not _check_models_exist():
        logger.error("Age model files not available. They should be downloaded during Docker build.")
        _models_available = False
        return None, None
    
    try:
        _face_net = cv2.dnn.readNetFromCaffe(
            str(MODELS_DIR / "face_deploy.prototxt"),
            str(MODELS_DIR / "face_net.caffemodel")
        )
        _age_net = cv2.dnn.readNetFromCaffe(
            str(MODELS_DIR / "age_deploy.prototxt"),
            str(MODELS_DIR / "age_net.caffemodel")
        )
        _models_available = True
        logger.info("Age estimation models loaded successfully")
        return _face_net, _age_net
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        _models_available = False
        return None, None


def _detect_face(face_net, image, conf_threshold=0.5):
    """
    Detect face in image and return the bounding box.
    Returns (startX, startY, endX, endY) or None if no face detected.
    """
    import cv2
    
    h, w = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), [104, 117, 123], True, False)
    face_net.setInput(blob)
    detections = face_net.forward()
    
    best_face = None
    best_conf = conf_threshold
    
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > best_conf:
            best_conf = confidence
            x1 = int(detections[0, 0, i, 3] * w)
            y1 = int(detections[0, 0, i, 4] * h)
            x2 = int(detections[0, 0, i, 5] * w)
            y2 = int(detections[0, 0, i, 6] * h)
            # Add padding
            padding = 20
            best_face = (
                max(0, x1 - padding),
                max(0, y1 - padding),
                min(w, x2 + padding),
                min(h, y2 + padding)
            )
    
    return best_face


def estimate_age(image_path: str) -> Dict[str, Any]:
    """
    Estimate age from a face image using OpenCV DNN.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        {
            "estimated_age": 28,
            "age_range": "(25-32)",
            "success": True,
            "error": None
        }
        
        On failure:
        {
            "estimated_age": None,
            "age_range": None,
            "success": False,
            "error": "Face not detected"
        }
    """
    try:
        import cv2
    except ImportError:
        logger.warning("OpenCV not installed. Age estimation unavailable.")
        return {
            "estimated_age": None,
            "age_range": None,
            "success": False,
            "error": "OpenCV not installed"
        }
    
    # Load models (uses cache)
    face_net, age_net = _load_models()
    if face_net is None or age_net is None:
        return {
            "estimated_age": None,
            "age_range": None,
            "success": False,
            "error": "Age models not available"
        }
    
    # Read image
    try:
        image = cv2.imread(image_path)
        if image is None:
            return {
                "estimated_age": None,
                "age_range": None,
                "success": False,
                "error": "Could not read image"
            }
    except Exception as e:
        logger.error(f"Error reading image: {e}")
        return {
            "estimated_age": None,
            "age_range": None,
            "success": False,
            "error": f"Error reading image: {e}"
        }
    
    # Detect face
    face_box = _detect_face(face_net, image, conf_threshold=0.3)
    
    if face_box is None:
        # Try with the whole image if no face detected
        logger.info("No face detected, using whole image for age estimation")
        h, w = image.shape[:2]
        face_box = (0, 0, w, h)
    
    # Extract face region
    x1, y1, x2, y2 = face_box
    face = image[y1:y2, x1:x2]
    
    if face.size == 0:
        return {
            "estimated_age": None,
            "age_range": None,
            "success": False,
            "error": "Invalid face region"
        }
    
    # Predict age
    try:
        blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
        age_net.setInput(blob)
        age_preds = age_net.forward()
        
        age_idx = age_preds[0].argmax()
        age_range = AGE_BUCKETS[age_idx]
        estimated_age = AGE_CENTERS[age_idx]
        confidence = float(age_preds[0][age_idx])
        
        logger.info(f"Age estimation: {age_range} (confidence: {confidence:.2f})")
        
        return {
            "estimated_age": estimated_age,
            "age_range": age_range,
            "confidence": round(confidence, 3),
            "success": True,
            "error": None
        }
    except Exception as e:
        logger.error(f"Age prediction failed: {e}")
        return {
            "estimated_age": None,
            "age_range": None,
            "success": False,
            "error": f"Prediction failed: {e}"
        }


def get_age_assessment(estimated_age: Optional[int], primary_concern: str) -> str:
    """
    Generate a human-readable age assessment message.
    
    Args:
        estimated_age: Estimated biological age
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
