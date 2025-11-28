"""
Utilities for aggregating per-image predictions into a session-level summary.

We keep this separate so both cosmetic and concern reporting can reuse it
without changing the external API shape.
"""

from typing import Any, Dict, Iterable, List, Tuple

import numpy as np


def aggregate_fitzpatrick_probs(predictions: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    """
    Average Fitzpatrick class probabilities across multiple images.

    Each element in `predictions` is expected to be a dict with a
    `\"fitzpatrick\"` key containing a `\"probs\"` mapping from label to prob.
    """
    probs_list: List[Dict[str, float]] = []
    for pred in predictions:
        fst = pred.get("fitzpatrick")
        if not fst:
            continue
        probs = fst.get("probs")
        if isinstance(probs, dict):
            probs_list.append({str(k): float(v) for k, v in probs.items()})

    if not probs_list:
        return {}

    # Ensure all dicts share the same keys
    labels = sorted(probs_list[0].keys())
    arr = np.array([[p.get(label, 0.0) for label in labels] for p in probs_list], dtype=float)
    mean = arr.mean(axis=0)
    return {label: float(prob) for label, prob in zip(labels, mean)}


def aggregate_concern_probs(
    per_image_concerns: Iterable[Dict[str, Dict[str, Any]]]
) -> Dict[str, float]:
    """
    Average concern probabilities across multiple images.

    Each element is expected to be a dict mapping concern tag -> {\"prob\": float, ...}.
    """
    sums: Dict[str, float] = {}
    counts: Dict[str, int] = {}

    for concerns in per_image_concerns:
        for tag, info in concerns.items():
            prob = float(info.get("prob", 0.0))
            sums[tag] = sums.get(tag, 0.0) + prob
            counts[tag] = counts.get(tag, 0) + 1

    if not sums:
        return {}

    return {tag: sums[tag] / counts[tag] for tag in sums}


