"""
Generate Derm Foundation embeddings for skin type classification dataset.

This script calls the private Vertex AI endpoint to get embeddings for all
images in the skin-type-merged/ folder. Must be run from the GCP VM where
the private endpoint is accessible.

Output: data/skintype_embeddings.npz
"""

import sys
import time
from pathlib import Path

import numpy as np

# Add app to path so we can import derm_local
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from lib.derm_local import embed_image_path


def generate_embeddings():
    base_dir = Path(__file__).parent.parent
    merged_dir = base_dir / "skin-type-merged"
    output_path = base_dir / "data" / "skintype_embeddings.npz"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Classes
    classes = ["dry", "normal", "oily", "redness"]
    
    print("=" * 60)
    print("GENERATING SKIN TYPE EMBEDDINGS")
    print("=" * 60)
    print(f"\nSource: {merged_dir}")
    print(f"Output: {output_path}")
    print(f"Classes: {classes}")
    
    embeddings_dict = {}
    labels_dict = {}
    
    total_images = 0
    failed_images = []
    
    for class_name in classes:
        class_dir = merged_dir / class_name
        
        if not class_dir.exists():
            print(f"\n⚠ WARNING: Class directory not found: {class_dir}")
            continue
        
        # Get all image files
        extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        image_files = sorted([
            f for f in class_dir.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ])
        
        print(f"\n[{class_name.upper()}] Processing {len(image_files)} images...")
        
        for i, img_path in enumerate(image_files):
            # Progress
            if (i + 1) % 10 == 0 or i == 0:
                print(f"  Processing {i+1}/{len(image_files)}: {img_path.name}")
            
            try:
                # Get embedding from Derm Foundation
                embedding = embed_image_path(str(img_path))
                
                # Store with relative path as key
                rel_path = f"{class_name}/{img_path.name}"
                embeddings_dict[rel_path] = embedding
                labels_dict[rel_path] = class_name
                
                total_images += 1
                
            except Exception as e:
                print(f"  ✗ FAILED: {img_path.name} - {e}")
                failed_images.append(str(img_path))
            
            # Small delay to avoid overwhelming the endpoint
            time.sleep(0.1)
    
    # Save embeddings
    print(f"\n{'='*60}")
    print("SAVING EMBEDDINGS")
    print("=" * 60)
    
    # Convert to arrays for efficient storage
    paths = list(embeddings_dict.keys())
    embeddings = np.array([embeddings_dict[p] for p in paths], dtype=np.float32)
    labels = np.array([labels_dict[p] for p in paths])
    
    # Save to NPZ
    np.savez(
        output_path,
        paths=paths,
        embeddings=embeddings,
        labels=labels,
        classes=classes,
    )
    
    print(f"  Saved to: {output_path}")
    print(f"  Embeddings shape: {embeddings.shape}")
    print(f"  Total images: {total_images}")
    
    if failed_images:
        print(f"\n⚠ Failed images ({len(failed_images)}):")
        for f in failed_images[:10]:
            print(f"  - {f}")
        if len(failed_images) > 10:
            print(f"  ... and {len(failed_images) - 10} more")
    
    # Summary per class
    print(f"\n{'='*60}")
    print("SUMMARY")
    print("=" * 60)
    
    for class_name in classes:
        count = sum(1 for l in labels if l == class_name)
        print(f"  {class_name}: {count} embeddings")
    
    print(f"\n  TOTAL: {total_images} embeddings")
    print(f"  Embedding dimension: {embeddings.shape[1] if len(embeddings) > 0 else 'N/A'}")
    
    return output_path


if __name__ == "__main__":
    generate_embeddings()

