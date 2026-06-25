#!/usr/bin/env python3
"""Build square metadata from the manifest and recognize a square by tile image."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "kyiv-route-google-squares" / "route-squares.json"
DEFAULT_QUERY = ROOT / "kyiv-route-google-squares" / "14_W-18.png"
DEFAULT_OUTPUT = ROOT / "tile-grid-recognition-example.output.json"
HISTOGRAM_BINS = 12
THUMBNAIL_SIZE = 24


def bilinear_resample() -> int:
    if hasattr(Image, "Resampling"):
        return Image.Resampling.BILINEAR
    return Image.BILINEAR


@dataclass(frozen=True)
class Cell:
    label: str
    filename: str
    bounds: dict[str, float]
    center: dict[str, float]
    zoom: int
    row: int
    col: int

    @property
    def file_path(self) -> Path:
        return ROOT / "kyiv-route-google-squares" / self.filename

    @property
    def corners(self) -> list[dict[str, float]]:
        return [
            {"corner": "north_west", "lat": self.bounds["north"], "lng": self.bounds["west"]},
            {"corner": "north_east", "lat": self.bounds["north"], "lng": self.bounds["east"]},
            {"corner": "south_east", "lat": self.bounds["south"], "lng": self.bounds["east"]},
            {"corner": "south_west", "lat": self.bounds["south"], "lng": self.bounds["west"]},
        ]

    def to_preview(self) -> dict[str, object]:
        return {
            "label": self.label,
            "filename": self.filename,
            "grid_position": {"row": self.row, "col": self.col},
            "bounds": self.bounds,
            "center": self.center,
            "corners": self.corners,
        }


def normalize(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm == 0.0:
        return v
    return v / norm


def compute_descriptor(image_path: Path) -> np.ndarray:
    resample = bilinear_resample()
    with Image.open(image_path) as image:
        rgb = image.convert("RGB").resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), resample=resample)
        gray = image.convert("L").resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), resample=resample)

    rgb_arr = np.asarray(rgb, dtype=np.float32) / 255.0
    gray_arr = np.asarray(gray, dtype=np.float32) / 255.0

    appearance = gray_arr.reshape(-1)

    histograms: list[np.ndarray] = []
    for channel in range(3):
        hist, _ = np.histogram(
            rgb_arr[:, :, channel],
            bins=HISTOGRAM_BINS,
            range=(0.0, 1.0),
            density=True,
        )
        histograms.append(hist.astype(np.float32))

    grad_x = np.abs(np.diff(gray_arr, axis=1))
    grad_y = np.abs(np.diff(gray_arr, axis=0))
    texture = np.array(
        [
            float(gray_arr.std()),
            float(grad_x.mean()),
            float(grad_y.mean()),
        ],
        dtype=np.float32,
    )

    descriptor = np.concatenate([appearance, *histograms, texture]).astype(np.float32)
    return normalize(descriptor)


def load_cells(manifest_path: Path) -> list[Cell]:
    data = json.loads(manifest_path.read_text())
    center_lats = sorted({round(cell["center"]["lat"], 12) for cell in data["cells"]}, reverse=True)
    center_lngs = sorted({round(cell["center"]["lng"], 12) for cell in data["cells"]})
    row_lookup = {lat: idx for idx, lat in enumerate(center_lats)}
    col_lookup = {lng: idx for idx, lng in enumerate(center_lngs)}

    cells: list[Cell] = []
    for raw_cell in data["cells"]:
        lat_key = round(raw_cell["center"]["lat"], 12)
        lng_key = round(raw_cell["center"]["lng"], 12)
        cells.append(
            Cell(
                label=raw_cell["label"],
                filename=raw_cell["filename"],
                bounds=raw_cell["bounds"],
                center=raw_cell["center"],
                zoom=raw_cell["zoom"],
                row=row_lookup[lat_key],
                col=col_lookup[lng_key],
            )
        )
    return cells


def score_against_reference(
    query_path: Path,
    cells: Iterable[Cell],
    top_k: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    query_descriptor = compute_descriptor(query_path)
    all_scores: list[dict[str, object]] = []
    non_self_scores: list[dict[str, object]] = []

    for cell in cells:
        similarity = float(np.dot(query_descriptor, compute_descriptor(cell.file_path)))
        row = {
            "label": cell.label,
            "filename": cell.filename,
            "similarity": round(similarity, 6),
        }
        all_scores.append(row)
        if cell.file_path.resolve() != query_path.resolve():
            non_self_scores.append(row)

    all_scores.sort(key=lambda item: item["similarity"], reverse=True)
    non_self_scores.sort(key=lambda item: item["similarity"], reverse=True)
    return all_scores[:top_k], non_self_scores[:top_k]


def find_cell_for_query(query_path: Path, cells: Iterable[Cell]) -> Cell | None:
    resolved_query = query_path.resolve()
    for cell in cells:
        if cell.file_path.resolve() == resolved_query:
            return cell
    return None


def build_output(query_path: Path, preview_count: int, top_k: int) -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    cells = load_cells(MANIFEST_PATH)
    exact_matches, neighbor_matches = score_against_reference(query_path, cells, top_k=top_k)
    query_cell = find_cell_for_query(query_path, cells)

    preview_cells = cells[:preview_count]
    output: dict[str, object] = {
        "tool": "tile_grid_recognition_example",
        "version": 1,
        "dataset": {
            "manifest": str(MANIFEST_PATH.relative_to(ROOT)),
            "tile_count": len(cells),
            "image_size": manifest["imageSize"],
            "map_type": manifest["mapType"],
        },
        "square_building_example": {
            "explanation": (
                "Each square is built directly from a manifest cell: bounds define the four corners, "
                "while row and col are reconstructed from unique center latitude and longitude values."
            ),
            "cells": [cell.to_preview() for cell in preview_cells],
        },
        "recognition_example": {
            "query_file": str(query_path.relative_to(ROOT)),
            "recognized_square": exact_matches[0],
            "nearest_alternative_squares": neighbor_matches,
        },
    }

    if query_cell is not None:
        output["recognition_example"]["query_square"] = query_cell.to_preview()

    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Example of square construction and square recognition for route tiles."
    )
    parser.add_argument(
        "--query",
        default=str(DEFAULT_QUERY),
        help="Path to the PNG tile that should be recognized.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="How many best matches to keep in the output.",
    )
    parser.add_argument(
        "--preview-count",
        type=int,
        default=4,
        help="How many manifest cells to show in the square-building section.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Where to write the JSON example output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query_path = Path(args.query).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")
    if not query_path.exists():
        raise FileNotFoundError(f"Query tile not found: {query_path}")

    result = build_output(query_path=query_path, preview_count=args.preview_count, top_k=args.top_k)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(output_path)


if __name__ == "__main__":
    main()
