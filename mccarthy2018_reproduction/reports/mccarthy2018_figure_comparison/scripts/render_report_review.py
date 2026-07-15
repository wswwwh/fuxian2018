#!/usr/bin/env python3
"""Render PDF contact sheets and selected full-page previews for visual review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageOps


def page_image(page: fitz.Page, dpi: int) -> Image.Image:
    pixmap = page.get_pixmap(dpi=dpi, alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def find_page(document: fitz.Document, marker: str, start_index: int = 0) -> int | None:
    for index in range(start_index, len(document)):
        page = document[index]
        if marker in page.get_text("text"):
            return index
    return None


def contact_sheet(
    document: fitz.Document,
    page_indices: list[int],
    output_path: Path,
    columns: int,
    thumb_width: int,
    dpi: int,
) -> None:
    margin = 18
    label_height = 30
    thumbs: list[tuple[int, Image.Image]] = []
    max_height = 0
    for index in page_indices:
        image = page_image(document[index], dpi)
        height = round(image.height * thumb_width / image.width)
        image = image.resize((thumb_width, height), Image.Resampling.LANCZOS)
        thumbs.append((index, image))
        max_height = max(max_height, height)
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new(
        "RGB",
        (
            margin + columns * (thumb_width + margin),
            margin + rows * (max_height + label_height + margin),
        ),
        "#d9dde3",
    )
    draw = ImageDraw.Draw(sheet)
    for position, (index, image) in enumerate(thumbs):
        row, column = divmod(position, columns)
        x = margin + column * (thumb_width + margin)
        y = margin + row * (max_height + label_height + margin)
        frame = Image.new("RGB", (thumb_width + 4, max_height + 4), "white")
        frame.paste(image, (2, 2))
        sheet.paste(frame, (x - 2, y - 2))
        draw.text((x, y + max_height + 7), f"PDF page {index + 1}", fill="#111827")
    sheet.save(output_path, quality=92)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    root = args.report_root.resolve()
    output_dir = (args.output_dir or root / "stage_e" / "visual_review").resolve()
    selected_dir = output_dir / "selected_pages"
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_dir.mkdir(parents=True, exist_ok=True)
    for existing in selected_dir.glob("page_*.png"):
        existing.unlink()
    for existing in output_dir.glob("current_page_*.png"):
        existing.unlink()
    pdf_path = root / "McCarthy2018_54图逐图复现对照报告.pdf"
    document = fitz.open(pdf_path)

    markers = [
        "McCarthy Fig. 2.1",
        "McCarthy Fig. 2.15",
        "McCarthy Fig. 3.10",
        "McCarthy Fig. 3.16",
        "McCarthy Fig. 4.3",
        "McCarthy Fig. 5.10",
        "Representative quantitative results and boundaries",
        "Index of grades and boundaries for all 54 figures",
        "Representative quantitative records for 28 core figures",
        "SHA-256 hashes of key report manifests",
        "Field-level items pending verification",
    ]
    selected = list(range(min(6, len(document))))
    marker_pages: dict[str, int | None] = {}
    for marker in markers:
        index = find_page(document, marker, start_index=4)
        marker_pages[marker] = None if index is None else index + 1
        if index is not None:
            selected.append(index)
    selected.extend([max(0, len(document) - 2), len(document) - 1])
    selected = sorted(set(selected))

    contact_sheet(document, list(range(len(document))), output_dir / "all_pages_contact_sheet.png", 7, 180, 58)
    contact_sheet(document, selected, output_dir / "selected_pages_contact_sheet.png", 4, 430, 105)
    for index in selected:
        image = page_image(document[index], 135)
        image = ImageOps.contain(image, image.size)
        image.save(selected_dir / f"page_{index + 1:03d}.png", optimize=True)

    manifest = {
        "pdf": str(pdf_path),
        "page_count": len(document),
        "selected_pages": [index + 1 for index in selected],
        "marker_pages": marker_pages,
        "all_pages_contact_sheet": str(output_dir / "all_pages_contact_sheet.png"),
        "selected_pages_contact_sheet": str(output_dir / "selected_pages_contact_sheet.png"),
    }
    (output_dir / "visual_review_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    document.close()
    print(f"report_render=PASS pages={manifest['page_count']} selected={len(selected)}")
    print(output_dir / "all_pages_contact_sheet.png")
    print(output_dir / "selected_pages_contact_sheet.png")


if __name__ == "__main__":
    main()
