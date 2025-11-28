"""
Configuration for SCIN condition-level labels used by the condition classifier.

We intentionally align condition names with the aggregated labels used in
`weighted_skin_condition_label` and `config.concerns.CONCERN_MAP` so that:

- each condition probability can be mapped back to one or more high-level
  concern tags; and
- the label space stays reasonably small and interpretable.
"""

from typing import Dict, List

from config.concerns import CONCERN_MAP


# We take the keys of CONCERN_MAP as our canonical condition labels.
# These correspond to aggregated SCIN condition names (e.g. "Eczema", "Psoriasis").
CONDITION_LABELS: List[str] = sorted(CONCERN_MAP.keys())


def get_condition_index_map() -> Dict[str, int]:
    """Return a mapping from condition label name to column index."""
    return {name: idx for idx, name in enumerate(CONDITION_LABELS)}



