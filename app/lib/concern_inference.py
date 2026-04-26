import functools
from pathlib import Path
from typing import Dict, List, Any

import joblib
import numpy as np

from config.concerns import CONCERN_CONFIG, CONCERN_TAGS, CONCERN_MAP
from config.brand_products import load_product_config
from lib.derm_local import embed_image_path
from lib.recommendations import build_routine
from lib.reporting import build_report


@functools.lru_cache(maxsize=1)
def _load_models(models_dir: str = "models") -> Dict[str, Any]:
    """Load scaler and concern classifier from disk (cached)."""
    models_path = Path(models_dir)
    scaler_path = models_path / "scin_concerns_scaler.joblib"
    model_path = models_path / "scin_concerns_logreg.joblib"

    if not scaler_path.exists() or not model_path.exists():
        raise FileNotFoundError(
            f"Expected concern models not found in {models_path}. "
            "Run `python scripts/train_scins_concerns.py` first."
        )

    scaler = joblib.load(scaler_path)
    clf = joblib.load(model_path)
    return {"scaler": scaler, "clf": clf}


def _proba_to_binary(proba_list: List[np.ndarray], threshold: float = 0.5) -> np.ndarray:
    cols = []
    for p in proba_list:
        if p.shape[1] == 2:
            cols.append((p[:, 1] >= threshold).astype(int))
        else:
            cols.append((p[:, -1] >= threshold).astype(int))
    return np.column_stack(cols)


def _build_scin_labels_lookup() -> Dict[str, List[str]]:
    """
    Build reverse mapping from concern tag to list of SCIN labels that map to it.
    This is informational only - shows which SCIN labels correspond to each concern.
    """
    reverse_map: Dict[str, List[str]] = {tag: [] for tag in CONCERN_TAGS}
    for scin_label, concern_tags in CONCERN_MAP.items():
        for concern_tag in concern_tags:
            if concern_tag in reverse_map:
                reverse_map[concern_tag].append(scin_label)
    return reverse_map


def analyze_embedding(
    embedding: np.ndarray,
    models_dir: str = "models",
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Run the trained concern classifier on a single Derm Foundation embedding.

    Returns a dict keyed by concern tag with probability, active flag, and
    user-facing metadata from CONCERN_CONFIG.
    """
    if embedding.ndim == 1:
        embedding = embedding.reshape(1, -1)

    models = _load_models(models_dir)
    scaler = models["scaler"]
    clf = models["clf"]

    emb_std = scaler.transform(embedding)
    proba_list = clf.predict_proba(emb_std)

    probs = []
    for p in proba_list:
        if p.shape[1] == 2:
            probs.append(float(p[0, 1]))
        else:
            probs.append(float(p[0, -1]))

    preds = _proba_to_binary(proba_list, threshold=threshold)[0]

    # Build reverse lookup: concern tag -> list of SCIN labels
    scin_labels_lookup = _build_scin_labels_lookup()

    result: Dict[str, Any] = {}
    for idx, tag in enumerate(CONCERN_TAGS):
        cfg = CONCERN_CONFIG.get(tag, {})
        result[tag] = {
            "prob": probs[idx],
            "active": bool(preds[idx]),
            "title": cfg.get("title", tag),
            "description": cfg.get("description", ""),
            "disclaimer": cfg.get("disclaimer", ""),
            "recommended_products": cfg.get("recommended_products", []),
            # Add SCIN labels that map to this concern tag (informational)
            "scin_labels": scin_labels_lookup.get(tag, []),
        }
    return result


def analyze_image(
    image_path: str,
    models_dir: str = "models",
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    High-level helper: embed a local image with Derm Foundation and run the
    concern classifier.
    """
    emb = embed_image_path(image_path)
    return analyze_embedding(emb, models_dir=models_dir, threshold=threshold)


def analyze_image_with_routine(
    image_path: str,
    models_dir: str = "models",
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Extended helper: run concern analysis and build a product routine
    using the brand product configuration.
    """
    concerns = analyze_image(image_path, models_dir=models_dir, threshold=threshold)
    product_cfg = load_product_config()
    routine = build_routine(concerns, product_cfg)
    return {
        "concerns": concerns,
        "routine": routine,
    }


def analyze_image_report(
    image_path: str,
    models_dir: str = "models",
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Full pipeline: embed image, get concerns, build routine, and assemble
    a user-friendly report structure.
    """
    concerns_only = analyze_image(image_path, models_dir=models_dir, threshold=threshold)
    product_cfg = load_product_config()
    routine = build_routine(concerns_only, product_cfg)
    report = build_report(concerns_only, routine)
    return report




