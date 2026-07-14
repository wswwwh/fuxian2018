"""Audit the predeclared 12.40-day halo source as a post-hoc diagnostic.

This script deliberately reads the already-exposed panel-(d) red masks.  It
must never alter the frozen v1 holdout result or establish paper 3D equality.
The candidate is selected only by proximity to the thesis-reported 12.40-day
source member before any reference mask is opened.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.chapter4_projection import (  # noqa: E402
    load_reference_panel_mask,
    project_surface_uv,
    projection_mask_metrics,
    rasterize_surface_mask,
)
from qp_orbits.chapter4_reproduction_lock import (  # noqa: E402
    load_chapter4_reproduction_lock,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import jacobi_constant  # noqa: E402
from qp_orbits.torus_stability import (  # noqa: E402
    corrected_curve_fixed_time_manifold_snapshots,
    corrected_l1_constant_energy_halo_high_order_dg_family,
    real_hyperbolic_eigen_index,
)


SCHEMA_VERSION = "chapter4_halo_12p40_posthoc_diagnostic_v1"
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
CSV_PATH = DATA / "chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv"
NPZ_PATH = DATA / "chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.npz"
DOC_PATH = DOCS / "chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.md"

PROTOCOL_PATH = DATA / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
CAMERA_NPZ = DATA / "chapter4_fig43_fig46_camera_calibration.npz"
FIT_NPZ = DATA / "chapter4_fig43_fig46_projection_fit_evidence.npz"
CURRENT_AUDIT_CSV = DATA / "chapter4_fig43_fig44_global_manifold_audit.csv"
CURRENT_AUDIT_NPZ = DATA / "chapter4_fig43_fig44_global_manifold_audit.npz"
HOLDOUT_CSV = DATA / "chapter4_fig43_fig46_projection_holdout_audit.csv"
TORUS_CORE = ROOT / "src" / "qp_orbits" / "torus_stability.py"
PROJECTION_CORE = ROOT / "src" / "qp_orbits" / "chapter4_projection.py"

THESIS_PERIOD_DAYS = 12.40
SNAPSHOT_DAYS = (7.79, 9.75, 11.39, 13.02)
HOLDOUT_PANEL = "d"
HOLDOUT_PANEL_INDEX = 3
FIGURES = {"4.3": ("plus_x", 0), "4.4": ("minus_x", 1)}
SOURCE_VARIANTS = ("current_n9", "thesis_12p40_n21")

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


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _posthoc_failures(metrics: dict[str, float]) -> list[str]:
    failures: list[str] = []
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


def _candidate_snapshots(mu: float, time_unit_days: float, epsilon: float):
    family = corrected_l1_constant_energy_halo_high_order_dg_family(
        mu,
        samples=21,
        members=25,
        member_indices=(0, 4, 8, 12, 16, 20, 24),
        tolerance=3.0e-10,
        max_iterations=64,
    )
    periods_days = np.asarray(
        [dg.mapping_time * time_unit_days for dg in family], dtype=float
    )
    selected_index = int(np.argmin(np.abs(periods_days - THESIS_PERIOD_DAYS)))
    dg = family[selected_index]
    snapshot_times = tuple(value / time_unit_days for value in SNAPSHOT_DAYS)
    candidates = tuple(
        corrected_curve_fixed_time_manifold_snapshots(
            mu,
            dg=dg,
            snapshot_times=snapshot_times,
            perturbation_scale=epsilon,
            perturbation_sign=sign,
            phase_samples=121,
            history_samples=161,
            max_step=0.01,
        )
        for sign in (-1.0, 1.0)
    )
    minus_x, plus_x = sorted(
        candidates,
        key=lambda item: float(np.mean(item.snapshot_states[-1, :, :, 0])),
    )
    return family, selected_index, dg, plus_x, minus_x


def _candidate_jacobi_drift(snapshots, mu: float) -> float:
    initial = jacobi_constant(snapshots.history_states[0], mu)
    history = jacobi_constant(snapshots.history_states, mu)
    snapshot = jacobi_constant(snapshots.snapshot_states, mu)
    history_drift = float(np.max(np.abs(history - initial[None, :])))
    snapshot_drift = float(
        np.max(np.abs(snapshot - initial[None, None, :]))
    )
    return max(history_drift, snapshot_drift)


def analyze() -> tuple[list[dict[str, str]], dict[str, np.ndarray]]:
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None:
        raise RuntimeError("Earth-Moon length unit is required")
    lock = load_chapter4_reproduction_lock(ROOT)
    epsilon = lock.epsilon_by_family["halo"]

    # Candidate selection is complete before any thesis red mask is opened.
    family, selected_index, dg, candidate_plus, candidate_minus = _candidate_snapshots(
        system.mu, system.time_unit_days, epsilon
    )
    selected_period_days = float(dg.mapping_time * system.time_unit_days)
    if abs(selected_period_days - 12.397983401715157) > 1.0e-9:
        raise RuntimeError("The predeclared 12.40-day source member drifted")

    protocol = {
        (row["figure_id"], row["panel_id"]): row
        for row in _read_csv(PROTOCOL_PATH)
    }
    holdout = {row["figure_id"]: row for row in _read_csv(HOLDOUT_CSV)}
    current_rows = _read_csv(CURRENT_AUDIT_CSV)
    current_meta = next(
        row
        for row in current_rows
        if row["figure_id"] == "4.3" and row["panel_index"] == "4"
    )

    with np.load(CAMERA_NPZ, allow_pickle=False) as camera, np.load(
        FIT_NPZ, allow_pickle=False
    ) as fit, np.load(CURRENT_AUDIT_NPZ, allow_pickle=False) as current:
        camera_hash = str(camera["camera_config_sha256"][0])
        if camera_hash != lock.camera_config_sha256:
            raise RuntimeError("Frozen camera hash drifted")
        current_states = np.asarray(fit["selected_halo_snapshot_states"], dtype=float)
        current_base_torus = np.asarray(current["plus_x_base_torus_states"], dtype=float)
        cameras = {
            figure_id: (
                np.asarray(
                    camera[f"fig_{figure_id.replace('.', '_')}_projection_matrix"],
                    dtype=float,
                ),
                np.asarray(
                    camera[f"fig_{figure_id.replace('.', '_')}_placement_matrix"],
                    dtype=float,
                ),
            )
            for figure_id in FIGURES
        }

    candidate_states = np.stack(
        (candidate_plus.snapshot_states, candidate_minus.snapshot_states)
    )
    candidate_base_torus = np.asarray(candidate_plus.base_torus_states, dtype=float)
    candidate_source = np.asarray(dg.correction.corrected_states, dtype=float)
    unstable_index = real_hyperbolic_eigen_index(dg, branch="unstable")
    unstable_eigenvalue = complex(dg.eigenvalues[unstable_index])
    relative_imaginary = abs(unstable_eigenvalue.imag) / max(
        abs(unstable_eigenvalue.real), np.finfo(float).tiny
    )
    source_jacobi = jacobi_constant(candidate_source, system.mu)
    candidate_drift = max(
        _candidate_jacobi_drift(candidate_plus, system.mu),
        _candidate_jacobi_drift(candidate_minus, system.mu),
    )

    source_metadata = {
        "current_n9": {
            "source_period_days": float(current_meta["source_mapping_time_days"]),
            "curve_samples": 9,
            "source_ay_km": float(np.max(np.abs(current_base_torus[..., 1])))
            * system.length_unit_km,
            "source_az_km": float(np.max(np.abs(current_base_torus[..., 2])))
            * system.length_unit_km,
            "source_curve_residual": float(current_meta["source_curve_residual"]),
            "dg_determinant_error_from_one": float(
                current_meta["dg_determinant_error_from_one"]
            ),
            "unstable_eigenvalue_real": float(current_meta["unstable_eigenvalue_real"]),
            "unstable_eigenvalue_relative_imaginary": float(
                current_meta["unstable_eigenvalue_relative_imaginary"]
            ),
            "source_jacobi_span": float(current_meta["source_jacobi_span"]),
            "manifold_jacobi_drift_max": max(
                float(row["combined_history_snapshot_jacobi_drift_max"])
                for row in current_rows
            ),
        },
        "thesis_12p40_n21": {
            "source_period_days": selected_period_days,
            "curve_samples": 21,
            "source_ay_km": float(np.max(np.abs(candidate_base_torus[..., 1])))
            * system.length_unit_km,
            "source_az_km": float(np.max(np.abs(candidate_base_torus[..., 2])))
            * system.length_unit_km,
            "source_curve_residual": float(dg.correction.final_residual_norms.max()),
            "dg_determinant_error_from_one": abs(float(dg.determinant) - 1.0),
            "unstable_eigenvalue_real": float(unstable_eigenvalue.real),
            "unstable_eigenvalue_relative_imaginary": relative_imaginary,
            "source_jacobi_span": float(np.ptp(source_jacobi)),
            "manifold_jacobi_drift_max": candidate_drift,
        },
    }
    states_by_variant = {
        "current_n9": current_states,
        "thesis_12p40_n21": candidate_states,
    }

    generator_hash = _sha256(Path(__file__))
    torus_hash = _sha256(TORUS_CORE)
    projection_hash = _sha256(PROJECTION_CORE)
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "source_variants": np.asarray(SOURCE_VARIANTS),
        "figure_ids": np.asarray(tuple(FIGURES)),
        "snapshot_times_days": np.asarray(SNAPSHOT_DAYS, dtype=float),
        "selected_epsilon": np.asarray([epsilon], dtype=float),
        "fit_lock_sha256": np.asarray([lock.fit_lock_sha256]),
        "holdout_run_id": np.asarray([lock.holdout_run_id]),
        "holdout_csv_sha256": np.asarray([lock.holdout_csv_sha256]),
        "camera_config_sha256": np.asarray([camera_hash]),
        "generator_sha256": np.asarray([generator_hash]),
        "torus_stability_sha256": np.asarray([torus_hash]),
        "projection_core_sha256": np.asarray([projection_hash]),
        "high_order_family_periods_days": np.asarray(
            [member.mapping_time * system.time_unit_days for member in family],
            dtype=float,
        ),
        "selected_family_index": np.asarray([selected_index], dtype=int),
        "current_snapshot_states": current_states,
        "current_base_torus_states": current_base_torus,
        "candidate_snapshot_states": candidate_states,
        "candidate_base_torus_states": candidate_base_torus,
        "candidate_source_states": candidate_source,
        "candidate_perturbation_directions": np.asarray(
            candidate_plus.perturbation_directions, dtype=float
        ),
        "candidate_dg_eigenvalues": np.asarray(dg.eigenvalues),
    }

    rows: list[dict[str, str]] = []
    metric_names = (
        "symmetric_chamfer_diagonal_fraction",
        "f1_at_0p01_diagonal",
        "hd95_diagonal_fraction",
        "area_ratio_prediction_over_paper",
        "projection_loss",
    )
    for source_variant in SOURCE_VARIANTS:
        metadata = source_metadata[source_variant]
        for figure_id, (branch, branch_index) in FIGURES.items():
            protocol_row = protocol[(figure_id, HOLDOUT_PANEL)]
            paper = load_reference_panel_mask(ROOT, protocol_row, allow_holdout=True)
            projection, placement = cameras[figure_id]
            surface = states_by_variant[source_variant][
                branch_index, HOLDOUT_PANEL_INDEX
            ]
            uv = project_surface_uv(surface, projection, placement)
            prediction = rasterize_surface_mask(uv)
            metrics = projection_mask_metrics(paper, prediction)
            failures = _posthoc_failures(metrics)
            if source_variant == "current_n9":
                frozen_row = holdout[figure_id]
                for name in metric_names:
                    if abs(float(frozen_row[name]) - float(metrics[name])) > 5.0e-13:
                        raise RuntimeError(
                            f"Frozen holdout replay drifted: {figure_id} {name}"
                        )
                replay_status = "exact_frozen_holdout_replay"
            else:
                replay_status = "posthoc_candidate_diagnostic"
            values: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "evidence_class": "posthoc_development_diagnostic_historical_exposure",
                "historical_exposure": True,
                "source_variant": source_variant,
                "source_selection_basis": (
                    "current_frozen_v1_source"
                    if source_variant == "current_n9"
                    else "nearest_accepted_member_to_thesis_reported_12.40_days"
                ),
                "source_selection_red_mask_read": False,
                "projection_red_mask_read": True,
                "replay_status": replay_status,
                "figure_id": figure_id,
                "panel_id": HOLDOUT_PANEL,
                "branch": branch,
                "selected_epsilon": epsilon,
                **metadata,
                **metrics,
                "posthoc_projection_gate": "pass" if not failures else "fail",
                "posthoc_failure_items": "none" if not failures else ";".join(failures),
                "chamfer_limit_diagonal_fraction": CHAMFER_MAX_FRACTION,
                "f1_min": F1_MIN,
                "hd95_limit_diagonal_fraction": HD95_MAX_FRACTION,
                "area_ratio_min": AREA_RATIO_MIN,
                "area_ratio_max": AREA_RATIO_MAX,
                "paper_projection_acceptance": lock.paper_projection_acceptance,
                "paper_projection_status": lock.paper_projection_status,
                "paper_3d_equivalence": False,
                "fit_lock_sha256": lock.fit_lock_sha256,
                "holdout_run_id": lock.holdout_run_id,
                "holdout_csv_sha256": lock.holdout_csv_sha256,
                "camera_config_sha256": camera_hash,
                "paper_source": protocol_row["paper_source"],
                "paper_source_sha256": protocol_row["paper_source_sha256"],
                "generator_sha256": generator_hash,
                "torus_stability_sha256": torus_hash,
                "projection_core_sha256": projection_hash,
            }
            rows.append({key: _fmt(value) for key, value in values.items()})
            stem = figure_id.replace(".", "_")
            prefix = f"{source_variant}_{stem}"
            arrays[prefix + "_reference_mask"] = paper
            arrays[prefix + "_prediction_mask"] = prediction
            arrays[prefix + "_projected_uv"] = uv
    return rows, arrays


def _verify_rows(rows: list[dict[str, str]]) -> None:
    expected = {
        (variant, figure_id) for variant in SOURCE_VARIANTS for figure_id in FIGURES
    }
    observed = {(row["source_variant"], row["figure_id"]) for row in rows}
    if len(rows) != 4 or observed != expected:
        raise RuntimeError("Expected four source-variant/figure rows")
    if any(row["paper_projection_acceptance"] != "fail" for row in rows):
        raise RuntimeError("Post-hoc diagnostic altered the frozen paper decision")
    if any(row["paper_3d_equivalence"] != "false" for row in rows):
        raise RuntimeError("Post-hoc diagnostic claimed paper 3D equivalence")
    candidate = [row for row in rows if row["source_variant"] == "thesis_12p40_n21"]
    if any(abs(float(row["source_period_days"]) - 12.40) > 0.005 for row in candidate):
        raise RuntimeError("12.40-day source target is not met")
    if any(abs(float(row["source_ay_km"]) - 41815.0) > 50.0 for row in candidate):
        raise RuntimeError("12.40-day source Ay target is not met")
    if any(abs(float(row["source_az_km"]) - 35783.0) > 50.0 for row in candidate):
        raise RuntimeError("12.40-day source Az target is not met")


def _compare_arrays(expected: dict[str, np.ndarray]) -> None:
    if not NPZ_PATH.is_file():
        raise RuntimeError("Stored post-hoc diagnostic NPZ is missing")
    with np.load(NPZ_PATH, allow_pickle=False) as stored:
        if set(stored.files) != set(expected):
            raise RuntimeError("Stored post-hoc diagnostic NPZ schema is stale")
        for key, values in expected.items():
            observed = np.asarray(stored[key])
            values = np.asarray(values)
            if observed.shape != values.shape or observed.dtype.kind != values.dtype.kind:
                raise RuntimeError(f"Stored NPZ array metadata is stale: {key}")
            if values.dtype.kind in "fc":
                if not np.allclose(observed, values, rtol=0.0, atol=5.0e-13):
                    raise RuntimeError(f"Stored NPZ numerical array is stale: {key}")
            elif not np.array_equal(observed, values):
                raise RuntimeError(f"Stored NPZ array is stale: {key}")


def _render_doc(rows: list[dict[str, str]], npz_hash: str) -> str:
    lines = [
        "# Chapter 4 halo 12.40-day post-hoc source diagnostic",
        "",
        "## Evidence boundary",
        "",
        "This generator replays the frozen N9 panel-(d) result and evaluates one",
        "predeclared N21 candidate selected only by proximity to the thesis-reported",
        "12.40-day source member. Panel (d) was already exposed. The candidate rows",
        "are post-hoc development diagnostics and cannot replace the frozen v1",
        "holdout, whose status remains `paper_projection=fail`, `paper_3d=false`.",
        "",
        "## Machine-readable result",
        "",
        "| Source | Figure | T0 [day] | N | Ay [km] | Az [km] | Loss | F1 | Chamfer/D | HD95/D | Area | Post-hoc gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['source_variant']}` | {row['figure_id']} | "
            f"{float(row['source_period_days']):.6f} | {row['curve_samples']} | "
            f"{float(row['source_ay_km']):.2f} | {float(row['source_az_km']):.2f} | "
            f"{float(row['projection_loss']):.4f} | "
            f"{float(row['f1_at_0p01_diagonal']):.3f} | "
            f"{float(row['symmetric_chamfer_diagonal_fraction']):.4f} | "
            f"{float(row['hd95_diagonal_fraction']):.4f} | "
            f"{float(row['area_ratio_prediction_over_paper']):.3f} | "
            f"{row['posthoc_projection_gate']} |"
        )
    candidate = next(
        row for row in rows if row["source_variant"] == "thesis_12p40_n21"
    )
    lines.extend(
        [
            "",
            "## Candidate source gates",
            "",
            f"- Curve residual: `{candidate['source_curve_residual']}`.",
            f"- Determinant error: `{candidate['dg_determinant_error_from_one']}`.",
            f"- Unstable multiplier: `{candidate['unstable_eigenvalue_real']}`; relative imaginary part "
            f"`{candidate['unstable_eigenvalue_relative_imaginary']}`.",
            f"- Source Jacobi span: `{candidate['source_jacobi_span']}`; manifold Jacobi drift "
            f"`{candidate['manifold_jacobi_drift_max']}`.",
            "- The source satisfies the predeclared period/Ay/Az gates. Fig. 4.3 improves",
            "  materially but still misses F1 and HD95; Fig. 4.4 remains below the",
            "  projection gates. No 4/4 outcome is claimed.",
            "",
            "## Traceability",
            "",
            f"- Frozen fit SHA256: `{candidate['fit_lock_sha256']}`.",
            f"- Frozen holdout run ID: `{candidate['holdout_run_id']}`.",
            f"- Frozen holdout CSV SHA256: `{candidate['holdout_csv_sha256']}`.",
            f"- Camera config SHA256: `{candidate['camera_config_sha256']}`.",
            f"- Generator SHA256: `{candidate['generator_sha256']}`.",
            f"- Torus core SHA256: `{candidate['torus_stability_sha256']}`.",
            f"- Projection core SHA256: `{candidate['projection_core_sha256']}`.",
            f"- CSV: `{_display(CSV_PATH)}`.",
            f"- NPZ: `{_display(NPZ_PATH)}` (SHA256 `{npz_hash}`).",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Recompute and verify the stored post-hoc diagnostic without rewriting.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows, arrays = analyze()
    _verify_rows(rows)
    if args.check:
        _compare_arrays(arrays)
        npz_hash = _sha256(NPZ_PATH)
        checked_rows = [dict(row, evidence_npz_sha256=npz_hash) for row in rows]
        if not CSV_PATH.is_file() or CSV_PATH.read_bytes() != _csv_bytes(checked_rows):
            raise RuntimeError("Stored post-hoc diagnostic CSV is stale")
        expected_doc = _render_doc(checked_rows, npz_hash)
        if not DOC_PATH.is_file() or DOC_PATH.read_text(encoding="utf-8") != expected_doc:
            raise RuntimeError("Stored post-hoc diagnostic report is stale")
        print(
            "chapter4_halo_12p40_posthoc_check: rows=4, "
            "frozen_holdout=fail, paper_3d=false"
        )
        return 0

    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ_PATH, **arrays)
    npz_hash = _sha256(NPZ_PATH)
    written_rows = [dict(row, evidence_npz_sha256=npz_hash) for row in rows]
    CSV_PATH.write_bytes(_csv_bytes(written_rows))
    DOC_PATH.write_text(_render_doc(written_rows, npz_hash), encoding="utf-8")
    print(f"wrote {_display(CSV_PATH)}")
    print(f"wrote {_display(NPZ_PATH)}")
    print(f"wrote {_display(DOC_PATH)}")
    print(
        "chapter4_halo_12p40_posthoc: rows=4, frozen_holdout=fail, paper_3d=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
