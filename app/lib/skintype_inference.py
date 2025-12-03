"""
Skin Type Classification Inference Module.

Provides inference for the 4-class skin type classifier:
- dry
- normal
- oily
- redness

Returns probabilities for all classes, not just the top prediction.
"""

import functools
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

from lib.derm_local import embed_image_path


SKINTYPE_MODELS_DIR_DEFAULT = "models/skintype"

SKIN_TYPE_CLASSES = ["dry", "normal", "oily", "redness"]


# ============================================================================
# PyTorch Model Classes (must match training script for joblib loading)
# ============================================================================

class SkinTypeMLP(nn.Module):
    """
    Multi-class classifier for skin type.
    Uses Softmax output (single label) not Sigmoid (multi-label).
    """
    
    def __init__(self, input_dim: int, hidden_units: List[int], num_classes: int, dropout: float = 0.3):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for units in hidden_units:
            layers.extend([
                nn.Linear(prev_dim, units),
                nn.ReLU(),
                nn.BatchNorm1d(units),
                nn.Dropout(dropout),
            ])
            prev_dim = units
        
        layers.append(nn.Linear(prev_dim, num_classes))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class SkinTypeMLPWrapper:
    """
    Sklearn-compatible wrapper for inference.
    Returns probabilities for each class.
    """
    
    def __init__(self, model: SkinTypeMLP, scaler: StandardScaler, classes: List[str]):
        self.model = model
        self.scaler = scaler
        self.classes = classes
        self.model.eval()
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return predicted class labels."""
        proba = self.predict_proba(X)
        return np.array([self.classes[i] for i in np.argmax(proba, axis=1)])
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return probability for each class (n_samples, n_classes)."""
        X_scaled = self.scaler.transform(X.astype(np.float32))
        X_t = torch.FloatTensor(X_scaled)
        
        with torch.no_grad():
            logits = self.model(X_t)
            proba = torch.softmax(logits, dim=1).numpy()
        
        return proba


# Register classes for joblib unpickling
sys.modules['__main__'].SkinTypeMLP = SkinTypeMLP
sys.modules['__main__'].SkinTypeMLPWrapper = SkinTypeMLPWrapper


# ============================================================================
# Model Loading
# ============================================================================

@functools.lru_cache(maxsize=1)
def _load_skintype_model(models_dir: str = SKINTYPE_MODELS_DIR_DEFAULT) -> Dict[str, Any]:
    """Load skin type model from disk (cached)."""
    base = Path(models_dir)
    
    # Check for MLP model first
    mlp_model_path = base / "skintype_mlp_model.joblib"
    mlp_scaler_path = base / "skintype_mlp_scaler.joblib"
    config_path = base / "skintype_config.json"
    
    # Also check for LogReg model as fallback
    logreg_model_path = base / "skintype_logreg_model.joblib"
    logreg_scaler_path = base / "skintype_logreg_scaler.joblib"
    
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
            f"No skin type model found in {base}. "
            "Run `python scripts/train_skintype_mlp.py` first."
        )
    
    # Load config if available
    if config_path.exists():
        with open(config_path) as f:
            models["config"] = json.load(f)
    else:
        models["config"] = {"classes": SKIN_TYPE_CLASSES}
    
    return models


def _ensure_2d(emb: np.ndarray) -> np.ndarray:
    if emb.ndim == 1:
        return emb.reshape(1, -1)
    return emb


# ============================================================================
# Inference Functions
# ============================================================================

def predict_skintype_from_embedding(
    embedding: np.ndarray,
    models_dir: str = SKINTYPE_MODELS_DIR_DEFAULT,
) -> Dict[str, Any]:
    """
    Predict skin type from a Derm Foundation embedding.
    
    Returns:
        {
            "predicted": "oily",
            "confidence": 0.58,
            "probabilities": {
                "dry": 0.12,
                "normal": 0.25,
                "oily": 0.58,
                "redness": 0.05
            }
        }
    """
    emb = _ensure_2d(embedding.astype(np.float32))
    models = _load_skintype_model(models_dir)
    
    model = models["model"]
    model_type = models["model_type"]
    classes = models["config"].get("classes", SKIN_TYPE_CLASSES)
    
    # Get probabilities
    if model_type == "mlp":
        # MLP wrapper handles scaling internally
        proba = model.predict_proba(emb)[0]
    else:
        # LogReg needs explicit scaling
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
    
    probabilities = {cls: round(float(p), 4) for cls, p in zip(classes, proba)}
    
    return {
        "predicted": predicted_class,
        "confidence": round(confidence, 4),
        "probabilities": probabilities,
    }


def analyze_skintype_image(
    image_path: str,
    models_dir: str = SKINTYPE_MODELS_DIR_DEFAULT,
) -> Dict[str, Any]:
    """
    High-level helper: embed image with Derm Foundation and predict skin type.
    
    Returns enriched result with educational content.
    """
    emb = embed_image_path(image_path)
    raw_result = predict_skintype_from_embedding(emb, models_dir=models_dir)
    
    # Enrich with educational content
    return _enrich_skintype_result(raw_result)


def _enrich_skintype_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Add educational content to skin type prediction."""
    
    predicted = raw.get("predicted", "")
    
    SKINTYPE_INFO = {
        "dry": {
            "title": "Dry Skin",
            "description": "Your skin tends to feel tight, rough, or flaky. It may lack moisture and natural oils.",
            "characteristics": [
                "Feels tight after cleansing",
                "May appear dull or rough",
                "Prone to flaking or peeling",
                "Fine lines may be more visible"
            ],
            "care_tips": [
                "Use a gentle, hydrating cleanser",
                "Apply moisturizer while skin is still damp",
                "Look for ingredients like hyaluronic acid and ceramides",
                "Avoid hot water and harsh products",
                "Consider a humidifier in dry environments"
            ],
        },
        "normal": {
            "title": "Normal/Balanced Skin",
            "description": "Your skin is well-balanced with adequate moisture and oil levels.",
            "characteristics": [
                "Neither too oily nor too dry",
                "Small, barely visible pores",
                "Even tone and smooth texture",
                "Few imperfections"
            ],
            "care_tips": [
                "Maintain your routine - it's working!",
                "Use a gentle cleanser twice daily",
                "Apply lightweight moisturizer",
                "Don't skip sunscreen",
                "Focus on maintenance and prevention"
            ],
        },
        "oily": {
            "title": "Oily Skin",
            "description": "Your skin produces excess sebum, which can lead to shine and enlarged pores.",
            "characteristics": [
                "Shiny or greasy appearance, especially in T-zone",
                "Enlarged or visible pores",
                "Prone to blackheads and breakouts",
                "Makeup may not stay put"
            ],
            "care_tips": [
                "Use a gentle, foaming cleanser",
                "Don't skip moisturizer - dehydration triggers more oil",
                "Look for oil-free, non-comedogenic products",
                "Consider niacinamide or salicylic acid",
                "Use blotting papers during the day"
            ],
        },
        "redness": {
            "title": "Skin Redness/Sensitivity",
            "description": "Your skin shows signs of redness, which may indicate sensitivity, irritation, or conditions like rosacea.",
            "characteristics": [
                "Visible redness or flushing",
                "May feel warm or irritated",
                "Reacts easily to products or environment",
                "Possible visible blood vessels"
            ],
            "care_tips": [
                "Use fragrance-free, gentle products",
                "Avoid known triggers (heat, spicy food, alcohol)",
                "Look for calming ingredients like aloe, centella, green tea",
                "Always patch test new products",
                "Consider seeing a dermatologist if persistent"
            ],
            "note": "Persistent redness should be evaluated by a dermatologist to rule out conditions like rosacea."
        },
    }
    
    info = SKINTYPE_INFO.get(predicted, {
        "title": predicted.capitalize(),
        "description": "",
        "characteristics": [],
        "care_tips": [],
    })
    
    return {
        **raw,
        "title": info.get("title", ""),
        "description": info.get("description", ""),
        "characteristics": info.get("characteristics", []),
        "care_tips": info.get("care_tips", []),
        "note": info.get("note"),
    }

