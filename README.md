### Know Your Skin – Vertex AI–backed skin analysis API

Private FastAPI backend for skin analysis, running Google Derm Foundation
embeddings from a Vertex AI endpoint plus custom SCIN-based classifiers for
cosmetic, concern, and condition-level outputs.

The service exposes a small HTTP API (via FastAPI) that:
- **/health**: simple health check
- **/analyze**: cosmetic + concern analysis from a single image
- **/analyze_session**: aggregates multiple images from the same person
- **/deep_analysis**: SCIN condition-level probabilities for a single image

All high-level logic lives under the `app/` package. The ASGI app is
defined in `app/api/server.py` and is re-exported from the top-level
`app.py` shim for convenience.


### Derm Foundation via Vertex AI + Private Service Connect

Instead of downloading the Derm Foundation SavedModel from Hugging Face,
this backend calls a **private Vertex AI endpoint** over HTTP from within
your GCE VM or Docker container.

Configuration is provided via environment variables:

- `DERM_VERTEX_PROJECT` – GCP project ID (e.g. `know-your-skin-478012`)
- `DERM_VERTEX_ENDPOINT` – Vertex AI Endpoint ID (numeric ID)
- `DERM_VERTEX_REGION` – Vertex AI region (default: `us-central1`)
- `DERM_VERTEX_PSC_IP` – Internal IP address of the PSC endpoint

`app/lib/derm_local.py` uses Application Default Credentials (ADC),
so on a GCE VM you can rely on the VM's service account; inside Docker
you can either:
- run the container on the VM with metadata-based auth, or
- mount a service account JSON and point `GOOGLE_APPLICATION_CREDENTIALS`
  at it.


### Running locally (no Docker)

1. Create and activate a virtualenv.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Export the required environment variables (`DERM_VERTEX_*`) so the
   backend can reach your Derm Foundation endpoint.

4. Start the API:

   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```


### Docker usage (high level)

This repo includes a `Dockerfile` and `.dockerignore` so you can build a
container image and run the backend on your VM:

```bash
docker build -t know-your-skin-backend .

docker run --rm -p 8000:8000 \
  -e DERM_VERTEX_PROJECT=know-your-skin-478012 \
  -e DERM_VERTEX_ENDPOINT=5562181934802534400 \
  -e DERM_VERTEX_REGION=us-central1 \
  -e DERM_VERTEX_PSC_IP=10.128.0.5 \
  know-your-skin-backend
```

When running on GCE, ensure the container has access to ADC (VM service
account or explicit credentials) so calls to Vertex AI succeed.

