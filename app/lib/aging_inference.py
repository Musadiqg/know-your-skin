"""
Aging Signs Classification Inference Module.

Provides inference for the 3-class aging signs classifier:
- dark spots
- puffy eyes
- wrinkles

Returns probabilities for all classes, not just the top prediction.
"""

import functools
import json
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np

from lib.derm_local import embed_image_path


AGING_MODELS_DIR_DEFAULT = "models/aging"

AGING_CLASSES = ["dark spots", "puffy eyes", "wrinkles"]


# ============================================================================
# Model Loading
# ============================================================================

@functools.lru_cache(maxsize=1)
def _load_aging_model(models_dir: str = AGING_MODELS_DIR_DEFAULT) -> Dict[str, Any]:
    """Load aging model from disk (cached)."""
    base = Path(models_dir)
    
    # Check for MLP model first
    mlp_model_path = base / "aging_mlp_model.joblib"
    mlp_scaler_path = base / "aging_mlp_scaler.joblib"
    config_path = base / "aging_config.json"
    
    # Also check for LogReg model as fallback
    logreg_model_path = base / "aging_logreg_model.joblib"
    logreg_scaler_path = base / "aging_logreg_scaler.joblib"
    
    models: Dict[str, Any] = {}
    
    if mlp_model_path.exists():
        models["model"] = joblib.load(mlp_model_path)
        models["scaler"] = joblib.load(mlp_scaler_path) if mlp_scaler_path.exists() else None
        models["model_type"] = "mlp"
    elif logreg_model_path.exists():
        models["model"] = joblib.load(logreg_model_path)
        models["scaler"] = joblib.load(logreg_scaler_path) if logreg_scaler_path.exists() else None
        models["model_type"] = "logreg"
    else:
        raise FileNotFoundError(
            f"No aging model found in {base}. "
            "Run `python scripts/train_aging_mlp.py` first."
        )
    
    # Load config if available
    if config_path.exists():
        with open(config_path) as f:
            models["config"] = json.load(f)
    else:
        models["config"] = {"classes": AGING_CLASSES}
    
    return models


def _ensure_2d(emb: np.ndarray) -> np.ndarray:
    if emb.ndim == 1:
        return emb.reshape(1, -1)
    return emb


# ============================================================================
# Inference Functions
# ============================================================================

def predict_aging_from_embedding(
    embedding: np.ndarray,
    models_dir: str = AGING_MODELS_DIR_DEFAULT,
) -> Dict[str, Any]:
    """
    Predict aging signs from a Derm Foundation embedding.
    
    Returns:
        {
            "primary_concern": "puffy_eyes",
            "confidence": 0.65,
            "aging_signs": {
                "dark_spots": 0.12,
                "puffy_eyes": 0.65,
                "wrinkles": 0.23
            }
        }
    """
    emb = _ensure_2d(embedding.astype(np.float32))
    models = _load_aging_model(models_dir)
    
    model = models["model"]
    model_type = models["model_type"]
    classes = models["config"].get("classes", AGING_CLASSES)
    
    # Get probabilities
    scaler = models.get("scaler")
    if scaler is not None:
        emb_scaled = scaler.transform(emb)
    else:
        emb_scaled = emb
    
    proba = model.predict_proba(emb_scaled)[0]
    
    # Build result
    predicted_idx = int(np.argmax(proba))
    predicted_class = classes[predicted_idx]
    confidence = float(proba[predicted_idx])
    
    # Use underscores for JSON keys
    aging_signs = {cls.replace(" ", "_"): round(float(p), 4) for cls, p in zip(classes, proba)}
    
    return {
        "primary_concern": predicted_class.replace(" ", "_"),
        "confidence": round(confidence, 4),
        "aging_signs": aging_signs,
    }


def analyze_aging_image(
    image_path: str,
    models_dir: str = AGING_MODELS_DIR_DEFAULT,
) -> Dict[str, Any]:
    """
    High-level helper: embed image with Derm Foundation and predict aging signs.
    
    Returns enriched result with recommendations.
    """
    emb = embed_image_path(image_path)
    raw_result = predict_aging_from_embedding(emb, models_dir=models_dir)
    
    # Enrich with recommendations
    return _enrich_aging_result(raw_result)


def _enrich_aging_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Add recommendations to aging prediction."""
    
    primary = raw.get("primary_concern", "")
    
    AGING_INFO = {
        "dark_spots": {
            "title": "Dark Spots / Hyperpigmentation",
            "description": "Dark spots, also known as age spots or sun spots, are areas of increased melanin production.",
            "causes": [
                "Sun exposure over time",
                "Hormonal changes",
                "Post-inflammatory hyperpigmentation",
                "Natural aging process"
            ],
            "recommendations": [
                "Use broad-spectrum SPF 30+ sunscreen daily",
                "Look for products with Vitamin C, niacinamide, or alpha arbutin",
                "Consider retinoids for evening skin tone",
                "Avoid picking at skin to prevent post-inflammatory marks",
                "Professional treatments like chemical peels may help"
            ],
        },
        "puffy_eyes": {
            "title": "Puffy Eyes / Under-Eye Bags",
            "description": "Puffiness around the eyes is often caused by fluid retention, genetics, or lifestyle factors.",
            "causes": [
                "Lack of sleep or poor sleep quality",
                "High sodium diet causing fluid retention",
                "Allergies or sinus issues",
                "Genetics and natural aging",
                "Screen fatigue and eye strain"
            ],
            "recommendations": [
                "Get 7-9 hours of quality sleep",
                "Reduce sodium intake and stay hydrated",
                "Use a cold compress in the morning",
                "Look for eye creams with caffeine or peptides",
                "Sleep with head slightly elevated",
                "Consider antihistamines if allergies are a factor"
            ],
        },
        "wrinkles": {
            "title": "Wrinkles / Fine Lines",
            "description": "Wrinkles are a natural part of aging, caused by decreased collagen and elastin production.",
            "causes": [
                "Natural aging and collagen loss",
                "Sun damage (photoaging)",
                "Repetitive facial expressions",
                "Smoking and environmental factors",
                "Dehydration"
            ],
            "recommendations": [
                "Use retinol or retinoids to boost collagen",
                "Apply SPF daily to prevent further damage",
                "Keep skin hydrated with hyaluronic acid",
                "Consider peptide-rich products",
                "Stay hydrated and maintain a healthy diet",
                "Professional treatments like microneedling may help"
            ],
        },
    }
    
    info = AGING_INFO.get(primary, {
        "title": primary.replace("_", " ").title(),
        "description": "",
        "causes": [],
        "recommendations": [],
    })
    
    return {
        **raw,
        "title": info.get("title", ""),
        "description": info.get("description", ""),
        "causes": info.get("causes", []),
        "recommendations": info.get("recommendations", []),
    }

