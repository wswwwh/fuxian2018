"""Register the frozen Chapter 4 camera/epsilon evaluation protocol.

This file deliberately records that every thesis panel has already been seen in
the legacy diagnostic.  Panel (d) is therefore a *programmatic frozen holdout*,
not a genuinely blind test.  The registered protocol must exist unchanged
before the new holdout evaluator is allowed to read any panel-(d) red mask.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

from _paths import find_thesis_pdf


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
CSV_PATH = DATA / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
DOC_PATH = DOCS / "chapter4_fig43_fig46_camera_holdout_protocol.md"
STATE_CSV_PATH = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.csv"

PROTOCOL_VERSION = "chapter4_camera_epsilon_holdout_v1"
EVIDENCE_CLASS = "programmatic_frozen_holdout_with_historical_exposure"
NORMALIZED_SIZE = 512
MASK_RULE = "R>=55;R-max(G,B)>=14;R>=1.10*max(G,B)"
CAMERA_MODEL = "shared_per_figure_orthographic_2x3_affine_from_static_fiducials"
CAMERA_FIT_PANELS = "a;b"
CAMERA_VALIDATION_PANEL = "c"
HOLDOUT_PANEL = "d"
EPSILON_HYPOTHESES = "H0_global;H1_family"
EPSILON_H1_VALIDATION_IMPROVEMENT_MIN = 0.10
EPSILON_H1_FAMILY_DEGRADATION_MAX = 0.0

# PDF-native embedded-image rectangles expressed in the existing full-figure
# reference-crop pixel coordinates.  Cropping is floor(x0,y0), ceil(x1,y1).
# Figure 4.3's PDF xref order differs from reading order; c/d are assigned by
# their actual bottom-left/bottom-right positions here.
PANEL_RECTS: dict[str, dict[str, tuple[float, float, float, float]]] = {
    "4.3": {
        "a": (21.036, 20.113, 419.330, 344.120),
        "b": (441.530, 20.113, 840.967, 344.120),
        "c": (20.958, 404.394, 414.387, 728.394),
        "d": (436.592, 404.377, 833.244, 728.394),
    },
    "4.4": {
        "a": (20.606, 20.017, 440.567, 308.020),
        "b": (462.768, 20.017, 875.398, 308.020),
        "c": (20.918, 368.302, 430.438, 656.294),
        "d": (452.648, 368.302, 867.275, 656.294),
    },
    "4.5": {
        "a": (24.866, 20.032, 436.899, 336.820),
        "b": (459.102, 20.032, 871.135, 336.820),
        "c": (20.964, 397.106, 432.997, 713.894),
        "d": (455.200, 397.106, 867.233, 713.894),
    },
    "4.6": {
        "a": (22.256, 20.010, 437.845, 279.220),
        "b": (460.050, 20.010, 873.743, 279.220),
        "c": (20.232, 339.486, 432.057, 598.696),
        "d": (454.262, 339.486, 867.966, 598.696),
    },
}

FIGURE_CONFIG: dict[str, dict[str, Any]] = {
    "4.3": {
        "family": "halo",
        "branch": "plus_x",
        "times_days": (7.79, 9.75, 11.39, 13.02),
        "npz": "chapter4_fig43_fig44_global_manifold_audit.npz",
        "array": "plus_x_snapshot_states",
    },
    "4.4": {
        "family": "halo",
        "branch": "minus_x",
        "times_days": (7.79, 9.75, 11.39, 13.02),
        "npz": "chapter4_fig43_fig44_global_manifold_audit.npz",
        "array": "minus_x_snapshot_states",
    },
    "4.5": {
        "family": "vertical",
        "branch": "plus_x",
        "times_days": (8.05, 10.08, 11.77, 13.46),
        "npz": "chapter4_fig45_fig48_vertical_manifold_audit.npz",
        "array": "plus_x_snapshot_states",
    },
    "4.6": {
        "family": "vertical",
        "branch": "minus_x",
        "times_days": (8.05, 10.08, 11.77, 13.46),
        "npz": "chapter4_fig45_fig48_vertical_manifold_audit.npz",
        "array": "minus_x_snapshot_states",
    },
}

PANEL_ROLES = {
    "a": "train",
    "b": "train",
    "c": "validation",
    "d": "programmatic_frozen_holdout",
}

# Project-defined gates, frozen before the new panel-(d) evaluation.  They are
# not thesis-reported tolerances and do not imply 3D equivalence.
ANCHOR_RMSE_MAX_PX = 4.0
ANCHOR_MAX_ERROR_MAX_PX = 8.0
CHAMFER_MAX_DIAGONAL_FRACTION = 0.02
F1_MIN = 0.70
HD95_MAX_DIAGONAL_FRACTION = 0.05
AREA_RATIO_MIN = 0.67
AREA_RATIO_MAX = 1.50

EPSILON0 = 4.5e-7
EPSILON_COARSE = tuple(EPSILON0 * 2.0 ** (k / 2.0) for k in range(-3, 4))
EPSILON_REFINEMENT_RULE = (
    "five_log2_points_inclusive_within_plus_minus_0.25_octave_around_"
    "training_selected_coarse_candidate"
)
EPSILON_MODEL_SELECTION_RULE = (
    "select_each_candidate_on_mean_train_projection_loss_ab_then_compare_H0_H1_"
    "once_on_validation_c;choose_H1_only_if_global_relative_improvement_ge_0.10_"
    "and_neither_family_validation_loss_worsens"
)
EPSILON_PROJECTION_LOSS = (
    "chamfer_over_D+0.5*(1-F1_at_0.01D)+0.25*abs(log(area_ratio))+"
    "0.25*HD95_over_D"
)


def _display(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.15g}"
    return str(value)


def _state_bound_source_hashes() -> dict[str, str] | None:
    """Recover the pre-fit source hashes after post-holdout regeneration.

    The sensitivity artifact is downstream of this protocol and is itself
    bound by the committed fit lock.  Once it exists, its source hashes are
    the historical registration inputs; the live fixed-time audit NPZ files
    may later be regenerated for explicitly labelled development figures.
    """

    if not STATE_CSV_PATH.is_file():
        return None
    if not CSV_PATH.is_file():
        raise RuntimeError("Stored protocol CSV is missing")
    with STATE_CSV_PATH.open(newline="", encoding="utf-8") as stream:
        state_rows = list(csv.DictReader(stream))
    if not state_rows:
        raise RuntimeError("Stored epsilon sensitivity rows are missing")
    protocol_hash = _sha256(CSV_PATH)
    if {row["protocol_sha256"] for row in state_rows} != {protocol_hash}:
        raise RuntimeError("Sensitivity evidence is not bound to this protocol")
    hashes: dict[str, str] = {}
    for row in state_rows:
        path = row["source_npz"]
        digest = row["source_npz_sha256"]
        previous = hashes.setdefault(path, digest)
        if previous != digest:
            raise RuntimeError(f"Inconsistent locked source hash for {path}")
    expected = {
        _display(DATA / str(config["npz"])) for config in FIGURE_CONFIG.values()
    }
    if set(hashes) != expected:
        raise RuntimeError("Sensitivity evidence has an unexpected source set")
    return hashes


def build_rows(
    *, source_hashes: Mapping[str, str] | None = None
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    thesis_path = find_thesis_pdf()
    thesis_hash = _sha256(thesis_path)
    for figure_id, config in FIGURE_CONFIG.items():
        paper_path = (
            ROOT
            / "outputs"
            / "reference_pages"
            / f"fig_{figure_id.replace('.', '_')}_reference.png"
        )
        npz_path = DATA / str(config["npz"])
        npz_display = _display(npz_path)
        if source_hashes is None:
            npz_hash = _sha256(npz_path)
        else:
            try:
                npz_hash = source_hashes[npz_display]
            except KeyError as error:
                raise RuntimeError(
                    f"Missing registered source hash for {npz_display}"
                ) from error
        for panel_index, panel_id in enumerate(("a", "b", "c", "d")):
            rect = PANEL_RECTS[figure_id][panel_id]
            values: dict[str, Any] = {
                "protocol_version": PROTOCOL_VERSION,
                "evidence_class": EVIDENCE_CLASS,
                "historical_exposure": True,
                "figure_id": figure_id,
                "panel_id": panel_id,
                "panel_role": PANEL_ROLES[panel_id],
                "snapshot_time_days": config["times_days"][panel_index],
                "family": config["family"],
                "branch": config["branch"],
                "camera_scope": "shared_within_figure",
                "epsilon_scope": "nested_H0_global_or_H1_family;never_branch_figure_panel",
                "paper_epsilon_numeric": "not_reported",
                "paper_epsilon_source": "Section_4.2_Equations_4.5_4.6_and_figure_captions",
                "thesis_source": _display(thesis_path),
                "thesis_source_sha256": thesis_hash,
                "epsilon_hypotheses": EPSILON_HYPOTHESES,
                "camera_fit_panels": CAMERA_FIT_PANELS,
                "camera_validation_panel": CAMERA_VALIDATION_PANEL,
                "holdout_panel": HOLDOUT_PANEL,
                "holdout_red_mask_allowed_during_fit": False,
                "paper_source": _display(paper_path),
                "paper_source_sha256": _sha256(paper_path),
                "source_npz": npz_display,
                "source_npz_sha256": npz_hash,
                "source_array": config["array"],
                "panel_rect_x0": rect[0],
                "panel_rect_y0": rect[1],
                "panel_rect_x1": rect[2],
                "panel_rect_y1": rect[3],
                "panel_crop_rule": "floor_lower_ceil_upper_pdf_native_rectangle",
                "normalized_width_px": NORMALIZED_SIZE,
                "normalized_height_px": NORMALIZED_SIZE,
                "camera_model": CAMERA_MODEL,
                "projection_type": "orthographic",
                "per_panel_transform_allowed": False,
                "mask_rule": MASK_RULE,
                "mask_morphology": "none",
                "epsilon_coarse_grid": json.dumps(EPSILON_COARSE),
                "epsilon_refinement_rule": EPSILON_REFINEMENT_RULE,
                "epsilon_projection_loss": EPSILON_PROJECTION_LOSS,
                "epsilon_model_selection_rule": EPSILON_MODEL_SELECTION_RULE,
                "epsilon_h1_validation_improvement_min": (
                    EPSILON_H1_VALIDATION_IMPROVEMENT_MIN
                ),
                "epsilon_h1_family_degradation_max": (
                    EPSILON_H1_FAMILY_DEGRADATION_MAX
                ),
                "anchor_rmse_max_px": ANCHOR_RMSE_MAX_PX,
                "anchor_max_error_max_px": ANCHOR_MAX_ERROR_MAX_PX,
                "chamfer_max_diagonal_fraction": CHAMFER_MAX_DIAGONAL_FRACTION,
                "f1_min": F1_MIN,
                "hd95_max_diagonal_fraction": HD95_MAX_DIAGONAL_FRACTION,
                "area_ratio_min": AREA_RATIO_MIN,
                "area_ratio_max": AREA_RATIO_MAX,
                "holdout_gate_aggregation": "all_four_panel_d_rows_must_pass",
                "paper_projection_acceptance": "not_run",
                "paper_3d_equivalence": False,
            }
            rows.append({key: _fmt(value) for key, value in values.items()})
    return rows


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _render_doc(rows: list[dict[str, str]]) -> str:
    hashes = {
        (row["paper_source"], row["paper_source_sha256"])
        for row in rows
    }
    npz_hashes = {
        (row["source_npz"], row["source_npz_sha256"])
        for row in rows
    }
    lines = [
        "# Chapter 4 Figures 4.3-4.6 frozen camera/epsilon protocol",
        "",
        f"Protocol: `{PROTOCOL_VERSION}`.",
        "",
        "## Evidence boundary",
        "",
        "All 16 thesis panels were already visible in the legacy diagnostic. Panel",
        "(d) is therefore only a **programmatic frozen holdout with historical",
        "exposure**, not a genuinely blind test. A pass may upgrade the project to",
        "`paper_projection_holdout_pass`; it can never set `paper_3d_equivalence=true`.",
        "",
        "## Frozen split and leakage rule",
        "",
        "- Panels (a),(b): camera/epsilon training.",
        "- Panel (c): model-selection validation.",
        "- Panel (d): one programmatic frozen-holdout evaluation after parameters,",
        "  thresholds, rendering, crops, and source hashes are locked.",
        "- The panel-(d) red mask is forbidden in fitting, model selection,",
        "  refinement, and threshold changes. If anything changes after viewing the",
        "  new result, panel (d) is downgraded to development evidence.",
        "",
        "## Frozen parameterization",
        "",
        f"- Camera: `{CAMERA_MODEL}`; one camera per figure, shared by all panels.",
        "- No panel-specific affine, homography, crop shift, ICP, or non-rigid",
        "  registration is allowed.",
        "- The thesis reports only a small epsilon, not its numeric value or whether",
        "  it is shared. The primary hypothesis H0 uses one global epsilon. H1 uses",
        "  one scalar per source-torus family, shared across +x/-x, and is admitted",
        "  only if panel-(c) validation loss improves by at least 10% globally and",
        "  neither family worsens. Branch/figure/panel-specific epsilon is forbidden.",
        f"- Coarse grid: `{json.dumps(EPSILON_COARSE)}`.",
        f"- Refinement: `{EPSILON_REFINEMENT_RULE}`.",
        f"- Projection loss: `{EPSILON_PROJECTION_LOSS}`.",
        f"- Model selection: `{EPSILON_MODEL_SELECTION_RULE}`.",
        f"- Red mask: `{MASK_RULE}`; morphology: `none`; normalized grid:",
        f"  `{NORMALIZED_SIZE}x{NORMALIZED_SIZE}`.",
        "",
        "## Project-defined holdout gates",
        "",
        f"- Static-anchor RMSE <= `{ANCHOR_RMSE_MAX_PX:.1f}` px and maximum error",
        f"  <= `{ANCHOR_MAX_ERROR_MAX_PX:.1f}` px.",
        f"- Symmetric Chamfer <= `{CHAMFER_MAX_DIAGONAL_FRACTION:.3f}D`.",
        f"- F1 at `0.01D` >= `{F1_MIN:.2f}`.",
        f"- HD95 <= `{HD95_MAX_DIAGONAL_FRACTION:.3f}D`.",
        f"- Area ratio in `[{AREA_RATIO_MIN:.2f}, {AREA_RATIO_MAX:.2f}]`.",
        "- Every one of the four panel-(d) rows must pass; averages cannot hide a",
        "  failed figure. These are project gates, not thesis-reported tolerances.",
        "",
        "## Registered panel rows",
        "",
        "| Figure | Panel | Role | Time [day] | Family | Branch |",
        "|---|---:|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['figure_id']} | ({row['panel_id']}) | "
            f"`{row['panel_role']}` | {row['snapshot_time_days']} | "
            f"{row['family']} | {row['branch']} |"
        )
    lines.extend(["", "## Bound sources", ""])
    for path, digest in sorted(hashes):
        lines.append(f"- `{path}`: SHA256 `{digest}`.")
    for path, digest in sorted(npz_hashes):
        lines.append(f"- `{path}`: SHA256 `{digest}`.")
    lines.extend(
        [
            "",
            "The machine-readable protocol is",
            f"`{_display(CSV_PATH)}`. At registration time,",
            "`paper_projection_acceptance=not_run` and",
            "`paper_3d_equivalence=false` for every row.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate(rows: list[dict[str, str]]) -> None:
    if len(rows) != 16:
        raise RuntimeError(f"Expected 16 protocol rows; observed {len(rows)}")
    if {row["panel_role"] for row in rows if row["panel_id"] == "d"} != {
        "programmatic_frozen_holdout"
    }:
        raise RuntimeError("Panel (d) is not uniquely registered as the holdout")
    if not all(row["historical_exposure"] == "true" for row in rows):
        raise RuntimeError("Historical exposure must be explicit on every row")
    if not all(row["paper_projection_acceptance"] == "not_run" for row in rows):
        raise RuntimeError("Projection acceptance must remain not_run at registration")
    if not all(row["paper_3d_equivalence"] == "false" for row in rows):
        raise RuntimeError("Protocol must never claim 3D equivalence")
    if any(row["per_panel_transform_allowed"] != "false" for row in rows):
        raise RuntimeError("Per-panel image transforms are forbidden")
    for row in rows:
        rect = tuple(float(row[key]) for key in (
            "panel_rect_x0", "panel_rect_y0", "panel_rect_x1", "panel_rect_y1"
        ))
        if not all(math.isfinite(value) for value in rect):
            raise RuntimeError("Non-finite panel rectangle")
        if rect[2] <= rect[0] or rect[3] <= rect[1]:
            raise RuntimeError("Invalid panel rectangle")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that stored protocol artifacts match the frozen definition.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.check and CSV_PATH.is_file() and STATE_CSV_PATH.is_file():
        raise RuntimeError(
            "Protocol is frozen by downstream state evidence; use --check "
            "or register a new protocol version"
        )
    locked_source_hashes = _state_bound_source_hashes() if args.check else None
    rows = build_rows(source_hashes=locked_source_hashes)
    _validate(rows)
    expected_csv = _csv_bytes(rows)
    expected_doc = _render_doc(rows)
    if args.check:
        if not CSV_PATH.is_file() or CSV_PATH.read_bytes() != expected_csv:
            raise RuntimeError("Stored camera/epsilon protocol CSV is stale")
        if not DOC_PATH.is_file() or DOC_PATH.read_text(encoding="utf-8") != expected_doc:
            raise RuntimeError("Stored camera/epsilon protocol report is stale")
        print(
            "chapter4_camera_holdout_protocol_check: rows=16, "
            "historical_exposure=true, paper_projection_acceptance=not_run, "
            "source_binding=historical_pre_fit"
        )
        return 0
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    CSV_PATH.write_bytes(expected_csv)
    DOC_PATH.write_text(expected_doc, encoding="utf-8")
    print(f"wrote {_display(CSV_PATH)}")
    print(f"wrote {_display(DOC_PATH)}")
    print(
        "chapter4_camera_holdout_protocol: rows=16, historical_exposure=true, "
        "paper_projection_acceptance=not_run"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
