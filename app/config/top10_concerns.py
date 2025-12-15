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
# Concern Tags (expanded based on CSV mapping from cosmo team)
# ============================================================================

CONCERN_TAGS_V2: List[str] = [
    "Dry_Sensitive",
    "Breakouts_Bumps",
    "Itchy_Hives",
    "Red_Scaly_Patches",
    "Pigment_Tone_Issues",
    "Possible_Infection",
    # New tags for product specificity
    "Dark_Spots",
    "Dull_Uneven_Tone",
    "Dry_Dehydrated",
    "Mild_Scars",
]


# ============================================================================
# Concern Mapping V2 (Rule-based aggregation based on CSV from cosmo team)
# ============================================================================

CONCERN_MAP_V2: Dict[str, Dict[str, Any]] = {
    "Dry_Sensitive": {
        "conditions": [
            "Eczema",  # Yes - Gentle hydration
            "Allergic Contact Dermatitis",  # Gentle Only
            "Irritant Contact Dermatitis",  # Gentle Only
        ],
        "threshold": 0.30,
        "aggregation": "max",
        "can_recommend_products": True,
        "recommendation_type": "yes",  # Eczema allows Yes, others are Gentle Only - default to Yes
        "severity_weight": 1.0,
        "notes": "Gentle hydration and barrier support recommended",
        "best_match_products": ["Daily Moisturizer", "Facial Moisture Balancing Cleanser"],
    },
    
    "Breakouts_Bumps": {
        "conditions": [
            "Acne",  # Yes - Acne treatment
            "Folliculitis",  # Yes - Acne-type bumps
        ],
        "threshold": 0.35,
        "aggregation": "max",
        "can_recommend_products": True,
        "recommendation_type": "yes",
        "severity_weight": 1.0,
        "notes": "Acne treatment and pore clearing",
        "best_match_products": ["Blemish + Age Defense Serum", "Salicylic Acid Cleanser"],
    },
    
    "Itchy_Hives": {
        "conditions": [
            "Insect Bite",  # Gentle Only - Mild soothing
            "Urticaria",  # Gentle Only - Soothe irritation
            "Allergic Contact Dermatitis",  # Gentle Only - Soothe irritation
        ],
        "threshold": 0.35,
        "aggregation": "max",
        "can_recommend_products": True,
        "recommendation_type": "gentle_only",
        "severity_weight": 1.2,
        "notes": "Soothe irritation with gentle products",
        "best_match_products": ["Daily Moisturizer"],
    },
    
    "Red_Scaly_Patches": {
        "conditions": [
            "Psoriasis",  # Gentle Only - Also advise dermatologist
            "Eczema",  # Gentle Only - Also advise dermatologist
        ],
        "threshold": 0.40,
        "aggregation": "max",
        "can_recommend_products": True,  # Changed from False - CSV says Gentle Only
        "recommendation_type": "gentle_only",
        "severity_weight": 1.5,
        "escalation_note": "Also advise dermatologist",
        "notes": "Gentle products only, professional evaluation recommended",
        "best_match_products": ["Daily Moisturizer"],
    },
    
    "Pigment_Tone_Issues": {
        # Maps to: Dark_Spots, Dull_Uneven_Tone, Post_Acne_Marks, Uneven_Tone, PIH
        "conditions": [],  # Derived from other signals or mapped from Dark_Spots/Dull_Uneven_Tone
        "threshold": 0.40,
        "aggregation": "max",
        "can_recommend_products": True,
        "recommendation_type": "yes",
        "severity_weight": 0.8,
        "notes": "SPF and brightening products recommended",
        "best_match_products": ["Discoloration Defense Serum", "C15 Antioxidant Serum"],
    },
    
    "Possible_Infection": {
        "conditions": [
            "Tinea",  # No - Advise see doctor
            "Herpes Zoster",  # No - Advise see doctor
            "Folliculitis",  # No - Advise see doctor (when flagged as infection)
        ],
        "threshold": 0.45,
        "aggregation": "max",
        "can_recommend_products": False,
        "recommendation_type": "no",
        "severity_weight": 2.0,
        "escalation_note": "Advise see doctor",
        "notes": "Must see healthcare provider - no product recommendations",
        "best_match_products": [],
    },
    
    # New concern tags
    "Dark_Spots": {
        "conditions": [],  # Not in top-10, but maps to Pigment_Tone_Issues
        "threshold": 0.40,
        "aggregation": "max",
        "can_recommend_products": True,
        "recommendation_type": "yes",
        "severity_weight": 0.8,
        "notes": "PIH/pigmentation - brightening products",
        "best_match_products": ["Discoloration Defense Serum"],
        # Maps to Pigment_Tone_Issues for aggregation
        "maps_to": "Pigment_Tone_Issues",
    },
    
    "Dull_Uneven_Tone": {
        "conditions": [],  # Not in top-10, but maps to Pigment_Tone_Issues
        "threshold": 0.40,
        "aggregation": "max",
        "can_recommend_products": True,
        "recommendation_type": "yes",
        "severity_weight": 0.8,
        "notes": "Brightening antioxidant for tone-evening",
        "best_match_products": ["C15 Antioxidant Serum"],
        # Maps to Pigment_Tone_Issues for aggregation
        "maps_to": "Pigment_Tone_Issues",
    },
    
    "Dry_Dehydrated": {
        "conditions": [],  # Not in top-10, but maps to Dry_Sensitive
        "threshold": 0.30,
        "aggregation": "max",
        "can_recommend_products": True,
        "recommendation_type": "yes",
        "severity_weight": 1.0,
        "notes": "Hydration booster",
        "best_match_products": ["Hyaluronic B5 Serum"],
        # Maps to Dry_Sensitive for aggregation
        "maps_to": "Dry_Sensitive",
    },
    
    "Mild_Scars": {
        "conditions": [],  # Not in top-10
        "threshold": 0.40,
        "aggregation": "max",
        "can_recommend_products": True,
        "recommendation_type": "yes",
        "severity_weight": 0.7,
        "notes": "Scar fading treatment",
        "best_match_products": ["Hudson Scar Gel"],
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
    
    # New concern tags
    "Dark_Spots": {
        "title": "Dark Spots and Post-Acne Marks",
        "description": (
            "Your photo shows patterns associated with dark spots or post-inflammatory "
            "hyperpigmentation, often appearing after breakouts or inflammation."
        ),
        "what_it_means": (
            "These spots occur when the skin produces extra pigment in response to inflammation. "
            "They can fade over time with proper care and sun protection."
        ),
        "care_focus": (
            "Focus on consistent sun protection and targeted brightening products to help fade "
            "discoloration gradually. Avoid picking or further irritating the area."
        ),
        "disclaimer": (
            "This is not a diagnosis. If spots are rapidly changing, asymmetric, or concerning, "
            "please see a dermatologist for evaluation."
        ),
        "recommended_products": [
            "discoloration_defense_serum",
            "facial_gel_sunscreen",
        ],
    },
    
    "Dull_Uneven_Tone": {
        "title": "Dull or Uneven Skin Tone",
        "description": (
            "Your photo shows patterns associated with lack of glow or uneven skin tone, "
            "which can result from sun exposure, dead skin buildup, or post-inflammatory changes."
        ),
        "what_it_means": (
            "Dullness often indicates a buildup of dead skin cells or uneven pigmentation. "
            "Gentle exfoliation and brightening antioxidants can help restore radiance."
        ),
        "care_focus": (
            "Focus on brightening antioxidants, gentle exfoliation, and consistent sun protection "
            "to promote a more even, radiant complexion."
        ),
        "disclaimer": (
            "This is a cosmetic assessment. For persistent or concerning changes in skin tone, "
            "consult a dermatologist."
        ),
        "recommended_products": [
            "c15_antioxidant_serum",
            "facial_gel_sunscreen",
        ],
    },
    
    "Dry_Dehydrated": {
        "title": "Dehydrated Skin",
        "description": (
            "Your photo shows patterns associated with dehydrated skin - tight, flaky, "
            "or lacking moisture despite potential oil production."
        ),
        "what_it_means": (
            "Dehydration occurs when the skin lacks water, which is different from dryness "
            "(lack of oil). Even oily skin can be dehydrated and benefit from hydration."
        ),
        "care_focus": (
            "Focus on hydrating serums with hyaluronic acid, gentle cleansers that don't strip, "
            "and moisturizers that help lock in hydration."
        ),
        "disclaimer": (
            "This is not a medical diagnosis. If dehydration is severe or persistent, "
            "consider consulting a dermatologist."
        ),
        "recommended_products": [
            "hyaluronic_b5_serum",
            "facial_moisture_balancing_cleanser",
            "daily_moisturizer",
        ],
    },
    
    "Mild_Scars": {
        "title": "Fresh Scars or Acne Marks",
        "description": (
            "Your photo shows patterns associated with fresh scars (less than 3 months) "
            "or post-acne marks that may benefit from targeted treatment."
        ),
        "what_it_means": (
            "Fresh scars are still in the healing phase and may respond better to treatment "
            "than older scars. Early intervention can help minimize their appearance."
        ),
        "care_focus": (
            "Focus on scar-fading treatments, consistent sun protection to prevent darkening, "
            "and gentle care to avoid further irritation."
        ),
        "disclaimer": (
            "This is not a medical diagnosis. For deep, painful, or keloid scars, "
            "please consult a dermatologist for professional treatment options."
        ),
        "recommended_products": [
            "hudson_scar_gel",
            "facial_gel_sunscreen",
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

