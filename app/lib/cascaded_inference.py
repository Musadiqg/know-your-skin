"""
Cascaded Inference Module for Interpretable Skin Analysis.

This module implements the cascaded approach:
1. Classify top-10 conditions from Derm Foundation embeddings
2. Derive concerns via rule-based aggregation
3. Provide interpretability by showing which conditions triggered which concerns

The key difference from the original classifiers:
- Single condition model (not separate concern model)
- Concerns are DERIVED from conditions, not predicted independently
- Full interpretability: "Dry_Sensitive because Eczema=75%"
"""

import functools
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

from config.top10_concerns import (
    TOP_10_CONDITIONS,
    CONCERN_MAP_V2,
    CONCERN_CONFIG_V2,
    CONCERN_TAGS_V2,
)
from lib.derm_local import embed_image_path


# ============================================================================
# PyTorch Model Classes (must be defined here for joblib to unpickle)
# ============================================================================

class MultiLabelMLP(nn.Module):
    """Google's architecture: 6144 -> 256 (relu, dropout) -> 128 (relu, dropout) -> 10 (sigmoid)"""
    
    def __init__(self, input_dim: int, hidden_units: List[int], output_dim: int, dropout: float = 0.1):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for units in hidden_units:
            layers.extend([
                nn.Linear(prev_dim, units),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            prev_dim = units
        
        layers.append(nn.Linear(prev_dim, output_dim))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class TorchMLPWrapper:
    """Provides sklearn-compatible predict_proba() for inference."""
    
    def __init__(self, model: MultiLabelMLP, scaler: StandardScaler):
        self.model = model
        self.scaler = scaler
        self.model.eval()
    
    def predict_proba(self, X: np.ndarray) -> List[np.ndarray]:
        X_scaled = self.scaler.transform(X.astype(np.float32))
        X_t = torch.FloatTensor(X_scaled)
        
        with torch.no_grad():
            proba = self.model(X_t).numpy()
        
        # Return list of (n_samples, 2) arrays for sklearn compatibility
        return [np.column_stack([1 - proba[:, i], proba[:, i]]) for i in range(proba.shape[1])]


# Register classes in __main__ so joblib can find them when unpickling
# (The model was saved from __main__ during training)
sys.modules['__main__'].MultiLabelMLP = MultiLabelMLP
sys.modules['__main__'].TorchMLPWrapper = TorchMLPWrapper


# ============================================================================
# Model Loading
# ============================================================================

MODELS_DIR = Path(__file__).parent.parent / "models"


@functools.lru_cache(maxsize=1)
def load_top10_model() -> Dict[str, Any]:
    """
    Load the top-10 MLP model, scaler, and config.
    
    Returns dict with keys: 'model', 'scaler', 'config', 'conditions'
    """
    model_path = MODELS_DIR / "top10_mlp_model.joblib"
    scaler_path = MODELS_DIR / "top10_mlp_scaler.joblib"
    config_path = MODELS_DIR / "top10_mlp_config.json"
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Top-10 MLP model not found at {model_path}. "
            "Run 'python scripts/train_top10_mlp.py' first."
        )
    
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    # Load config
    config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)
    
    conditions = config.get("conditions", TOP_10_CONDITIONS)
    
    return {
        "model": model,
        "scaler": scaler,
        "config": config,
        "conditions": conditions,
    }


# ============================================================================
# Condition Prediction
# ============================================================================

def predict_top10_conditions(
    embedding: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, Dict[str, Any]]:
    """
    Predict probabilities for top-10 conditions from an embedding.
    
    Args:
        embedding: Derm Foundation embedding (6144-dim)
        threshold: Probability threshold for 'active' flag
    
    Returns:
        Dict mapping condition name to {prob, active}
    """
    # Ensure 2D
    if embedding.ndim == 1:
        embedding = embedding.reshape(1, -1)
    
    # Load model (wrapper includes scaler internally)
    model_data = load_top10_model()
    model = model_data["model"]
    conditions = model_data["conditions"]
    
    # Predict (wrapper handles scaling internally)
    proba_list = model.predict_proba(embedding.astype(np.float32))
    
    # Extract probability of positive class for each condition
    proba = np.array([
        p[0, 1] if p.shape[1] == 2 else p[0, -1]
        for p in proba_list
    ])
    
    # Build result
    result = {}
    for i, condition in enumerate(conditions):
        prob = float(proba[i])
        result[condition] = {
            "prob": prob,
            "active": prob >= threshold,
        }
    
    return result


# ============================================================================
# Concern Derivation (Rule-Based)
# ============================================================================

def derive_concerns(
    condition_probs: Dict[str, Dict[str, Any]],
    min_contributing_prob: float = 0.2,
) -> Dict[str, Dict[str, Any]]:
    """
    Derive concerns from condition probabilities using rule-based aggregation.
    
    This is the key function that provides interpretability by showing
    which conditions contributed to each concern.
    
    Args:
        condition_probs: Output from predict_top10_conditions()
        min_contributing_prob: Minimum prob to list as contributing condition
    
    Returns:
        Dict mapping concern tag to full concern info including:
        - prob: Aggregated probability
        - active: Whether concern exceeds threshold
        - contributing_conditions: Which conditions triggered this concern
        - User-facing text and config
    """
    concerns = {}
    
    for concern_tag in CONCERN_TAGS_V2:
        mapping = CONCERN_MAP_V2.get(concern_tag, {})
        config = CONCERN_CONFIG_V2.get(concern_tag, {})
        
        mapped_conditions = mapping.get("conditions", [])
        threshold = mapping.get("threshold", 0.5)
        aggregation = mapping.get("aggregation", "max")
        
        # Collect probabilities for mapped conditions
        relevant_probs = []
        contributing = {}
        
        for cond in mapped_conditions:
            if cond in condition_probs:
                prob = condition_probs[cond]["prob"]
                relevant_probs.append(prob)
                
                # Track which conditions contributed significantly
                if prob >= min_contributing_prob:
                    contributing[cond] = round(prob, 3)
        
        # Aggregate
        if aggregation == "max" and relevant_probs:
            agg_prob = max(relevant_probs)
        elif aggregation == "mean" and relevant_probs:
            agg_prob = sum(relevant_probs) / len(relevant_probs)
        else:
            agg_prob = 0.0
        
        # Determine if active
        is_active = agg_prob >= threshold
        
        # Build concern entry
        concerns[concern_tag] = {
            # Core prediction
            "prob": round(agg_prob, 3),
            "active": is_active,
            "threshold": threshold,
            
            # Interpretability
            "contributing_conditions": contributing,
            "mapped_conditions": mapped_conditions,
            
            # From mapping config
            "can_recommend_products": mapping.get("can_recommend_products", True),
            "severity_weight": mapping.get("severity_weight", 1.0),
            "escalation_note": mapping.get("escalation_note"),
            
            # User-facing text
            "title": config.get("title", concern_tag),
            "description": config.get("description", ""),
            "what_it_means": config.get("what_it_means", ""),
            "care_focus": config.get("care_focus", ""),
            "disclaimer": config.get("disclaimer", ""),
            "recommended_products": config.get("recommended_products", []),
        }
    
    return concerns


def rank_concerns(concerns: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Rank active concerns by severity and probability.
    
    Returns list of concern tags sorted by priority (highest first).
    """
    active_concerns = [
        (tag, info)
        for tag, info in concerns.items()
        if info["active"]
    ]
    
    # Sort by: severity_weight * prob (descending)
    active_concerns.sort(
        key=lambda x: x[1]["severity_weight"] * x[1]["prob"],
        reverse=True,
    )
    
    return [tag for tag, _ in active_concerns]


# ============================================================================
# Full Analysis Pipeline
# ============================================================================

def analyze_cascaded(
    image_path: str,
    condition_threshold: float = 0.5,
    min_contributing_prob: float = 0.2,
) -> Dict[str, Any]:
    """
    Full cascaded analysis pipeline.
    
    1. Embed image with Derm Foundation
    2. Predict top-10 conditions with MLP
    3. Derive concerns via rule-based aggregation
    4. Return interpretable results
    
    Args:
        image_path: Path to skin image
        condition_threshold: Threshold for marking conditions as active
        min_contributing_prob: Minimum prob to show as contributing condition
    
    Returns:
        {
            "conditions": { condition_name: {prob, active}, ... },
            "concerns": { concern_tag: {prob, active, contributing_conditions, ...}, ... },
            "ranked_concerns": [concern_tags in priority order],
            "summary": { brief overview }
        }
    """
    # Step 1: Get embedding
    embedding = embed_image_path(image_path)
    
    # Step 2: Predict conditions
    condition_probs = predict_top10_conditions(embedding, threshold=condition_threshold)
    
    # Step 3: Derive concerns
    concerns = derive_concerns(condition_probs, min_contributing_prob=min_contributing_prob)
    
    # Step 4: Rank active concerns
    ranked = rank_concerns(concerns)
    
    # Step 5: Build summary
    active_conditions = [
        cond for cond, info in condition_probs.items()
        if info["active"]
    ]
    active_concerns = [tag for tag in ranked]
    
    summary = {
        "num_active_conditions": len(active_conditions),
        "num_active_concerns": len(active_concerns),
        "top_condition": max(condition_probs.items(), key=lambda x: x[1]["prob"])[0] if condition_probs else None,
        "primary_concern": ranked[0] if ranked else None,
        "needs_escalation": any(
            concerns[tag]["active"] and not concerns[tag]["can_recommend_products"]
            for tag in active_concerns
        ),
    }
    
    return {
        "conditions": condition_probs,
        "concerns": concerns,
        "ranked_concerns": ranked,
        "summary": summary,
    }


def analyze_cascaded_from_embedding(
    embedding: np.ndarray,
    condition_threshold: float = 0.5,
    min_contributing_prob: float = 0.2,
) -> Dict[str, Any]:
    """
    Same as analyze_cascaded but accepts a pre-computed embedding.
    
    Useful for session-level analysis where embeddings are computed once.
    """
    # Step 2: Predict conditions
    condition_probs = predict_top10_conditions(embedding, threshold=condition_threshold)
    
    # Step 3: Derive concerns
    concerns = derive_concerns(condition_probs, min_contributing_prob=min_contributing_prob)
    
    # Step 4: Rank active concerns
    ranked = rank_concerns(concerns)
    
    # Step 5: Build summary
    active_conditions = [
        cond for cond, info in condition_probs.items()
        if info["active"]
    ]
    active_concerns = [tag for tag in ranked]
    
    summary = {
        "num_active_conditions": len(active_conditions),
        "num_active_concerns": len(active_concerns),
        "top_condition": max(condition_probs.items(), key=lambda x: x[1]["prob"])[0] if condition_probs else None,
        "primary_concern": ranked[0] if ranked else None,
        "needs_escalation": any(
            concerns[tag]["active"] and not concerns[tag]["can_recommend_products"]
            for tag in active_concerns
        ),
    }
    
    return {
        "conditions": condition_probs,
        "concerns": concerns,
        "ranked_concerns": ranked,
        "summary": summary,
    }


# ============================================================================
# Session Analysis (Multiple Images)
# ============================================================================

def analyze_cascaded_session(
    image_paths: List[str],
    condition_threshold: float = 0.5,
    min_contributing_prob: float = 0.2,
) -> Dict[str, Any]:
    """
    Analyze multiple images and aggregate results.
    
    For each condition, we take the MAX probability across images
    (if any image shows it clearly, we consider it present).
    
    Args:
        image_paths: List of image paths
        condition_threshold: Threshold for active conditions
        min_contributing_prob: Min prob to show as contributing
    
    Returns:
        Same structure as analyze_cascaded but aggregated across images
    """
    if not image_paths:
        raise ValueError("At least one image path required")
    
    # Collect predictions from all images
    all_condition_probs: Dict[str, List[float]] = {cond: [] for cond in TOP_10_CONDITIONS}
    
    for path in image_paths:
        embedding = embed_image_path(path)
        cond_probs = predict_top10_conditions(embedding, threshold=0.0)  # Get all probs
        
        for cond, info in cond_probs.items():
            if cond in all_condition_probs:
                all_condition_probs[cond].append(info["prob"])
    
    # Aggregate: MAX across images
    aggregated_conditions = {}
    for cond, probs in all_condition_probs.items():
        max_prob = max(probs) if probs else 0.0
        aggregated_conditions[cond] = {
            "prob": round(max_prob, 3),
            "active": max_prob >= condition_threshold,
            "per_image_probs": [round(p, 3) for p in probs],  # For transparency
        }
    
    # Derive concerns from aggregated conditions
    concerns = derive_concerns(aggregated_conditions, min_contributing_prob=min_contributing_prob)
    
    # Rank
    ranked = rank_concerns(concerns)
    
    # Summary
    active_conditions = [
        cond for cond, info in aggregated_conditions.items()
        if info["active"]
    ]
    
    summary = {
        "num_images": len(image_paths),
        "num_active_conditions": len(active_conditions),
        "num_active_concerns": len(ranked),
        "top_condition": max(aggregated_conditions.items(), key=lambda x: x[1]["prob"])[0] if aggregated_conditions else None,
        "primary_concern": ranked[0] if ranked else None,
        "needs_escalation": any(
            concerns[tag]["active"] and not concerns[tag]["can_recommend_products"]
            for tag in ranked
        ),
    }
    
    return {
        "conditions": aggregated_conditions,
        "concerns": concerns,
        "ranked_concerns": ranked,
        "summary": summary,
    }

