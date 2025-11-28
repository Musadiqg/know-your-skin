from tempfile import NamedTemporaryFile
from typing import Any, Dict, List
import logging
import os
import shutil

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from lib.full_analysis import analyze_full_image, analyze_full_session
from lib.condition_inference import analyze_conditions_image


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
