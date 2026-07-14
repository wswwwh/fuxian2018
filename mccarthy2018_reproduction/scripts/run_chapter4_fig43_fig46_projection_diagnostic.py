"""Run a diagnostic-only red-surface comparison for Figures 4.3--4.6.

The thesis and reproduction bitmaps are split into their four layout
quadrants, converted to deterministic red-dominance masks, and resized to a
common 512 x 512 panel grid.  No camera fit, Moon/axis registration, rigid
alignment, or mask registration is performed.  The resulting pixel metrics
therefore locate projection gaps but cannot establish paper equivalence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURE_IDS = ("4.3", "4.4", "4.5", "4.6")
PANEL_LAYOUT = (
    ("a", 0, 0),
    ("b", 1, 0),
    ("c", 0, 1),
    ("d", 1, 1),
)

NORMALIZED_PANEL_SIZE = (512, 512)
MATCH_TOLERANCE_PX = 5.0

# Deliberately broad red-dominance threshold.  It retains dark/translucent
# manifold pixels in both the thesis raster and the Matplotlib reproduction.
RED_MINIMUM = 55
RED_DOMINANCE_MINIMUM = 14
RED_RATIO_MINIMUM = 1.10

# These are diagnostic alert thresholds, not paper-acceptance gates.
CHAMFER_ALERT_MAX_PX = 10.0
PRECISION_ALERT_MIN = 0.50
RECALL_ALERT_MIN = 0.50
AREA_RATIO_ALERT_MIN = 0.50
AREA_RATIO_ALERT_MAX = 2.00

CSV_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter4_fig43_fig46_projection_diagnostic.csv"
)
DOC_OUTPUT = (
    PROJECT_ROOT / "docs" / "chapter4_fig43_fig46_projection_diagnostic.md"
)
QA_OUTPUT = (
    PROJECT_ROOT
    / "outputs"
    / "figure_qa"
    / "chapter4_fig43_fig46_projection_diagnostic_masks.png"
)

BOUNDARY_REASON = (
    "camera/axis/Moon fit not run and no image registration applied; "
    "pixel proximity is diagnostic-only and cannot establish 3D or paper equivalence"
)


def _fmt(value: Any) -> str:
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not np.isfinite(number):
            return ""
        return f"{number:.16g}"
    return str(value)


def _display_path(path: Path) -> str:
    return os.path.relpath(path, PROJECT_ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _source_paths(figure_id: str) -> tuple[Path, Path]:
    stem = f"fig_{figure_id.replace('.', '_')}"
    paper = PROJECT_ROOT / "outputs" / "reference_pages" / f"{stem}_reference.png"
    reproduction = PROJECT_ROOT / "outputs" / "figures_png" / f"{stem}.png"
    for path in (paper, reproduction):
        if not path.exists():
            raise FileNotFoundError(path)
    return paper, reproduction


def _panel_box(
    image_size: tuple[int, int], column: int, row: int
) -> tuple[int, int, int, int]:
    width, height = image_size
    x_edges = (0, width // 2, width)
    y_edges = (0, height // 2, height)
    return (
        x_edges[column],
        y_edges[row],
        x_edges[column + 1],
        y_edges[row + 1],
    )


def _red_mask(image: Image.Image) -> np.ndarray:
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    red = rgb[:, :, 0]
    green = rgb[:, :, 1]
    blue = rgb[:, :, 2]
    competitor = np.maximum(green, blue)
    return (
        (red >= RED_MINIMUM)
        & (red - competitor >= RED_DOMINANCE_MINIMUM)
        & (red >= RED_RATIO_MINIMUM * competitor)
    )


def _normalized_panel_mask(
    image: Image.Image, column: int, row: int
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    box = _panel_box(image.size, column, row)
    native_mask = _red_mask(image.crop(box))
    resized = Image.fromarray(native_mask.astype(np.uint8) * 255, mode="L").resize(
        NORMALIZED_PANEL_SIZE,
        Image.Resampling.NEAREST,
    )
    return np.asarray(resized, dtype=np.uint8) > 0, box


def _mask_metrics(paper: np.ndarray, reproduction: np.ndarray) -> dict[str, float]:
    if not paper.any():
        raise RuntimeError("Paper red mask is empty")
    if not reproduction.any():
        raise RuntimeError("Reproduction red mask is empty")

    distance_to_paper = distance_transform_edt(~paper)
    distance_to_reproduction = distance_transform_edt(~reproduction)
    paper_to_reproduction = float(np.mean(distance_to_reproduction[paper]))
    reproduction_to_paper = float(np.mean(distance_to_paper[reproduction]))
    symmetric = 0.5 * (paper_to_reproduction + reproduction_to_paper)
    precision = float(
        np.mean(distance_to_paper[reproduction] <= MATCH_TOLERANCE_PX)
    )
    recall = float(
        np.mean(distance_to_reproduction[paper] <= MATCH_TOLERANCE_PX)
    )
    area_ratio = float(np.count_nonzero(reproduction) / np.count_nonzero(paper))
    diagonal = float(np.hypot(*NORMALIZED_PANEL_SIZE))
    return {
        "paper_to_reproduction_chamfer_px": paper_to_reproduction,
        "reproduction_to_paper_chamfer_px": reproduction_to_paper,
        "symmetric_chamfer_px": symmetric,
        "symmetric_chamfer_panel_diagonal_fraction": symmetric / diagonal,
        "precision_at_5px": precision,
        "recall_at_5px": recall,
        "area_ratio_reproduction_over_paper": area_ratio,
    }


def _diagnostic_failures(metrics: dict[str, float]) -> list[str]:
    failures: list[str] = []
    if metrics["symmetric_chamfer_px"] > CHAMFER_ALERT_MAX_PX:
        failures.append("symmetric_chamfer_gt_10px")
    if metrics["precision_at_5px"] < PRECISION_ALERT_MIN:
        failures.append("precision_at_5px_lt_0.50")
    if metrics["recall_at_5px"] < RECALL_ALERT_MIN:
        failures.append("recall_at_5px_lt_0.50")
    area_ratio = metrics["area_ratio_reproduction_over_paper"]
    if area_ratio < AREA_RATIO_ALERT_MIN:
        failures.append("area_ratio_lt_0.50")
    elif area_ratio > AREA_RATIO_ALERT_MAX:
        failures.append("area_ratio_gt_2.00")
    return failures


def analyze() -> tuple[list[dict[str, str]], list[tuple[str, str, np.ndarray, np.ndarray]]]:
    rows: list[dict[str, str]] = []
    qa_masks: list[tuple[str, str, np.ndarray, np.ndarray]] = []
    for figure_id in FIGURE_IDS:
        paper_path, reproduction_path = _source_paths(figure_id)
        with Image.open(paper_path) as paper_source:
            paper_image = paper_source.convert("RGB")
        with Image.open(reproduction_path) as reproduction_source:
            reproduction_image = reproduction_source.convert("RGB")
        paper_hash = _sha256(paper_path)
        reproduction_hash = _sha256(reproduction_path)

        for panel_id, column, panel_row in PANEL_LAYOUT:
            paper_mask, paper_box = _normalized_panel_mask(
                paper_image, column, panel_row
            )
            reproduction_mask, reproduction_box = _normalized_panel_mask(
                reproduction_image, column, panel_row
            )
            metrics = _mask_metrics(paper_mask, reproduction_mask)
            failures = _diagnostic_failures(metrics)
            values: dict[str, Any] = {
                "figure_id": figure_id,
                "panel_id": panel_id,
                "status": "diagnostic_only",
                "audit_scope": "diagnostic_only",
                "paper_projection_acceptance": "not_run",
                "paper_3d_equivalence": "false",
                "camera_axis_moon_fit": "not_run",
                "image_registration": "none",
                "paper_source": _display_path(paper_path),
                "paper_source_sha256": paper_hash,
                "reproduction_source": _display_path(reproduction_path),
                "reproduction_source_sha256": reproduction_hash,
                "paper_panel_box_px": ",".join(map(str, paper_box)),
                "reproduction_panel_box_px": ",".join(
                    map(str, reproduction_box)
                ),
                "panel_split_method": "equal_image_quadrants_2x2",
                "mask_method": (
                    "native_rgb_red_dominance_then_nearest_neighbor_resize"
                ),
                "red_minimum": RED_MINIMUM,
                "red_dominance_minimum": RED_DOMINANCE_MINIMUM,
                "red_ratio_minimum": RED_RATIO_MINIMUM,
                "normalized_panel_width_px": NORMALIZED_PANEL_SIZE[0],
                "normalized_panel_height_px": NORMALIZED_PANEL_SIZE[1],
                "paper_mask_pixels": int(np.count_nonzero(paper_mask)),
                "reproduction_mask_pixels": int(
                    np.count_nonzero(reproduction_mask)
                ),
                **metrics,
                "match_tolerance_px": MATCH_TOLERANCE_PX,
                "diagnostic_chamfer_alert_max_px": CHAMFER_ALERT_MAX_PX,
                "diagnostic_precision_alert_min": PRECISION_ALERT_MIN,
                "diagnostic_recall_alert_min": RECALL_ALERT_MIN,
                "diagnostic_area_ratio_alert_min": AREA_RATIO_ALERT_MIN,
                "diagnostic_area_ratio_alert_max": AREA_RATIO_ALERT_MAX,
                "diagnostic_threshold_status": (
                    "alerts_present" if failures else "no_alerts"
                ),
                "failure_items": ";".join(failures) if failures else "none",
                "boundary_reason": BOUNDARY_REASON,
            }
            rows.append({key: _fmt(value) for key, value in values.items()})
            qa_masks.append((figure_id, panel_id, paper_mask, reproduction_mask))
    return rows, qa_masks


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _render_qa(
    masks: list[tuple[str, str, np.ndarray, np.ndarray]]
) -> Image.Image:
    tile_width = 220
    tile_height = 235
    legend_height = 42
    preview_size = 200
    canvas = Image.new(
        "RGB",
        (tile_width * len(PANEL_LAYOUT), legend_height + tile_height * len(FIGURE_IDS)),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text(
        (10, 8),
        "Red = paper mask; blue = reproduction mask; purple = overlap. "
        "Quadrant resize only; no registration.",
        fill="black",
        font=font,
    )

    by_key = {(figure_id, panel): (paper, reproduction)
              for figure_id, panel, paper, reproduction in masks}
    for figure_row, figure_id in enumerate(FIGURE_IDS):
        for panel_column, (panel_id, _, _) in enumerate(PANEL_LAYOUT):
            paper, reproduction = by_key[(figure_id, panel_id)]
            overlay = np.full((*paper.shape, 3), 255, dtype=np.uint8)
            paper_only = paper & ~reproduction
            reproduction_only = reproduction & ~paper
            overlap = paper & reproduction
            overlay[paper_only] = (214, 39, 40)
            overlay[reproduction_only] = (31, 119, 180)
            overlay[overlap] = (117, 90, 170)
            preview = Image.fromarray(overlay, mode="RGB").resize(
                (preview_size, preview_size), Image.Resampling.NEAREST
            )
            x0 = panel_column * tile_width + 10
            y0 = legend_height + figure_row * tile_height
            draw.text(
                (x0, y0 + 4),
                f"Fig. {figure_id} panel ({panel_id})",
                fill="black",
                font=font,
            )
            canvas.paste(preview, (x0, y0 + 24))
    return canvas


def _render_doc(rows: list[dict[str, str]]) -> str:
    alert_rows = [row for row in rows if row["failure_items"] != "none"]
    lines = [
        "# Chapter 4 Figures 4.3-4.6 projection diagnostic",
        "",
        "Generated by `scripts/run_chapter4_fig43_fig46_projection_diagnostic.py`.",
        "",
        "## Scope boundary",
        "",
        "- Status: `diagnostic_only`.",
        "- Paper projection acceptance: `not_run`.",
        "- Paper 3D equivalence: `false`.",
        "- Camera/axis/Moon fitting: `not_run`; image registration: `none`.",
        "- The metrics below identify 2D red-surface projection gaps. They do not",
        "  establish 3D state-space agreement or paper equivalence, including for a",
        "  panel with no diagnostic alerts.",
        "",
        "## Deterministic method",
        "",
        "1. Split each thesis crop and reproduction PNG into equal 2x2 image",
        "   quadrants; no content-based crop or alignment is applied.",
        "2. Segment red pixels in native RGB using `R >= 55`,",
        "   `R - max(G,B) >= 14`, and `R >= 1.10 * max(G,B)`.",
        "3. Resize each binary mask to `512x512` with nearest-neighbor sampling.",
        "4. Compute foreground-pixel directed Chamfer distances and report their",
        "   symmetric mean. Precision is the fraction of reproduction-mask pixels",
        "   within 5 px of the paper mask; recall reverses those roles. Area ratio is",
        "   reproduction-mask area divided by paper-mask area.",
        "",
        "Diagnostic alerts use: symmetric Chamfer `<= 10 px`, precision and recall",
        "`>= 0.50`, and area ratio within `[0.50, 2.00]`. These thresholds are",
        "triage aids only; they are not acceptance criteria.",
        "",
        "## Panel results",
        "",
        "| Figure | Panel | Symmetric Chamfer [px] | Precision @5px | Recall @5px | Area ratio | Failure items |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['figure_id']} | ({row['panel_id']}) | "
            f"{float(row['symmetric_chamfer_px']):.3f} | "
            f"{float(row['precision_at_5px']):.3f} | "
            f"{float(row['recall_at_5px']):.3f} | "
            f"{float(row['area_ratio_reproduction_over_paper']):.3f} | "
            f"`{row['failure_items']}` |"
        )

    lines.extend(
        [
            "",
            "## Diagnostic summary",
            "",
            f"- Panels evaluated: `{len(rows)}`.",
            f"- Panels with one or more diagnostic alerts: `{len(alert_rows)}`.",
            f"- Panels without alerts at the stated triage thresholds: "
            f"`{len(rows) - len(alert_rows)}`.",
            "- Paper projection acceptance remains `not_run` for all panels.",
            "",
            "## Failure inventory",
            "",
        ]
    )
    for row in alert_rows:
        lines.append(
            f"- Fig. {row['figure_id']} panel ({row['panel_id']}): "
            f"`{row['failure_items']}`."
        )
    if not alert_rows:
        lines.append("- No diagnostic alerts at the stated thresholds.")

    lines.extend(["", "## Provenance", ""])
    seen: set[str] = set()
    for row in rows:
        key = row["figure_id"]
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"- Fig. {key} paper: `{row['paper_source']}` "
            f"(SHA256 `{row['paper_source_sha256']}`)."
        )
        lines.append(
            f"- Fig. {key} reproduction: `{row['reproduction_source']}` "
            f"(SHA256 `{row['reproduction_source_sha256']}`)."
        )
    lines.extend(
        [
            f"- Machine-readable rows: `{_display_path(CSV_OUTPUT)}`.",
            f"- Mask QA image: `{_display_path(QA_OUTPUT)}`.",
            "",
            "The QA overlay also remains diagnostic-only: red denotes thesis-only",
            "mask pixels, blue reproduction-only pixels, and purple overlap after the",
            "same quadrant resize. Black mesh occlusion, transparency, antialiasing,",
            "camera differences, and crop margins all affect these bitmap metrics.",
            "",
        ]
    )
    return "\n".join(lines)


def _verify_boundaries(rows: list[dict[str, str]]) -> None:
    if len(rows) != len(FIGURE_IDS) * len(PANEL_LAYOUT):
        raise RuntimeError(f"Expected 16 panel rows; observed {len(rows)}")
    for row in rows:
        if row["status"] != "diagnostic_only":
            raise RuntimeError("A row escaped the diagnostic_only boundary")
        if row["paper_projection_acceptance"] != "not_run":
            raise RuntimeError("Paper projection acceptance must remain not_run")
        if row["paper_3d_equivalence"] != "false":
            raise RuntimeError("Paper 3D equivalence must remain false")
        for field in (
            "symmetric_chamfer_px",
            "precision_at_5px",
            "recall_at_5px",
            "area_ratio_reproduction_over_paper",
        ):
            if not np.isfinite(float(row[field])):
                raise RuntimeError(f"Non-finite {field} in Fig. {row['figure_id']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Recompute and validate the diagnostic without rewriting artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows, masks = analyze()
    _verify_boundaries(rows)
    alerts = sum(row["failure_items"] != "none" for row in rows)
    if args.check:
        expected_csv = _csv_bytes(rows)
        if not CSV_OUTPUT.is_file() or CSV_OUTPUT.read_bytes() != expected_csv:
            raise RuntimeError(
                "Stored projection diagnostic CSV is stale relative to current sources"
            )
        expected_doc = _render_doc(rows)
        if not DOC_OUTPUT.is_file() or DOC_OUTPUT.read_text(encoding="utf-8") != expected_doc:
            raise RuntimeError(
                "Stored projection diagnostic report is stale relative to current sources"
            )
        expected_qa = np.asarray(_render_qa(masks).convert("RGB"))
        if not QA_OUTPUT.is_file():
            raise RuntimeError("Stored projection diagnostic QA image is missing")
        with Image.open(QA_OUTPUT) as stored_qa_image:
            stored_qa = np.asarray(stored_qa_image.convert("RGB"))
        if stored_qa.shape != expected_qa.shape or not np.array_equal(
            stored_qa,
            expected_qa,
        ):
            raise RuntimeError(
                "Stored projection diagnostic QA image is stale relative to current sources"
            )
        print(
            "chapter4_projection_diagnostic_check: "
            f"rows={len(rows)}, alerts={alerts}, "
            "status=diagnostic_only, paper_projection_acceptance=not_run"
        )
        return 0

    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    CSV_OUTPUT.write_bytes(_csv_bytes(rows))
    DOC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUTPUT.write_text(_render_doc(rows), encoding="utf-8")
    QA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _render_qa(masks).save(QA_OUTPUT)
    print(f"wrote {_display_path(CSV_OUTPUT)}")
    print(f"wrote {_display_path(DOC_OUTPUT)}")
    print(f"wrote {_display_path(QA_OUTPUT)}")
    print(
        "chapter4_projection_diagnostic: "
        f"rows={len(rows)}, alerts={alerts}, "
        "status=diagnostic_only, paper_projection_acceptance=not_run"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
