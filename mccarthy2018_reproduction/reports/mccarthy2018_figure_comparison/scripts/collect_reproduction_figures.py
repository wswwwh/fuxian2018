"""Collect the current 54 script-generated reproduction figures without overwriting them."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import shutil
from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=PROJECT_ROOT / "data" / "figure_index.csv")
    parser.add_argument("--source-png-dir", type=Path, default=PROJECT_ROOT / "outputs" / "figures_png")
    parser.add_argument("--source-pdf-dir", type=Path, default=PROJECT_ROOT / "outputs" / "figures_pdf")
    parser.add_argument("--output-dir", type=Path, default=REPORT_ROOT / "assets" / "reproduced")
    parser.add_argument("--manifest", type=Path, default=REPORT_ROOT / "reproduction_figure_manifest.csv")
    args = parser.parse_args()

    rows = read_csv(args.index)
    if len(rows) != 54 or len({row["figure_id"] for row in rows}) != 54:
        raise RuntimeError("Figure index must contain 54 unique rows")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    hashes: collections.defaultdict[str, list[str]] = collections.defaultdict(list)

    for row in rows:
        figure_id = row["figure_id"]
        stem = f"fig_{figure_id.replace('.', '_')}"
        source_png = args.source_png_dir / f"{stem}.png"
        source_pdf = args.source_pdf_dir / f"{stem}.pdf"
        script = PROJECT_ROOT / row["script"]
        if not source_png.is_file() or not source_pdf.is_file() or not script.is_file():
            raise FileNotFoundError(
                f"Incomplete reproduction source for Fig. {figure_id}: "
                f"png={source_png.is_file()} pdf={source_pdf.is_file()} script={script.is_file()}"
            )
        if source_png.stat().st_size == 0 or source_pdf.stat().st_size == 0:
            raise RuntimeError(f"Empty reproduction source for Fig. {figure_id}")
        source_png_hash = sha256(source_png)
        source_pdf_hash = sha256(source_pdf)
        destination = args.output_dir / f"{stem}_reproduced.png"
        shutil.copy2(source_png, destination)
        destination_hash = sha256(destination)
        if destination_hash != source_png_hash:
            raise RuntimeError(f"Hash mismatch after copying Fig. {figure_id}")
        with Image.open(destination) as image:
            width, height = image.size
        hashes[destination_hash].append(figure_id)
        records.append(
            {
                "target_id": figure_id,
                "script": rel(script),
                "script_sha256": sha256(script),
                "source_png": rel(source_png),
                "source_png_bytes": source_png.stat().st_size,
                "source_png_sha256": source_png_hash,
                "source_vector_pdf": rel(source_pdf),
                "source_vector_pdf_bytes": source_pdf.stat().st_size,
                "source_vector_pdf_sha256": source_pdf_hash,
                "asset": rel(destination),
                "asset_exists": True,
                "asset_bytes": destination.stat().st_size,
                "width_px": width,
                "height_px": height,
                "asset_sha256": destination_hash,
                "collection_method": "hash-preserving copy from current script-generated output",
                "reexported_in_report_build": False,
                "reexport_reason": "existing nonempty PNG/PDF outputs are authoritative; report build does not overwrite project figures",
                "stage_b_quality": "pass" if width >= 1000 and height >= 600 else "dimension_review",
            }
        )

    duplicates = [ids for ids in hashes.values() if len(ids) > 1]
    if len(records) != 54 or duplicates:
        raise RuntimeError(f"Reproduction collection failed: rows={len(records)} duplicate_groups={duplicates}")
    records.sort(key=lambda row: tuple(int(part) for part in str(row["target_id"]).split(".")))
    write_csv(args.manifest, records)
    counts = collections.Counter(str(row["stage_b_quality"]) for row in records)
    print(f"reproduction_figures=54 unique_hashes=54 quality={dict(counts)} reexported=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
