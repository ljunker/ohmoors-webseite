#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg"}


def caption_from_filename(filename):
    stem = Path(filename).stem
    normalized = stem.replace("_", "-")
    # Remove leading date prefix like 2026-01-31-
    normalized = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", normalized)
    # Remove trailing sequence suffix like -01 or -12
    normalized = re.sub(r"-\d+$", "", normalized)
    caption = " ".join(part for part in normalized.split("-") if part and not part.isdigit())
    return caption.title() if caption else stem.replace("-", " ").strip().title()


def collect_images(images_dir):
    items = []
    for path in sorted(images_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VALID_EXTENSIONS:
            continue
        caption = caption_from_filename(path.name)
        items.append(
            {
                "src": f"gallery-pics/{path.name}",
                "alt": caption,
                "caption": caption,
            }
        )
    return items


def main():
    parser = argparse.ArgumentParser(description="Build gallery manifest JSON from image directory.")
    parser.add_argument("--images-dir", required=True, help="Directory containing gallery images")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    output_file = Path(args.output)

    if not images_dir.exists():
        raise SystemExit(f"Images directory not found: {images_dir}")

    items = collect_images(images_dir)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote {len(items)} gallery items to {output_file}")


if __name__ == "__main__":
    main()
