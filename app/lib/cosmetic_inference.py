import functools
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np

from config.cosmetic_targets import FST_LABELS, MONK_TONE_VALUES, TEXTURE_TAGS
from lib.derm_local import embed_image_path


COSMETIC_MODELS_DIR_DEFAULT = "models/cosmetic"


# Filenames for Fitzpatrick models. We default to the MLP version when present,
# but keep the original logistic regression as a fallback.
FST_MLP_SCALER_NAME = "fst_mlp_scaler.joblib"
FST_MLP_MODEL_NAME = "fst_mlp_model.joblib"
FST_LR_SCALER_NAME = "fst_scaler.joblib"
FST_LR_MODEL_NAME = "fst_logreg.joblib"


@functools.lru_cache(maxsize=1)
def _load_cosmetic_models(models_dir: str = COSMETIC_MODELS_DIR_DEFAULT) -> Dict[str, Any]:
    """Load all cosmetic scalers and models from disk (cached)."""
    base = Path(models_dir)

    models: Dict[str, Any] = {}

    # Fitzpatrick: prefer MLP, fall back to logistic regression if needed.
    fst_mlp_scaler_path = base / FST_MLP_SCALER_NAME
    fst_mlp_model_path = base / FST_MLP_MODEL_NAME
    if fst_mlp_scaler_path.exists() and fst_mlp_model_path.exists():
        models["fst_scaler"] = joblib.load(fst_mlp_scaler_path)
        models["fst_model"] = joblib.load(fst_mlp_model_path)
        models["fst_model_type"] = "mlp"
    else:
        fst_scaler_path = base / FST_LR_SCALER_NAME
        fst_model_path = base / FST_LR_MODEL_NAME
        if fst_scaler_path.exists() and fst_model_path.exists():
            models["fst_scaler"] = joblib.load(fst_scaler_path)
            models["fst_model"] = joblib.load(fst_model_path)
            models["fst_model_type"] = "logreg"

    # Monk tone
    monk_scaler_path = base / "monk_scaler.joblib"
    monk_model_path = base / "monk_logreg.joblib"
    if monk_scaler_path.exists() and monk_model_path.exists():
        models["monk_scaler"] = joblib.load(monk_scaler_path)
        models["monk_model"] = joblib.load(monk_model_path)

    # Texture
    texture_scaler_path = base / "texture_scaler.joblib"
    texture_model_path = base / "texture_logreg.joblib"
    if texture_scaler_path.exists() and texture_model_path.exists():
        models["texture_scaler"] = joblib.load(texture_scaler_path)
        models["texture_model"] = joblib.load(texture_model_path)

    if not models:
        raise FileNotFoundError(
            f"No cosmetic models found in {base}. "
            "Run `python scripts/train_cosmetic_attributes.py` first."
        )

    return models


def _ensure_2d(emb: np.ndarray) -> np.ndarray:
    if emb.ndim == 1:
        return emb.reshape(1, -1)
    return emb


def predict_cosmetic_from_embedding(
    embedding: np.ndarray,
    models_dir: str = COSMETIC_MODELS_DIR_DEFAULT,
) -> Dict[str, Any]:
    """
    Run Fitzpatrick, Monk tone, and texture classifiers on a Derm embedding.
    Returns a nested dict suitable for cosmetic reporting.
    """
    emb = _ensure_2d(embedding.astype(np.float32))
    models = _load_cosmetic_models(models_dir)
    result: Dict[str, Any] = {}

    # Fitzpatrick
    fst_scaler = models.get("fst_scaler")
    fst_model = models.get("fst_model")
    if fst_scaler is not None and fst_model is not None:
        X_std = fst_scaler.transform(emb)
        proba = fst_model.predict_proba(X_std)[0]
        label_idx = int(np.argmax(proba))
        result["fitzpatrick"] = {
            "label": FST_LABELS[label_idx],
            "probs": {FST_LABELS[i]: float(p) for i, p in enumerate(proba)},
        }

    # Monk tone
    monk_scaler = models.get("monk_scaler")
    monk_model = models.get("monk_model")
    if monk_scaler is not None and monk_model is not None:
        X_std = monk_scaler.transform(emb)
        proba = monk_model.predict_proba(X_std)[0]
        label_idx = int(np.argmax(proba))
        result["monk_tone"] = {
            "label": MONK_TONE_VALUES[label_idx],
            "probs": {str(MONK_TONE_VALUES[i]): float(p) for i, p in enumerate(proba)},
        }

    # Texture (multi-label)
    texture_scaler = models.get("texture_scaler")
    texture_model = models.get("texture_model")
    if texture_scaler is not None and texture_model is not None:
        X_std = texture_scaler.transform(emb)
        proba_list: List[np.ndarray] = texture_model.predict_proba(X_std)
        texture_info: Dict[str, Any] = {}
        for tag, p in zip(TEXTURE_TAGS, proba_list):
            # p shape: (n_samples, 2); probability of positive class is column 1
            if p.shape[1] >= 2:
                prob_pos = float(p[0, 1])
            else:
                prob_pos = float(p[0, -1])
            texture_info[tag] = {
                "prob": prob_pos,
                "active": bool(prob_pos >= 0.5),
            }
        result["texture"] = texture_info

    return result


def analyze_cosmetic_image(
    image_path: str,
    models_dir: str = COSMETIC_MODELS_DIR_DEFAULT,
) -> Dict[str, Any]:
    """
    High-level helper: embed image with Derm Foundation and run cosmetic attribute classifiers.
    """
    emb = embed_image_path(image_path)
    return predict_cosmetic_from_embedding(emb, models_dir=models_dir)



