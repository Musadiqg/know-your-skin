"""
Product configuration for brand skincare products, normalised for recommendations.

This file is the single place you customise when deploying Know Your Skin for
a new brand. Replace the example products below with your own catalog — the
structure is intentionally simple so any team can adapt it quickly.

Schema per product:
  id                  Stable string key (used in API responses and mappings).
  name                Display name shown to end users.
  step                Routine slot: "cleanser" | "treatment" | "moisturizer" | "sunscreen" | "other"
  supported_concerns  List of concern tags this product addresses.
                      Tags must match those defined in config.concerns.CONCERN_TAGS.
  portfolio           Optional grouping label (e.g. "Hydration", "Anti-Acne").
  why_template        Optional explanation shown to users. Use {name} as a placeholder.
  image_name          Optional filename relative to your product-images directory.

Adding a new brand:
  1. Clear PRODUCT_CONFIG below and add your own products.
  2. Map each product's supported_concerns to the tags in config/concerns.py.
  3. (Optional) Provide why_template strings in your brand voice.
  4. Restart the API — no retraining needed.
"""

from typing import Dict, List, TypedDict


class ProductConfig(TypedDict):
    id: str
    name: str
    step: str
    supported_concerns: List[str]
    portfolio: str | None
    why_template: str | None
    image_name: str | None


# ---------------------------------------------------------------------------
# Example product catalog — replace with your brand's products.
# The structure below is derived from a real skincare brand deployment and
# shows how to map a full product range across concern categories.
# ---------------------------------------------------------------------------

PRODUCT_CONFIG: Dict[str, ProductConfig] = {
    # ── Hydration / Dry & Sensitive ──────────────────────────────────────────
    "b5_serum": {
        "id": "b5_serum",
        "name": "B5 Hydrating Serum",
        "step": "treatment",
        "supported_concerns": ["Dry_Sensitive", "Pigment_Tone_Issues"],
        "portfolio": "Hydration",
        "why_template": (
            "Because your skin shows signs of dryness or tone irregularities, "
            "we suggest {name}, a lightweight hydrating serum that helps plump and support the skin barrier."
        ),
        "image_name": "b5-serum.png",
    },
    "body_clarifying_cleanser": {
        "id": "body_clarifying_cleanser",
        "name": "Body Clarifying Cleanser",
        "step": "cleanser",
        "supported_concerns": ["Dry_Sensitive"],
        "portfolio": "Hydration",
        "why_template": (
            "We recommend {name}, a gentle body cleanser designed to cleanse and moisturise dry or reactive skin "
            "without harsh surfactants."
        ),
        "image_name": "body_clarifying_cleanser.png",
    },
    "daily_moisturizer": {
        "id": "daily_moisturizer",
        "name": "Daily Moisturiser",
        "step": "moisturizer",
        "supported_concerns": ["Dry_Sensitive", "Red_Scaly_Patches", "Itchy_Hives"],
        "portfolio": "Hydration",
        "why_template": (
            "{name} is an everyday moisturiser formulated for sensitive, dry, or redness-prone skin, "
            "to help keep the barrier comfortable and hydrated."
        ),
        "image_name": "daily_moisturizer.png",
    },
    "facial_moisture_balancing_cleanser": {
        "id": "facial_moisture_balancing_cleanser",
        "name": "Facial Moisture Balancing Cleanser",
        "step": "cleanser",
        "supported_concerns": ["Dry_Sensitive"],
        "portfolio": "Hydration",
        "why_template": (
            "{name} is a gentle facial cleanser that helps remove impurities while respecting a dry or sensitive skin barrier."
        ),
        "image_name": "facial-moisture-balancing-cleanser.png",
    },
    "moisture_balancing_cleanser": {
        "id": "moisture_balancing_cleanser",
        "name": "Moisture Balancing Cleanser",
        "step": "cleanser",
        "supported_concerns": ["Dry_Sensitive", "Itchy_Hives", "Red_Scaly_Patches", "Breakouts_Bumps"],
        "portfolio": "Hydration + Anti-Acne",
        "why_template": (
            "{name} gently cleanses while supporting dry, sensitive, or acne-prone areas with a hypochlorous-based formula."
        ),
        "image_name": "brand-cleanser.png",
    },

    # ── Anti-Acne / Breakouts ────────────────────────────────────────────────
    "blemish_age_defense_serum": {
        "id": "blemish_age_defense_serum",
        "name": "Blemish + Age Defense Serum",
        "step": "treatment",
        "supported_concerns": ["Breakouts_Bumps", "Pigment_Tone_Issues"],
        "portfolio": "Anti-Acne",
        "why_template": (
            "Since we see features linked to breakouts or post-blemish marks, {name} can help clarify pores, "
            "balance oil, and improve the look of blemishes over time."
        ),
        "image_name": "blemish_plus_age_defense_serum.png",
    },
    "salicylic_acid_cleanser": {
        "id": "salicylic_acid_cleanser",
        "name": "Salicylic Acid Cleanser",
        "step": "cleanser",
        "supported_concerns": ["Breakouts_Bumps"],
        "portfolio": "Anti-Acne",
        "why_template": (
            "{name} combines salicylic acid with a hypochlorous base to help reduce excess oil, clear pores, "
            "and support skin that is prone to acne breakouts."
        ),
        "image_name": "salicylic_acid_cleanser.png",
    },
    "silymarin_c15_serum": {
        "id": "silymarin_c15_serum",
        "name": "Silymarin C15 Serum",
        "step": "treatment",
        "supported_concerns": ["Breakouts_Bumps", "Pigment_Tone_Issues"],
        "portfolio": "Anti-Acne",
        "why_template": (
            "{name} pairs vitamin C with targeted actives to help reduce blemishes, refine texture, "
            "and support a more even-looking tone."
        ),
        "image_name": "silymarin_c15_serum.png",
    },

    # ── Pigmentation / Antioxidant ───────────────────────────────────────────
    "brightening_cream": {
        "id": "brightening_cream",
        "name": "Brightening Cream",
        "step": "treatment",
        "supported_concerns": ["Pigment_Tone_Issues"],
        "portfolio": "Anti-Ageing / Anti-Discoloration",
        "why_template": (
            "Because your skin shows tone irregularities or dark spots, {name} is a night treatment designed to "
            "gradually fade discoloration and brighten overall radiance."
        ),
        "image_name": "brightening-cream.png",
    },
    "discoloration_defense_serum": {
        "id": "discoloration_defense_serum",
        "name": "Discoloration Defense Serum",
        "step": "treatment",
        "supported_concerns": ["Pigment_Tone_Issues", "Dark_Spots"],
        "portfolio": "Anti-Ageing / Anti-Discoloration",
        "why_template": (
            "{name} targets stubborn discoloration and uneven tone, making it a good fit when we detect pigment-related concerns."
        ),
        "image_name": "discoloartion-defense_serum.png",
    },
    "c15_antioxidant_serum": {
        "id": "c15_antioxidant_serum",
        "name": "C15 Antioxidant Serum",
        "step": "treatment",
        "supported_concerns": ["Pigment_Tone_Issues", "Dull_Uneven_Tone"],
        "portfolio": "Anti-Ageing / Anti-Discoloration",
        "why_template": (
            "{name} delivers antioxidant vitamin C to help soften the look of fine lines and uneven tone, "
            "while supporting blemish-prone skin."
        ),
        "image_name": "c15_anti_oxidant_serum.png",
    },
    "hyaluronic_b5_serum": {
        "id": "hyaluronic_b5_serum",
        "name": "Hyaluronic B5 Serum",
        "step": "treatment",
        "supported_concerns": ["Dry_Sensitive", "Dry_Dehydrated"],
        "portfolio": "Hydration",
        "why_template": (
            "Because your skin shows signs of dehydration or barrier compromise, {name} provides "
            "intensive hydration to help plump and support the skin barrier."
        ),
        "image_name": "hyaluronic_b5_serum.png",
    },
    "scar_gel": {
        "id": "scar_gel",
        "name": "Scar Gel",
        "step": "treatment",
        "supported_concerns": ["Mild_Scars", "Pigment_Tone_Issues"],
        "portfolio": "Treatment",
        "why_template": (
            "For fresh scars or post-acne marks, {name} is designed to help fade the appearance "
            "of scars and support smoother texture over time."
        ),
        "image_name": "scar_gel.png",
    },

    # ── Sunscreen ────────────────────────────────────────────────────────────
    "facial_gel_sunscreen": {
        "id": "facial_gel_sunscreen",
        "name": "Facial Sunscreen Gel",
        "step": "sunscreen",
        "supported_concerns": ["Pigment_Tone_Issues"],
        "portfolio": "Sunscreen",
        "why_template": (
            "Daily SPF is essential when any skin concern is present. {name} offers broad-spectrum protection in a "
            "lightweight, no-white-cast gel formula that fits easily into most routines."
        ),
        "image_name": "facial-gel-sunscreen.png",
    },
    "facial_sunscreen_gel": {
        "id": "facial_sunscreen_gel",
        "name": "Facial Sunscreen Gel SPF 50+",
        "step": "sunscreen",
        "supported_concerns": ["Pigment_Tone_Issues", "Dry_Sensitive", "Red_Scaly_Patches", "Breakouts_Bumps", "Itchy_Hives", "Possible_Infection"],
        "portfolio": "Sunscreen",
        "why_template": (
            "Because consistent sun protection helps with nearly all skin goals, {name} is recommended as a "
            "broad-spectrum gel sunscreen that layers well over your routine."
        ),
        "image_name": "facial-sunscreen-gel.png",
    },
}


ROUTINE_STEPS: List[str] = ["cleanser", "treatment", "moisturizer", "sunscreen"]


def load_product_config() -> Dict[str, ProductConfig]:
    """
    Return the normalised product configuration.

    Swap this implementation to load from a JSON file, database, or external
    API if your brand's catalog is dynamic or managed externally.
    """
    return PRODUCT_CONFIG
