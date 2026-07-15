"""Extract all 54 McCarthy thesis figures into the report asset directory."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def render_page(document: fitz.Document, page_number: int, zoom: float) -> Image.Image:
    page = document.load_page(page_number - 1)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)


def union_rects(rectangles: list[fitz.Rect]) -> fitz.Rect:
    result = fitz.Rect(rectangles[0])
    for rectangle in rectangles[1:]:
        result.include_rect(rectangle)
    return result


def figure_image_bands(page: fitz.Page) -> list[fitz.Rect]:
    rectangles: list[fitz.Rect] = []
    for image_info in page.get_images(full=True):
        xref = image_info[0]
        for rectangle in page.get_image_rects(xref):
            if rectangle.width * rectangle.height > 1_000:
                rectangles.append(rectangle)
    rectangles.sort(key=lambda rectangle: (rectangle.y0, rectangle.x0))
    bands: list[list[fitz.Rect]] = []
    for rectangle in rectangles:
        if not bands:
            bands.append([rectangle])
            continue
        current = union_rects(bands[-1])
        if rectangle.y0 <= current.y1 + 8:
            bands[-1].append(rectangle)
        else:
            bands.append([rectangle])
    return [union_rects(band) for band in bands]


def content_bbox(image: Image.Image, pad: int) -> tuple[int, int, int, int]:
    gray = np.asarray(image.convert("L"))
    height, width = gray.shape
    mask = gray < 245
    mask[: int(0.04 * height), :] = False
    mask[int(0.96 * height) :, :] = False
    ys, xs = np.where(mask)
    if not len(xs):
        return (0, 0, width, height)
    return (
        max(int(xs.min()) - pad, 0),
        max(int(ys.min()) - pad, 0),
        min(int(xs.max()) + pad, width),
        min(int(ys.max()) + pad, height),
    )


def pixel_bbox(rectangle: fitz.Rect, page: fitz.Page, zoom: float, pad: int) -> tuple[int, int, int, int]:
    return (
        max(int(rectangle.x0 * zoom) - pad, 0),
        max(int(rectangle.y0 * zoom) - pad, 0),
        min(int(rectangle.x1 * zoom) + pad, int(page.rect.width * zoom)),
        min(int(rectangle.y1 * zoom) + pad, int(page.rect.height * zoom)),
    )


def format_rect(rectangle: fitz.Rect | None) -> str:
    if rectangle is None:
        return "full_content_bbox"
    return json.dumps([round(value, 3) for value in rectangle], separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=WORKSPACE_ROOT / "2018_McCarthy_拟周期轨道.pdf")
    parser.add_argument("--index", type=Path, default=PROJECT_ROOT / "data" / "figure_index.csv")
    parser.add_argument("--catalog", type=Path, default=REPORT_ROOT / "stage_a" / "mccarthy_figure_catalog.csv")
    parser.add_argument("--output-dir", type=Path, default=REPORT_ROOT / "assets" / "original")
    parser.add_argument("--manifest", type=Path, default=REPORT_ROOT / "source_figure_manifest.csv")
    parser.add_argument("--zoom", type=float, default=4.2)
    args = parser.parse_args()

    index_rows = read_csv(args.index)
    catalog = {row["target_id"]: row for row in read_csv(args.catalog)}
    if len(index_rows) != 54 or len(catalog) != 54:
        raise RuntimeError("Figure index and Stage-A catalog must both contain 54 rows")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pdf_hash = sha256(args.pdf)
    document = fitz.open(args.pdf)
    rendered_pages: dict[int, Image.Image] = {}
    rows_by_page: collections.defaultdict[int, list[dict[str, str]]] = collections.defaultdict(list)
    for row in index_rows:
        rows_by_page[int(row["pdf_page"])].append(row)

    records: list[dict[str, object]] = []
    pad = max(20, round(10 * args.zoom))
    for pdf_page in sorted(rows_by_page):
        page_rows = sorted(
            rows_by_page[pdf_page],
            key=lambda row: tuple(int(part) for part in row["figure_id"].split(".")),
        )
        page = document.load_page(pdf_page - 1)
        rendered_pages[pdf_page] = render_page(document, pdf_page, args.zoom)
        rendered = rendered_pages[pdf_page]
        bands = figure_image_bands(page)
        if len(bands) == len(page_rows):
            assigned: list[tuple[fitz.Rect | None, str]] = [(band, "embedded_band_exact") for band in bands]
        elif len(page_rows) == 1 and bands:
            assigned = [(union_rects(bands), "embedded_band_union")]
        elif not bands and len(page_rows) == 1:
            assigned = [(None, "page_content_fallback")]
        else:
            raise RuntimeError(
                f"Ambiguous crop mapping on PDF page {pdf_page}: figures={len(page_rows)} bands={len(bands)}"
            )

        for row, (band, crop_status) in zip(page_rows, assigned):
            figure_id = row["figure_id"]
            bbox = pixel_bbox(band, page, args.zoom, pad) if band is not None else content_bbox(rendered, pad)
            cropped = rendered.crop(bbox)
            output = args.output_dir / f"fig_{figure_id.replace('.', '_')}_original.png"
            cropped.save(output, format="PNG", optimize=True)
            width, height = cropped.size
            catalog_row = catalog[figure_id]
            records.append(
                {
                    "target_id": figure_id,
                    "paper_page": row["source_page"],
                    "pdf_page": pdf_page,
                    "paper_caption": catalog_row["paper_caption"],
                    "caption_status": catalog_row["caption_status"],
                    "source_pdf": str(args.pdf.resolve()),
                    "source_pdf_sha256": pdf_hash,
                    "crop_method": "PyMuPDF page render + embedded-image vertical-band crop",
                    "crop_status": crop_status,
                    "crop_bbox_pdf_points": format_rect(band),
                    "render_zoom": args.zoom,
                    "nominal_dpi": round(72.0 * args.zoom, 1),
                    "embedded_raster_note": "render zoom does not create detail absent from embedded raster source",
                    "asset": rel(output),
                    "asset_exists": True,
                    "asset_bytes": output.stat().st_size,
                    "width_px": width,
                    "height_px": height,
                    "asset_sha256": sha256(output),
                    "stage_b_quality": "pass" if width >= 800 and height >= 300 else "dimension_review",
                }
            )

    records.sort(key=lambda row: tuple(int(part) for part in str(row["target_id"]).split(".")))
    hashes: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    for record in records:
        hashes[str(record["asset_sha256"])].append(str(record["target_id"]))
    duplicates = [ids for ids in hashes.values() if len(ids) > 1]
    if len(records) != 54 or duplicates:
        raise RuntimeError(f"Original extraction failed: rows={len(records)} duplicate_groups={duplicates}")
    write_csv(args.manifest, records)
    quality_counts = collections.Counter(str(row["stage_b_quality"]) for row in records)
    print(
        f"original_figures=54 unique_hashes=54 zoom={args.zoom} nominal_dpi={72*args.zoom:.1f} "
        f"quality={dict(quality_counts)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
