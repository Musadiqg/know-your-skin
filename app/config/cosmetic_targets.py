"""
Canonical label mappings for cosmetic skin attributes derived from SCIN:

- Fitzpatrick Skin Type (FST I–VI)
- Monk Skin Tone (1–10)
- Texture tags (smooth / bumpy / rough/flaky / optional fluid-filled)

These mappings are used by the cosmetic attribute training and inference code.
"""

from typing import Dict, List


# Canonical Fitzpatrick labels we expose in our cosmetic layer.
# SCIN stores values such as "FST1" .. "FST6" or "NONE_SELECTED".
FST_LABELS: List[str] = ["FST1", "FST2", "FST3", "FST4", "FST5", "FST6"]

# Values in the SCIN CSV for Fitzpatrick skin type from users / dermatologists
# are expected to match these strings. Any value not in this set (e.g.
# "NONE_SELECTED" or missing) will be treated as unknown and skipped for
# training.
VALID_FST_VALUES = set(FST_LABELS)


# Monk skin tone labels (1–10). SCIN stores these as integers 1..10.
MONK_TONE_VALUES: List[int] = list(range(1, 11))


# Cosmetic texture tags we expose in our report.
TEXTURE_TAGS: List[str] = [
    "Texture_Smooth",
    "Texture_Bumpy",
    "Texture_Rough_Flakey",
    "Texture_Fluid_Filled",
]

# Mapping from SCIN textures_* column suffix to our cosmetic texture tags.
# SCIN schema describes textures_* booleans with suffixes such as:
#   - TEXTURE_UNSPECIFIED
#   - RAISED_OR_BUMPY
#   - FLAT
#   - ROUGH_OR_FLAKY
#   - FLUID_FILLED
TEXTURE_FIELD_TO_TAG: Dict[str, str] = {
    "RAISED_OR_BUMPY": "Texture_Bumpy",
    "ROUGH_OR_FLAKY": "Texture_Rough_Flakey",
    "FLAT": "Texture_Smooth",
    "FLUID_FILLED": "Texture_Fluid_Filled",
}



