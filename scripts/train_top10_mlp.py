"""
Train a Multi-Layer Perceptron classifier for top-10 SCIN conditions.

Uses Google's exact architecture with PyTorch:
- Input(6144) -> Dense(256, relu) -> Dropout(0.1) -> Dense(128, relu) -> Dropout(0.1) -> Dense(10, sigmoid)
- Binary cross-entropy loss
- Adam optimizer with learning_rate=1e-4

Run: python scripts/train_top10_mlp.py
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer
from sklearn.metrics import classification_report, hamming_loss


# ============================================================================
# Configuration (matching Google's notebook)
# ============================================================================

TOP_10_CONDITIONS: List[str] = [
    "Eczema",
    "Allergic Contact Dermatitis",
    "Insect Bite",
    "Urticaria",
    "Psoriasis",
    "Folliculitis",
    "Irritant Contact Dermatitis",
    "Tinea",
    "Herpes Zoster",
    "Acne",
]

MIN_CONFIDENCE = 3
HIDDEN_UNITS = [256, 128]
DROPOUT_RATE = 0.1
WEIGHT_DECAY = 1e-4
LEARNING_RATE = 1e-4  # Google's exact value
EPOCHS = 20
BATCH_SIZE = 32

DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR = Path(__file__).parent.parent / "app" / "models"


# ============================================================================
# PyTorch Model (Google's Architecture)
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


# ============================================================================
# Wrapper for sklearn-compatible inference
# ============================================================================

class TorchMLPWrapper:
    """Provides sklearn-compatible predict_proba() for cascaded_inference.py"""
    
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


# ============================================================================
# Data Loading
# ============================================================================

def load_embeddings(data_dir: Path) -> Dict[str, np.ndarray]:
    emb_path = data_dir / "scin_embeddings.npz"
    print(f"Loading embeddings from {emb_path}...")
    data = np.load(emb_path)
    embeddings = {key: data[key] for key in data.files}
    print(f"  Loaded {len(embeddings)} embeddings")
    return embeddings


def load_scin_data(data_dir: Path) -> pd.DataFrame:
    print("Loading SCIN data...")
    cases_df = pd.read_csv(data_dir / "scin_cases.csv", dtype={"case_id": str})
    labels_df = pd.read_csv(data_dir / "scin_labels.csv", dtype={"case_id": str})
    df = pd.merge(cases_df, labels_df, on="case_id")
    print(f"  Loaded {len(df)} cases")
    return df


def prepare_data(df: pd.DataFrame, embeddings: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray, MultiLabelBinarizer]:
    print(f"\nPreparing training data...")
    
    X_list, y_list = [], []
    
    for _, row in df.iterrows():
        # Filter by image quality
        if row.get("dermatologist_gradable_for_skin_condition_1") != "DEFAULT_YES_IMAGE_QUALITY_SUFFICIENT":
            continue
        
        # Parse labels
        labels_str = row.get("dermatologist_skin_condition_on_label_name")
        conf_str = row.get("dermatologist_skin_condition_confidence")
        
        if pd.isna(labels_str) or pd.isna(conf_str):
            continue
        
        try:
            labels = eval(labels_str)
            confs = eval(conf_str)
            row_labels = [l for l, c in zip(labels, confs) if c >= MIN_CONFIDENCE and l in TOP_10_CONDITIONS]
        except:
            continue
        
        # Add each image
        for col in ["image_1_path", "image_2_path", "image_3_path"]:
            path = row.get(col)
            if pd.notna(path) and path in embeddings:
                X_list.append(embeddings[path])
                y_list.append(row_labels)
    
    X = np.array(X_list, dtype=np.float32)
    mlb = MultiLabelBinarizer(classes=TOP_10_CONDITIONS)
    y = mlb.fit_transform(y_list).astype(np.float32)
    
    print(f"  X: {X.shape}, y: {y.shape}")
    print(f"  Label counts: {dict(zip(TOP_10_CONDITIONS, y.sum(axis=0).astype(int)))}")
    
    return X, y, mlb


# ============================================================================
# Training
# ============================================================================

def train(X_train, y_train, X_val, y_val, scaler):
    # Scale
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    
    # To tensors
    train_ds = TensorDataset(torch.FloatTensor(X_train_s), torch.FloatTensor(y_train))
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    X_val_t = torch.FloatTensor(X_val_s)
    y_val_t = torch.FloatTensor(y_val)
    
    # Model
    model = MultiLabelMLP(X_train.shape[1], HIDDEN_UNITS, len(TOP_10_CONDITIONS), DROPOUT_RATE)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    
    print(f"\nModel: {model}")
    print(f"\nTraining for {EPOCHS} epochs...")
    
    best_loss = float('inf')
    best_state = None
    
    for epoch in range(EPOCHS):
        # Train
        model.train()
        train_loss = 0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(X_batch), y_batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        train_loss /= len(train_loader)
        
        # Validate
        model.eval()
        with torch.no_grad():
            val_pred = model(X_val_t)
            val_loss = criterion(val_pred, y_val_t).item()
            val_hamming = hamming_loss(y_val, (val_pred.numpy() >= 0.5).astype(int))
        
        print(f"  Epoch {epoch+1:2d}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, val_hamming={val_hamming:.4f}")
        
        if val_loss < best_loss:
            best_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
    
    model.load_state_dict(best_state)
    return model


def evaluate(model, X_test, y_test, scaler, mlb):
    X_test_s = scaler.transform(X_test)
    
    model.eval()
    with torch.no_grad():
        y_proba = model(torch.FloatTensor(X_test_s)).numpy()
    
    y_pred = (y_proba >= 0.5).astype(int)
    h_loss = hamming_loss(y_test, y_pred)
    
    print(f"\n{'='*60}")
    print(f"Hamming Loss: {h_loss:.4f}")
    print(f"{'='*60}")
    
    report = classification_report(y_test, y_pred, target_names=mlb.classes_, output_dict=True, zero_division=0)
    print(classification_report(y_test, y_pred, target_names=mlb.classes_, zero_division=0))
    
    metrics = {
        "hamming_loss": float(h_loss),
        "conditions": {c: {k: float(v) if k != "support" else int(v) for k, v in report[c].items()} for c in mlb.classes_ if c in report},
        "macro_avg": {k: float(v) for k, v in report["macro avg"].items() if k != "support"},
    }
    return metrics


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 60)
    print("Training Top-10 Condition MLP (PyTorch)")
    print("Google's Architecture: 6144 -> 256 -> 128 -> 10")
    print("=" * 60)
    
    embeddings = load_embeddings(DATA_DIR)
    df = load_scin_data(DATA_DIR)
    X, y, mlb = prepare_data(df, embeddings)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\nTrain: {len(X_train)}, Test: {len(X_test)}")
    
    scaler = StandardScaler()
    model = train(X_train, y_train, X_test, y_test, scaler)
    metrics = evaluate(model, X_test, y_test, scaler, mlb)
    
    # Save
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    wrapper = TorchMLPWrapper(model, scaler)
    joblib.dump(wrapper, MODELS_DIR / "top10_mlp_model.joblib")
    joblib.dump(scaler, MODELS_DIR / "top10_mlp_scaler.joblib")
    
    with open(MODELS_DIR / "top10_mlp_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    config = {"conditions": list(mlb.classes_), "embedding_dim": 6144, "threshold": 0.5, "architecture": "pytorch_mlp"}
    with open(MODELS_DIR / "top10_mlp_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"\nSaved to {MODELS_DIR}")
    print(f"Hamming Loss: {metrics['hamming_loss']:.4f} (Google's benchmark: ~0.114)")
    print(f"Macro F1: {metrics['macro_avg']['f1-score']:.4f}")


if __name__ == "__main__":
    main()
