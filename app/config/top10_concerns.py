"""
Configuration for the Top-10 Cascaded Classifier with Interpretable Concerns.

This module defines:
- TOP_10_CONDITIONS: The 10 skin conditions we classify
- CONCERN_MAP_V2: Rule-based mapping from conditions to concerns with thresholds
- CONCERN_CONFIG_V2: User-facing messaging for each concern

The cascaded approach:
1. Classify conditions from embeddings
2. Derive concerns via rule-based aggregation (max pooling)
3. Provide interpretability by showing contributing conditions
"""

from typing import Any, Dict, List


# ============================================================================
# Top 10 Conditions (by frequency in SCIN dataset)
# ============================================================================

TOP_10_CONDITIONS: List[str] = [
    "Eczema",                       # 1211 examples - chronic inflammatory
    "Allergic Contact Dermatitis",  # 952 examples - allergic reaction
    "Insect Bite",                  # 449 examples - reactive
    "Urticaria",                    # 377 examples - hives
    "Psoriasis",                    # 348 examples - autoimmune inflammatory
    "Folliculitis",                 # 297 examples - hair follicle infection
    "Irritant Contact Dermatitis",  # 254 examples - chemical irritation
    "Tinea",                        # 232 examples - fungal infection
    "Herpes Zoster",                # 157 examples - viral (shingles)
    "Acne",                         # 109 examples - pore/sebum related
]


# ============================================================================
# Concern Tags (same 6 categories as before, for consistency)
# ============================================================================

CONCERN_TAGS_V2: List[str] = [
    "Dry_Sensitive",
    "Breakouts_Bumps",
    "Itchy_Hives",
    "Red_Scaly_Patches",
    "Pigment_Tone_Issues",
    "Possible_Infection",
]


# ============================================================================
# Concern Mapping V2 (Rule-based aggregation)
# ============================================================================

CONCERN_MAP_V2: Dict[str, Dict[str, Any]] = {
    "Dry_Sensitive": {
        "conditions": [
            "Eczema",
            "Allergic Contact Dermatitis",
            "Irritant Contact Dermatitis",
        ],
        "threshold": 0.40,  # Lower threshold - safe to suggest hydration
        "aggregation": "max",  # Take max probability among conditions
        "can_recommend_products": True,
        "severity_weight": 1.0,  # For ranking concerns
    },
    
    "Breakouts_Bumps": {
        "conditions": [
            "Acne",
            "Folliculitis",
        ],
        "threshold": 0.45,
        "aggregation": "max",
        "can_recommend_products": True,
        "severity_weight": 1.0,
    },
    
    "Itchy_Hives": {
        "conditions": [
            "Insect Bite",
            "Urticaria",
            "Allergic Contact Dermatitis",  # Often itchy
        ],
        "threshold": 0.45,
        "aggregation": "max",
        "can_recommend_products": True,  # Soothing products only
        "severity_weight": 1.2,  # Slightly higher - may need attention
    },
    
    "Red_Scaly_Patches": {
        "conditions": [
            "Psoriasis",
            "Eczema",  # Can present as scaly
        ],
        "threshold": 0.50,  # Higher threshold - needs caution
        "aggregation": "max",
        "can_recommend_products": False,  # Recommend seeing dermatologist
        "severity_weight": 1.5,
        "escalation_note": "These patterns often benefit from professional evaluation.",
    },
    
    "Pigment_Tone_Issues": {
        # None of the top-10 directly cause pigmentation issues,
        # but post-inflammatory hyperpigmentation can follow any inflammation
        "conditions": [],  # Derived from other signals if needed
        "threshold": 0.50,
        "aggregation": "max",
        "can_recommend_products": True,  # SPF, brightening
        "severity_weight": 0.8,
        "note": "Consider PIH risk if other inflammatory conditions present.",
    },
    
    "Possible_Infection": {
        "conditions": [
            "Tinea",          # Fungal
            "Herpes Zoster",  # Viral (shingles)
            "Folliculitis",   # Can be bacterial
        ],
        "threshold": 0.55,  # High threshold - only flag if confident
        "aggregation": "max",
        "can_recommend_products": False,  # Must see healthcare provider
        "severity_weight": 2.0,  # Highest priority
        "escalation_note": "Please consider consulting a healthcare provider.",
    },
}


# ============================================================================
# User-Facing Concern Configuration
# ============================================================================

CONCERN_CONFIG_V2: Dict[str, Dict[str, Any]] = {
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
            "This can happen when excess oil, dead skin, or bacteria build up in pores or around "
            "hair follicles, leading to blemishes or tiny bumps on the skin."
        ),
        "care_focus": (
            "Focus on balancing oil, gently exfoliating to keep pores clear, and avoiding "
            "products that clog pores."
        ),
        "disclaimer": (
            "This is not a medical diagnosis. For severe, painful, or persistent breakouts, "
            "consult a dermatologist."
        ),
        "recommended_products": [
            "clarifying_cleanser",
            "lightweight_noncomedogenic_moisturizer",
            "targeted_bha_serum",
        ],
    },
    
    "Itchy_Hives": {
        "title": "Itch, Hives, or Reactive Skin Patterns",
        "description": (
            "Your image shows patterns that can be associated with itchy, hive-like, or "
            "reactive areas on the skin."
        ),
        "what_it_means": (
            "These patterns may reflect irritation or a reactive response in the skin, "
            "which can be triggered by many factors such as friction, bites, allergens, or stress."
        ),
        "care_focus": (
            "Focus on calming and protecting the skin, avoiding harsh products, and keeping "
            "the area moisturized without over-scrubbing."
        ),
        "disclaimer": (
            "Only a clinician can diagnose allergic reactions or identify specific triggers. "
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
            "Red and scaly areas can appear when the skin is inflamed and turning over more "
            "quickly, which is seen in several common skin conditions that often benefit from "
            "professional care."
        ),
        "care_focus": (
            "Focus on very gentle cleansing, rich but non-irritating moisturizers, and daily "
            "sun protection. Consider discussing persistent patches with a dermatologist."
        ),
        "disclaimer": (
            "Conditions like psoriasis or chronic dermatitis require professional diagnosis "
            "and management. This analysis is cosmetic only and may miss important findings."
        ),
        "recommended_products": [
            "rich_emollient_cream",
            "gentle_scalp_or_body_wash",
        ],
    },
    
    "Pigment_Tone_Issues": {
        "title": "Pigment and Tone Considerations",
        "description": (
            "Based on patterns detected, your skin may be at risk for or showing signs of "
            "uneven tone or post-inflammatory changes."
        ),
        "what_it_means": (
            "When skin is inflamed or irritated, it can sometimes develop areas of extra or "
            "reduced pigment as it heals. This is especially common with darker skin tones."
        ),
        "care_focus": (
            "Focus on consistent sun protection and gentle care to minimize further irritation. "
            "Brightening products may help over time, but patience is key."
        ),
        "disclaimer": (
            "This is not a diagnosis of any pigment disorder. If you notice rapidly changing "
            "spots or moles, see a dermatologist promptly."
        ),
        "recommended_products": [
            "brightening_serum",
            "daily_spf",
            "gentle_exfoliant",
        ],
    },
    
    "Possible_Infection": {
        "title": "Patterns Sometimes Associated with Infection",
        "description": (
            "Some features in the image are sometimes seen with skin infections or microbial "
            "overgrowth. Only a medical professional can confirm this."
        ),
        "what_it_means": (
            "This may reflect areas where the skin barrier is disrupted and microbes "
            "(bacteria, fungi, or viruses) can more easily grow. However, many conditions "
            "can look similar, so professional evaluation is important."
        ),
        "care_focus": (
            "Focus on gentle cleansing and supporting the skin barrier. Avoid picking or "
            "irritating the area. Consider seeking in-person medical advice."
        ),
        "disclaimer": (
            "This tool cannot diagnose infections or rule out serious conditions. If you have "
            "pain, fever, rapid spreading, or feel unwell, please seek medical advice promptly."
        ),
        "recommended_products": [
            "gentle_cleanser",
            "barrier_support_moisturizer",
        ],
    },
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_condition_index(condition: str) -> int:
    """Get the index of a condition in TOP_10_CONDITIONS."""
    return TOP_10_CONDITIONS.index(condition)


def get_concern_config(concern_tag: str) -> Dict[str, Any]:
    """Get the full configuration for a concern tag."""
    mapping = CONCERN_MAP_V2.get(concern_tag, {})
    config = CONCERN_CONFIG_V2.get(concern_tag, {})
    return {**mapping, **config}

