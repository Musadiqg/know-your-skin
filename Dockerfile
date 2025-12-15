FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (minimal + wget for model downloads)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (185MB vs 900MB CUDA version)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download age estimation models (fail gracefully if unavailable)
RUN mkdir -p /app/app/models/age && \
    cd /app/app/models/age && \
    wget -q --no-check-certificate "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/master/age_net_definitions/deploy.prototxt" -O age_deploy.prototxt || true && \
    wget -q --no-check-certificate "https://raw.githubusercontent.com/GilLevi/AgeGenderDeepLearning/master/models/age_net.caffemodel" -O age_net.caffemodel || true && \
    wget -q --no-check-certificate "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/dnn/face_detector/deploy.prototxt" -O face_deploy.prototxt || true && \
    wget -q --no-check-certificate "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel" -O face_net.caffemodel || true && \
    ls -la

# Run inside the inner app package so `lib.*` imports work as expected
WORKDIR /app/app

# Default port for FastAPI/uvicorn
EXPOSE 8000

# Start the API using the same target that works in the venv
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]


