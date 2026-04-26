# Contributing to Know Your Skin

Thanks for your interest. Contributions are welcome — whether that's a bug fix, a new classifier head, an improved brand integration, or documentation.

## Getting started

1. Fork the repo and clone your fork.
2. Copy `env.example` to `.env` and configure your Vertex AI credentials.
3. Follow the training steps in the README to generate classifier artifacts.
4. Run the API locally with `docker-compose up --build`.

## What to work on

Good first contributions:

- **Brand integrations** — example `brand_products.py` configs for different product categories or brand sizes.
- **New API endpoints** — e.g. a lightweight "skin type only" endpoint for brands that only need that.
- **Classifier improvements** — better training scripts, additional concern tags, improved aggregation logic.
- **Documentation** — clearer setup instructions, architecture diagrams, deployment guides.
- **Tests** — the project currently has no test suite. Any coverage is welcome.

## Pull request guidelines

- Keep PRs focused — one concern per PR.
- Include a short description of *why* the change is needed, not just what it does.
- If you add a new classifier or training script, document the expected input/output format and any dataset requirements.
- Do not commit `.env` files, API keys, `.joblib` model artifacts, or personal data.

## Sensitive data

This project analyses skin photos. Please:

- Do not commit any real skin images to the repository.
- Do not include personally identifiable information in issues or PRs.
- Use synthetic or properly licensed test images only.

## Questions

Open an issue and tag it `question`. Response time is best-effort.
