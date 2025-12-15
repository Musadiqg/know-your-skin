# Frontend Update Prompt: Skin Age Analysis Endpoint

## Overview

A new endpoint `/get_skin_age` has been added to the backend. This endpoint combines:
1. **Aging Signs Classifier** - Detects dark spots, puffy eyes, and wrinkles using Derm Foundation embeddings
2. **DeepFace Age Estimation** - Estimates biological/apparent age from the face

This is a **standalone endpoint** that can be called independently or alongside existing analysis endpoints.

---

## Endpoint Details

### `POST /get_skin_age`

**Request:**
```
Content-Type: multipart/form-data
Field: image (file, JPG/PNG)
```

**Example curl:**
```bash
curl -X POST "http://34.132.152.136:8000/get_skin_age" \
  -F "image=@face_photo.jpg"
```

**Response:**
```json
{
  "estimated_age": 32,
  "primary_concern": "puffy_eyes",
  "confidence": 0.65,
  "aging_signs": {
    "dark_spots": 0.12,
    "puffy_eyes": 0.65,
    "wrinkles": 0.23
  },
  "title": "Puffy Eyes / Under-Eye Bags",
  "description": "Puffiness around the eyes is often caused by fluid retention, genetics, or lifestyle factors.",
  "causes": [
    "Lack of sleep or poor sleep quality",
    "High sodium diet causing fluid retention",
    "Allergies or sinus issues",
    "Genetics and natural aging",
    "Screen fatigue and eye strain"
  ],
  "recommendations": [
    "Get 7-9 hours of quality sleep",
    "Reduce sodium intake and stay hydrated",
    "Use a cold compress in the morning",
    "Look for eye creams with caffeine or peptides",
    "Sleep with head slightly elevated",
    "Consider antihistamines if allergies are a factor"
  ],
  "assessment": "Based on your image, your skin appears to be around 32 years old with puffiness around the eyes as your primary aging concern.",
  "age_estimation_success": true
}
```

---

## Response Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `estimated_age` | `number \| null` | Estimated biological age from DeepFace. May be `null` if face detection fails. |
| `primary_concern` | `string` | The dominant aging sign detected: `"dark_spots"`, `"puffy_eyes"`, or `"wrinkles"` |
| `confidence` | `number` | Confidence score (0-1) for the primary concern |
| `aging_signs` | `object` | Probabilities for all 3 aging categories (sum to ~1.0) |
| `title` | `string` | Human-friendly title for the primary concern |
| `description` | `string` | Educational description of the aging concern |
| `causes` | `string[]` | List of common causes for this aging sign |
| `recommendations` | `string[]` | Actionable skincare/lifestyle recommendations |
| `assessment` | `string` | Combined narrative summarizing age + concern |
| `age_estimation_success` | `boolean` | Whether DeepFace successfully estimated age |
| `age_estimation_error` | `string \| undefined` | Error message if age estimation failed (only present on failure) |

---

## The Three Aging Categories

| Category | Display Name | Description |
|----------|--------------|-------------|
| `dark_spots` | Dark Spots / Hyperpigmentation | Age spots, sun spots, post-inflammatory marks |
| `puffy_eyes` | Puffy Eyes / Under-Eye Bags | Fluid retention, genetics, fatigue |
| `wrinkles` | Wrinkles / Fine Lines | Collagen loss, photoaging, expressions |

---

## TypeScript Interface

```typescript
interface AgingSigns {
  dark_spots: number;
  puffy_eyes: number;
  wrinkles: number;
}

interface SkinAgeResponse {
  estimated_age: number | null;
  primary_concern: "dark_spots" | "puffy_eyes" | "wrinkles";
  confidence: number;
  aging_signs: AgingSigns;
  title: string;
  description: string;
  causes: string[];
  recommendations: string[];
  assessment: string;
  age_estimation_success: boolean;
  age_estimation_error?: string;
}
```

---

## Fetching Logic Example

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getSkinAge(image: File): Promise<SkinAgeResponse> {
  const formData = new FormData();
  formData.append("image", image);
  
  const response = await fetch(`${API_BASE_URL}/get_skin_age`, {
    method: "POST",
    body: formData,
  });
  
  if (!response.ok) {
    throw new Error(`Skin age analysis failed: ${response.statusText}`);
  }
  
  return response.json();
}
```

---

## Handling Age Estimation Failures

DeepFace age estimation may fail if:
- No face is detected in the image
- Image is too blurry or low quality
- Face is partially obscured or at extreme angles

When `age_estimation_success: false`:
- `estimated_age` will be `null`
- `age_estimation_error` will contain the error message
- All other fields (aging signs, recommendations) will still be populated

**Example handling:**
```typescript
if (!response.age_estimation_success) {
  // Show aging signs without age
  console.log("Age couldn't be determined:", response.age_estimation_error);
  console.log("Primary concern:", response.primary_concern);
} else {
  console.log("Estimated age:", response.estimated_age);
}
```

---

## Relationship to Other Endpoints

| Endpoint | Purpose | Can Run Together? |
|----------|---------|-------------------|
| `/get_skin_type` | Oily/Dry/Normal/Redness classification | ✅ Yes |
| `/get_skin_profile` | FST + Monk Tone + Texture | ✅ Yes |
| `/analyze_v2` or `/analyze_v2_session` | Conditions + Concerns + Routine | ✅ Yes |
| `/get_skin_age` | **Aging signs + Age estimation** | ✅ Yes |

These endpoints are independent and can be called in parallel for a comprehensive analysis.

---

## Model Information

- **Aging Classifier**: Logistic Regression trained on Derm Foundation embeddings
  - 3 classes: dark spots, puffy eyes, wrinkles
  - ~900 training images
  - Test accuracy: 89%
  
- **Age Estimation**: DeepFace library
  - Uses pre-trained deep learning model
  - Returns integer age estimate
  - Works best with clear frontal face images

---

## Notes

1. **First call may be slow**: DeepFace downloads models (~200MB) on first use
2. **Face detection**: Works best with clear, well-lit face photos
3. **Single image only**: This endpoint accepts one image (unlike `analyze_v2_session` which handles multiple)
4. **Complementary data**: Use alongside `/get_skin_profile` for complete skin analysis (tone + texture + aging)

---

## Summary

**New Endpoint:** `POST /get_skin_age`

**What it does:**
- Classifies aging concerns (dark spots, puffy eyes, wrinkles)
- Estimates apparent/biological age
- Provides personalized recommendations

**Key fields to display:**
- `estimated_age` - The age number
- `aging_signs` - Probabilities for each category
- `primary_concern` + `title` - What to focus on
- `recommendations` - Actionable tips
- `assessment` - Summary narrative

**Error handling:**
- Check `age_estimation_success` before showing age
- Aging signs analysis works even if face detection fails

