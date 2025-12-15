import base64
import io
import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Dict, Literal, Optional

import google.auth
from google.auth.transport.requests import AuthorizedSession
import numpy as np
from PIL import Image
from dotenv import load_dotenv


logger = logging.getLogger(__name__)

# Configure logging to show timing info
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Image format for embedding generation
# Options: 'png', 'jpeg', 'raw', 'auto'
# - 'png': Always re-encode as PNG (lossless, but doesn't restore JPEG artifacts)
# - 'jpeg': Always re-encode as JPEG (adds artifacts - NOT recommended)
# - 'raw': Send original file bytes (best for avoiding double-compression)
# - 'auto': Use 'raw' for JPEG/PNG inputs, 'png' for other formats
DEFAULT_FORMAT = os.getenv("DERM_IMAGE_FORMAT", "raw").lower()

ImageFormat = Literal["png", "jpeg", "raw", "auto"]


def _encode_png_bytes(img: Image.Image) -> bytes:
    """Encode image as PNG (lossless). Matches Google's original training pipeline."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def _encode_jpeg_bytes(img: Image.Image, quality: int = 95) -> bytes:
    """Encode image as JPEG. Faster but lossy - may affect embedding quality."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _image_file_to_base64(path: str, image_format: Optional[ImageFormat] = None) -> str:
    """
    Load an image file and return base64 string for the Derm Foundation model.
    
    Args:
        path: Path to image file
        image_format: 
            - 'raw': Send original file bytes (best for JPEG/PNG - avoids double-compression)
            - 'png': Re-encode as PNG (lossless, but doesn't fix existing JPEG artifacts)
            - 'jpeg': Re-encode as JPEG (NOT recommended - adds more artifacts)
            - 'auto': Use 'raw' for JPEG/PNG, 'png' for other formats (BMP, GIF, etc.)
            If None, uses DERM_IMAGE_FORMAT env var (default: 'raw')
    
    NOTE: For JPEG source images, 'raw' is recommended to avoid double-compression.
    The Derm Foundation model accepts both JPEG and PNG formats.
    """
    fmt = (image_format or DEFAULT_FORMAT).lower()
    img_path = Path(path)
    
    if not img_path.is_file():
        raise FileNotFoundError(f"Image not found: {img_path}")

    # Determine actual format for 'auto' mode
    suffix = img_path.suffix.lower()
    
    if fmt == "auto":
        # For common formats that the model accepts directly, use raw
        if suffix in {'.jpg', '.jpeg', '.png'}:
            fmt = "raw"
        else:
            # For other formats (BMP, GIF, WEBP, etc.), convert to PNG
            fmt = "png"
        logger.debug(f"[FORMAT] Auto-detected: using '{fmt}' for {suffix} file")

    if fmt == "raw":
        # Send original file bytes directly - no re-encoding
        # This is optimal for JPEG inputs (avoids double-compression)
        with open(img_path, "rb") as f:
            raw_bytes = f.read()
        logger.debug(f"[FORMAT] Using RAW bytes ({len(raw_bytes)} bytes, original: {suffix})")
        return base64.b64encode(raw_bytes).decode("utf-8")

    # For explicit png/jpeg, decode and re-encode
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        
        if fmt == "png":
            image_bytes = _encode_png_bytes(im)
            logger.debug(f"[FORMAT] Re-encoded as PNG ({len(image_bytes)} bytes)")
        else:  # jpeg
            image_bytes = _encode_jpeg_bytes(im, quality=95)
            logger.debug(f"[FORMAT] Re-encoded as JPEG ({len(image_bytes)} bytes)")

    return base64.b64encode(image_bytes).decode("utf-8")


def _load_vertex_config() -> Dict[str, str]:
    """
    Read Vertex AI / PSC configuration from environment variables.

    Required:
      - DERM_VERTEX_PROJECT:    GCP project ID
      - DERM_VERTEX_ENDPOINT:   Vertex AI endpoint ID
      - DERM_VERTEX_PSC_IP:     Internal IP of the PSC endpoint

    Optional:
      - DERM_VERTEX_REGION:     Vertex AI region (default: \"us-central1\")
    """
    # Load .env (if present) so local scripts can pick up DERM_VERTEX_* values
    # without having to export them in the shell. In Docker/VM, actual env
    # variables will still override anything in .env.
    load_dotenv()

    project = os.getenv("DERM_VERTEX_PROJECT")
    endpoint = os.getenv("DERM_VERTEX_ENDPOINT")
    region = os.getenv("DERM_VERTEX_REGION", "us-central1")
    psc_ip = os.getenv("DERM_VERTEX_PSC_IP")

    missing = [name for name, val in [
        ("DERM_VERTEX_PROJECT", project),
        ("DERM_VERTEX_ENDPOINT", endpoint),
        ("DERM_VERTEX_PSC_IP", psc_ip),
    ] if not val]

    if missing:
        raise RuntimeError(
            "Missing required environment variables for Derm Foundation Vertex endpoint: "
            + ", ".join(missing)
        )

    return {
        "project": project,
        "endpoint": endpoint,
        "region": region,
        "psc_ip": psc_ip,
    }


@lru_cache(maxsize=1)
def _get_authorized_session() -> AuthorizedSession:
    """
    Return an AuthorizedSession using Application Default Credentials.

    On GCE this will use the VM's service account; inside Docker you can either
    rely on the VM metadata server or provide explicit credentials via
    GOOGLE_APPLICATION_CREDENTIALS.
    """
    creds, _ = google.auth.default()
    return AuthorizedSession(creds)


def _predict_embedding_from_b64(image_b64: str) -> np.ndarray:
    """
    Call the Derm Foundation Vertex AI endpoint over HTTP and return the
    embedding as a 1D float32 numpy array.
    """
    cfg = _load_vertex_config()
    session = _get_authorized_session()

    url = (
        f"http://{cfg['psc_ip']}/v1/projects/{cfg['project']}"
        f"/locations/{cfg['region']}/endpoints/{cfg['endpoint']}:predict"
    )

    payload = {"instances": [{"input_bytes": image_b64}]}

    start_time = time.time()
    try:
        resp = session.post(url, json=payload, timeout=60)
    except Exception as exc:  # pragma: no cover - thin network wrapper
        logger.exception("Error calling Derm Foundation Vertex endpoint")
        raise RuntimeError(f"Error calling Derm Foundation endpoint: {exc}") from exc
    
    vertex_time = time.time() - start_time
    logger.info(f"[TIMING] Vertex AI HTTP request took {vertex_time:.2f}s")

    if resp.status_code != 200:
        # Try to surface helpful error text if present.
        try:
            detail = resp.text
        except Exception:  # pragma: no cover - defensive
            detail = "<no response body>"
        raise RuntimeError(
            f"Derm Foundation endpoint returned HTTP {resp.status_code}: {detail}"
        )

    data = resp.json()
    preds = data.get("predictions", [])
    if not preds:
        raise RuntimeError("Derm Foundation endpoint returned no predictions.")

    first = preds[0]
    if isinstance(first, dict) and "embedding" in first:
        emb = np.asarray(first["embedding"], dtype=np.float32).flatten()
    else:
        emb = np.asarray(first, dtype=np.float32).flatten()

    return emb


def embed_image_path(path: str, image_format: Optional[ImageFormat] = None) -> np.ndarray:
    """
    Return 1D embedding vector (float32) for an image file path.

    This calls the private Derm Foundation Vertex AI endpoint over HTTP
    through a Private Service Connect (PSC) internal IP, using ADC-based auth.
    
    Args:
        path: Path to the image file
        image_format: 
            - 'raw': Send original bytes (default, best for JPEG/PNG inputs)
            - 'png': Re-encode as PNG  
            - 'jpeg': Re-encode as JPEG (not recommended)
            - 'auto': Smart selection based on file type
            If None, uses DERM_IMAGE_FORMAT env var (default: 'raw')
    
    Returns:
        6144-dimensional embedding vector as float32 numpy array
        
    NOTE: For JPEG source images, 'raw' avoids double-compression artifacts.
    The Derm Foundation model accepts both JPEG and PNG formats natively.
    """
    start_time = time.time()
    
    # Time image preprocessing
    preprocess_start = time.time()
    image_b64 = _image_file_to_base64(path, image_format=image_format)
    preprocess_time = time.time() - preprocess_start
    logger.info(f"[TIMING] Image preprocessing (load+base64) took {preprocess_time:.2f}s")
    
    # Time embedding call
    embedding = _predict_embedding_from_b64(image_b64)
    
    total_time = time.time() - start_time
    logger.info(f"[TIMING] Total embed_image_path took {total_time:.2f}s")
    
    return embedding


