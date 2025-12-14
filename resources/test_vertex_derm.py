import argparse
from pathlib import Path

from app.lib.derm_local import embed_image_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Test Derm Foundation Vertex AI PSC endpoint via the backend helper "
            "and print embedding stats. Configuration is taken from DERM_VERTEX_* "
            "environment variables."
        )
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to a local image file (PNG/JPEG) to test.",
    )
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.is_file():
        raise FileNotFoundError(f"Image not found: {img_path}")

    emb = embed_image_path(str(img_path))

    print(f"Embedding length: {emb.shape[0]}")
    print("First 10 values:", emb[:10])


if __name__ == "__main__":
    main()


