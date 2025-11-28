import functools
import json
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np

from config.scin_conditions import CONDITION_LABELS
from lib.derm_local import embed_image_path


@functools.lru_cache(maxsize=1)
def _load_condition_models(models_dir: str = "models") -> Dict[str, Any]:
    """
    Load scaler and SCIN condition classifier from disk (cached).

    Expects the following files (as written by `scripts/train_scin_conditions.py`):
      - scin_conditions_scaler.joblib
      - scin_conditions_logreg.joblib
      - scin_conditions_metrics.json (optional but recommended)
    """
    models_path = Path(models_dir)
    scaler_path = models_path / "scin_conditions_scaler.joblib"
    model_path = models_path / "scin_conditions_logreg.joblib"
    metrics_path = models_path / "scin_conditions_metrics.json"

    if not scaler_path.exists() or not model_path.exists():
        raise FileNotFoundError(
            f"Expected condition models not found in {models_path}. "
            "Run `python scripts/train_scin_conditions.py` first."
        )

    scaler = joblib.load(scaler_path)
    clf = joblib.load(model_path)

    metrics: Dict[str, Any] | None = None
    if metrics_path.exists():
        try:
            with metrics_path.open("r", encoding="utf-8") as f:
                metrics = json.load(f)
        except Exception:
            metrics = None

    return {"scaler": scaler, "clf": clf, "metrics": metrics}


def _ensure_2d(emb: np.ndarray) -> np.ndarray:
    if emb.ndim == 1:
        return emb.reshape(1, -1)
    return emb


def _summarize_reliability(f1: float | None, support: int | None) -> Dict[str, str]:
    """
    Turn test-set F1/support into a coarse reliability label and short text.

    This does NOT describe per-image correctness. It summarizes how this
    label performed on the held-out SCIN validation set.
    """
    if f1 is None or support is None:
        return {
            "level": "unknown",
            "text": "We do not yet have enough validation data to summarize performance for this label.",
        }

    # Very rough buckets that you can tune as needed.
    if f1 >= 0.6 and support >= 50:
        level = "high"
        text = (
            f"On a dermatology validation set, this label showed relatively strong performance "
            f"(about {f1*100:.0f}% F1 over {support} examples)."
        )
    elif f1 >= 0.45 and support >= 20:
        level = "medium"
        text = (
            f"On a dermatology validation set, this label performed moderately well "
            f"(about {f1*100:.0f}% F1 over {support} examples)."
        )
    else:
        level = "low"
        text = (
            f"For this label, the model had limited performance or data in validation "
            f"(about {f1*100:.0f}% F1 over {support} examples), so treat it as a softer hint."
        )

    return {"level": level, "text": text}


def predict_conditions_from_embedding(
    embedding: np.ndarray,
    models_dir: str = "models",
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Run the SCIN condition classifier on a Derm Foundation embedding.

    Returns a dict:
      {
        "conditions": {
          "<condition_name>": {"prob": float, "active": bool},
          ...
        }
      }
    where `prob` is the classifier's probability for that condition being present
    in this image, and `active` is True when prob >= threshold.
    """
    emb = _ensure_2d(embedding.astype(np.float32))
    models = _load_condition_models(models_dir)
    scaler = models["scaler"]
    clf = models["clf"]
    metrics = models.get("metrics") or {}

    emb_std = scaler.transform(emb)
    proba_list: List[np.ndarray] = clf.predict_proba(emb_std)

    result: Dict[str, Any] = {}
    for cond_name, p in zip(CONDITION_LABELS, proba_list):
        # p shape: (n_samples, 2) for each binary classifier
        if p.shape[1] >= 2:
            prob_pos = float(p[0, 1])
        else:
            prob_pos = float(p[0, -1])

        # Attach training-time reliability metrics if available. These come
        # from the held-out test set classification report and give a rough
        # sense of how well this label performs overall (not case-specific).
        cond_metrics_raw = metrics.get(cond_name) if isinstance(metrics, dict) else None
        cond_metrics: Dict[str, Any] = {}
        if isinstance(cond_metrics_raw, dict):
            for key in ("precision", "recall", "f1-score", "support"):
                if key in cond_metrics_raw:
                    # Cast to plain Python types for JSON friendliness.
                    if key == "support":
                        cond_metrics["support"] = int(cond_metrics_raw[key])
                    elif key == "f1-score":
                        cond_metrics["f1"] = float(cond_metrics_raw[key])
                    else:
                        cond_metrics[key] = float(cond_metrics_raw[key])

        # Human-friendly reliability summary based on F1/support.
        f1_val = cond_metrics.get("f1")
        support_val = cond_metrics.get("support")
        reliability = _summarize_reliability(
            f1_val if isinstance(f1_val, (int, float)) else None,
            support_val if isinstance(support_val, int) else None,
        )

        result[cond_name] = {
            "prob": prob_pos,
            "active": bool(prob_pos >= threshold),
            "metrics": cond_metrics,
            "reliability": reliability,
        }

    return {"conditions": result}


def analyze_conditions_image(
    image_path: str,
    models_dir: str = "models",
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    High-level helper: embed a local image with Derm Foundation and run the
    SCIN condition classifier to get per-condition probabilities.
    """
    emb = embed_image_path(image_path)
    return predict_conditions_from_embedding(emb, models_dir=models_dir, threshold=threshold)



