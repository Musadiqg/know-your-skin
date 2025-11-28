"""
Turn cosmetic predictions (Fitzpatrick, Monk tone, texture) into a
user-facing educational report.
"""

from typing import Any, Dict, List, Tuple

from config.cosmetic_copy import (
    FST_COPY,
    MONK_TONE_RANGES,
    MONK_COPY,
    TEXTURE_COPY,
    COSMETIC_DISCLAIMER,
)


def _pick_monk_range_label(tone_label: int) -> str:
    for entry in MONK_TONE_RANGES:
        if tone_label in entry["range"]:
            return entry["name"]
    # Fallback
    return "medium tones"


def _active_textures(texture_pred: Dict[str, Dict[str, Any]]) -> List[Tuple[str, Dict[str, str]]]:
    active: List[Tuple[str, Dict[str, str]]] = []
    for tag, info in texture_pred.items():
        if info.get("active"):
            copy = TEXTURE_COPY.get(tag)
            if copy:
                active.append((tag, copy))
    # If none are above threshold, still show the highest-prob one as a soft hint.
    if not active and texture_pred:
        best_tag = max(texture_pred.items(), key=lambda kv: kv[1].get("prob", 0.0))[0]
        copy = TEXTURE_COPY.get(best_tag)
        if copy:
            active.append((best_tag, copy))
    return active


def _pick_fitzpatrick_labels(probs: Dict[str, float]) -> Dict[str, Any]:
    """
    Decide whether to present a single Fitzpatrick type or a 2-type range
    based on class probabilities.
    """
    if not probs:
        return {
            "label_mode": "unknown",
            "labels": [],
            "primary_label": None,
        }

    # Sort labels by probability descending
    items = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    (top1_label, top1_prob) = items[0]
    if len(items) > 1:
        (top2_label, top2_prob) = items[1]
    else:
        top2_label, top2_prob = None, 0.0

    # Single label if confident and well separated from the second best.
    if top1_prob >= 0.6 and (top1_prob - top2_prob) >= 0.15:
        return {
            "label_mode": "single",
            "labels": [top1_label],
            "primary_label": top1_label,
        }

    # Otherwise present a range over the top two labels.
    labels = [top1_label]
    if top2_label is not None:
        labels.append(top2_label)

    return {
        "label_mode": "range",
        "labels": labels,
        "primary_label": top1_label,
    }


def build_cosmetic_report(cosmetic_predictions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a structured cosmetic report from predictions:

    {
      "summary": str,
      "tone_section": { ... },
      "texture_section": { ... },
      "disclaimer": str,
    }
    """
    fst = cosmetic_predictions.get("fitzpatrick")
    monk = cosmetic_predictions.get("monk_tone")
    texture = cosmetic_predictions.get("texture", {})

    summary_parts: List[str] = []
    if fst:
        fst_probs = fst.get("probs", {})
        fst_labels_info = _pick_fitzpatrick_labels(fst_probs)
        labels = fst_labels_info.get("labels", [])
        primary_label = fst_labels_info.get("primary_label")

        if primary_label:
            fst_copy = FST_COPY.get(primary_label, {})
            if fst_copy:
                if fst_labels_info.get("label_mode") == "range" and len(labels) == 2:
                    label_titles = [
                        FST_COPY.get(lbl, {}).get("title", lbl) for lbl in labels
                    ]
                    range_text = "–".join(label_titles)
                    summary_parts.append(
                        f"We see features that place your skin between {range_text}, "
                        "which gives us a sense of how your skin may respond to sun and active ingredients."
                    )
                else:
                    summary_parts.append(
                        f"We see features that align with {fst_copy.get('title', 'your skin type')}, "
                        "which gives us a sense of how your skin may respond to sun and active ingredients."
                    )
    if monk:
        tone_label = int(monk.get("label"))
        tone_name = _pick_monk_range_label(tone_label)
        monk_text = MONK_COPY.get(tone_name)
        if monk_text:
            summary_parts.append(
                f"Your overall tone appears to sit in the range of {tone_name}, which influences how marks and color "
                "changes show up on your skin."
            )

    if not summary_parts:
        summary = (
            "We used an AI-based model to estimate a few cosmetic characteristics of your skin from this photo, "
            "such as overall tone and visible texture. These insights can guide gentle daily care and product choices."
        )
    else:
        summary = " ".join(summary_parts)

    tone_section: Dict[str, Any] = {}
    if fst:
        fst_probs = fst.get("probs", {})
        fst_labels_info = _pick_fitzpatrick_labels(fst_probs)
        labels = fst_labels_info.get("labels", [])
        primary_label = fst_labels_info.get("primary_label")
        label_mode = fst_labels_info.get("label_mode")

        if primary_label:
            fst_copy = FST_COPY.get(primary_label, {})
            if fst_copy:
                tone_section["fitzpatrick"] = {
                    "label": primary_label,
                    "label_mode": label_mode,
                    "labels": labels,
                    "title": fst_copy.get("title"),
                    "overview": fst_copy.get("overview"),
                    "care_focus": fst_copy.get("care_focus"),
                    "probs": fst_probs,
                }
    if monk:
        tone_label = int(monk.get("label"))
        tone_name = _pick_monk_range_label(tone_label)
        tone_section["monk_tone"] = {
            "label": tone_label,
            "group_name": tone_name,
            "education": MONK_COPY.get(tone_name),
            "probs": monk.get("probs", {}),
        }

    texture_section: Dict[str, Any] = {}
    if texture:
        active = _active_textures(texture)
        if active:
            texture_section["items"] = [
                {"tag": tag, "title": copy["title"], "body": copy["body"], "prob": float(texture[tag]["prob"])}
                for tag, copy in active
            ]

    return {
        "summary": summary,
        "tone_section": tone_section,
        "texture_section": texture_section,
        "disclaimer": COSMETIC_DISCLAIMER,
    }



