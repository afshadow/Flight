#!/usr/bin/env python3
"""Run square recognition across all tiles and generate summary artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from square_recognition_lib import (
    ROOT,
    build_variant_image,
    load_cells,
    precompute_reference_descriptors,
    recognize_square,
)


OUTPUT_JSON = ROOT / "square-recognition-batch.output.json"
OUTPUT_PNG = ROOT / "square-recognition-batch-report.png"
TOP_K = 3
THUMB_SIZE = (120, 120)
PADDING = 16
HEADER_HEIGHT = 72
ROW_HEIGHT = 168
COL_WIDTH = 156
BG_COLOR = (247, 246, 240)
CARD_COLOR = (255, 255, 252)
CARD_OUTLINE = (206, 202, 191)
TEXT_COLOR = (38, 41, 46)
MUTED_COLOR = (100, 105, 112)
OK_COLOR = (71, 122, 68)
ERR_COLOR = (156, 67, 57)


def load_font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def render_thumb(image: Image.Image) -> Image.Image:
    return ImageOps.fit(image.convert("RGB"), THUMB_SIZE, method=Image.Resampling.BILINEAR)


def build_batch_output() -> dict[str, object]:
    cells = load_cells()
    reference_descriptors = precompute_reference_descriptors(cells)
    results: list[dict[str, object]] = []

    top1_hits = 0
    top3_hits = 0

    for cell in cells:
        result = recognize_square(
            query_path=cell.path,
            top_k=TOP_K,
            cells=cells,
            reference_descriptors=reference_descriptors,
        )
        top_matches = result["top_matches"]
        predicted_label = result["recognized_square"]["label"]
        top_labels = [match["label"] for match in top_matches]
        top1_ok = predicted_label == cell.label
        top3_ok = cell.label in top_labels

        if top1_ok:
            top1_hits += 1
        if top3_ok:
            top3_hits += 1

        results.append(
            {
                "query_label": cell.label,
                "query_filename": cell.filename,
                "predicted_label": predicted_label,
                "top1_ok": top1_ok,
                "top3_ok": top3_ok,
                "top_matches": top_matches,
            }
        )

    tile_count = len(cells)
    summary = {
        "tool": "square_recognition_batch",
        "version": 1,
        "query_mode": "cropped_and_rescaled_variant",
        "tile_count": tile_count,
        "top1_accuracy": round(top1_hits / tile_count, 6),
        "top3_accuracy": round(top3_hits / tile_count, 6),
        "results": results,
    }
    return summary


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: tuple[int, int, int]) -> None:
    draw.text(xy, text, fill=fill, font=load_font())


def render_visual_report(batch_output: dict[str, object], output_path: Path) -> None:
    results = batch_output["results"]
    cells = {cell.filename: cell for cell in load_cells()}

    width = PADDING * 2 + COL_WIDTH * 4
    height = HEADER_HEIGHT + PADDING + len(results) * ROW_HEIGHT + PADDING
    canvas = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    draw_text(draw, (PADDING, 12), "Square Recognition Batch Report", TEXT_COLOR)
    draw_text(
        draw,
        (PADDING, 30),
        (
            f"tiles={batch_output['tile_count']}  "
            f"top1={batch_output['top1_accuracy']:.3f}  "
            f"top3={batch_output['top3_accuracy']:.3f}"
        ),
        MUTED_COLOR,
    )
    draw_text(draw, (PADDING, 50), "query variant | top-1 | top-2 | top-3", MUTED_COLOR)

    for row_index, result in enumerate(results):
        y = HEADER_HEIGHT + row_index * ROW_HEIGHT
        row_box = (PADDING, y, width - PADDING, y + ROW_HEIGHT - 12)
        border_color = OK_COLOR if result["top1_ok"] else ERR_COLOR
        draw.rounded_rectangle(row_box, radius=10, fill=CARD_COLOR, outline=border_color, width=2)

        query_cell = cells[result["query_filename"]]
        with Image.open(query_cell.path) as query_image:
            query_thumb = render_thumb(build_variant_image(query_image))

        header_text = f"{row_index + 1:02d}. query {result['query_label']} -> predicted {result['predicted_label']}"
        draw_text(draw, (PADDING + 12, y + 10), header_text, TEXT_COLOR)
        draw_text(draw, (PADDING + 12, y + 28), f"top1_ok={result['top1_ok']}", border_color)

        x_positions = [PADDING + 12 + COL_WIDTH * idx for idx in range(4)]
        image_y = y + 44
        canvas.paste(query_thumb, (x_positions[0], image_y))
        draw_text(draw, (x_positions[0], image_y + THUMB_SIZE[1] + 6), f"query {result['query_label']}", TEXT_COLOR)

        for idx, match in enumerate(result["top_matches"]):
            match_cell = cells[match["filename"]]
            with Image.open(match_cell.path) as match_image:
                match_thumb = render_thumb(match_image)
            x = x_positions[idx + 1]
            canvas.paste(match_thumb, (x, image_y))
            draw_text(draw, (x, image_y + THUMB_SIZE[1] + 6), f"{match['label']} {match['similarity']:.3f}", TEXT_COLOR)

    canvas.save(output_path)


def main() -> None:
    batch_output = build_batch_output()
    OUTPUT_JSON.write_text(json.dumps(batch_output, indent=2, ensure_ascii=False) + "\n")
    render_visual_report(batch_output, OUTPUT_PNG)
    print(OUTPUT_JSON)
    print(OUTPUT_PNG)


if __name__ == "__main__":
    main()
