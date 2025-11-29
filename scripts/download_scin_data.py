"""
Download SCIN dataset embeddings and labels for training.

This script downloads:
1. Pre-computed Derm Foundation embeddings from HuggingFace
2. SCIN case metadata and labels from Google Cloud Storage

Run: python scripts/download_scin_data.py
"""

import io
import os
from pathlib import Path

import numpy as np
import pandas as pd
from google.cloud import storage
from huggingface_hub import hf_hub_download


# Configuration
SCIN_HF_REPO = "google/derm-foundation"
SCIN_HF_EMBEDDING_FILE = "scin_dataset_precomputed_embeddings.npz"

SCIN_GCP_PROJECT = "dx-scin-public"
SCIN_GCS_BUCKET = "dx-scin-public-data"
SCIN_CASES_CSV = "dataset/scin_cases.csv"
SCIN_LABELS_CSV = "dataset/scin_labels.csv"

# Output paths
DATA_DIR = Path(__file__).parent.parent / "data"


def download_embeddings():
    """Download pre-computed embeddings from HuggingFace."""
    print(f"Downloading embeddings from HuggingFace ({SCIN_HF_REPO})...")
    
    output_path = DATA_DIR / "scin_embeddings.npz"
    
    if output_path.exists():
        print(f"  Embeddings already exist at {output_path}")
        # Verify the file
        try:
            data = np.load(output_path)
            print(f"  Verified: {len(data.files)} embeddings found")
            return output_path
        except Exception as e:
            print(f"  Existing file is corrupted, re-downloading: {e}")
    
    # Download from HuggingFace
    downloaded_path = hf_hub_download(
        repo_id=SCIN_HF_REPO,
        filename=SCIN_HF_EMBEDDING_FILE,
        local_dir=str(DATA_DIR),
    )
    
    # Rename to our standard name if needed
    downloaded_path = Path(downloaded_path)
    if downloaded_path != output_path:
        if output_path.exists():
            output_path.unlink()
        downloaded_path.rename(output_path)
    
    # Verify
    data = np.load(output_path)
    print(f"  Downloaded {len(data.files)} embeddings to {output_path}")
    
    # Show sample
    for key in list(data.keys())[:1]:
        print(f"  Sample: {key} -> shape {data[key].shape}")
    
    return output_path


def download_scin_csv(bucket, csv_path: str, output_name: str) -> Path:
    """Download a CSV file from GCS."""
    output_path = DATA_DIR / output_name
    
    if output_path.exists():
        print(f"  {output_name} already exists at {output_path}")
        return output_path
    
    print(f"  Downloading {csv_path}...")
    blob = bucket.blob(csv_path)
    csv_bytes = blob.download_as_string()
    
    # Parse and save
    df = pd.read_csv(io.BytesIO(csv_bytes), dtype={"case_id": str})
    df.to_csv(output_path, index=False)
    print(f"  Saved {len(df)} rows to {output_path}")
    
    return output_path


def download_labels():
    """Download SCIN case and label CSVs from GCS."""
    print(f"Downloading SCIN labels from GCS ({SCIN_GCS_BUCKET})...")
    
    # Initialize GCS client (uses ADC or gcloud auth)
    try:
        client = storage.Client(project=SCIN_GCP_PROJECT)
    except Exception:
        # Try without explicit project (for public buckets)
        client = storage.Client.create_anonymous_client()
    
    bucket = client.bucket(SCIN_GCS_BUCKET)
    
    cases_path = download_scin_csv(bucket, SCIN_CASES_CSV, "scin_cases.csv")
    labels_path = download_scin_csv(bucket, SCIN_LABELS_CSV, "scin_labels.csv")
    
    return cases_path, labels_path


def verify_data():
    """Verify all data is downloaded and compatible."""
    print("\nVerifying downloaded data...")
    
    # Load embeddings
    emb_path = DATA_DIR / "scin_embeddings.npz"
    embeddings = np.load(emb_path)
    emb_keys = set(embeddings.files)
    print(f"  Embeddings: {len(emb_keys)} images")
    
    # Load cases
    cases_df = pd.read_csv(DATA_DIR / "scin_cases.csv", dtype={"case_id": str})
    print(f"  Cases: {len(cases_df)} rows")
    
    # Load labels
    labels_df = pd.read_csv(DATA_DIR / "scin_labels.csv", dtype={"case_id": str})
    print(f"  Labels: {len(labels_df)} rows")
    
    # Check image path overlap
    image_paths_in_cases = set()
    for col in ["image_1_path", "image_2_path", "image_3_path"]:
        if col in cases_df.columns:
            paths = cases_df[col].dropna().tolist()
            image_paths_in_cases.update(paths)
    
    # Embeddings use paths like "dataset/images/xxx.png"
    overlap = len(image_paths_in_cases & emb_keys)
    print(f"  Matching images: {overlap}/{len(image_paths_in_cases)}")
    
    if overlap < 1000:
        print("  WARNING: Low overlap. Checking path format...")
        sample_emb_key = list(emb_keys)[:3]
        sample_case_path = list(image_paths_in_cases)[:3]
        print(f"    Embedding keys sample: {sample_emb_key}")
        print(f"    Case paths sample: {sample_case_path}")
    
    print("\nData download complete!")


def main():
    # Create data directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Data directory: {DATA_DIR}\n")
    
    # Download embeddings
    download_embeddings()
    
    # Download labels
    download_labels()
    
    # Verify
    verify_data()


if __name__ == "__main__":
    main()

