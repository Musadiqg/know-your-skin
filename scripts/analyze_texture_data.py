"""
Analyze SCIN dataset to determine if texture data is sufficient for training.

This script checks:
1. How many cases have texture labels
2. Distribution of each texture type
3. Whether we have enough data for reliable classification
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

def main():
    print("=" * 60)
    print("TEXTURE DATA ANALYSIS FOR SCIN DATASET")
    print("=" * 60)
    
    # Load cases data
    cases_path = DATA_DIR / "scin_cases.csv"
    if not cases_path.exists():
        print(f"ERROR: {cases_path} not found!")
        return
    
    cases = pd.read_csv(cases_path)
    total_cases = len(cases)
    print(f"\nTotal cases in dataset: {total_cases}")
    
    # Find texture columns
    texture_cols = [c for c in cases.columns if 'texture' in c.lower()]
    print(f"\nTexture columns found: {texture_cols}")
    
    if not texture_cols:
        print("ERROR: No texture columns found in dataset!")
        return
    
    # First, let's inspect the actual data format
    print("\n" + "-" * 60)
    print("DATA FORMAT INSPECTION")
    print("-" * 60)
    
    for col in texture_cols:
        print(f"\n{col}:")
        print(f"  dtype: {cases[col].dtype}")
        unique_vals = cases[col].dropna().unique()[:10]  # First 10 unique values
        print(f"  Sample values: {unique_vals}")
        print(f"  Value counts:")
        vc = cases[col].value_counts(dropna=False).head(5)
        for val, count in vc.items():
            print(f"    {repr(val)}: {count}")
    
    print("\n" + "-" * 60)
    print("TEXTURE COLUMN STATISTICS")
    print("-" * 60)
    
    texture_true_counts = {}
    
    for col in texture_cols:
        non_null = cases[col].notna().sum()
        
        # More robust True detection - check all possible formats
        col_data = cases[col]
        
        # Convert to string and check for various True representations
        true_count = 0
        false_count = 0
        
        for val in col_data.dropna().unique():
            val_str = str(val).lower().strip()
            count = (col_data == val).sum()
            
            if val_str in ['true', '1', '1.0', 'yes', 't']:
                true_count += count
            elif val_str in ['false', '0', '0.0', 'no', 'f']:
                false_count += count
        
        pct_true = (true_count / total_cases * 100) if total_cases > 0 else 0
        texture_true_counts[col] = true_count
        
        print(f"\n{col}:")
        print(f"  Non-null values: {non_null} ({non_null/total_cases*100:.1f}%)")
        print(f"  True (positive): {true_count} ({pct_true:.1f}%)")
        print(f"  False (negative): {false_count}")
    
    # Check cases with ANY texture data
    print("\n" + "-" * 60)
    print("CASES WITH TEXTURE DATA")
    print("-" * 60)
    
    cases_with_texture = cases[texture_cols].notna().any(axis=1).sum()
    print(f"Cases with at least one texture label: {cases_with_texture} ({cases_with_texture/total_cases*100:.1f}%)")
    
    # Summary of True counts
    print("\n" + "-" * 60)
    print("SUMMARY OF POSITIVE (TRUE) LABELS")
    print("-" * 60)
    
    total_true = 0
    for col, count in texture_true_counts.items():
        short_name = col.replace('textures_', '').upper()
        print(f"  {short_name}: {count} cases")
        total_true += count
    
    print(f"\n  TOTAL positive texture labels: {total_true}")
    
    # Summary recommendation
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    
    # Find the most common texture type
    if texture_true_counts:
        max_texture = max(texture_true_counts, key=texture_true_counts.get)
        max_count = texture_true_counts[max_texture]
        
        print(f"\nMost common texture: {max_texture.replace('textures_', '')} ({max_count} cases)")
        
        if max_count >= 1000:
            print("✅ GOOD: Sufficient data for texture classification")
            print("   Recommendation: Train texture classifier")
        elif max_count >= 500:
            print("⚠️  MARGINAL: Limited data, may have lower accuracy")
            print("   Recommendation: Consider training with caution")
        elif max_count >= 100:
            print("⚠️  LIMITED: Some data available but accuracy may vary")
            print("   Recommendation: Can try, but expect variable results")
        else:
            print("❌ POOR: Insufficient data for reliable texture classification")
            print("   Recommendation: Skip texture, focus on FST + Monk")


if __name__ == "__main__":
    main()

