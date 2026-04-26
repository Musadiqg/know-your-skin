"""
Rule-based product recommendation module.

Takes concern classifier output and the brand product config, and builds a
simple skincare routine (cleanser, treatment, moisturizer, sunscreen).
"""

from typing import Any, Dict, List, Tuple

from config.brand_products import PRODUCT_CONFIG, ROUTINE_STEPS, ProductConfig


# Business-tunable parameters
MIN_PROB_FOR_CONCERN: float = 0.25
MAX_PRODUCTS_PER_STEP: int = 1


def _get_active_concerns(concern_results: Dict[str, Dict[str, Any]]) -> List[Tuple[str, float]]:
    """Return list of (tag, prob) for active concerns, sorted by prob desc."""
    items: List[Tuple[str, float]] = []
    for tag, info in concern_results.items():
        prob = float(info.get("prob", 0.0))
        # Only include concerns that allow product recommendations
        can_recommend = info.get("can_recommend_products", True)
        if prob >= MIN_PROB_FOR_CONCERN and can_recommend:
            items.append((tag, prob))
    # If nothing passes the threshold, fall back to the single highest-prob concern that allows recommendations
    if not items and concern_results:
        eligible = {
            tag: info for tag, info in concern_results.items()
            if info.get("can_recommend_products", True)
        }
        if eligible:
            tag, info = max(eligible.items(), key=lambda kv: float(kv[1].get("prob", 0.0)))
            items.append((tag, float(info.get("prob", 0.0))))
    # Sort by probability descending
    items.sort(key=lambda tp: tp[1], reverse=True)
    return items


def build_routine(
    concern_results: Dict[str, Dict[str, Any]],
    product_config: Dict[str, ProductConfig] | None = None,
) -> Dict[str, Any]:
    """
    Build a simple routine from concern results and product config.

    concern_results: output from analyze_embedding/analyze_image
        {concern_tag: {"prob": float, "active": bool, ...}}

    Returns:
        {
          "concerns": [("Dry_Sensitive", 0.82), ...],
          "steps": {
            "cleanser": ["moisture_balancing_cleanser"],
            "treatment": ["blemish_age_defense_serum"],
            "moisturizer": ["daily_moisturizer"],
            "sunscreen": ["facial_gel_sunscreen"],
          }
        }
    """
    if product_config is None:
        product_config = PRODUCT_CONFIG

    active_concerns = _get_active_concerns(concern_results)
    concern_prob_map = {tag: prob for tag, prob in active_concerns}

    # Determine if we need gentle-only products
    needs_gentle_only = any(
        concern_results.get(tag, {}).get("recommendation_type") == "gentle_only"
        for tag, _ in active_concerns
    )
    
    # Score products by how well they match active concerns
    candidates_by_step: Dict[str, List[Tuple[str, float]]] = {step: [] for step in ROUTINE_STEPS}

    for pid, cfg in product_config.items():
        step = cfg["step"]
        if step not in ROUTINE_STEPS:
            continue
        supported = cfg.get("supported_concerns", [])
        score = 0.0
        
        # Check if product matches any active concern
        for tag in supported:
            if tag in concern_prob_map:
                score += concern_prob_map[tag]
        
        # If gentle_only is required, prioritize gentle products
        # (For now, we assume all products in our config are gentle enough,
        # but we could add a "gentle" flag to products if needed)
        if score > 0.0:
            candidates_by_step[step].append((pid, score))

    # Pick top products per step
    chosen_steps: Dict[str, List[str]] = {}
    for step in ROUTINE_STEPS:
        cands = candidates_by_step.get(step, [])
        if not cands:
            continue
        # Sort by score desc, then by product id for determinism
        cands.sort(key=lambda x: (x[1], x[0]), reverse=True)
        chosen_steps[step] = [pid for pid, _ in cands[:MAX_PRODUCTS_PER_STEP]]

    routine = {
        "concerns": active_concerns,
        "steps": chosen_steps,
    }
    return routine



