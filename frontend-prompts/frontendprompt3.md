# Frontend Update Prompt: Backend Mapping Updates (V2.1)

## Overview

The backend rule-based condition-to-concern and product-to-concern mappings have been updated based on the cosmo team's CSV mapping. The API response structure remains **fully backward compatible** - all existing fields work the same way. However, there are **new optional fields** you can use to enhance the UI.

**No breaking changes** - your existing frontend code will continue to work without modifications.

---

## What Changed in Backend

### 1. New Concern Tags (4 additional)

The backend now supports **10 concern tags** instead of 6:

**Original 6 (unchanged):**
- `Dry_Sensitive`
- `Breakouts_Bumps`
- `Itchy_Hives`
- `Red_Scaly_Patches`
- `Pigment_Tone_Issues`
- `Possible_Infection`

**New 4 (optional to display):**
- `Dark_Spots` - Maps to Pigment_Tone_Issues for aggregation
- `Dull_Uneven_Tone` - Maps to Pigment_Tone_Issues for aggregation
- `Dry_Dehydrated` - Maps to Dry_Sensitive for aggregation
- `Mild_Scars` - Standalone concern for scar-specific products

**Frontend Impact:** These will appear in the `concerns` object if active. Your existing dynamic concern rendering should handle them automatically since you iterate over `concerns` keys. However, you may want to add display names for the new tags.

---

### 2. New Fields in Concern Objects

Each concern object in the `/analyze_v2` response now includes these **optional new fields**:

```typescript
interface ConcernResult {
  // ... existing fields (prob, active, title, description, etc.) ...
  
  // NEW OPTIONAL FIELDS:
  recommendation_type?: "yes" | "gentle_only" | "no";  // Product recommendation level
  notes?: string;                                       // Internal notes from CSV
  best_match_products?: string[];                      // Suggested products from CSV
  maps_to?: string;                                    // For concerns that aggregate (e.g., "Pigment_Tone_Issues")
}
```

**Frontend Impact:** These fields are optional. You can ignore them completely, or use them to enhance the UI (see suggestions below).

---

### 3. Updated Product Mappings

Product-to-concern mappings have been updated to match the CSV. This means:
- Product recommendations may change slightly
- New products may be recommended: `hyaluronic_b5_serum`, `hudson_scar_gel`
- Product IDs remain the same, but their `supported_concerns` arrays may have changed

**Frontend Impact:** The `routine.steps` structure is unchanged. Products will be recommended based on the updated mappings automatically.

---

## Recommended Frontend Enhancements (Optional)

### 1. Display Recommendation Type Badge

If a concern has `recommendation_type: "gentle_only"`, show a visual indicator:

```typescript
// In your ConcernCard component
{concern.recommendation_type === "gentle_only" && (
  <Badge color="blue">Gentle Products Only</Badge>
)}

{concern.recommendation_type === "no" && (
  <Alert>Please consult a dermatologist for this concern.</Alert>
)}
```

### 2. Show Best Match Products

If `best_match_products` exists, you could highlight those products in the routine:

```typescript
// In ProductSuggestions component
const isBestMatch = concern.best_match_products?.includes(product.id);
{isBestMatch && <StarIcon />} // Show star or highlight
```

### 3. Add Display Names for New Concern Tags

Update your concern display name mapping:

```typescript
const CONCERN_DISPLAY_NAMES: Record<string, string> = {
  // ... existing 6 ...
  "Dark_Spots": "Dark Spots and Post-Acne Marks",
  "Dull_Uneven_Tone": "Dull or Uneven Skin Tone",
  "Dry_Dehydrated": "Dehydrated Skin",
  "Mild_Scars": "Fresh Scars or Acne Marks",
};
```

### 4. Handle Aggregated Concerns (Optional)

If a concern has `maps_to`, it means it aggregates into another concern. You can:
- Show both concerns (the specific one + the aggregated one)
- OR only show the aggregated concern and hide the mapped one
- OR show a note: "This concern is related to [maps_to]"

Example:
```typescript
if (concern.maps_to) {
  // Dark_Spots maps to Pigment_Tone_Issues
  // You could show: "Dark Spots (related to Pigment & Tone Issues)"
}
```

---

## What You DON'T Need to Change

✅ **Keep as-is:**
- All existing API calls (`/analyze_v2`, `/analyze_v2_session`)
- Response structure parsing (all existing fields work)
- Concern card rendering (will automatically show new concerns)
- Product recommendation display (routine structure unchanged)
- Condition display logic
- Summary section logic

---

## Testing Checklist

After implementing (if you choose to), test:

1. ✅ Existing 6 concerns still display correctly
2. ✅ New 4 concerns display if they appear in results
3. ✅ Product recommendations still work
4. ✅ No TypeScript errors (new fields are optional)
5. ✅ Backward compatibility maintained

---

## Example: New Concern in Response

If the backend detects `Dark_Spots`, you'll see:

```json
{
  "concerns": {
    "Dark_Spots": {
      "prob": 0.65,
      "active": true,
      "title": "Dark Spots and Post-Acne Marks",
      "description": "Your photo shows patterns associated with dark spots...",
      "recommendation_type": "yes",
      "notes": "PIH/pigmentation - brightening products",
      "best_match_products": ["Discoloration Defense Serum"],
      "maps_to": "Pigment_Tone_Issues",
      // ... other existing fields ...
    },
    "Pigment_Tone_Issues": {
      "prob": 0.65,  // Aggregated from Dark_Spots
      "active": true,
      // ... existing fields ...
    }
  }
}
```

Your frontend should handle this automatically if you're iterating over `Object.keys(response.concerns)`.

---

## Summary

**TL;DR:**
- ✅ No breaking changes - existing code works
- ✅ 4 new concern tags may appear (handle dynamically)
- ✅ 4 new optional fields available (use if you want)
- ✅ Product mappings updated (automatic, no frontend changes needed)
- ✅ All existing functionality preserved

**Action Items (Optional):**
1. Add display names for 4 new concern tags
2. Optionally show `recommendation_type` badge
3. Optionally highlight `best_match_products`
4. Test that new concerns render correctly

**No Action Required:**
- API calls remain the same
- Response structure is backward compatible
- Existing concern/product display logic works as-is

