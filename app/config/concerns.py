"""
Definitions for high-level skin concerns, mappings from SCIN condition labels,
and user-facing messaging + product hooks for the prototype.
"""

from typing import Dict, List


# Six customer-facing concern tags
CONCERN_TAGS: List[str] = [
    "Dry_Sensitive",
    "Breakouts_Bumps",
    "Itchy_Hives",
    "Red_Scaly_Patches",
    "Pigment_Tone_Issues",
    "Possible_Infection",
]


# Minimum dermatologist confidence (1–5) for using a SCIN label
MIN_DERM_CONFIDENCE: int = 3


# Mapping from SCIN condition label (exact string) to one or more concern tags.
# This is not exhaustive; we only map the most common / relevant conditions for
# this prototype. Unmapped conditions are ignored when building concern labels.
CONCERN_MAP: Dict[str, List[str]] = {
    # Dry / sensitive / eczematous patterns
    "Eczema": ["Dry_Sensitive"],
    "Acute dermatitis, NOS": ["Dry_Sensitive"],
    "Acute and chronic dermatitis": ["Dry_Sensitive"],
    "Seborrheic Dermatitis": ["Dry_Sensitive", "Red_Scaly_Patches"],
    "Irritant Contact Dermatitis": ["Dry_Sensitive"],
    "Allergic Contact Dermatitis": ["Dry_Sensitive", "Itchy_Hives"],
    "CD - Contact dermatitis": ["Dry_Sensitive"],
    "Stasis Dermatitis": ["Dry_Sensitive", "Red_Scaly_Patches"],
    "Lichen Simplex Chronicus": ["Dry_Sensitive"],

    # Breakouts / bumps
    "Acne": ["Breakouts_Bumps"],
    "Folliculitis": ["Breakouts_Bumps"],
    "Molluscum Contagiosum": ["Breakouts_Bumps"],
    "Prurigo nodularis": ["Breakouts_Bumps", "Dry_Sensitive"],

    # Itchy / hives / bites / hypersensitivity
    "Insect Bite": ["Itchy_Hives"],
    "Urticaria": ["Itchy_Hives"],
    "Hypersensitivity": ["Itchy_Hives"],
    "Viral Exanthem": ["Itchy_Hives", "Possible_Infection"],

    # Red, scaly patches / inflammatory plaques
    "Psoriasis": ["Red_Scaly_Patches"],
    "Pityriasis rosea": ["Red_Scaly_Patches"],
    "Lichen planus/lichenoid eruption": ["Red_Scaly_Patches"],
    "Pityriasis lichenoides": ["Red_Scaly_Patches"],
    "Cutaneous lupus": ["Red_Scaly_Patches"],

    # Pigmentation / tone issues
    "Post-Inflammatory hyperpigmentation": ["Pigment_Tone_Issues"],
    "Pigmented purpuric eruption": ["Pigment_Tone_Issues"],
    "Keratosis pilaris": ["Pigment_Tone_Issues", "Breakouts_Bumps"],
    "O/E - ecchymoses present": ["Pigment_Tone_Issues"],

    # Possible infections (use carefully, non-diagnostic wording)
    "Tinea": ["Possible_Infection"],
    "Tinea Versicolor": ["Possible_Infection", "Pigment_Tone_Issues"],
    "Impetigo": ["Possible_Infection"],
    "Herpes Zoster": ["Possible_Infection"],
    "Herpes Simplex": ["Possible_Infection"],
    "Cellulitis": ["Possible_Infection"],
    "Abscess": ["Possible_Infection"],
    "Scabies": ["Possible_Infection", "Itchy_Hives"],
}


# User-facing messaging and product hooks per concern tag.
# Product IDs are placeholders for now – replace with real SKUs from your catalog.
CONCERN_CONFIG: Dict[str, Dict[str, object]] = {
    "Dry_Sensitive": {
        "title": "Dry or Sensitive Skin Tendencies",
        "description": (
            "Your photo shows patterns often associated with dry or easily irritated skin. "
            "This may include visible flaking, redness, or rough patches."
        ),
        "what_it_means": (
            "These features suggest that your skin barrier may be a bit fragile or dehydrated, "
            "so it can lose moisture more quickly and react to harsh products or weather changes."
        ),
        "care_focus": (
            "Focus on gentle cleansing, replenishing moisture, and protecting the skin barrier with "
            "soothing, fragrance-free products."
        ),
        "disclaimer": (
            "This is an AI-based cosmetic skin analysis, not a medical diagnosis. "
            "If you have pain, rapid changes, or health concerns, please see a dermatologist."
        ),
        "recommended_products": [
            "hydrating_cleanser",
            "barrier_repair_moisturizer",
            "gentle_spf",
        ],
    },
    "Breakouts_Bumps": {
        "title": "Breakouts and Bumps",
        "description": (
            "We detect patterns often seen with clogged pores, breakouts, or follicle-related bumps."
        ),
        "what_it_means": (
            "This can happen when excess oil, dead skin, or bacteria build up in pores or around hair follicles, "
            "leading to blemishes or tiny bumps on the skin."
        ),
        "care_focus": (
            "Focus on balancing oil, gently exfoliating to keep pores clear, and avoiding products that clog pores."
        ),
        "disclaimer": (
            "This is not a medical diagnosis. For severe, painful, or persistent acne, "
            "consult a dermatologist."
        ),
        "recommended_products": [
            "clarifying_cleanser",
            "lightweight_noncomedogenic_moisturizer",
            "targeted_bha_serum",
        ],
    },
    "Itchy_Hives": {
        "title": "Itch, Hives, or Bite-like Areas",
        "description": (
            "Your image shows patterns that can be seen with itchy, hive-like, or bite-like areas."
        ),
        "what_it_means": (
            "These patterns may reflect irritation or a reactive response in the skin, which can be triggered by "
            "many factors such as friction, bites, or contact with allergens."
        ),
        "care_focus": (
            "Focus on calming and protecting the skin, avoiding harsh products, and keeping the area moisturized "
            "without over-scrubbing."
        ),
        "disclaimer": (
            "Only a clinician can diagnose allergic reactions or bites. "
            "If symptoms are severe, spreading, or accompanied by other signs, seek medical care."
        ),
        "recommended_products": [
            "soothing_lotion",
            "fragrance_free_moisturizer",
        ],
    },
    "Red_Scaly_Patches": {
        "title": "Red or Scaly Patches",
        "description": (
            "We see features that may correspond to red, scaly, or plaque-like areas on the skin."
        ),
        "what_it_means": (
            "Red and scaly areas can appear when the skin is inflamed and turning over more quickly, "
            "which is seen in several common skin conditions."
        ),
        "care_focus": (
            "Focus on very gentle cleansing, rich but non-irritating moisturizers, and daily sun protection "
            "to support the skin while you discuss any persistent patches with a professional."
        ),
        "disclaimer": (
            "Conditions like psoriasis or dermatitis require professional diagnosis. "
            "This analysis is cosmetic only and may miss important findings."
        ),
        "recommended_products": [
            "rich_emollient_cream",
            "gentle_scalp_or_body_wash",
        ],
    },
    "Pigment_Tone_Issues": {
        "title": "Pigment and Tone Irregularities",
        "description": (
            "Your photo shows patterns that can be associated with uneven skin tone or spots, "
            "such as post-blemish marks or areas of darker or lighter pigmentation."
        ),
        "what_it_means": (
            "These findings suggest that your skin may be developing or holding onto areas of extra or reduced pigment, "
            "often after breakouts, sun exposure, or previous irritation."
        ),
        "care_focus": (
            "Focus on consistent sun protection and targeted brightening steps, while keeping the skin barrier healthy "
            "and avoiding aggressive at-home treatments."
        ),
        "disclaimer": (
            "This is not a diagnosis of any pigment disorder. "
            "If you notice rapidly changing spots or moles, see a dermatologist."
        ),
        "recommended_products": [
            "brightening_serum",
            "daily_spf",
            "gentle_exfoliant",
        ],
    },
    "Possible_Infection": {
        "title": "Patterns Sometimes Seen in Infections",
        "description": (
            "Some features in the image can be seen in skin infections or overgrowth of microbes. "
            "Only a medical professional can confirm this."
        ),
        "what_it_means": (
            "This may reflect areas where the skin barrier is disrupted and microbes can more easily grow, "
            "but many look-alike conditions exist, so only a clinician can tell what is really going on."
        ),
        "care_focus": (
            "Focus on gentle cleansing, supporting the skin barrier, and seeking in-person medical advice for "
            "painful, spreading, or worrying areas."
        ),
        "disclaimer": (
            "This tool cannot rule out serious conditions. If you have pain, fever, "
            "rapid spreading, or feel unwell, please seek urgent medical advice."
        ),
        "recommended_products": [
            "gentle_cleanser",
            "barrier_support_moisturizer",
        ],
    },
}


def get_concern_index_map() -> Dict[str, int]:
    """Return a mapping from concern tag name to column index."""
    return {name: idx for idx, name in enumerate(CONCERN_TAGS)}



