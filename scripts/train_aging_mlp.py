"""
Train an aging signs classifier using Derm Foundation embeddings.

This is a SINGLE-LABEL MULTI-CLASS problem (3 classes: dark spots, puffy eyes, wrinkles).

Architecture options:
1. Logistic Regression (simpler, better for small datasets)
2. Small MLP (if data permits)

Uses 5-fold stratified cross-validation for reliable accuracy estimates.

Run: python scripts/train_aging_mlp.py
"""

import json
from pathlib import Path
from typing import List, Tuple, Dict

import joblib
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# Configuration
# ============================================================================

AGING_CLASSES = ["dark spots", "puffy eyes", "wrinkles"]

# MLP Architecture (smaller due to smaller dataset ~900 images)
HIDDEN_UNITS = [128, 64]
DROPOUT_RATE = 0.3  # Higher dropout for smaller dataset
WEIGHT_DECAY = 1e-3  # Stronger regularization
LEARNING_RATE = 5e-4
EPOCHS = 50
BATCH_SIZE = 16  # Smaller batch size for small dataset

# Cross-validation
N_FOLDS = 5
RANDOM_STATE = 42

DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR = Path(__file__).parent.parent / "app" / "models" / "aging"


# ============================================================================
# PyTorch Model (Multi-class, NOT multi-label)
# ============================================================================

class AgingMLP(nn.Module):
    """
    Multi-class classifier for aging signs.
    Uses Softmax output (single label) not Sigmoid (multi-label).
    """
    
    def __init__(self, input_dim: int, hidden_units: List[int], num_classes: int, dropout: float = 0.3):
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        for units in hidden_units:
            layers.extend([
                nn.Linear(prev_dim, units),
                nn.ReLU(),
                nn.BatchNorm1d(units),  # Added batch norm for stability
                nn.Dropout(dropout),
            ])
            prev_dim = units
        
        # Output layer - no activation (we use CrossEntropyLoss which includes softmax)
        layers.append(nn.Linear(prev_dim, num_classes))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


# ============================================================================
# Wrapper for sklearn-compatible inference
# ============================================================================

class AgingMLPWrapper:
    """
    Sklearn-compatible wrapper for inference.
    Returns probabilities for each class.
    """
    
    def __init__(self, model: AgingMLP, scaler: StandardScaler, classes: List[str]):
        self.model = model
        self.scaler = scaler
        self.classes = classes
        self.model.eval()
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return predicted class labels."""
        proba = self.predict_proba(X)
        return np.array([self.classes[i] for i in np.argmax(proba, axis=1)])
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return probability for each class (n_samples, n_classes)."""
        X_scaled = self.scaler.transform(X.astype(np.float32))
        X_t = torch.FloatTensor(X_scaled)
        
        with torch.no_grad():
            logits = self.model(X_t)
            proba = torch.softmax(logits, dim=1).numpy()
        
        return proba


# ============================================================================
# Data Loading
# ============================================================================

def load_data() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load embeddings and labels from NPZ file."""
    emb_path = DATA_DIR / "aging_embeddings.npz"
    
    if not emb_path.exists():
        raise FileNotFoundError(
            f"Embeddings not found at {emb_path}. "
            f"Run generate_aging_embeddings.py first."
        )
    
    print(f"Loading embeddings from {emb_path}...")
    data = np.load(emb_path, allow_pickle=True)
    
    paths = data['paths']
    embeddings = data['embeddings']
    labels = data['labels']
    
    print(f"  Loaded {len(embeddings)} embeddings")
    print(f"  Embedding dimension: {embeddings.shape[1]}")
    print(f"  Classes: {np.unique(labels)}")
    
    # Class distribution
    print("\n  Class distribution:")
    for cls in AGING_CLASSES:
        count = np.sum(labels == cls)
        print(f"    {cls}: {count}")
    
    return embeddings, labels, paths


# ============================================================================
# Training Functions
# ============================================================================

def train_mlp_fold(X_train, y_train, X_val, y_val, scaler, label_encoder, fold_num):
    """Train MLP for one fold."""
    
    # Scale
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    
    # Encode labels
    y_train_enc = label_encoder.fit_transform(y_train)
    y_val_enc = label_encoder.transform(y_val)
    
    # To tensors
    train_ds = TensorDataset(
        torch.FloatTensor(X_train_s), 
        torch.LongTensor(y_train_enc)
    )
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    
    X_val_t = torch.FloatTensor(X_val_s)
    y_val_t = torch.LongTensor(y_val_enc)
    
    # Model
    model = AgingMLP(
        input_dim=X_train.shape[1],
        hidden_units=HIDDEN_UNITS,
        num_classes=len(AGING_CLASSES),
        dropout=DROPOUT_RATE
    )
    
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        model.parameters(), 
        lr=LEARNING_RATE, 
        weight_decay=WEIGHT_DECAY
    )
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )
    
    best_val_acc = 0
    best_state = None
    patience_counter = 0
    patience = 10
    
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
            val_logits = model(X_val_t)
            val_loss = criterion(val_logits, y_val_t).item()
            val_pred = torch.argmax(val_logits, dim=1).numpy()
            val_acc = accuracy_score(y_val_enc, val_pred)
        
        scheduler.step(val_loss)
        
        # Early stopping
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
        
        if patience_counter >= patience:
            break
    
    model.load_state_dict(best_state)
    return model, best_val_acc


def train_logreg_fold(X_train, y_train, X_val, y_val, scaler):
    """Train Logistic Regression for one fold."""
    
    # Scale
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    
    # Train with strong regularization
    clf = LogisticRegression(
        C=0.1,  # Strong regularization (lower = stronger)
        max_iter=1000,
        class_weight='balanced',
        solver='lbfgs',
        random_state=RANDOM_STATE
    )
    
    clf.fit(X_train_s, y_train)
    
    val_pred = clf.predict(X_val_s)
    val_acc = accuracy_score(y_val, val_pred)
    
    return clf, val_acc


def cross_validate(X, y, model_type='both'):
    """
    Run 5-fold stratified cross-validation.
    
    model_type: 'mlp', 'logreg', or 'both'
    """
    
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    
    results = {'mlp': [], 'logreg': []}
    
    print(f"\n{'='*60}")
    print(f"CROSS-VALIDATION ({N_FOLDS} folds)")
    print("=" * 60)
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        print(f"\nFold {fold+1}/{N_FOLDS}:")
        print(f"  Train: {len(X_train)}, Val: {len(X_val)}")
        
        if model_type in ['logreg', 'both']:
            scaler = StandardScaler()
            _, logreg_acc = train_logreg_fold(X_train, y_train, X_val, y_val, scaler)
            results['logreg'].append(logreg_acc)
            print(f"  LogReg accuracy: {logreg_acc:.1%}")
        
        if model_type in ['mlp', 'both']:
            scaler = StandardScaler()
            label_encoder = LabelEncoder()
            label_encoder.fit(AGING_CLASSES)
            _, mlp_acc = train_mlp_fold(X_train, y_train, X_val, y_val, scaler, label_encoder, fold)
            results['mlp'].append(mlp_acc)
            print(f"  MLP accuracy:    {mlp_acc:.1%}")
    
    return results


def train_final_model(X, y, model_type='mlp'):
    """
    Train final model on 80% data, evaluate on 20% holdout.
    """
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    
    print(f"\n{'='*60}")
    print("FINAL MODEL TRAINING")
    print("=" * 60)
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    scaler = StandardScaler()
    label_encoder = LabelEncoder()
    label_encoder.fit(AGING_CLASSES)
    
    if model_type == 'mlp':
        model, _ = train_mlp_fold(X_train, y_train, X_test, y_test, scaler, label_encoder, 0)
        
        # Fit scaler on full training data
        scaler = StandardScaler()
        scaler.fit(X_train)
        
        # Wrap for inference
        wrapper = AgingMLPWrapper(model, scaler, AGING_CLASSES)
        
        # Predictions
        y_pred = wrapper.predict(X_test)
        y_proba = wrapper.predict_proba(X_test)
        
    else:  # logreg
        scaler.fit(X_train)
        X_train_s = scaler.transform(X_train)
        X_test_s = scaler.transform(X_test)
        
        model = LogisticRegression(
            C=0.1,
            max_iter=1000,
            class_weight='balanced',
            solver='lbfgs',
            random_state=RANDOM_STATE
        )
        model.fit(X_train_s, y_train)
        
        wrapper = model  # LogReg is already sklearn-compatible
        
        y_pred = model.predict(X_test_s)
        y_proba = model.predict_proba(X_test_s)
    
    # Evaluate
    test_acc = accuracy_score(y_test, y_pred)
    
    print(f"\n{'='*60}")
    print(f"TEST SET RESULTS ({model_type.upper()})")
    print("=" * 60)
    print(f"\nAccuracy: {test_acc:.1%}")
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=AGING_CLASSES))
    
    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred, labels=AGING_CLASSES)
    # Truncate class names for display
    display_names = ["dark_sp", "puffy_e", "wrinkle"]
    print(f"{'':>10} " + " ".join(f"{c:>8}" for c in display_names))
    for i, cls in enumerate(AGING_CLASSES):
        print(f"{display_names[i]:>10} " + " ".join(f"{cm[i,j]:>8}" for j in range(len(AGING_CLASSES))))
    
    return wrapper, scaler, test_acc, y_test, y_pred


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 60)
    print("AGING SIGNS CLASSIFIER TRAINING")
    print("=" * 60)
    print(f"Classes: {AGING_CLASSES}")
    print(f"Architecture: MLP {HIDDEN_UNITS} or Logistic Regression")
    
    # Load data
    X, y, paths = load_data()
    
    # Cross-validation to compare models
    cv_results = cross_validate(X, y, model_type='both')
    
    # Print CV summary
    print(f"\n{'='*60}")
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 60)
    
    for model_name, scores in cv_results.items():
        if scores:
            mean = np.mean(scores)
            std = np.std(scores)
            print(f"\n{model_name.upper()}:")
            print(f"  Accuracy: {mean:.1%} ± {std:.1%}")
            print(f"  Folds: {[f'{s:.1%}' for s in scores]}")
    
    # Determine best model
    logreg_mean = np.mean(cv_results['logreg']) if cv_results['logreg'] else 0
    mlp_mean = np.mean(cv_results['mlp']) if cv_results['mlp'] else 0
    
    # Prefer LogReg if similar (simpler model, less overfitting risk)
    if logreg_mean >= mlp_mean - 0.02:  # Within 2%
        best_model_type = 'logreg'
        print(f"\n→ Selecting LOGISTIC REGRESSION (simpler, similar performance)")
    else:
        best_model_type = 'mlp'
        print(f"\n→ Selecting MLP (better performance)")
    
    # Train final model
    wrapper, scaler, test_acc, y_test, y_pred = train_final_model(X, y, best_model_type)
    
    # Save model
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    if best_model_type == 'mlp':
        joblib.dump(wrapper, MODELS_DIR / "aging_mlp_model.joblib")
        joblib.dump(scaler, MODELS_DIR / "aging_mlp_scaler.joblib")
    else:
        joblib.dump(wrapper, MODELS_DIR / "aging_logreg_model.joblib")
        joblib.dump(scaler, MODELS_DIR / "aging_logreg_scaler.joblib")
    
    # Save config
    config = {
        "classes": AGING_CLASSES,
        "embedding_dim": 6144,
        "model_type": best_model_type,
        "cv_accuracy_mean": float(np.mean(cv_results[best_model_type])),
        "cv_accuracy_std": float(np.std(cv_results[best_model_type])),
        "test_accuracy": float(test_acc),
    }
    
    with open(MODELS_DIR / "aging_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Summary
    print(f"\n{'='*60}")
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Model saved to: {MODELS_DIR}")
    print(f"Model type: {best_model_type}")
    print(f"CV Accuracy: {np.mean(cv_results[best_model_type]):.1%} ± {np.std(cv_results[best_model_type]):.1%}")
    print(f"Test Accuracy: {test_acc:.1%}")
    print(f"\nRandom baseline (3 classes): 33.3%")
    print(f"Improvement over random: {(test_acc - 0.333) / 0.333:.0%}")
    
    # Final recommendation
    print(f"\n{'='*60}")
    print("RECOMMENDATION")
    print("=" * 60)
    if test_acc >= 0.70:
        print("✅ GOOD: Model accuracy is sufficient for production use.")
    elif test_acc >= 0.50:
        print("⚠️  ACCEPTABLE: Model is learning but could be improved.")
        print("   Consider: more training data, data augmentation, or different model.")
    else:
        print("❌ POOR: Model accuracy is too low for reliable predictions.")
        print("   Derm Foundation may not capture aging features well.")
        print("   Consider: face-specific embeddings (FaceNet, ArcFace) or CNNs.")


if __name__ == "__main__":
    main()

