"""Quick check of embeddings file structure."""
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
emb_path = DATA_DIR / "scin_embeddings.npz"

emb_data = np.load(emb_path, allow_pickle=True)
print("Keys in embeddings file:", list(emb_data.keys()))

for key in emb_data.keys():
    arr = emb_data[key]
    print(f"  {key}: shape={getattr(arr, 'shape', 'N/A')}, dtype={arr.dtype}, sample={arr[:3] if len(arr) < 10 else arr[:3]}")

