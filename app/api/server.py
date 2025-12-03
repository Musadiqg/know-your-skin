from tempfile import NamedTemporaryFile
from typing import Any, Dict, List
import logging
import os
import shutil

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from lib.full_analysis import analyze_full_image, analyze_full_session
from lib.condition_inference import analyze_conditions_image
from lib.cascaded_inference import analyze_cascaded, analyze_cascaded_session
from lib.cosmetic_inference import analyze_cosmetic_image
from lib.skintype_inference import analyze_skintype_image


logger = logging.getLogger(__name__)


app = FastAPI(
    title="Hudson Skin Analysis API",
    description=(
        "Local API for running Derm Foundation + SCIN-based cosmetic attributes "
        "and concern analysis, returning a combined narrative report with Hudson "
        "product recommendations."
    ),
    version="0.2.0",
)

# For prototype purposes, allow all origins. You can tighten this later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Analyze a single skin image and return a combined JSON structure:

    {
      "cosmetic": { ... },  # tone / type education
      "concerns": { ... }   # concern sections + routine + disclaimer
    }

    Expected request (multipart/form-data):
        - field name: 'image'
        - value: image file (JPEG/PNG)
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    # Basic content-type check (relaxed for prototype)
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    suffix = os.path.splitext(image.filename)[1] or ".jpg"

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(image.file, tmp)

    try:
        # cosmetic + concerns in one call so the mobile app can show both layers
        result = analyze_full_image(tmp_path)
    except Exception as exc:  # pragma: no cover - thin wrapper
        logger.exception("Error during analyze_full_image")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return result


@app.post("/analyze_session")
async def analyze_session(images: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """
    Analyze multiple images from the same person and return a single
    session-level combined JSON structure (cosmetic + concerns).

    Expected request (multipart/form-data):
        - field name: 'images'
        - value: one or more image files (JPEG/PNG)

    This uses the same report shape as /analyze, but aggregates
    probabilities across all provided images before building the report.
    """
    if not images:
        raise HTTPException(status_code=400, detail="At least one image must be provided.")

    tmp_paths: List[str] = []

    try:
        for image in images:
            if not image.filename:
                raise HTTPException(status_code=400, detail="Each uploaded file must have a filename.")

            if image.content_type and not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="All uploaded files must be images.")

            suffix = os.path.splitext(image.filename)[1] or ".jpg"
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp_path = tmp.name
                shutil.copyfileobj(image.file, tmp)
            tmp_paths.append(tmp_path)

        result = analyze_full_session(tmp_paths)
    except HTTPException:
        # Re-raise FastAPI HTTP errors unchanged
        raise
    except Exception as exc:  # pragma: no cover - thin wrapper
        logger.exception("Error during analyze_full_session")
        raise HTTPException(status_code=500, detail=f"Session analysis failed: {exc}") from exc
    finally:
        for path in tmp_paths:
            try:
                os.remove(path)
            except OSError:
                pass

    return result


@app.post("/deep_analysis")
async def deep_analysis(
    image: UploadFile = File(...),
    threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Run the SCIN condition-level classifier on a single image and return
    per-condition probabilities.

    This endpoint is intended as an optional "deep dive" after the main
    concern classifier. It re-embeds the uploaded image with Derm Foundation
    and returns:

        {
          "conditions": {
            "<condition_name>": {"prob": float, "active": bool},
            ...
          }
        }

    Expected request (multipart/form-data):
        - field name: 'image'
        - value: image file (JPEG/PNG)
        - optional field: 'threshold' (float), probability cutoff for 'active'
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    suffix = os.path.splitext(image.filename)[1] or ".jpg"

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(image.file, tmp)

    try:
        result = analyze_conditions_image(tmp_path, threshold=threshold)
    except Exception as exc:  # pragma: no cover - thin wrapper
        logger.exception("Error during deep condition analysis")
        raise HTTPException(status_code=500, detail=f"Deep analysis failed: {exc}") from exc
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return result


@app.post("/analyze_v2")
async def analyze_v2(
    image: UploadFile = File(...),
    condition_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Cascaded analysis with interpretable concerns (V2).

    This endpoint uses the improved top-10 condition classifier and derives
    concerns via rule-based aggregation, providing full interpretability.

    Returns:
        {
          "conditions": {
            "<condition_name>": {"prob": float, "active": bool},
            ...
          },
          "concerns": {
            "<concern_tag>": {
              "prob": float,
              "active": bool,
              "contributing_conditions": {"Eczema": 0.75, ...},
              "title": "...",
              "description": "...",
              "can_recommend_products": bool,
              ...
            },
            ...
          },
          "ranked_concerns": ["Dry_Sensitive", ...],
          "summary": {
            "num_active_conditions": int,
            "num_active_concerns": int,
            "top_condition": str,
            "primary_concern": str,
            "needs_escalation": bool
          }
        }

    Expected request (multipart/form-data):
        - field name: 'image'
        - value: image file (JPEG/PNG)
        - optional: 'condition_threshold' (float, default 0.5)
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    suffix = os.path.splitext(image.filename)[1] or ".jpg"

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(image.file, tmp)

    try:
        result = analyze_cascaded(tmp_path, condition_threshold=condition_threshold)
    except FileNotFoundError as exc:
        logger.exception("Top-10 model not found")
        raise HTTPException(
            status_code=503,
            detail=f"Model not available: {exc}. Run training script first."
        ) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Error during cascaded analysis")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return result


@app.post("/analyze_v2_session")
async def analyze_v2_session(
    images: List[UploadFile] = File(...),
    condition_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Cascaded analysis for multiple images with interpretable concerns (V2).

    Analyzes multiple images from the same person and aggregates condition
    probabilities (using MAX across images) before deriving concerns.

    Returns same structure as /analyze_v2 but with aggregated results and
    per-image probability breakdowns.

    Expected request (multipart/form-data):
        - field name: 'images'
        - value: one or more image files (JPEG/PNG)
        - optional: 'condition_threshold' (float, default 0.5)
    """
    if not images:
        raise HTTPException(status_code=400, detail="At least one image must be provided.")

    tmp_paths: List[str] = []

    try:
        for img in images:
            if not img.filename:
                raise HTTPException(status_code=400, detail="Each uploaded file must have a filename.")

            if img.content_type and not img.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="All uploaded files must be images.")

            suffix = os.path.splitext(img.filename)[1] or ".jpg"
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp_path = tmp.name
                shutil.copyfileobj(img.file, tmp)
            tmp_paths.append(tmp_path)

        result = analyze_cascaded_session(tmp_paths, condition_threshold=condition_threshold)
    except FileNotFoundError as exc:
        logger.exception("Top-10 model not found")
        raise HTTPException(
            status_code=503,
            detail=f"Model not available: {exc}. Run training script first."
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        logger.exception("Error during cascaded session analysis")
        raise HTTPException(status_code=500, detail=f"Session analysis failed: {exc}") from exc
    finally:
        for path in tmp_paths:
            try:
                os.remove(path)
            except OSError:
                pass

    return result


@app.post("/get_skin_profile")
async def get_skin_profile(image: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Get skin profile information: Fitzpatrick Type, Monk Tone, and Texture.
    
    This is a lightweight endpoint for educational skin information,
    separate from the condition/concern analysis.
    
    Returns:
        {
          "fitzpatrick": {
            "label": "FST2",
            "probs": {"FST1": 0.02, "FST2": 0.94, ...},
            "title": "Type II - Fair skin, usually burns",
            "description": "...",
            "sun_advice": "..."
          },
          "monk_tone": {
            "label": 3,
            "probs": {"1": 0.01, "2": 0.05, "3": 0.67, ...},
            "group": "lighter",
            "education": "..."
          },
          "texture": {
            "Texture_Bumpy": {"prob": 0.72, "active": true},
            "Texture_Smooth": {"prob": 0.15, "active": false},
            "Texture_Rough_Flakey": {"prob": 0.45, "active": false},
            "Texture_Fluid_Filled": {"prob": 0.08, "active": false},
            "primary": "Texture_Bumpy",
            "education": "..."
          }
        }
    
    Expected request (multipart/form-data):
        - field name: 'image'
        - value: image file (JPEG/PNG)
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")
    
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    
    suffix = os.path.splitext(image.filename)[1] or ".jpg"
    
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(image.file, tmp)
    
    try:
        # Get raw cosmetic predictions
        raw_result = analyze_cosmetic_image(tmp_path)
        
        # Enrich with educational content
        result = _enrich_skin_profile(raw_result)
        
    except FileNotFoundError as exc:
        logger.exception("Cosmetic models not found")
        raise HTTPException(
            status_code=503,
            detail=f"Model not available: {exc}."
        ) from exc
    except Exception as exc:
        logger.exception("Error during skin profile analysis")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    
    return result


def _enrich_skin_profile(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Add educational content to raw cosmetic predictions."""
    result = {}
    
    # Fitzpatrick enrichment
    if "fitzpatrick" in raw:
        fst = raw["fitzpatrick"]
        label = fst.get("label", "")
        
        FST_INFO = {
            "FST1": {
                "title": "Type I - Very Fair",
                "description": "Very fair skin that always burns and never tans.",
                "sun_advice": "Always use SPF 30+ and seek shade. Your skin is highly sensitive to UV damage."
            },
            "FST2": {
                "title": "Type II - Fair",
                "description": "Fair skin that usually burns and tans minimally.",
                "sun_advice": "Use SPF 30+ daily. You're prone to sunburn, so reapply frequently outdoors."
            },
            "FST3": {
                "title": "Type III - Medium",
                "description": "Medium skin that sometimes burns and tans uniformly.",
                "sun_advice": "SPF 15-30 recommended. You can tan but still need protection from UV damage."
            },
            "FST4": {
                "title": "Type IV - Olive",
                "description": "Olive skin that rarely burns and tans easily.",
                "sun_advice": "SPF 15+ recommended. While you tan easily, UV protection prevents premature aging."
            },
            "FST5": {
                "title": "Type V - Brown",
                "description": "Brown skin that very rarely burns and tans very easily.",
                "sun_advice": "SPF 15+ still beneficial. Focus on even tone and hyperpigmentation prevention."
            },
            "FST6": {
                "title": "Type VI - Dark Brown/Black",
                "description": "Dark brown or black skin that never burns.",
                "sun_advice": "SPF still helps prevent uneven tone. Focus on moisturization and barrier health."
            },
        }
        
        info = FST_INFO.get(label, {"title": label, "description": "", "sun_advice": ""})
        result["fitzpatrick"] = {
            **fst,
            "title": info["title"],
            "description": info["description"],
            "sun_advice": info["sun_advice"],
        }
    
    # Monk tone enrichment
    if "monk_tone" in raw:
        monk = raw["monk_tone"]
        label = monk.get("label", 5)
        
        if label <= 3:
            group = "lighter"
            education = "On lighter skin tones, redness, sunburn, and vascular changes tend to show up more visibly. Focus on sun protection and anti-redness care."
        elif label <= 6:
            group = "medium"
            education = "Medium skin tones may show both redness and hyperpigmentation. Balance sun protection with products that promote even tone."
        else:
            group = "deeper"
            education = "On deeper skin tones, hyperpigmentation and uneven tone are common concerns after inflammation. Gentle exfoliation and brightening ingredients can help."
        
        result["monk_tone"] = {
            **monk,
            "group": group,
            "education": education,
        }
    
    # Texture enrichment
    if "texture" in raw:
        texture = raw["texture"]
        
        # Find primary (highest prob) texture
        primary = None
        max_prob = 0
        for tag, info in texture.items():
            if isinstance(info, dict) and info.get("prob", 0) > max_prob:
                max_prob = info["prob"]
                primary = tag
        
        TEXTURE_EDUCATION = {
            "Texture_Bumpy": "Raised or bumpy texture often indicates inflammation, clogged pores, or irritation. Gentle exfoliation and non-comedogenic products may help.",
            "Texture_Smooth": "Smooth, flat texture suggests the skin surface is even. Maintain with gentle cleansing and regular moisturization.",
            "Texture_Rough_Flakey": "Rough or flaky texture often indicates dryness or barrier disruption. Focus on hydrating and barrier-repair products.",
            "Texture_Fluid_Filled": "Fluid-filled areas may indicate blisters or vesicles. Avoid popping and keep the area clean. Consider consulting a dermatologist if persistent.",
        }
        
        education = TEXTURE_EDUCATION.get(primary, "")
        
        result["texture"] = {
            **texture,
            "primary": primary,
            "education": education,
        }
    
    return result


@app.post("/get_skin_type")
async def get_skin_type(image: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Classify skin type into one of 4 categories with probabilities for all classes.
    
    Categories:
    - dry: Skin lacking moisture, feels tight
    - normal: Balanced skin, neither too oily nor dry
    - oily: Excess sebum production, prone to shine
    - redness: Visible redness, sensitivity, possible irritation
    
    Returns:
        {
            "predicted": "oily",
            "confidence": 0.58,
            "probabilities": {
                "dry": 0.12,
                "normal": 0.25,
                "oily": 0.58,
                "redness": 0.05
            },
            "title": "Oily Skin",
            "description": "Your skin produces excess sebum...",
            "characteristics": ["Shiny appearance", ...],
            "care_tips": ["Use gentle cleanser", ...]
        }
    
    Expected request (multipart/form-data):
        - field name: 'image'
        - value: image file (JPEG/PNG)
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")
    
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    
    suffix = os.path.splitext(image.filename)[1] or ".jpg"
    
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(image.file, tmp)
    
    try:
        result = analyze_skintype_image(tmp_path)
    except FileNotFoundError as exc:
        logger.exception("Skin type model not found")
        raise HTTPException(
            status_code=503,
            detail=f"Skin type model not available: {exc}. Run training script first."
        ) from exc
    except Exception as exc:
        logger.exception("Error during skin type analysis")
        raise HTTPException(status_code=500, detail=f"Skin type analysis failed: {exc}") from exc
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    
    return result
