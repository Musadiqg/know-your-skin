"""
Age Estimation Module using OpenCV DNN.

Uses lightweight Caffe models for face detection and age estimation.
No TensorFlow required - just OpenCV.
"""

import logging
import os
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Model directory
MODELS_DIR = Path(__file__).parent.parent / "models" / "age"

# Age buckets from the Levi-Hassner model
AGE_BUCKETS = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']

# Approximate center age for each bucket (for numeric output)
AGE_CENTERS = [1, 5, 10, 17, 28, 40, 50, 70]

# Model URLs (from public repos)
MODEL_URLS = {
    "age_deploy.prototxt": "https://raw.githubusercontent.com/spmallick/learnopencv/master/AgeGender/age_deploy.prototxt",
    "age_net.caffemodel": "https://github.com/spmallick/learnopencv/raw/master/AgeGender/age_net.caffemodel",
    "opencv_face_detector.pbtxt": "https://raw.githubusercontent.com/spmallick/learnopencv/master/AgeGender/opencv_face_detector.pbtxt",
    "opencv_face_detector_uint8.pb": "https://github.com/spmallick/learnopencv/raw/master/AgeGender/opencv_face_detector_uint8.pb",
}

# Mean values for face preprocessing
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)


def _ensure_models_exist() -> bool:
    """
    Download model files if they don't exist.
    Returns True if all models are available, False otherwise.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    all_present = True
    for filename, url in MODEL_URLS.items():
        filepath = MODELS_DIR / filename
        if not filepath.exists():
            logger.info(f"Downloading {filename}...")
            try:
                urllib.request.urlretrieve(url, filepath)
                logger.info(f"Downloaded {filename}")
            except Exception as e:
                logger.error(f"Failed to download {filename}: {e}")
                all_present = False
    
    return all_present


def _load_models():
    """
    Load the face detector and age estimator models.
    Returns (face_net, age_net) or (None, None) on failure.
    """
    try:
        import cv2
    except ImportError:
        logger.error("OpenCV not installed")
        return None, None
    
    if not _ensure_models_exist():
        logger.error("Model files not available")
        return None, None
    
    try:
        face_net = cv2.dnn.readNet(
            str(MODELS_DIR / "opencv_face_detector_uint8.pb"),
            str(MODELS_DIR / "opencv_face_detector.pbtxt")
        )
        age_net = cv2.dnn.readNet(
            str(MODELS_DIR / "age_net.caffemodel"),
            str(MODELS_DIR / "age_deploy.prototxt")
        )
        return face_net, age_net
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
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
    
    # Load models
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
