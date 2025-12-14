# Frontend Update Prompt: V2 Skin Analysis Endpoint

## Overview

You are updating an existing Next.js frontend to use a **new, improved skin analysis endpoint** (`/analyze_v2` and `/analyze_v2_session`). This replaces the old separate "Cosmetic Analysis" and "Deep Analysis" flows with a **single unified analysis** that is more accurate and interpretable.

**Important**: Do NOT delete the old endpoints (`/analyze`, `/analyze_session`, `/deep_analysis`) from the codebase—just remove their buttons from the UI. We're keeping them for backwards compatibility, but the user should only interact with the new V2 endpoint.

---

## Backend Base URL

The backend is running on the same GCP VM:

```
http://34.132.152.136:8000
```

The existing endpoints still exist:
- `GET /health` — unchanged
- `POST /analyze` — OLD, keep but hide button
- `POST /analyze_session` — OLD, keep but hide button  
- `POST /deep_analysis` — OLD, keep but hide button
- `POST /analyze_v2` — **NEW** (single image) - includes routine!
- `POST /analyze_v2_session` — **NEW** (multiple images) - includes routine!
- `POST /get_skin_profile` — **NEW** (FST + Monk + Texture)

---

## UI Changes Required

### Remove These Buttons (but keep code):
- "Analyse my Skin" (old cosmetic analysis)
- "Deep Analysis" (old condition analysis)

### Add This Button:
- **"Run Skin Analysis"** — calls `/analyze_v2` (1 image) or `/analyze_v2_session` (2-3 images)

### Keep As-Is:
- Image upload (1-3 images)
- Fitzpatrick Type display (from existing `/analyze` if needed, OR you can keep FST/Monk separate)
- Monk Skin Tone display

**Note**: Use the NEW `/get_skin_profile` endpoint for FST, Monk, and Texture!

```
POST /get_skin_profile
- Returns: Fitzpatrick Type + Monk Tone + Texture (with educational content)
- Call this in parallel with /analyze_v2 for complete results
```

The main "Run Skin Analysis" button should use V2 for the primary analysis.

---

## New V2 Endpoint Details

### `POST /analyze_v2` — Single Image

**Request:**
```
Content-Type: multipart/form-data
Field: image (file)
Optional: condition_threshold (float, default 0.5)
```

**Example curl:**
```bash
curl -X POST "http://34.132.152.136:8000/analyze_v2" \
  -F "image=@skin_photo.jpg"
```

### `POST /analyze_v2_session` — Multiple Images

**Request:**
```
Content-Type: multipart/form-data
Field: images (multiple files, same field name)
Optional: condition_threshold (float, default 0.5)
```

**Example curl:**
```bash
curl -X POST "http://34.132.152.136:8000/analyze_v2_session" \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.jpg" \
  -F "images=@photo3.jpg"
```

### `POST /get_skin_profile` — Skin Tone & Texture

**NEW endpoint** for educational skin information (FST, Monk, Texture).

**Request:**
```
Content-Type: multipart/form-data
Field: image (file)
```

**Response:**
```json
{
  "fitzpatrick": {
    "label": "FST2",
    "probs": {"FST1": 0.02, "FST2": 0.94, "FST3": 0.02, ...},
    "title": "Type II - Fair",
    "description": "Fair skin that usually burns and tans minimally.",
    "sun_advice": "Use SPF 30+ daily. You're prone to sunburn."
  },
  "monk_tone": {
    "label": 3,
    "probs": {"1": 0.01, "2": 0.05, "3": 0.67, ...},
    "group": "lighter",
    "education": "On lighter skin tones, redness and sunburn show up more visibly..."
  },
  "texture": {
    "Texture_Bumpy": {"prob": 0.72, "active": true},
    "Texture_Smooth": {"prob": 0.15, "active": false},
    "Texture_Rough_Flakey": {"prob": 0.45, "active": false},
    "Texture_Fluid_Filled": {"prob": 0.08, "active": false},
    "primary": "Texture_Bumpy",
    "education": "Raised or bumpy texture often indicates inflammation..."
  }
}
```

---

## V2 Response Structure

Here is the complete response structure with explanations:

```json
{
  "conditions": {
    "Eczema": {
      "prob": 0.0016,
      "active": false
    },
    "Allergic Contact Dermatitis": {
      "prob": 0.0007,
      "active": false
    },
    "Insect Bite": {
      "prob": 0.0008,
      "active": false
    },
    "Urticaria": {
      "prob": 0.00005,
      "active": false
    },
    "Psoriasis": {
      "prob": 0.00009,
      "active": false
    },
    "Folliculitis": {
      "prob": 0.013,
      "active": false
    },
    "Irritant Contact Dermatitis": {
      "prob": 0.0005,
      "active": false
    },
    "Tinea": {
      "prob": 0.0006,
      "active": false
    },
    "Herpes Zoster": {
      "prob": 0.00008,
      "active": false
    },
    "Acne": {
      "prob": 0.69,
      "active": true
    }
  },
  "concerns": {
    "Dry_Sensitive": {
      "prob": 0.002,
      "active": false,
      "threshold": 0.4,
      "contributing_conditions": {},
      "mapped_conditions": ["Eczema", "Allergic Contact Dermatitis", "Irritant Contact Dermatitis"],
      "can_recommend_products": true,
      "severity_weight": 1.0,
      "escalation_note": null,
      "title": "Dry or Sensitive Skin Tendencies",
      "description": "Your photo shows patterns often associated with dry or easily irritated skin...",
      "what_it_means": "These features suggest that your skin barrier may be fragile...",
      "care_focus": "Focus on gentle cleansing, replenishing moisture...",
      "disclaimer": "This is an AI-based cosmetic skin analysis, not a medical diagnosis...",
      "recommended_products": ["hydrating_cleanser", "barrier_repair_moisturizer", "gentle_spf"]
    },
    "Breakouts_Bumps": {
      "prob": 0.69,
      "active": true,
      "threshold": 0.45,
      "contributing_conditions": {
        "Acne": 0.69
      },
      "mapped_conditions": ["Acne", "Folliculitis"],
      "can_recommend_products": true,
      "severity_weight": 1.0,
      "escalation_note": null,
      "title": "Breakouts and Bumps",
      "description": "We detect patterns often seen with clogged pores, breakouts...",
      "what_it_means": "This can happen when excess oil, dead skin, or bacteria build up...",
      "care_focus": "Focus on balancing oil, gently exfoliating to keep pores clear...",
      "disclaimer": "This is not a medical diagnosis...",
      "recommended_products": ["clarifying_cleanser", "lightweight_noncomedogenic_moisturizer", "targeted_bha_serum"]
    },
    "Itchy_Hives": { /* similar structure */ },
    "Red_Scaly_Patches": { /* similar structure */ },
    "Pigment_Tone_Issues": { /* similar structure */ },
    "Possible_Infection": { /* similar structure */ }
  },
  "routine": {
    "active_concerns": [["Breakouts_Bumps", 0.69]],
    "steps": {
      "cleanser": [{"id": "clarifying_cleanser", "name": "Clarifying Cleanser", "step": "cleanser", "image_name": "clarifying_cleanser.png", "why": "Because your skin shows breakout patterns..."}],
      "treatment": [{"id": "bha_serum", "name": "BHA Serum", "step": "treatment", "image_name": null, "why": "Helps unclog pores..."}],
      "moisturizer": [{"id": "lightweight_moisturizer", "name": "Lightweight Moisturizer", "step": "moisturizer", "image_name": null, "why": "..."}],
      "sunscreen": [{"id": "daily_spf", "name": "Daily SPF", "step": "sunscreen", "image_name": null, "why": "..."}]
    }
  },
  "ranked_concerns": ["Breakouts_Bumps"],
  "summary": {
    "num_active_conditions": 1,
    "num_active_concerns": 1,
    "top_condition": "Acne",
    "primary_concern": "Breakouts_Bumps",
    "needs_escalation": false
  }
}
```

---

## Key Differences from V1

| Aspect | V1 (Old) | V2 (New) |
|--------|----------|----------|
| **Endpoints** | `/analyze` for cosmetic, `/deep_analysis` for conditions | Single `/analyze_v2` for both |
| **Conditions** | 34 conditions, shown separately | 10 conditions (top by data quality) |
| **Concerns** | Independently predicted | **Derived from conditions** (interpretable!) |
| **Interpretability** | "Breakouts_Bumps: 99%" (why?) | "Breakouts_Bumps: 69% **because Acne=69%**" |
| **User flow** | Two buttons, two analyses | One button, one unified result |

---

## How to Present Results (UX Guidelines)

### 1. Summary Section (Top)

Show a quick overview using `summary`:

```
✓ 1 skin pattern detected
✓ 1 cosmetic concern identified
  Primary: Breakouts and Bumps
```

If `needs_escalation` is true, show a gentle note:
> "Some patterns we detected may benefit from professional evaluation. Consider consulting a dermatologist."

### 2. Concerns Section (Main Focus)

**Only show ACTIVE concerns** (where `active: true`).

For each active concern, display:

```
┌─────────────────────────────────────────────────────┐
│ 🔵 Breakouts and Bumps                    69% match │
├─────────────────────────────────────────────────────┤
│ We detect patterns often seen with clogged pores,  │
│ breakouts, or follicle-related bumps.              │
│                                                     │
│ What this means:                                    │
│ This can happen when excess oil, dead skin, or     │
│ bacteria build up in pores...                       │
│                                                     │
│ Care focus:                                         │
│ Focus on balancing oil, gently exfoliating...      │
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ WHY THIS CONCERN:                               ││
│ │ • Acne detected: 69%                            ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ Suggested products:                                 │
│ • Clarifying Cleanser                              │
│ • Lightweight Non-comedogenic Moisturizer          │
│ • Targeted BHA Serum                               │
└─────────────────────────────────────────────────────┘
```

**Key interpretability feature**: The `contributing_conditions` object shows exactly WHY the concern was triggered. Display this prominently! This is what makes V2 special.

### 3. Conditions Section (Expandable/Secondary)

Show all 10 conditions, but make it secondary/collapsible since concerns are the main user-facing output.

```
▼ Detailed Skin Patterns Detected

  Acne                              ████████████░░░ 69% ✓ Active
  Folliculitis                      █░░░░░░░░░░░░░░  1%
  Eczema                            ░░░░░░░░░░░░░░░  0%
  Allergic Contact Dermatitis       ░░░░░░░░░░░░░░░  0%
  Insect Bite                       ░░░░░░░░░░░░░░░  0%
  Urticaria                         ░░░░░░░░░░░░░░░  0%
  Psoriasis                         ░░░░░░░░░░░░░░░  0%
  Irritant Contact Dermatitis       ░░░░░░░░░░░░░░░  0%
  Tinea                             ░░░░░░░░░░░░░░░  0%
  Herpes Zoster                     ░░░░░░░░░░░░░░░  0%
```

### 4. Products Section

For each active concern where `can_recommend_products: true`, show the `recommended_products` array.

Map product IDs to display names:

```typescript
const PRODUCT_DISPLAY_NAMES: Record<string, string> = {
  hydrating_cleanser: "Hydrating Cleanser",
  barrier_repair_moisturizer: "Barrier Repair Moisturizer",
  gentle_spf: "Gentle SPF Sunscreen",
  clarifying_cleanser: "Clarifying Cleanser",
  lightweight_noncomedogenic_moisturizer: "Lightweight Non-comedogenic Moisturizer",
  targeted_bha_serum: "Targeted BHA Serum",
  soothing_lotion: "Soothing Lotion",
  fragrance_free_moisturizer: "Fragrance-Free Moisturizer",
  rich_emollient_cream: "Rich Emollient Cream",
  gentle_scalp_or_body_wash: "Gentle Scalp/Body Wash",
  brightening_serum: "Brightening Serum",
  daily_spf: "Daily SPF",
  gentle_exfoliant: "Gentle Exfoliant",
  gentle_cleanser: "Gentle Cleanser",
  barrier_support_moisturizer: "Barrier Support Moisturizer",
};
```

If `can_recommend_products: false`, show:
> "For this concern, we recommend consulting a dermatologist rather than suggesting over-the-counter products."

### 5. Escalation Notes

If a concern has `escalation_note` (not null), display it prominently:

```
⚠️ Note: These patterns often benefit from professional evaluation.
```

### 6. Disclaimers

Always show the concern-level `disclaimer` at the bottom:

```
This is an AI-based cosmetic skin analysis, not a medical diagnosis. 
If you have pain, rapid changes, or health concerns, please see a dermatologist.
```

---

## TypeScript Interfaces for V2

```typescript
// Condition from the classifier
interface ConditionResult {
  prob: number;      // 0.0 to 1.0
  active: boolean;   // true if prob >= threshold
}

// Concern derived from conditions
interface ConcernResult {
  prob: number;
  active: boolean;
  threshold: number;
  contributing_conditions: Record<string, number>;  // KEY FIELD for interpretability
  mapped_conditions: string[];                      // Which conditions map to this concern
  can_recommend_products: boolean;
  severity_weight: number;
  escalation_note: string | null;
  title: string;
  description: string;
  what_it_means: string;
  care_focus: string;
  disclaimer: string;
  recommended_products: string[];
}

// Summary stats
interface AnalysisSummary {
  num_active_conditions: number;
  num_active_concerns: number;
  top_condition: string | null;
  primary_concern: string | null;
  needs_escalation: boolean;
}

// Full V2 response
interface AnalyzeV2Response {
  conditions: Record<string, ConditionResult>;
  concerns: Record<string, ConcernResult>;
  ranked_concerns: string[];
  summary: AnalysisSummary;
}
```

---

## Fetching Logic

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function analyzeV2(images: File[]): Promise<AnalyzeV2Response> {
  const formData = new FormData();
  
  if (images.length === 1) {
    // Single image → /analyze_v2
    formData.append("image", images[0]);
    const response = await fetch(`${API_BASE_URL}/analyze_v2`, {
      method: "POST",
      body: formData,
    });
    return response.json();
  } else {
    // Multiple images → /analyze_v2_session
    images.forEach((img) => formData.append("images", img));
    const response = await fetch(`${API_BASE_URL}/analyze_v2_session`, {
      method: "POST",
      body: formData,
    });
    return response.json();
  }
}
```

---

## The Six Concern Categories (Same as Before)

| Tag | Display Title | Mapped Conditions |
|-----|---------------|-------------------|
| `Dry_Sensitive` | Dry or Sensitive Skin Tendencies | Eczema, Allergic Contact Dermatitis, Irritant Contact Dermatitis |
| `Breakouts_Bumps` | Breakouts and Bumps | Acne, Folliculitis |
| `Itchy_Hives` | Itch, Hives, or Reactive Skin Patterns | Insect Bite, Urticaria, Allergic Contact Dermatitis |
| `Red_Scaly_Patches` | Red or Scaly Patches | Psoriasis, Eczema |
| `Pigment_Tone_Issues` | Pigment and Tone Considerations | *(derived from inflammatory conditions)* |
| `Possible_Infection` | Patterns Sometimes Associated with Infection | Tinea, Herpes Zoster, Folliculitis |

---

## Interpretability: The Key Improvement

**V1 Problem**: User sees "Breakouts_Bumps: 99%" but doesn't know WHY.

**V2 Solution**: User sees:
- "Breakouts_Bumps: 69%"
- "Why: Acne detected at 69%"

This is achieved through the `contributing_conditions` field. Always display this!

**How it works under the hood:**
1. Model predicts 10 condition probabilities
2. Each concern looks at its mapped conditions
3. Takes MAX probability among them
4. If above threshold → concern is active
5. Shows which condition(s) contributed

---

## Results Presentation: Sensible Interpretation

### Probability → Confidence Labels

Don't show raw percentages to users. Map to friendly labels:

```typescript
function getConfidenceLabel(prob: number): { label: string; color: string } {
  if (prob >= 0.7) return { label: "Strong match", color: "red" };
  if (prob >= 0.5) return { label: "Moderate match", color: "orange" };
  if (prob >= 0.3) return { label: "Possible match", color: "yellow" };
  return { label: "Unlikely", color: "gray" };
}
```

### Active vs Inactive

- **Active concerns**: Show full card with details
- **Inactive concerns**: Either hide completely OR show in a collapsed "Other patterns checked" section

### No Active Concerns

If `ranked_concerns` is empty:

```
✓ Great news! We didn't detect any strong patterns of concern.

Your skin appears healthy based on this analysis. Keep up your current 
skincare routine and remember to use sun protection daily.
```

---

## Component Structure Suggestion

```
src/
├── components/
│   ├── ImageUploader.tsx          # Existing, no change
│   ├── AnalysisButton.tsx         # NEW: "Run Skin Analysis" button
│   ├── V2Results/
│   │   ├── SummaryCard.tsx        # Quick overview
│   │   ├── ConcernCard.tsx        # Individual concern with WHY
│   │   ├── ConditionsPanel.tsx    # Collapsible conditions list
│   │   ├── ProductSuggestions.tsx # Products for active concerns
│   │   └── DisclaimerBox.tsx      # Legal disclaimer
│   ├── ToneSection.tsx            # FST + Monk (keep from old flow)
│   └── LoadingOverlay.tsx         # Existing, no change
```

---

## Summary of Changes

1. **Remove** old "Analyse my Skin" and "Deep Analysis" buttons from UI
2. **Add** single "Run Skin Analysis" button
3. **Call** `/analyze_v2` (1 image) or `/analyze_v2_session` (2-3 images)
4. **Display** unified results:
   - Summary at top
   - Active concerns with interpretability (show contributing conditions!)
   - Collapsible conditions panel
   - Product recommendations
   - Disclaimers
5. **Keep** FST/Monk tone section (can use old `/analyze` for this, or integrate if needed)

---

## Example User Flow

1. User uploads 1-3 photos
2. Clicks "Run Skin Analysis"
3. Loading spinner appears
4. Results show:
   ```
   ┌─────────────────────────────────────────────┐
   │ SUMMARY                                     │
   │ ✓ 1 pattern detected: Acne                 │
   │ ✓ 1 concern identified: Breakouts & Bumps  │
   └─────────────────────────────────────────────┘
   
   ┌─────────────────────────────────────────────┐
   │ 🔵 BREAKOUTS AND BUMPS              69%    │
   │                                             │
   │ We detect patterns often seen with...      │
   │                                             │
   │ WHY: Acne detected (69%)                   │  ← INTERPRETABILITY!
   │                                             │
   │ Care focus: Balance oil, gentle exfoliate  │
   │                                             │
   │ Suggested: Clarifying Cleanser, BHA Serum  │
   └─────────────────────────────────────────────┘
   
   ▼ All Patterns Checked (tap to expand)
   
   ┌─────────────────────────────────────────────┐
   │ ⚠️ DISCLAIMER                              │
   │ This is AI-based cosmetic analysis...      │
   └─────────────────────────────────────────────┘
   ```

---

## Final Notes

- The V2 endpoint is more accurate (trained on top-10 conditions with best data)
- The interpretability (showing WHY) is the key differentiator—make it prominent!
- The 6 concerns are the same as before, just derived differently
- Always show disclaimers
- If `needs_escalation` is true, emphasize seeing a professional

