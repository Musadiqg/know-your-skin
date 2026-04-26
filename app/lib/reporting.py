"""
Reporting utilities to turn model outputs into a user-friendly skin report.
"""

from typing import Any, Dict, List, Tuple

from config.concerns import CONCERN_CONFIG
from config.brand_products import PRODUCT_CONFIG, ProductConfig


# Tunable parameters
MAX_CONCERNS_IN_SUMMARY = 3
# Minimum probability for including a concern section at all.
MIN_PROB_FOR_SECTION = 0.25
# Thresholds for primary / secondary concern logic.
PRIMARY_MIN_PROB = 0.4
SECONDARY_MIN_PROB = 0.25
SECONDARY_MAX_GAP = 0.15


def _describe_probability(prob: float) -> str:
    """Map numeric probability to friendly language."""
    if prob >= 0.6:
        return "strong patterns"
    if prob >= 0.4:
        return "clear patterns"
    if prob >= 0.25:
        return "some features"
    return "subtle hints"


def _format_concern_body(tag: str, prob: float) -> str:
    cfg = CONCERN_CONFIG.get(tag, {})
    description = cfg.get("description", "")
    what_it_means = cfg.get("what_it_means", "")
    care_focus = cfg.get("care_focus", "")
    intensity = _describe_probability(prob)

    parts: List[str] = []
    if description:
        parts.append(description)
    if what_it_means:
        parts.append(what_it_means)
    if care_focus:
        parts.append(f"In terms of care, a good focus is: {care_focus}")

    # Prepend intensity phrase if we have any text
    if parts:
        intro = f"We see {intensity} that can be seen with this type of skin pattern."
        return " ".join([intro] + parts)
    return ""


def _split_primary_secondary(
    active_concerns: List[Tuple[str, float]]
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """
    Given (tag, prob) pairs sorted by prob desc, split into primary and secondary
    concerns using configurable thresholds.
    """
    if not active_concerns:
        return [], []

    # active_concerns are already sorted by prob desc (see recommendations.build_routine)
    primary_tag, primary_prob = active_concerns[0]
    if primary_prob < PRIMARY_MIN_PROB:
        # No strong primary concern; treat all as secondary
        return [], active_concerns

    primary = [(primary_tag, primary_prob)]
    secondary: List[Tuple[str, float]] = []

    for tag, prob in active_concerns[1:]:
        if prob >= SECONDARY_MIN_PROB and (primary_prob - prob) <= SECONDARY_MAX_GAP:
            secondary.append((tag, prob))

    return primary, secondary


def _build_summary(active_concerns: List[Tuple[str, float]]) -> str:
    if not active_concerns:
        return (
            "We analyzed this photo but did not find any strong, consistent patterns. "
            "Your skin may still benefit from gentle daily care and sunscreen, and for any worries "
            "it's always best to speak with a skin professional."
        )

    max_prob = max(prob for _, prob in active_concerns)

    # If no concern stands out strongly, lean into a reassuring, maintenance-focused message.
    if max_prob < 0.45:
        return (
            "We used an AI-based cosmetic model to review the image you shared and did not see strong patterns "
            "of common skin concerns. That is generally reassuring. "
            "Gentle cleansing, a suitable moisturizer, and daily sunscreen are usually enough to maintain healthy-looking skin. "
            "If anything about your skin is worrying or changing quickly, it's still a good idea to check in with a skin professional."
        )

    top = active_concerns[:MAX_CONCERNS_IN_SUMMARY]
    concern_phrases = []
    for tag, prob in top:
        cfg = CONCERN_CONFIG.get(tag, {})
        title = cfg.get("title", tag.replace("_", " "))
        intensity = _describe_probability(prob)
        concern_phrases.append(f"{intensity} associated with {title.lower()}")

    if len(concern_phrases) == 1:
        concerns_text = concern_phrases[0]
    elif len(concern_phrases) == 2:
        concerns_text = " and ".join(concern_phrases)
    else:
        concerns_text = ", ".join(concern_phrases[:-1]) + f", and {concern_phrases[-1]}"

    return (
        "We used an AI-based cosmetic model to review the image you shared. "
        f"In this photo we see {concerns_text}. "
        "Different skin patterns can overlap, so this is not a diagnosis, but a guide to the kinds of care "
        "that may support your skin."
    )


def _enrich_routine(
    routine: Dict[str, Any],
    active_concerns: List[Tuple[str, float]],
) -> Dict[str, Any]:
    """Attach per-product rationales to the routine steps."""
    active_tags = [tag for tag, _ in active_concerns]
    enriched_steps: Dict[str, List[Dict[str, Any]]] = {}

    for step, product_ids in routine.get("steps", {}).items():
        enriched_steps[step] = []
        for pid in product_ids:
            cfg: ProductConfig | None = PRODUCT_CONFIG.get(pid)  # type: ignore[assignment]
            if not cfg:
                continue

            name = cfg["name"]
            portfolio = cfg.get("portfolio") or ""
            supported = cfg.get("supported_concerns", [])
            matched = [t for t in supported if t in active_tags]
            concern_titles = [
                CONCERN_CONFIG.get(t, {}).get("title", t.replace("_", " ")) for t in matched
            ]
            concern_text = ", ".join(concern_titles) if concern_titles else "your overall skin goals"

            template = cfg.get("why_template")
            if template:
                why = template.format(name=name, concerns=concern_text, step=step, portfolio=portfolio)
            else:
                why = (
                    f"Because your photo suggests {concern_text}, we recommend {name}, a {step} "
                    f"from our {portfolio} range to support this area."
                ).strip()

            enriched_steps[step].append(
                {
                    "id": cfg["id"],
                    "name": name,
                    "step": step,
                    # Optional product image filename (e.g. \"daily_moisturizer.png\").
                    # The client can map this to an actual asset or URL.
                    "image_name": cfg.get("image_name"),
                    "why": why,
                }
            )

    enriched = dict(routine)
    enriched["steps"] = enriched_steps
    return enriched


def build_report(
    concern_results: Dict[str, Dict[str, Any]],
    routine: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assemble a full user-facing report from concerns and routine.
    """
    # Active concerns list is already computed by the recommendation module
    active_concerns: List[Tuple[str, float]] = routine.get("concerns", [])

    summary = _build_summary(active_concerns)

    concern_sections: List[Dict[str, Any]] = []
    for tag, prob in active_concerns:
        if prob < MIN_PROB_FOR_SECTION:
            continue
        cfg = CONCERN_CONFIG.get(tag, {})
        body = _format_concern_body(tag, prob)
        # Include SCIN labels if available in concern_results
        scin_labels = concern_results.get(tag, {}).get("scin_labels", [])
        concern_sections.append(
            {
                "tag": tag,
                "title": cfg.get("title", tag.replace("_", " ")),
                "body": body,
                "prob": prob,
                "scin_labels": scin_labels,  # SCIN labels that map to this concern
            }
        )

    enriched_routine = _enrich_routine(routine, active_concerns)

    disclaimer = (
        "This experience is powered by an AI-based cosmetic skin analysis and is not a medical diagnosis. "
        "It cannot rule out skin disease or serious conditions. If you notice pain, bleeding, rapidly changing areas, "
        "or anything that worries you, please consult a dermatologist or healthcare professional."
    )

    return {
        "summary": summary,
        "concern_sections": concern_sections,
        "routine": enriched_routine,
        "disclaimer": disclaimer,
    }



