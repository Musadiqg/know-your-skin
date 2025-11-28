import os
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"

# Load local .env for development (Docker/VM typically pass env directly).
load_dotenv(ROOT / ".env")

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Match original container layout so relative "models" paths resolve correctly.
os.chdir(APP_DIR)

# Expose the FastAPI app defined in api.server so an ASGI server (uvicorn, etc.)
# can import `app:app` as the main application.
from api.server import app  # noqa: E402,F401