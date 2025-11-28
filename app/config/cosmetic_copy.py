"""
Copy and educational content for cosmetic attributes.

This is used by the cosmetic reporting layer to turn predictions into
user-friendly text. All wording here is cosmetic/non-medical.
"""

from typing import Dict, Any


# Fitzpatrick skin type copy
FST_COPY: Dict[str, Dict[str, Any]] = {
    "FST1": {
        "title": "Fitzpatrick Type I (very fair, always burns)",
        "overview": (
            "This type of skin is very fair and tends to burn easily with minimal sun exposure "
            "and rarely tans. It often needs extra gentle care and diligent daily sun protection."
        ),
        "care_focus": (
            "Prioritize broad-spectrum sunscreen every day, seek shade where possible, and build up active "
            "ingredients gradually to avoid irritation. Hydrating, barrier-supporting products are usually helpful."
        ),
    },
    "FST2": {
        "title": "Fitzpatrick Type II (fair, usually burns, may tan lightly)",
        "overview": (
            "This type of skin is fair and can burn with sun exposure, sometimes followed by a light tan. "
            "It has moderate sensitivity to the sun."
        ),
        "care_focus": (
            "Daily SPF and gentle hydrators are key. Introduce exfoliants and brightening ingredients slowly and "
            "watch for dryness or redness."
        ),
    },
    "FST3": {
        "title": "Fitzpatrick Type III (medium, sometimes burns, gradually tans)",
        "overview": (
            "This type of skin has a light-to-medium tone, may burn with strong sun at first, and then gradually tans. "
            "It can be somewhat prone to uneven tone or post-blemish marks."
        ),
        "care_focus": (
            "Consistent SPF helps prevent dark spots. Balanced routines with gentle exfoliation and brightening products "
            "can support an even, healthy-looking tone."
        ),
    },
    "FST4": {
        "title": "Fitzpatrick Type IV (olive to brown, rarely burns, tans easily)",
        "overview": (
            "This type of skin is naturally deeper in color and tends to tan easily while rarely burning. "
            "It may be more prone to pigmentation changes after irritation or breakouts."
        ),
        "care_focus": (
            "Daily sunscreen is still important to protect against long-term damage and uneven tone. "
            "Focus on gentle, non-irritating actives and hydrating care to support a smooth, radiant complexion."
        ),
    },
    "FST5": {
        "id": "FST5",
        "title": "Fitzpatrick Type V (brown, rarely burns, tans deeply)",
        "overview": (
            "This type of skin has a deeper brown tone, usually tans deeply and rarely burns. "
            "It can be more prone to dark marks lingering after inflammation."
        ),
        "care_focus": (
            "Gentle daily cleansing, consistent SPF, and pigment-safe brightening ingredients can help manage "
            "uneven tone while maintaining the skin's natural richness."
        ),
    },
    "FST6": {
        "title": "Fitzpatrick Type VI (very dark, deeply pigmented)",
        "overview": (
            "This type of skin is very richly pigmented and typically does not burn, but can still experience sun damage "
            "and is often prone to visible dark marks after irritation."
        ),
        "care_focus": (
            "Broad-spectrum sunscreen is still valuable to protect skin health and tone. Focus on barrier support, "
            "hydration, and gentle brightening where needed, avoiding harsh or stripping products."
        ),
    },
}


# Monk tone copy grouped into simple ranges for education.
MONK_TONE_RANGES = [
    {"name": "lighter tones", "range": range(1, 4)},
    {"name": "medium tones", "range": range(4, 8)},
    {"name": "deeper tones", "range": range(8, 11)},
]

MONK_COPY: Dict[str, str] = {
    "lighter tones": (
        "On lighter skin tones, redness and sunburn often show up quickly, while dark marks may appear tan or pink. "
        "Consistent sunscreen and gentle barrier care help prevent irritation and long-term discoloration."
    ),
    "medium tones": (
        "On medium skin tones, both redness and dark marks can appear, especially after breakouts or sun exposure. "
        "Daily SPF and balanced routines with hydrating and brightening ingredients support an even complexion."
    ),
    "deeper tones": (
        "On deeper skin tones, dark spots and uneven patches may linger longer, even if redness is less visible. "
        "Sun protection plus pigment-safe brightening products can help maintain a smooth, radiant tone."
    ),
}


# Texture copy per tag.
TEXTURE_COPY: Dict[str, Dict[str, str]] = {
    "Texture_Smooth": {
        "title": "Mostly smooth texture",
        "body": (
            "Your skin texture looks mostly smooth and even in this photo. That’s a great foundation. "
            "A gentle cleanser, consistent moisturizer, and daily sunscreen can help keep it that way."
        ),
    },
    "Texture_Bumpy": {
        "title": "Uneven or bumpy texture",
        "body": (
            "We see some raised or bumpy areas that can happen with clogged pores or small textural changes. "
            "Gentle exfoliation, non-comedogenic hydrators, and balanced oil control can help smooth the look over time."
        ),
    },
    "Texture_Rough_Flakey": {
        "title": "Dry or flaky texture",
        "body": (
            "Your skin shows some rough or flaky areas, which often indicate dryness or a compromised barrier. "
            "Hydrating cleansers, richer moisturizers, and barrier-supporting ingredients can help restore softness."
        ),
    },
    "Texture_Fluid_Filled": {
        "title": "Fluid-filled or very raised areas",
        "body": (
            "We notice some fluid-filled or very raised areas. While some bumps can be part of normal skin, "
            "sudden or painful changes are best reviewed with a dermatologist. In the meantime, focus on gentle care "
            "and avoid picking or harsh scrubs."
        ),
    },
}


COSMETIC_DISCLAIMER = (
    "The information above describes cosmetic characteristics such as skin tone and texture based on this single photo. "
    "It is not a medical diagnosis and may not capture the full picture of your skin. For any concerns, persistent "
    "changes, or symptoms like pain or bleeding, please consult a dermatologist or healthcare professional."
)



