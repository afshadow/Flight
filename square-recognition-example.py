#!/usr/bin/env python3
"""Recognize which square a query tile belongs to."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from square_recognition_lib import MANIFEST_PATH, ROOT, TILES_DIR, recognize_square


DEFAULT_QUERY = TILES_DIR / "14_W-18.png"
DEFAULT_OUTPUT = ROOT / "square-recognition-example.output.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recognize square labels from route tile images.")
    parser.add_argument(
        "--query",
        default=str(DEFAULT_QUERY),
        help="Path to the query PNG tile.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of best matches to include in the output.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to the JSON output file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query_path = Path(args.query).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")
    if not query_path.exists():
        raise FileNotFoundError(f"Query image not found: {query_path}")

    result = recognize_square(query_path=query_path, top_k=args.top_k)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(output_path)


if __name__ == "__main__":
    main()
