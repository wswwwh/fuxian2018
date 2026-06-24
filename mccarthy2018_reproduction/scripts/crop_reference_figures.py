"""Render and crop thesis pages for figure-level visual comparison."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

from _paths import PROJECT_ROOT, find_thesis_pdf


def content_bbox(image: Image.Image, threshold: int = 245, pad: int = 20) -> tuple[int, int, int, int]:
    """Find a conservative bounding box around non-white page content."""

    gray = image.convert("L")
    arr = np.asarray(gray)
    height, width = arr.shape

    mask = arr < threshold
    margin_top = int(0.04 * height)
    margin_bottom = int(0.96 * height)
    mask[:margin_top, :] = False
    mask[margin_bottom:, :] = False

    ys, xs = np.where(mask)
    if len(xs) == 0 or len(ys) == 0:
        return (0, 0, width, height)

    left = max(int(xs.min()) - pad, 0)
    upper = max(int(ys.min()) - pad, 0)
    right = min(int(xs.max()) + pad, width)
    lower = min(int(ys.max()) + pad, height)
    return (left, upper, right, lower)


def read_index(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def render_page(doc: fitz.Document, page_number_1based: int, zoom: float) -> Image.Image:
    page = doc.load_page(page_number_1based - 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def _scale_rect(
    rect: fitz.Rect,
    page: fitz.Page,
    zoom: float,
    pad: int = 20,
) -> tuple[int, int, int, int]:
    image_rect = page.rect
    left = max(int(rect.x0 * zoom) - pad, 0)
    upper = max(int(rect.y0 * zoom) - pad, 0)
    right = min(int(rect.x1 * zoom) + pad, int(image_rect.width * zoom))
    lower = min(int(rect.y1 * zoom) + pad, int(image_rect.height * zoom))
    return (left, upper, right, lower)


def _union_rects(rects: list[fitz.Rect]) -> fitz.Rect:
    union = fitz.Rect(rects[0])
    for rect in rects[1:]:
        union.include_rect(rect)
    return union


def figure_image_bands(page: fitz.Page) -> list[fitz.Rect]:
    """Group embedded figure-image rectangles into vertical figure bands."""

    rects: list[fitz.Rect] = []
    for image_info in page.get_images(full=True):
        xref = image_info[0]
        for rect in page.get_image_rects(xref):
            if rect.width * rect.height > 1_000:
                rects.append(rect)

    if not rects:
        return []

    rects.sort(key=lambda r: (r.y0, r.x0))
    bands: list[list[fitz.Rect]] = []
    for rect in rects:
        if not bands:
            bands.append([rect])
            continue
        current = _union_rects(bands[-1])
        overlaps_vertically = rect.y0 <= current.y1 + 8
        if overlaps_vertically:
            bands[-1].append(rect)
        else:
            bands.append([rect])
    return [_union_rects(band) for band in bands]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=find_thesis_pdf())
    parser.add_argument("--index", type=Path, default=PROJECT_ROOT / "data" / "figure_index.csv")
    parser.add_argument("--zoom", type=float, default=2.0)
    args = parser.parse_args()

    if not args.index.exists():
        raise FileNotFoundError(f"Missing {args.index}; run build_figure_index.py first")

    rows = read_index(args.index)
    output_dir = PROJECT_ROOT / "outputs" / "reference_pages"
    output_dir.mkdir(parents=True, exist_ok=True)

    rows_by_page: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        rows_by_page.setdefault(int(row["pdf_page"]), []).append(row)

    doc = fitz.open(args.pdf)
    rendered_pages: dict[int, Image.Image] = {}
    written = 0
    for pdf_page, page_rows in rows_by_page.items():
        page_rows.sort(key=lambda r: tuple(int(part) for part in r["figure_id"].split(".")))
        if pdf_page not in rendered_pages:
            rendered_pages[pdf_page] = render_page(doc, pdf_page, args.zoom)
        image = rendered_pages[pdf_page]
        page = doc.load_page(pdf_page - 1)
        bands = figure_image_bands(page)

        if len(page_rows) > 1 and len(bands) == len(page_rows):
            assigned_bands = bands
        elif bands:
            assigned_bands = [_union_rects(bands)] * len(page_rows)
        else:
            assigned_bands = [None] * len(page_rows)

        for row, band in zip(page_rows, assigned_bands):
            figure_id = row["figure_id"]
            bbox = _scale_rect(band, page, args.zoom) if band else content_bbox(image)
            cropped = image.crop(bbox)
            cropped.save(output_dir / f"fig_{figure_id.replace('.', '_')}_reference.png")
            written += 1

    print(f"Wrote {written} reference crops to {output_dir}")


if __name__ == "__main__":
    main()
