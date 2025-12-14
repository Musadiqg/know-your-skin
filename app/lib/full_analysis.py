"""
Top-level orchestrator to run both cosmetic and concern analysis.

Exposes helpers for analyzing a single image (current API) and for aggregating
results across multiple images from the same person/session.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from config.hudson_products import load_product_config
from lib.cosmetic_inference import analyze_cosmetic_image, predict_cosmetic_from_embedding
from lib.cosmetic_reporting import build_cosmetic_report
from lib.concern_inference import analyze_image, analyze_image_report, analyze_embedding
from lib.derm_local import embed_image_path
from lib.recommendations import build_routine
from lib.reporting import build_report
from lib.session_aggregation import aggregate_concern_probs, aggregate_fitzpatrick_probs


def analyze_full_image(
    image_path: str,
    cosmetic_models_dir: str = "models/cosmetic",
    concern_models_dir: str = "models",
) -> Dict[str, Any]:
    """
    Run cosmetic attribute analysis and concern+routine analysis on the same image
    and return a combined JSON structure:

    {
      "cosmetic": { ... },
      "concerns": { ... }
    }

    The cosmetic and concern layers remain logically separate so they can be
    used together or independently.
    """
    cosmetic_pred = analyze_cosmetic_image(image_path, models_dir=cosmetic_models_dir)
    cosmetic_report = build_cosmetic_report(cosmetic_pred)

    concern_report = analyze_image_report(image_path, models_dir=concern_models_dir)

    return {
        "cosmetic": cosmetic_report,
        "concerns": concern_report,
    }


def analyze_full_session(
    image_paths: List[str],
    cosmetic_models_dir: str = "models/cosmetic",
    concern_models_dir: str = "models",
) -> Dict[str, Any]:
    """
    Run cosmetic and concern analysis on multiple images from the same person
    and aggregate probabilities into a single session-level report.

    OPTIMIZED: Computes embeddings once per image and reuses them for both
    cosmetic and concern analysis, significantly reducing latency.
    """
    if not image_paths:
        raise ValueError("analyze_full_session requires at least one image path")

    # STEP 1: Compute embeddings for all images in PARALLEL
    # This is the expensive Vertex AI call - do it once per image
    with ThreadPoolExecutor(max_workers=len(image_paths)) as executor:
        embeddings = list(executor.map(embed_image_path, image_paths))

    # STEP 2: Run cosmetic and concern predictions on pre-computed embeddings
    # These are fast CPU operations (MLP inference)
    cosmetic_preds = [
        predict_cosmetic_from_embedding(emb, models_dir=cosmetic_models_dir)
        for emb in embeddings
    ]
    concern_preds = [
        analyze_embedding(emb, models_dir=concern_models_dir)
        for emb in embeddings
    ]

    # Aggregate Fitzpatrick probabilities across images.
    fst_mean_probs = aggregate_fitzpatrick_probs(cosmetic_preds)
    if fst_mean_probs:
        fst_items = sorted(fst_mean_probs.items(), key=lambda kv: kv[1], reverse=True)
        fst_primary_label = fst_items[0][0]
        agg_fst = {
            "label": fst_primary_label,
            "probs": fst_mean_probs,
        }
    else:
        agg_fst = None

    # Start from the first image's cosmetic prediction and override FST with
    # the aggregated probabilities.
    cosmetic_base = dict(cosmetic_preds[0]) if cosmetic_preds else {}
    if agg_fst is not None:
        cosmetic_base["fitzpatrick"] = agg_fst

    cosmetic_report = build_cosmetic_report(cosmetic_base)

    # Aggregate concern probabilities and build routine + report using them.
    concern_mean_probs = aggregate_concern_probs(concern_preds)
    if concern_mean_probs:
        base_concerns = dict(concern_preds[0])
        for tag, prob in concern_mean_probs.items():
            info = base_concerns.get(tag, {})
            info["prob"] = float(prob)
            info["active"] = bool(prob >= 0.5)
            base_concerns[tag] = info
    else:
        base_concerns = concern_preds[0] if concern_preds else {}

    product_cfg = load_product_config()
    routine = build_routine(base_concerns, product_cfg)
    concern_report = build_report(base_concerns, routine)

    return {
        "cosmetic": cosmetic_report,
        "concerns": concern_report,
    }



