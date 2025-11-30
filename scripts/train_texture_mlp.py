"""
Train a multi-label MLP classifier for skin texture using Derm Foundation embeddings.

Texture labels (from SCIN):
- RAISED_OR_BUMPY
- FLAT  
- ROUGH_OR_FLAKY
- FLUID_FILLED

This follows Google's approach: pre-computed embeddings → MLP classifier.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, hamming_loss, f1_score
import joblib

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR = Path(__file__).parent.parent / "app" / "models" / "cosmetic"

# Texture labels we're training on
TEXTURE_LABELS = [
    "textures_raised_or_bumpy",
    "textures_flat",
    "textures_rough_or_flaky",
    "textures_fluid_filled",
]

# Display names for output
TEXTURE_DISPLAY_NAMES = {
    "textures_raised_or_bumpy": "Raised/Bumpy",
    "textures_flat": "Flat",
    "textures_rough_or_flaky": "Rough/Flaky",
    "textures_fluid_filled": "Fluid-Filled",
}


class MultiLabelMLP(nn.Module):
    """
    Multi-label MLP following Google's architecture.
    Input: 6144-dim Derm Foundation embedding
    Hidden: 256 → 128 with ReLU and Dropout
    Output: 4 texture labels with Sigmoid
    """
    
    def __init__(self, input_dim: int = 6144, hidden_units: list = [256, 128], 
                 output_dim: int = 4, dropout: float = 0.1):
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
        # Note: No sigmoid here - we'll use BCEWithLogitsLoss for numerical stability
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class TorchMLPWrapper:
    """Wrapper for sklearn-compatible predict_proba interface."""
    
    def __init__(self, model: MultiLabelMLP, scaler: StandardScaler):
        self.model = model
        self.scaler = scaler
        self.model.eval()
    
    def predict_proba(self, X: np.ndarray) -> list:
        X_scaled = self.scaler.transform(X.astype(np.float32))
        X_t = torch.FloatTensor(X_scaled)
        
        with torch.no_grad():
            logits = self.model(X_t)
            proba = torch.sigmoid(logits).numpy()
        
        # Return list of (n_samples, 2) arrays for sklearn compatibility
        return [np.column_stack([1 - proba[:, i], proba[:, i]]) for i in range(proba.shape[1])]


def load_data():
    """Load embeddings and texture labels, merge by image path."""
    print("Loading data...")
    
    # Load embeddings - keys are image paths like 'dataset/images/123456.png'
    emb_path = DATA_DIR / "scin_embeddings.npz"
    emb_data = np.load(emb_path, allow_pickle=True)
    
    # Get all image paths (keys) and their embeddings
    image_paths = list(emb_data.keys())
    print(f"  Loaded {len(image_paths)} embeddings")
    print(f"  Sample key: {image_paths[0]}")
    
    # Create a dict for fast lookup: image_path -> embedding
    path_to_embedding = {path: emb_data[path] for path in image_paths}
    
    # Load cases CSV (contains texture labels and image paths)
    cases_path = DATA_DIR / "scin_cases.csv"
    cases_df = pd.read_csv(cases_path)
    print(f"  Loaded {len(cases_df)} cases from CSV")
    
    # Find image path columns
    image_cols = [c for c in cases_df.columns if 'image' in c.lower() and 'path' in c.lower()]
    print(f"  Image path columns: {image_cols}")
    
    # Build a list of (embedding, texture_labels) pairs
    # Each case can have up to 3 images, we'll use all of them
    X_list = []
    y_list = []
    matched_count = 0
    
    for idx, row in cases_df.iterrows():
        # Check if this case has texture data
        has_texture = False
        for col in TEXTURE_LABELS:
            if pd.notna(row.get(col)):
                has_texture = True
                break
        
        if not has_texture:
            continue
        
        # Get texture labels for this case
        texture_values = []
        for col in TEXTURE_LABELS:
            val = row.get(col)
            texture_values.append(1 if val == 'YES' else 0)
        
        # Try to find embeddings for this case's images
        for img_col in image_cols:
            img_path = row.get(img_col)
            if pd.isna(img_path):
                continue
            
            # Try different path formats
            if img_path in path_to_embedding:
                X_list.append(path_to_embedding[img_path])
                y_list.append(texture_values)
                matched_count += 1
            elif f"dataset/images/{img_path}" in path_to_embedding:
                X_list.append(path_to_embedding[f"dataset/images/{img_path}"])
                y_list.append(texture_values)
                matched_count += 1
            elif img_path.split('/')[-1] in [p.split('/')[-1] for p in image_paths]:
                # Match by filename only
                filename = img_path.split('/')[-1]
                for p in image_paths:
                    if p.endswith(filename):
                        X_list.append(path_to_embedding[p])
                        y_list.append(texture_values)
                        matched_count += 1
                        break
    
    print(f"  Matched {matched_count} image-texture pairs")
    
    if len(X_list) == 0:
        # Debug: show what paths look like
        print("\n  DEBUG - Sample image paths from CSV:")
        for img_col in image_cols:
            sample_paths = cases_df[img_col].dropna().head(3).tolist()
            print(f"    {img_col}: {sample_paths}")
        print("\n  DEBUG - Sample embedding keys:")
        print(f"    {image_paths[:3]}")
        raise ValueError("No matching embeddings found! Check path formats.")
    
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)
    
    print(f"  Final dataset: X shape {X.shape}, y shape {y.shape}")
    
    # Print label distribution
    print("\n  Label distribution:")
    for i, col in enumerate(TEXTURE_LABELS):
        pos_count = y[:, i].sum()
        print(f"    {TEXTURE_DISPLAY_NAMES[col]}: {int(pos_count)} positive ({pos_count/len(y)*100:.1f}%)")
    
    return X, y


def train_model(X_train, y_train, X_val, y_val, epochs=50, lr=1e-3, batch_size=64):
    """Train the MLP with class weighting for imbalanced data."""
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train.astype(np.float32))
    X_val_scaled = scaler.transform(X_val.astype(np.float32))
    
    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train_scaled)
    y_train_t = torch.FloatTensor(y_train)
    X_val_t = torch.FloatTensor(X_val_scaled)
    y_val_t = torch.FloatTensor(y_val)
    
    # Calculate class weights for imbalanced data
    pos_counts = y_train.sum(axis=0)
    neg_counts = len(y_train) - pos_counts
    pos_weights = neg_counts / (pos_counts + 1e-6)
    pos_weights = np.clip(pos_weights, 1.0, 10.0)  # Cap weights
    pos_weights_t = torch.FloatTensor(pos_weights)
    
    print(f"\nClass weights: {pos_weights}")
    
    # Model
    model = MultiLabelMLP(
        input_dim=X_train.shape[1],
        hidden_units=[256, 128],
        output_dim=y_train.shape[1],
        dropout=0.1
    )
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    # Training loop
    best_val_f1 = 0
    best_model_state = None
    patience = 10
    patience_counter = 0
    
    for epoch in range(epochs):
        model.train()
        
        # Mini-batch training
        indices = torch.randperm(len(X_train_t))
        total_loss = 0
        n_batches = 0
        
        for i in range(0, len(indices), batch_size):
            batch_idx = indices[i:i+batch_size]
            X_batch = X_train_t[batch_idx]
            y_batch = y_train_t[batch_idx]
            
            optimizer.zero_grad()
            logits = model(X_batch)
            
            # Weighted BCE loss
            loss = F.binary_cross_entropy_with_logits(
                logits, y_batch, 
                pos_weight=pos_weights_t
            )
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            n_batches += 1
        
        avg_loss = total_loss / n_batches
        
        # Validation
        model.eval()
        with torch.no_grad():
            val_logits = model(X_val_t)
            val_probs = torch.sigmoid(val_logits).numpy()
            val_preds = (val_probs >= 0.5).astype(int)
            
            val_f1 = f1_score(y_val, val_preds, average='macro', zero_division=0)
            val_hamming = hamming_loss(y_val, val_preds)
        
        if (epoch + 1) % 5 == 0:
            print(f"  Epoch {epoch+1}/{epochs}: Loss={avg_loss:.4f}, Val F1={val_f1:.4f}, Val Hamming={val_hamming:.4f}")
        
        # Early stopping
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_model_state = model.state_dict().copy()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping at epoch {epoch+1}")
                break
    
    # Load best model
    model.load_state_dict(best_model_state)
    
    return model, scaler


def evaluate_model(model, scaler, X_test, y_test):
    """Evaluate model and print metrics."""
    
    X_test_scaled = scaler.transform(X_test.astype(np.float32))
    X_test_t = torch.FloatTensor(X_test_scaled)
    
    model.eval()
    with torch.no_grad():
        logits = model(X_test_t)
        probs = torch.sigmoid(logits).numpy()
        preds = (probs >= 0.5).astype(int)
    
    print("\n" + "=" * 60)
    print("TEST SET EVALUATION")
    print("=" * 60)
    
    # Per-label metrics
    print("\nPer-label classification report:")
    print(classification_report(
        y_test, preds,
        target_names=[TEXTURE_DISPLAY_NAMES[t] for t in TEXTURE_LABELS],
        zero_division=0
    ))
    
    # Overall metrics
    hamming = hamming_loss(y_test, preds)
    macro_f1 = f1_score(y_test, preds, average='macro', zero_division=0)
    
    print(f"\nOverall Metrics:")
    print(f"  Hamming Loss: {hamming:.4f}")
    print(f"  Macro F1: {macro_f1:.4f}")
    
    return {
        "hamming_loss": hamming,
        "macro_f1": macro_f1,
        "per_label_f1": {
            TEXTURE_DISPLAY_NAMES[t]: f1_score(y_test[:, i], preds[:, i], zero_division=0)
            for i, t in enumerate(TEXTURE_LABELS)
        }
    }


def main():
    print("=" * 60)
    print("TEXTURE MLP TRAINING (Google's Approach)")
    print("=" * 60)
    
    # Load data
    X, y = load_data()
    
    # Train/val/test split
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42
    )
    
    print(f"\nSplit sizes:")
    print(f"  Train: {len(X_train)}")
    print(f"  Val: {len(X_val)}")
    print(f"  Test: {len(X_test)}")
    
    # Train
    print("\nTraining MLP...")
    model, scaler = train_model(X_train, y_train, X_val, y_val, epochs=100)
    
    # Evaluate
    metrics = evaluate_model(model, scaler, X_test, y_test)
    
    # Save model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create wrapper and save
    wrapper = TorchMLPWrapper(model, scaler)
    
    model_path = MODELS_DIR / "texture_mlp_model.joblib"
    scaler_path = MODELS_DIR / "texture_mlp_scaler.joblib"
    config_path = MODELS_DIR / "texture_mlp_config.json"
    
    # Save PyTorch model state + scaler together
    joblib.dump(wrapper, model_path)
    joblib.dump(scaler, scaler_path)
    
    # Save config
    config = {
        "labels": TEXTURE_LABELS,
        "display_names": TEXTURE_DISPLAY_NAMES,
        "input_dim": X.shape[1],
        "hidden_units": [256, 128],
        "dropout": 0.1,
        "metrics": metrics
    }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Model saved to {MODELS_DIR}")
    print(f"   - {model_path.name}")
    print(f"   - {scaler_path.name}")
    print(f"   - {config_path.name}")


if __name__ == "__main__":
    main()

