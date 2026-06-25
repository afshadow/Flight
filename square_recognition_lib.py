#!/usr/bin/env python3
"""Shared helpers for square recognition examples."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "kyiv-route-google-squares" / "route-squares.json"
TILES_DIR = ROOT / "kyiv-route-google-squares"
HISTOGRAM_BINS = 12
THUMBNAIL_SIZE = 24
DEFAULT_QUERY_MODE = "cropped_and_rescaled_variant"


def bilinear_resample() -> int:
    if hasattr(Image, "Resampling"):
        return Image.Resampling.BILINEAR
    return Image.BILINEAR


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector
    return vector / norm


@dataclass(frozen=True)
class Cell:
    label: str
    filename: str
    bounds: dict[str, float]
    center: dict[str, float]
    zoom: int

    @property
    def path(self) -> Path:
        return TILES_DIR / self.filename


def load_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text())


def load_cells() -> list[Cell]:
    data = load_manifest()
    return [
        Cell(
            label=cell["label"],
            filename=cell["filename"],
            bounds=cell["bounds"],
            center=cell["center"],
            zoom=cell["zoom"],
        )
        for cell in data["cells"]
    ]


def load_cell_lookup() -> dict[str, Cell]:
    return {cell.filename: cell for cell in load_cells()}


def compute_descriptor(image: Image.Image) -> np.ndarray:
    resample = bilinear_resample()
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

    return normalize(np.concatenate([appearance, *histograms, texture]).astype(np.float32))


def compute_descriptor_for_path(image_path: Path) -> np.ndarray:
    with Image.open(image_path) as image:
        return compute_descriptor(image)


def build_variant_image(image: Image.Image) -> Image.Image:
    resample = bilinear_resample()
    width, height = image.size
    dx = max(24, width // 20)
    dy = max(24, height // 20)
    return image.crop((dx, dy, width - dx, height - dy)).resize((width, height), resample=resample)


def build_query_descriptor(query_path: Path, query_mode: str = DEFAULT_QUERY_MODE) -> np.ndarray:
    if query_mode == "exact":
        return compute_descriptor_for_path(query_path)

    if query_mode == DEFAULT_QUERY_MODE:
        with Image.open(query_path) as image:
            return compute_descriptor(build_variant_image(image))

    raise ValueError(f"Unsupported query_mode: {query_mode}")


def precompute_reference_descriptors(cells: list[Cell]) -> dict[str, np.ndarray]:
    return {cell.filename: compute_descriptor_for_path(cell.path) for cell in cells}


def score_query_descriptor(
    query_descriptor: np.ndarray,
    cells: list[Cell],
    reference_descriptors: dict[str, np.ndarray] | None = None,
) -> list[dict[str, object]]:
    if reference_descriptors is None:
        reference_descriptors = precompute_reference_descriptors(cells)

    scored_matches: list[dict[str, object]] = []
    for cell in cells:
        similarity = float(np.dot(query_descriptor, reference_descriptors[cell.filename]))
        scored_matches.append(
            {
                "label": cell.label,
                "filename": cell.filename,
                "similarity": round(similarity, 6),
                "center": cell.center,
                "bounds": cell.bounds,
            }
        )

    scored_matches.sort(key=lambda item: item["similarity"], reverse=True)
    return scored_matches


def recognize_square(
    query_path: Path,
    top_k: int = 5,
    query_mode: str = DEFAULT_QUERY_MODE,
    cells: list[Cell] | None = None,
    reference_descriptors: dict[str, np.ndarray] | None = None,
) -> dict[str, object]:
    if cells is None:
        cells = load_cells()

    query_descriptor = build_query_descriptor(query_path, query_mode=query_mode)
    scored_matches = score_query_descriptor(
        query_descriptor=query_descriptor,
        cells=cells,
        reference_descriptors=reference_descriptors,
    )

    return {
        "query_file": str(query_path.relative_to(ROOT)),
        "query_mode": query_mode,
        "recognized_square": scored_matches[0],
        "top_matches": scored_matches[:top_k],
        "method": {
            "appearance_grid": THUMBNAIL_SIZE,
            "histogram_bins_per_channel": HISTOGRAM_BINS,
            "similarity": "cosine_similarity",
            "note": (
                "Recognition uses image content only. The default query mode applies a central crop "
                "followed by rescaling before matching."
            ),
        },
    }
