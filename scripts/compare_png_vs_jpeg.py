"""
Compare different image encoding formats for Derm Foundation embeddings.

This script compares embeddings generated with different image formats:
- RAW: Original file bytes (no re-encoding)
- PNG: Re-encode as PNG (lossless)
- JPEG: Re-encode as JPEG (lossy - adds artifacts)

For JPEG source images, RAW and PNG should produce similar embeddings
(same pixel values), while JPEG re-encoding adds double-compression.

Run from VM where Derm Foundation endpoint is accessible:
    python scripts/compare_png_vs_jpeg.py --image path/to/test_image.jpg
    
Or compare all images in a directory:
    python scripts/compare_png_vs_jpeg.py --dir datasets/DATASET/eczema --max 5

Metrics computed:
- Cosine similarity between embeddings
- L2 (Euclidean) distance
- Max/mean absolute difference
"""

import argparse
import sys
from pathlib import Path

import numpy as np

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

# Import with format support
from lib.derm_local import embed_image_path


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def compare_formats(image_path: str) -> dict:
    """
    Generate embeddings with RAW, PNG, and JPEG formats and compare.
    
    For JPEG source images:
    - RAW vs PNG should be nearly identical (same pixels, different encoding)
    - RAW/PNG vs JPEG will differ (JPEG re-encoding adds artifacts)
    
    Returns dict with cosine similarities and distances.
    """
    from pathlib import Path
    
    img_path = Path(image_path)
    suffix = img_path.suffix.lower()
    
    print(f"\n{'='*60}")
    print(f"Comparing: {image_path}")
    print(f"Original format: {suffix}")
    print('='*60)
    
    # Generate embeddings with each format
    print("\n[1/3] Generating RAW embedding (original bytes)...")
    emb_raw = embed_image_path(image_path, image_format="raw")
    
    print("\n[2/3] Generating PNG embedding (re-encoded as PNG)...")
    emb_png = embed_image_path(image_path, image_format="png")
    
    print("\n[3/3] Generating JPEG embedding (re-encoded as JPEG)...")
    emb_jpeg = embed_image_path(image_path, image_format="jpeg")
    
    # Compute metrics
    cos_raw_png = cosine_similarity(emb_raw, emb_png)
    cos_raw_jpeg = cosine_similarity(emb_raw, emb_jpeg)
    cos_png_jpeg = cosine_similarity(emb_png, emb_jpeg)
    
    l2_raw_png = np.linalg.norm(emb_raw - emb_png)
    l2_raw_jpeg = np.linalg.norm(emb_raw - emb_jpeg)
    l2_png_jpeg = np.linalg.norm(emb_png - emb_jpeg)
    
    results = {
        "image": str(image_path),
        "original_format": suffix,
        "cosine_raw_png": float(cos_raw_png),
        "cosine_raw_jpeg": float(cos_raw_jpeg),
        "cosine_png_jpeg": float(cos_png_jpeg),
        "l2_raw_png": float(l2_raw_png),
        "l2_raw_jpeg": float(l2_raw_jpeg),
        "l2_png_jpeg": float(l2_png_jpeg),
    }
    
    # Print results
    print(f"\n{'='*60}")
    print("RESULTS - Cosine Similarity (1.0 = identical)")
    print('='*60)
    print(f"  RAW vs PNG:  {cos_raw_png:.6f}  (should be ~1.0 for JPEG source)")
    print(f"  RAW vs JPEG: {cos_raw_jpeg:.6f}  (double-compression effect)")
    print(f"  PNG vs JPEG: {cos_png_jpeg:.6f}")
    
    print(f"\n  L2 Distance:")
    print(f"  RAW vs PNG:  {l2_raw_png:.4f}")
    print(f"  RAW vs JPEG: {l2_raw_jpeg:.4f}")
    print(f"  PNG vs JPEG: {l2_png_jpeg:.4f}")
    
    # Interpretation
    print(f"\n{'='*60}")
    print("INTERPRETATION")
    print('='*60)
    
    if suffix in {'.jpg', '.jpeg'}:
        print(f"  Source is JPEG - already has compression artifacts.")
        if cos_raw_png >= 0.9999:
            print(f"  ✓ RAW ≈ PNG: Both preserve original JPEG pixels")
        if cos_raw_jpeg < cos_raw_png:
            diff = cos_raw_png - cos_raw_jpeg
            print(f"  ⚠ JPEG re-encoding degrades by {diff:.6f}")
            print(f"    → Use 'raw' format to avoid double-compression!")
    elif suffix == '.png':
        print(f"  Source is PNG (lossless) - no compression artifacts.")
        if cos_raw_jpeg < 0.999:
            print(f"  ⚠ JPEG encoding introduces significant artifacts")
            print(f"    → Use 'raw' or 'png' format for PNG sources!")
    
    # Recommendation
    print(f"\n  RECOMMENDATION: Use 'raw' format (default)")
    print(f"    - Avoids double-compression for JPEG sources")
    print(f"    - Preserves quality for PNG sources")
    
    return results


def compare_directory(dir_path: str, max_images: int = 10) -> list:
    """Compare all images in a directory."""
    from pathlib import Path
    
    dir_path = Path(dir_path)
    extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    images = sorted([
        f for f in dir_path.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ])[:max_images]
    
    print(f"\nFound {len(images)} images in {dir_path}")
    
    all_results = []
    for img in images:
        try:
            results = compare_formats(str(img))
            all_results.append(results)
        except Exception as e:
            print(f"ERROR processing {img}: {e}")
    
    # Summary
    if all_results:
        cos_raw_png = [r["cosine_raw_png"] for r in all_results]
        cos_raw_jpeg = [r["cosine_raw_jpeg"] for r in all_results]
        
        print(f"\n{'='*60}")
        print("SUMMARY ACROSS ALL IMAGES")
        print('='*60)
        print(f"  Images compared: {len(all_results)}")
        print(f"\n  RAW vs PNG (should be ~1.0):")
        print(f"    Avg: {np.mean(cos_raw_png):.6f}")
        print(f"    Min: {np.min(cos_raw_png):.6f}")
        print(f"\n  RAW vs JPEG (double-compression effect):")
        print(f"    Avg: {np.mean(cos_raw_jpeg):.6f}")
        print(f"    Min: {np.min(cos_raw_jpeg):.6f}")
        
        degradation = np.mean(cos_raw_png) - np.mean(cos_raw_jpeg)
        print(f"\n  Average degradation from JPEG re-encoding: {degradation:.6f}")
        
        if degradation > 0.001:
            print(f"\n  ⚠ JPEG re-encoding causes measurable degradation!")
            print(f"    Use 'raw' format (now the default) to avoid this.")
    
    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Compare PNG vs JPEG embeddings for Derm Foundation"
    )
    parser.add_argument(
        "--image",
        help="Path to a single image to compare"
    )
    parser.add_argument(
        "--dir",
        help="Path to a directory of images to compare"
    )
    parser.add_argument(
        "--max",
        type=int,
        default=10,
        help="Max images to compare from directory (default: 10)"
    )
    
    args = parser.parse_args()
    
    if not args.image and not args.dir:
        parser.error("Must specify either --image or --dir")
    
    if args.image:
        compare_formats(args.image)
    elif args.dir:
        compare_directory(args.dir, max_images=args.max)


if __name__ == "__main__":
    main()

