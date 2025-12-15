FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (OpenGL libs required for OpenCV/DeepFace)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (185MB vs 900MB CUDA version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run inside the inner app package so `lib.*` imports work as expected
WORKDIR /app/app

# Default port for FastAPI/uvicorn
EXPOSE 8000

# Start the API using the same target that works in the venv
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]


