"""Evaluate the once-frozen panel-(d) projection holdout for Figures 4.3--4.6."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.chapter4_projection import (  # noqa: E402
    load_reference_panel_mask,
    project_surface_uv,
    projection_mask_metrics,
    rasterize_surface_mask,
)


SCHEMA_VERSION = "chapter4_projection_holdout_audit_v1"
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
OUTPUTS = ROOT / "outputs" / "figure_qa"
PROTOCOL_PATH = DATA / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
CAMERA_NPZ = DATA / "chapter4_fig43_fig46_camera_calibration.npz"
CAMERA_METRICS = DATA / "chapter4_fig43_fig46_camera_static_metrics.csv"
STATE_NPZ = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.npz"
STATE_CSV = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.csv"
FIT_NPZ = DATA / "chapter4_fig43_fig46_projection_fit_evidence.npz"
FIT_LOCK = DATA / "chapter4_fig43_fig46_projection_fit_lock.json"
SELECTION_CSV = DATA / "chapter4_fig43_fig46_epsilon_model_selection.csv"
FIT_GENERATOR = ROOT / "scripts" / "run_chapter4_fig43_fig46_projection_fit.py"
PROJECTION_CORE = ROOT / "src" / "qp_orbits" / "chapter4_projection.py"
CSV_PATH = DATA / "chapter4_fig43_fig46_projection_holdout_audit.csv"
NPZ_PATH = DATA / "chapter4_fig43_fig46_projection_holdout_audit.npz"
DOC_PATH = DOCS / "chapter4_fig43_fig46_projection_holdout_audit.md"
QA_PATH = OUTPUTS / "chapter4_fig43_fig46_projection_holdout_overlay.png"

FIGURES = {
    "4.3": ("halo", 0),
    "4.4": ("halo", 1),
    "4.5": ("vertical", 0),
    "4.6": ("vertical", 1),
}
HOLDOUT_PANEL = "d"
HOLDOUT_PANEL_INDEX = 3

ANCHOR_RMSE_MAX_PX = 4.0
ANCHOR_MAX_ERROR_MAX_PX = 8.0
CHAMFER_MAX_FRACTION = 0.02
F1_MIN = 0.70
HD95_MAX_FRACTION = 0.05
AREA_RATIO_MIN = 0.67
AREA_RATIO_MAX = 1.50


def _display(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _fmt(value: Any) -> str:
    if isinstance(value, (bool, np.bool_)):
        return str(bool(value)).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not np.isfinite(number):
            return ""
        return f"{number:.15g}"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _git_commit_for(path: Path) -> str:
    result = subprocess.run(
        [
            "git",
            "log",
            "-1",
            "--format=%H",
            "--",
            str(path.relative_to(ROOT)),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if len(commit) != 40:
        raise RuntimeError(f"Could not bind a committed revision for {path}")
    return commit


def _holdout_failures(
    metrics: dict[str, float], *, anchor_rmse: float, anchor_max: float
) -> list[str]:
    failures: list[str] = []
    if anchor_rmse > ANCHOR_RMSE_MAX_PX:
        failures.append("anchor_rmse_gt_4px")
    if anchor_max > ANCHOR_MAX_ERROR_MAX_PX:
        failures.append("anchor_max_gt_8px")
    if metrics["symmetric_chamfer_diagonal_fraction"] > CHAMFER_MAX_FRACTION:
        failures.append("chamfer_gt_0.02D")
    if metrics["f1_at_0p01_diagonal"] < F1_MIN:
        failures.append("f1_lt_0.70")
    if metrics["hd95_diagonal_fraction"] > HD95_MAX_FRACTION:
        failures.append("hd95_gt_0.05D")
    area_ratio = metrics["area_ratio_prediction_over_paper"]
    if area_ratio < AREA_RATIO_MIN:
        failures.append("area_ratio_lt_0.67")
    elif area_ratio > AREA_RATIO_MAX:
        failures.append("area_ratio_gt_1.50")
    return failures


def _verify_fit_lock(lock: dict[str, Any]) -> tuple[str, str, str]:
    if lock["holdout_red_mask_read"] is not False:
        raise RuntimeError("Fit lock is not holdout-clean")
    if lock["paper_projection_acceptance"] != "not_run":
        raise RuntimeError("Fit lock was modified after a projection decision")
    expected_inputs = {
        "protocol": _sha256(PROTOCOL_PATH),
        "camera": _sha256(CAMERA_NPZ),
        "camera_metrics": _sha256(CAMERA_METRICS),
        "state": _sha256(STATE_NPZ),
        "state_rows": _sha256(STATE_CSV),
        "generator": _sha256(FIT_GENERATOR),
        "projection_core": _sha256(PROJECTION_CORE),
    }
    if lock["input_sha256"] != expected_inputs:
        raise RuntimeError("Fit lock input hashes are stale")
    selection = _read_csv(SELECTION_CSV)
    selected = [row for row in selection if row["selected_model"] == "true"]
    if len(selected) != 1:
        raise RuntimeError("Fit selection is not unique")
    fit_lock_hash = _sha256(FIT_LOCK)
    if selected[0]["fit_lock_sha256"] != fit_lock_hash:
        raise RuntimeError("Fit selection does not bind the current lock")
    if selected[0]["evidence_npz_sha256"] != _sha256(FIT_NPZ):
        raise RuntimeError("Fit selection does not bind the current NPZ")
    return fit_lock_hash, _git_commit_for(FIT_LOCK), _git_commit_for(Path(__file__))


def analyze() -> tuple[
    list[dict[str, str]],
    list[tuple[str, np.ndarray, np.ndarray]],
    dict[str, np.ndarray],
    dict[str, Any],
]:
    lock = json.loads(FIT_LOCK.read_text(encoding="utf-8"))
    fit_lock_hash, fit_lock_commit, evaluator_commit = _verify_fit_lock(lock)
    protocol = {
        (row["figure_id"], row["panel_id"]): row
        for row in _read_csv(PROTOCOL_PATH)
    }
    static_metrics = {
        (row["figure_id"], row["panel_id"]): row
        for row in _read_csv(CAMERA_METRICS)
    }
    generator_hash = _sha256(Path(__file__))
    core_hash = _sha256(PROJECTION_CORE)
    run_id = _sha256_bytes(
        (
            fit_lock_hash
            + fit_lock_commit
            + evaluator_commit
            + generator_hash
            + "".join(
                protocol[(figure_id, HOLDOUT_PANEL)]["paper_source_sha256"]
                for figure_id in FIGURES
            )
        ).encode("ascii")
    )

    with np.load(CAMERA_NPZ, allow_pickle=False) as camera_evidence, np.load(
        FIT_NPZ, allow_pickle=False
    ) as fit_evidence:
        camera_hash = str(camera_evidence["camera_config_sha256"][0])
        if camera_hash != lock["camera_config_sha256"]:
            raise RuntimeError("Fit lock camera hash is stale")
        selected_states = {
            family: np.asarray(
                fit_evidence[f"selected_{family}_snapshot_states"], dtype=float
            )
            for family in ("halo", "vertical")
        }
        cameras = {}
        for figure_id in FIGURES:
            stem = figure_id.replace(".", "_")
            cameras[figure_id] = (
                np.asarray(camera_evidence[f"fig_{stem}_projection_matrix"], dtype=float),
                np.asarray(camera_evidence[f"fig_{stem}_placement_matrix"], dtype=float),
            )

    rows_unformatted: list[dict[str, Any]] = []
    masks: list[tuple[str, np.ndarray, np.ndarray]] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "figure_ids": np.asarray(tuple(FIGURES)),
        "panel_id": np.asarray([HOLDOUT_PANEL]),
        "fit_lock_sha256": np.asarray([fit_lock_hash]),
        "fit_lock_commit": np.asarray([fit_lock_commit]),
        "evaluator_commit": np.asarray([evaluator_commit]),
        "holdout_run_id": np.asarray([run_id]),
        "camera_config_sha256": np.asarray([camera_hash]),
    }
    for figure_id, (family, branch_index) in FIGURES.items():
        protocol_row = protocol[(figure_id, HOLDOUT_PANEL)]
        paper = load_reference_panel_mask(
            ROOT, protocol_row, allow_holdout=True
        )
        surface = selected_states[family][branch_index, HOLDOUT_PANEL_INDEX]
        projection, placement = cameras[figure_id]
        uv = project_surface_uv(surface, projection, placement)
        prediction = rasterize_surface_mask(uv)
        metrics = projection_mask_metrics(paper, prediction)
        static = static_metrics[(figure_id, HOLDOUT_PANEL)]
        anchor_rmse = float(static["anchor_rmse_px_on_512_grid"])
        anchor_max = float(static["anchor_max_error_px_on_512_grid"])
        failures = _holdout_failures(
            metrics,
            anchor_rmse=anchor_rmse,
            anchor_max=anchor_max,
        )
        passed = not failures
        values: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "holdout_run_id": run_id,
            "evidence_class": "programmatic_frozen_holdout_with_historical_exposure",
            "historical_exposure": True,
            "figure_id": figure_id,
            "panel_id": HOLDOUT_PANEL,
            "panel_role": "programmatic_frozen_holdout",
            "family": family,
            "branch": "plus_x" if branch_index == 0 else "minus_x",
            "selected_model": lock["selected_model"],
            "selected_epsilon": lock["epsilon_by_family"][family],
            "anchor_rmse_px_on_512_grid": anchor_rmse,
            "anchor_max_error_px_on_512_grid": anchor_max,
            **metrics,
            "anchor_rmse_limit_px": ANCHOR_RMSE_MAX_PX,
            "anchor_max_error_limit_px": ANCHOR_MAX_ERROR_MAX_PX,
            "chamfer_limit_diagonal_fraction": CHAMFER_MAX_FRACTION,
            "f1_min": F1_MIN,
            "hd95_limit_diagonal_fraction": HD95_MAX_FRACTION,
            "area_ratio_min": AREA_RATIO_MIN,
            "area_ratio_max": AREA_RATIO_MAX,
            "holdout_gate": "pass" if passed else "fail",
            "failure_items": "none" if passed else ";".join(failures),
            "paper_projection_acceptance": "pass" if passed else "fail",
            "paper_projection_status": (
                "paper_projection_holdout_pass"
                if passed
                else "paper_projection_holdout_fail"
            ),
            "paper_3d_equivalence": False,
            "physical_flight_status": "not_assessed_selected_epsilon_mathematical_cr3bp",
            "fit_lock": _display(FIT_LOCK),
            "fit_lock_sha256": fit_lock_hash,
            "fit_lock_commit": fit_lock_commit,
            "evaluator_commit": evaluator_commit,
            "generator_sha256": generator_hash,
            "projection_core_sha256": core_hash,
            "camera_config_sha256": camera_hash,
            "paper_source": protocol_row["paper_source"],
            "paper_source_sha256": protocol_row["paper_source_sha256"],
        }
        rows_unformatted.append(values)
        masks.append((figure_id, paper, prediction))
        stem = figure_id.replace(".", "_")
        arrays[f"fig_{stem}_reference_mask"] = paper
        arrays[f"fig_{stem}_prediction_mask"] = prediction
        arrays[f"fig_{stem}_projected_uv"] = uv
    overall = all(row["holdout_gate"] == "pass" for row in rows_unformatted)
    summary = {
        "holdout_run_id": run_id,
        "fit_lock_sha256": fit_lock_hash,
        "fit_lock_commit": fit_lock_commit,
        "evaluator_commit": evaluator_commit,
        "selected_model": lock["selected_model"],
        "epsilon_by_family": lock["epsilon_by_family"],
        "panel_passes": sum(row["holdout_gate"] == "pass" for row in rows_unformatted),
        "panel_count": len(rows_unformatted),
        "chapter4_projection_holdout_gate": "pass" if overall else "fail",
        "paper_projection_status": (
            "paper_projection_holdout_pass"
            if overall
            else "paper_projection_holdout_fail"
        ),
        "paper_3d_equivalence": False,
    }
    arrays["chapter4_projection_holdout_gate"] = np.asarray(
        [summary["chapter4_projection_holdout_gate"]]
    )
    arrays["paper_3d_equivalence"] = np.asarray([False])
    rows = [{key: _fmt(value) for key, value in row.items()} for row in rows_unformatted]
    return rows, masks, arrays, summary


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _render_qa(masks: list[tuple[str, np.ndarray, np.ndarray]]) -> Image.Image:
    tile = 230
    preview = 210
    header = 46
    canvas = Image.new("RGB", (tile * len(masks), header + tile), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text(
        (10, 8),
        "Frozen panel (d): red=paper, blue=prediction, purple=overlap",
        fill="black",
        font=font,
    )
    for column, (figure_id, paper, prediction) in enumerate(masks):
        overlay = np.full((*paper.shape, 3), 255, dtype=np.uint8)
        overlay[paper & ~prediction] = (214, 39, 40)
        overlay[prediction & ~paper] = (31, 119, 180)
        overlay[paper & prediction] = (117, 90, 170)
        image = Image.fromarray(overlay, mode="RGB").resize(
            (preview, preview), Image.Resampling.NEAREST
        )
        x0 = column * tile + 10
        draw.text((x0, header), f"Fig. {figure_id} (d)", fill="black", font=font)
        canvas.paste(image, (x0, header + 18))
    return canvas


def _render_doc(
    rows: list[dict[str, str]], summary: dict[str, Any], npz_hash: str
) -> str:
    lines = [
        "# Chapter 4 Figures 4.3-4.6 frozen projection holdout audit",
        "",
        "Generated by `scripts/run_chapter4_fig43_fig46_projection_holdout_audit.py`.",
        "",
        "## Outcome",
        "",
        f"- Chapter 4 projection holdout gate: "
        f"`{summary['chapter4_projection_holdout_gate']}` "
        f"({summary['panel_passes']}/{summary['panel_count']} panels).",
        f"- Projection status: `{summary['paper_projection_status']}`.",
        "- Paper 3D equivalence remains `false`; a 2D silhouette audit cannot prove",
        "  equality of the thesis's original 3D states.",
        "- This is a programmatic frozen holdout with historical exposure, not a",
        "  genuinely blind test. The fit lock was committed before this evaluator",
        "  first opened any panel-(d) red mask.",
        "",
        "## Panel results",
        "",
        "| Figure | Epsilon | Anchor RMSE | Chamfer/D | F1 | HD95/D | Area ratio | Gate | Failures |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['figure_id']} | {float(row['selected_epsilon']):.6e} | "
            f"{float(row['anchor_rmse_px_on_512_grid']):.3f} | "
            f"{float(row['symmetric_chamfer_diagonal_fraction']):.4f} | "
            f"{float(row['f1_at_0p01_diagonal']):.3f} | "
            f"{float(row['hd95_diagonal_fraction']):.4f} | "
            f"{float(row['area_ratio_prediction_over_paper']):.3f} | "
            f"{row['holdout_gate']} | `{row['failure_items']}` |"
        )
    lines.extend(
        [
            "",
            "## Frozen provenance",
            "",
            f"- Holdout run ID: `{summary['holdout_run_id']}`.",
            f"- Fit lock SHA256: `{summary['fit_lock_sha256']}`.",
            f"- Fit lock commit: `{summary['fit_lock_commit']}`.",
            f"- Evaluator commit: `{summary['evaluator_commit']}`.",
            f"- Selected model: `{summary['selected_model']}`; epsilon map: "
            f"`{summary['epsilon_by_family']}`.",
            f"- Machine-readable rows: `{_display(CSV_PATH)}`.",
            f"- Evidence arrays: `{_display(NPZ_PATH)}` (SHA256 `{npz_hash}`).",
            f"- QA overlay: `{_display(QA_PATH)}`.",
            "",
        ]
    )
    return "\n".join(lines)


def _verify(rows: list[dict[str, str]], summary: dict[str, Any]) -> None:
    if len(rows) != 4 or {row["panel_id"] for row in rows} != {HOLDOUT_PANEL}:
        raise RuntimeError("Expected exactly four panel-(d) holdout rows")
    if any(row["paper_3d_equivalence"] != "false" for row in rows):
        raise RuntimeError("Projection holdout cannot establish 3D equivalence")
    passes = sum(row["holdout_gate"] == "pass" for row in rows)
    if passes != summary["panel_passes"]:
        raise RuntimeError("Holdout summary pass count is inconsistent")


def _compare_arrays(expected: dict[str, np.ndarray]) -> None:
    with np.load(NPZ_PATH, allow_pickle=False) as stored:
        if set(stored.files) != set(expected):
            raise RuntimeError("Stored holdout NPZ schema is stale")
        for key, values in expected.items():
            observed = np.asarray(stored[key])
            values = np.asarray(values)
            if observed.shape != values.shape:
                raise RuntimeError(f"Stored holdout array shape is stale: {key}")
            if values.dtype.kind in "fc":
                if not np.allclose(observed, values, rtol=0.0, atol=1.0e-13):
                    raise RuntimeError(f"Stored holdout array is stale: {key}")
            elif not np.array_equal(observed, values):
                raise RuntimeError(f"Stored holdout array is stale: {key}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows, masks, arrays, summary = analyze()
    _verify(rows, summary)
    if args.check:
        _compare_arrays(arrays)
        npz_hash = _sha256(NPZ_PATH)
        enriched = [dict(row, evidence_npz_sha256=npz_hash) for row in rows]
        if not CSV_PATH.is_file() or CSV_PATH.read_bytes() != _csv_bytes(enriched):
            raise RuntimeError("Stored holdout CSV is stale")
        expected_doc = _render_doc(enriched, summary, npz_hash)
        if not DOC_PATH.is_file() or DOC_PATH.read_text(encoding="utf-8") != expected_doc:
            raise RuntimeError("Stored holdout report is stale")
        expected_qa = np.asarray(_render_qa(masks).convert("RGB"))
        with Image.open(QA_PATH) as opened:
            observed_qa = np.asarray(opened.convert("RGB"))
        if observed_qa.shape != expected_qa.shape or not np.array_equal(
            observed_qa, expected_qa
        ):
            raise RuntimeError("Stored holdout QA overlay is stale")
        print(
            "chapter4_projection_holdout_check: "
            f"gate={summary['chapter4_projection_holdout_gate']}, "
            f"panels={summary['panel_passes']}/4, paper_3d=false"
        )
        return 0

    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ_PATH, **arrays)
    npz_hash = _sha256(NPZ_PATH)
    enriched = [dict(row, evidence_npz_sha256=npz_hash) for row in rows]
    CSV_PATH.write_bytes(_csv_bytes(enriched))
    DOC_PATH.write_text(_render_doc(enriched, summary, npz_hash), encoding="utf-8")
    _render_qa(masks).save(QA_PATH)
    for path in (CSV_PATH, NPZ_PATH, DOC_PATH, QA_PATH):
        print(f"wrote {_display(path)}")
    print(
        "chapter4_projection_holdout: "
        f"gate={summary['chapter4_projection_holdout_gate']}, "
        f"panels={summary['panel_passes']}/4, paper_3d=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
