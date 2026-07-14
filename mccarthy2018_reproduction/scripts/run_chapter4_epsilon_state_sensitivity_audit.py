"""Run a state-space epsilon sensitivity audit for Chapter 4 Figures 4.3--4.6.

The accepted fixed-time audit NPZ files are treated as persistent source/DG
caches.  Each ``(epsilon, sign)`` ensemble is propagated in its own adaptive
solve so SciPy's global error norm cannot dilute accuracy across candidates.
No thesis red mask, including the registered panel-(d) mask, is read here.
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

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_states_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.ephemeris import MOON_RADIUS_KM  # noqa: E402


SCHEMA_VERSION = "chapter4_epsilon_state_sensitivity_v1"
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
CSV_PATH = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.csv"
NPZ_PATH = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.npz"
DOC_PATH = DOCS / "chapter4_fig43_fig46_epsilon_state_sensitivity.md"
PROTOCOL_PATH = DATA / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
MOON_RADIUS_SOURCE = ROOT / "src" / "qp_orbits" / "ephemeris.py"

EPSILON0 = 4.5e-7
EPSILON_GRID = np.asarray(
    [EPSILON0 * 2.0 ** (k / 2.0) for k in range(-3, 4)],
    dtype=float,
)
BRANCHES = ("plus_x", "minus_x")
RTOL = 1.0e-12
ATOL = 1.0e-14
MAX_STEP = 0.01
LOCAL_LINEAR_REFERENCE_MULTIPLIER = 100.0
LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT = 1.0e-3
JACOBI_DRIFT_LIMIT = 1.0e-10

FAMILY_CONFIG = {
    "halo": {
        "source_npz": DATA / "chapter4_fig43_fig44_global_manifold_audit.npz",
        "figures": {"plus_x": "4.3", "minus_x": "4.4"},
    },
    "vertical": {
        "source_npz": DATA / "chapter4_fig45_fig48_vertical_manifold_audit.npz",
        "figures": {"plus_x": "4.5", "minus_x": "4.6"},
    },
}


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


def _indices_for_times(grid: np.ndarray, requested: np.ndarray) -> np.ndarray:
    indices = np.searchsorted(grid, requested)
    if np.any(indices >= grid.size):
        raise RuntimeError("Requested time is outside the evaluation grid")
    if float(np.max(np.abs(grid[indices] - requested), initial=0.0)) > 1.0e-12:
        raise RuntimeError("Requested time is missing from the evaluation grid")
    return indices


def _branch_sign(
    *, source: np.ndarray, direction: np.ndarray, history0: np.ndarray, epsilon: float
) -> float:
    scores = np.sum((history0 - source) * direction, axis=1) / epsilon
    sign = float(np.sign(np.mean(scores)))
    if sign not in (-1.0, 1.0) or float(np.max(np.abs(scores - sign))) > 1.0e-8:
        raise RuntimeError("Could not recover the accepted branch perturbation sign")
    return sign


def _surface_area(surface_states: np.ndarray) -> float:
    """Triangulate phase strips while closing only the periodic curve axis."""

    xyz = np.asarray(surface_states, dtype=float)[..., :3]
    if xyz.ndim != 3 or xyz.shape[0] < 2 or xyz.shape[1] < 2:
        raise ValueError("surface_states must have shape (phase, curve, 6)")
    q00 = xyz[:-1]
    q10 = xyz[1:]
    q01 = np.roll(q00, -1, axis=1)
    q11 = np.roll(q10, -1, axis=1)
    area1 = 0.5 * np.linalg.norm(np.cross(q10 - q00, q11 - q00), axis=2)
    area2 = 0.5 * np.linalg.norm(np.cross(q11 - q00, q01 - q00), axis=2)
    return float(np.sum(area1 + area2))


def _load_family(family: str) -> dict[str, Any]:
    config = FAMILY_CONFIG[family]
    source_npz = Path(config["source_npz"])
    with np.load(source_npz, allow_pickle=False) as evidence:
        epsilon = float(np.asarray(evidence["perturbation_scale"]).reshape(-1)[0])
        if abs(epsilon - EPSILON0) > 1.0e-18:
            raise RuntimeError(f"Unexpected accepted epsilon in {source_npz}")
        source = np.asarray(evidence["plus_x_source_states"], dtype=float)
        direction = np.asarray(
            evidence["plus_x_perturbation_directions"], dtype=float
        )
        phase_times = np.asarray(evidence["plus_x_phase_times_nd"], dtype=float)
        history_times = np.asarray(evidence["plus_x_history_times_nd"], dtype=float)
        snapshot_times = np.asarray(evidence["plus_x_snapshot_times_nd"], dtype=float)
        for key, accepted in (
            ("minus_x_source_states", source),
            ("minus_x_perturbation_directions", direction),
            ("minus_x_phase_times_nd", phase_times),
            ("minus_x_history_times_nd", history_times),
            ("minus_x_snapshot_times_nd", snapshot_times),
        ):
            if not np.array_equal(np.asarray(evidence[key]), accepted):
                raise RuntimeError(f"Accepted branches disagree on source input: {key}")
        branch_signs = np.asarray(
            [
                _branch_sign(
                    source=source,
                    direction=direction,
                    history0=np.asarray(evidence[f"{branch}_history_states"])[0],
                    epsilon=epsilon,
                )
                for branch in BRANCHES
            ],
            dtype=float,
        )
        base_history = np.asarray(evidence["plus_x_base_history_states"], dtype=float)
        base_snapshots = np.asarray(evidence["plus_x_base_snapshot_states"], dtype=float)
        scale_free_linear_history = (
            np.asarray(
                evidence["plus_x_linear_history_state_separation_norms"],
                dtype=float,
            )
            / epsilon
        )
        payload = {
            "family": family,
            "source_npz": source_npz,
            "source_npz_sha256": _sha256(source_npz),
            "source_states": source,
            "directions": direction,
            "branch_signs": branch_signs,
            "phase_times": phase_times,
            "history_times": history_times,
            "snapshot_times": snapshot_times,
            "base_history_states": base_history,
            "base_snapshot_states": base_snapshots,
            "scale_free_linear_history_norms": scale_free_linear_history,
        }
    snapshot_evaluation_times = np.concatenate(
        [elapsed + phase_times for elapsed in snapshot_times]
    )
    evaluation_times = np.unique(np.r_[history_times, snapshot_evaluation_times])
    payload["evaluation_times"] = evaluation_times
    payload["history_indices"] = _indices_for_times(evaluation_times, history_times)
    payload["snapshot_indices"] = _indices_for_times(
        evaluation_times, snapshot_evaluation_times
    ).reshape(snapshot_times.size, phase_times.size)
    return payload


def _propagate_family(payload: dict[str, Any], mu: float) -> dict[str, Any]:
    source = payload["source_states"]
    direction = payload["directions"]
    times = payload["evaluation_times"]
    sample_count = source.shape[0]
    evaluated = np.empty(
        (EPSILON_GRID.size, len(BRANCHES), times.size, sample_count, 6),
        dtype=float,
    )
    nfev = np.empty((EPSILON_GRID.size, len(BRANCHES)), dtype=int)
    for epsilon_index, epsilon in enumerate(EPSILON_GRID):
        for branch_index, sign in enumerate(payload["branch_signs"]):
            initial = source + float(sign) * float(epsilon) * direction
            solution = integrate_states_cr3bp(
                initial,
                (0.0, float(times[-1])),
                mu,
                t_eval=times,
                rtol=RTOL,
                atol=ATOL,
                max_step=MAX_STEP,
            )
            if not solution.success:
                raise RuntimeError(
                    f"{payload['family']} epsilon={epsilon:.6g} sign={sign:+g}: "
                    f"{solution.message}"
                )
            values = solution.y.T.reshape(times.size, sample_count, 6)
            if not np.all(np.isfinite(values)):
                raise RuntimeError("Non-finite epsilon sensitivity state")
            evaluated[epsilon_index, branch_index] = values
            nfev[epsilon_index, branch_index] = int(solution.nfev)
    history = evaluated[:, :, payload["history_indices"]]
    snapshots = evaluated[:, :, payload["snapshot_indices"]]
    return {
        "evaluated_states": evaluated,
        "history_states": history,
        "snapshot_states": snapshots,
        "nfev": nfev,
    }


def _panel_metrics(
    *,
    payload: dict[str, Any],
    propagated: dict[str, Any],
    epsilon_index: int,
    branch_index: int,
    panel_index: int,
    system: Any,
) -> dict[str, Any]:
    epsilon = float(EPSILON_GRID[epsilon_index])
    snapshot_times = payload["snapshot_times"]
    history_times = payload["history_times"]
    elapsed = float(snapshot_times[panel_index])
    history_stop = int(np.searchsorted(history_times, elapsed, side="right"))
    history = propagated["history_states"][
        epsilon_index, branch_index, :history_stop
    ]
    snapshot = propagated["snapshot_states"][
        epsilon_index, branch_index, panel_index
    ]
    base_history = payload["base_history_states"][:history_stop]
    base_snapshot = payload["base_snapshot_states"][panel_index]
    combined = np.concatenate((history, snapshot), axis=0)
    positions = snapshot[..., :3]
    flat_positions = positions.reshape(-1, 3)
    snapshot_state_separation = np.linalg.norm(snapshot - base_snapshot, axis=2)
    snapshot_position_separation = np.linalg.norm(
        snapshot[..., :3] - base_snapshot[..., :3], axis=2
    )

    jacobi = jacobi_constant(combined.reshape(-1, 6), system.mu).reshape(
        combined.shape[0], combined.shape[1]
    )
    jacobi_drift = float(np.max(np.ptp(jacobi, axis=0)))
    xyz = combined[..., :3]
    primary_distance = np.sqrt(
        (xyz[..., 0] + system.mu) ** 2 + xyz[..., 1] ** 2 + xyz[..., 2] ** 2
    )
    secondary_distance = np.sqrt(
        (xyz[..., 0] - 1.0 + system.mu) ** 2
        + xyz[..., 1] ** 2
        + xyz[..., 2] ** 2
    )
    primary_distance_min = float(np.min(primary_distance))
    secondary_distance_min = float(np.min(secondary_distance))
    moon_clearance_km = (
        secondary_distance_min * float(system.length_unit_km) - MOON_RADIUS_KM
    )
    moon_intersection = moon_clearance_km < 0.0

    measured_history = np.linalg.norm(history - base_history, axis=2)
    scale_free = payload["scale_free_linear_history_norms"][:history_stop]
    expected_history = epsilon * scale_free
    local_mask = (scale_free <= LOCAL_LINEAR_REFERENCE_MULTIPLIER) & (
        expected_history > 0.0
    )
    local_relative_error = np.abs(measured_history - expected_history) / np.maximum(
        expected_history, np.finfo(float).tiny
    )
    local_sample_count = int(np.count_nonzero(local_mask))
    local_error_max = (
        float(np.max(local_relative_error[local_mask]))
        if local_sample_count
        else float("nan")
    )
    local_gate = bool(
        local_sample_count > 0
        and local_error_max <= LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT
    )
    numerical_gate = bool(jacobi_drift <= JACOBI_DRIFT_LIMIT and local_gate)

    state_quantiles = np.quantile(snapshot_state_separation, (0.5, 0.9, 0.99))
    position_quantiles = np.quantile(
        snapshot_position_separation, (0.5, 0.9, 0.99)
    )
    return {
        "snapshot_x_min": float(np.min(flat_positions[:, 0])),
        "snapshot_x_max": float(np.max(flat_positions[:, 0])),
        "snapshot_y_min": float(np.min(flat_positions[:, 1])),
        "snapshot_y_max": float(np.max(flat_positions[:, 1])),
        "snapshot_z_min": float(np.min(flat_positions[:, 2])),
        "snapshot_z_max": float(np.max(flat_positions[:, 2])),
        "snapshot_x_centroid": float(np.mean(flat_positions[:, 0])),
        "snapshot_y_centroid": float(np.mean(flat_positions[:, 1])),
        "snapshot_z_centroid": float(np.mean(flat_positions[:, 2])),
        "snapshot_surface_area_nd2": _surface_area(snapshot),
        "snapshot_state_separation_p50": float(state_quantiles[0]),
        "snapshot_state_separation_p90": float(state_quantiles[1]),
        "snapshot_state_separation_p99": float(state_quantiles[2]),
        "snapshot_state_separation_max": float(np.max(snapshot_state_separation)),
        "snapshot_position_separation_p50": float(position_quantiles[0]),
        "snapshot_position_separation_p90": float(position_quantiles[1]),
        "snapshot_position_separation_p99": float(position_quantiles[2]),
        "snapshot_position_separation_max": float(
            np.max(snapshot_position_separation)
        ),
        "combined_jacobi_drift_max": jacobi_drift,
        "primary_center_distance_min_nd": primary_distance_min,
        "secondary_center_distance_min_nd": secondary_distance_min,
        "moon_surface_clearance_min_km": moon_clearance_km,
        "moon_body_intersection": moon_intersection,
        "physical_flight_status": (
            "moon_body_intersection_mathematical_cr3bp_only"
            if moon_intersection
            else "body_radius_clear_operational_altitude_not_assessed"
        ),
        "local_linearization_sample_count": local_sample_count,
        "local_linearization_max_relative_error": local_error_max,
        "local_linearization_gate": "pass" if local_gate else "fail",
        "numerical_acceptance": "pass" if numerical_gate else "fail",
    }


def analyze() -> tuple[list[dict[str, str]], dict[str, np.ndarray]]:
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None:
        raise RuntimeError("Earth-Moon length unit is required")
    protocol_hash = _sha256(PROTOCOL_PATH)
    moon_radius_source_hash = _sha256(MOON_RADIUS_SOURCE)
    rows: list[dict[str, str]] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "epsilon_grid": EPSILON_GRID,
        "branch_names": np.asarray(BRANCHES),
        "protocol_sha256": np.asarray([protocol_hash]),
        "moon_radius_km": np.asarray([MOON_RADIUS_KM], dtype=float),
        "moon_radius_source_sha256": np.asarray([moon_radius_source_hash]),
        "rtol": np.asarray([RTOL], dtype=float),
        "atol": np.asarray([ATOL], dtype=float),
        "max_step": np.asarray([MAX_STEP], dtype=float),
    }
    for family, config in FAMILY_CONFIG.items():
        payload = _load_family(family)
        propagated = _propagate_family(payload, system.mu)
        prefix = f"{family}_"
        arrays.update(
            {
                prefix + "source_npz_sha256": np.asarray(
                    [payload["source_npz_sha256"]]
                ),
                prefix + "source_states": payload["source_states"],
                prefix + "perturbation_directions": payload["directions"],
                prefix + "branch_signs": payload["branch_signs"],
                prefix + "phase_times_nd": payload["phase_times"],
                prefix + "history_times_nd": payload["history_times"],
                prefix + "snapshot_times_nd": payload["snapshot_times"],
                prefix + "evaluation_times_nd": payload["evaluation_times"],
                prefix + "base_history_states": payload["base_history_states"],
                prefix + "base_snapshot_states": payload["base_snapshot_states"],
                prefix + "scale_free_linear_history_norms": payload[
                    "scale_free_linear_history_norms"
                ],
                prefix + "history_states": propagated["history_states"],
                prefix + "snapshot_states": propagated["snapshot_states"],
                prefix + "nfev": propagated["nfev"],
            }
        )
        for epsilon_index, epsilon in enumerate(EPSILON_GRID):
            for branch_index, branch in enumerate(BRANCHES):
                figure_id = config["figures"][branch]
                for panel_index, elapsed in enumerate(payload["snapshot_times"]):
                    metrics = _panel_metrics(
                        payload=payload,
                        propagated=propagated,
                        epsilon_index=epsilon_index,
                        branch_index=branch_index,
                        panel_index=panel_index,
                        system=system,
                    )
                    values: dict[str, Any] = {
                        "schema_version": SCHEMA_VERSION,
                        "family": family,
                        "epsilon_index": epsilon_index,
                        "epsilon": epsilon,
                        "branch": branch,
                        "perturbation_sign": payload["branch_signs"][branch_index],
                        "figure_id": figure_id,
                        "panel_id": chr(ord("a") + panel_index),
                        "panel_index": panel_index,
                        "snapshot_time_nd": elapsed,
                        "snapshot_time_days": elapsed * system.time_unit_days,
                        "curve_samples": payload["source_states"].shape[0],
                        "phase_samples": payload["phase_times"].size,
                        "history_samples_through_panel": int(
                            np.searchsorted(
                                payload["history_times"], elapsed, side="right"
                            )
                        ),
                        "integration_method": "DOP853_independent_per_epsilon_sign",
                        "rtol": RTOL,
                        "atol": ATOL,
                        "max_step": MAX_STEP,
                        "nfev": propagated["nfev"][epsilon_index, branch_index],
                        "integration_success": True,
                        **metrics,
                        "jacobi_drift_limit": JACOBI_DRIFT_LIMIT,
                        "local_linearization_relative_error_limit": (
                            LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT
                        ),
                        "moon_radius_km": MOON_RADIUS_KM,
                        "moon_radius_source": _display(MOON_RADIUS_SOURCE),
                        "moon_radius_source_sha256": moon_radius_source_hash,
                        "earth_radius_status": "not_configured_not_needed_for_observed_range",
                        "epsilon_selection_status": "sensitivity_candidate_unselected",
                        "projection_metrics_status": "not_run_no_thesis_mask_read",
                        "paper_projection_acceptance": "not_run",
                        "paper_3d_equivalence": False,
                        "source_npz": _display(payload["source_npz"]),
                        "source_npz_sha256": payload["source_npz_sha256"],
                        "protocol": _display(PROTOCOL_PATH),
                        "protocol_sha256": protocol_hash,
                    }
                    rows.append({key: _fmt(value) for key, value in values.items()})
    return rows, arrays


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _render_doc(rows: list[dict[str, str]], npz_sha256: str) -> str:
    final_rows = [row for row in rows if row["panel_id"] == "d"]
    intersections = [row for row in rows if row["moon_body_intersection"] == "true"]
    numerical_failures = [row for row in rows if row["numerical_acceptance"] != "pass"]
    lines = [
        "# Chapter 4 epsilon state-space sensitivity audit",
        "",
        "Generated by `scripts/run_chapter4_epsilon_state_sensitivity_audit.py`.",
        "",
        "## Scope",
        "",
        "- The thesis reports only a small epsilon in Section 4.2; it does not",
        "  provide a numeric epsilon. This sweep therefore evaluates a pre-registered",
        "  sensitivity grid and does **not** select epsilon.",
        "- No thesis bitmap or red mask is read. In particular, registered panel (d)",
        "  remains unused by the camera/epsilon projection evaluator.",
        "- Each `(epsilon, sign)` ensemble is integrated separately with DOP853",
        f"  (`rtol={RTOL:.0e}`, `atol={ATOL:.0e}`, `max_step={MAX_STEP}`), avoiding",
        "  cross-candidate adaptive-error dilution.",
        "- The accepted fixed-time NPZ files supply source states, directions, base",
        "  states, time grids, and scale-free STM norms; their hashes are bound below.",
        "",
        "## Numerical and physical boundary",
        "",
        f"- Rows: `{len(rows)}`; numerical failures: `{len(numerical_failures)}`.",
        f"- Rows intersecting the configured Moon radius `{MOON_RADIUS_KM:.1f} km`: "
        f"`{len(intersections)}`.",
        "- A Moon-radius intersection does not invalidate the mathematical point-mass",
        "  CR3BP integration, but it forbids a physical-flight claim. Even a clear",
        "  radius is not an operational-altitude assessment.",
        "- Projection acceptance remains `not_run`; paper 3D equivalence remains",
        "  `false` for every candidate.",
        "",
        "## Final-panel sensitivity inventory",
        "",
        "| Family | Epsilon | Figure | Branch | x min | x max | Moon clearance [km] | J drift | local STM | physical status |",
        "|---|---:|---:|---|---:|---:|---:|---:|---|---|",
    ]
    for row in final_rows:
        lines.append(
            f"| {row['family']} | {float(row['epsilon']):.6e} | {row['figure_id']} | "
            f"{row['branch']} | {float(row['snapshot_x_min']):.6f} | "
            f"{float(row['snapshot_x_max']):.6f} | "
            f"{float(row['moon_surface_clearance_min_km']):.2f} | "
            f"{float(row['combined_jacobi_drift_max']):.3e} | "
            f"{row['local_linearization_gate']} | `{row['physical_flight_status']}` |"
        )
    lines.extend(
        [
            "",
            "## Traceability",
            "",
            f"- Protocol: `{_display(PROTOCOL_PATH)}` (SHA256 `{_sha256(PROTOCOL_PATH)}`).",
            f"- Moon radius source: `{_display(MOON_RADIUS_SOURCE)}` "
            f"(SHA256 `{_sha256(MOON_RADIUS_SOURCE)}`).",
        ]
    )
    for family, config in FAMILY_CONFIG.items():
        path = Path(config["source_npz"])
        lines.append(
            f"- {family} source: `{_display(path)}` (SHA256 `{_sha256(path)}`)."
        )
    lines.extend(
        [
            f"- Machine-readable rows: `{_display(CSV_PATH)}`.",
            f"- State arrays: `{_display(NPZ_PATH)}` (SHA256 `{npz_sha256}`).",
            "",
        ]
    )
    return "\n".join(lines)


def _verify_rows(rows: list[dict[str, str]]) -> None:
    expected = len(FAMILY_CONFIG) * EPSILON_GRID.size * len(BRANCHES) * 4
    if len(rows) != expected:
        raise RuntimeError(f"Expected {expected} rows; observed {len(rows)}")
    if not all(row["integration_success"] == "true" for row in rows):
        raise RuntimeError("A sensitivity integration failed")
    if not all(row["projection_metrics_status"] == "not_run_no_thesis_mask_read" for row in rows):
        raise RuntimeError("State-only audit escaped its projection boundary")
    if not all(row["paper_projection_acceptance"] == "not_run" for row in rows):
        raise RuntimeError("Projection acceptance must remain not_run")
    if not all(row["paper_3d_equivalence"] == "false" for row in rows):
        raise RuntimeError("State sensitivity cannot establish paper 3D equivalence")


def _compare_arrays(expected: dict[str, np.ndarray]) -> None:
    if not NPZ_PATH.is_file():
        raise RuntimeError("Stored epsilon sensitivity NPZ is missing")
    with np.load(NPZ_PATH, allow_pickle=False) as stored:
        if set(stored.files) != set(expected):
            raise RuntimeError("Stored epsilon sensitivity NPZ schema is stale")
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Reintegrate the sweep and verify all stored artifacts without rewriting.",
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
            raise RuntimeError("Stored epsilon sensitivity CSV is stale")
        expected_doc = _render_doc(checked_rows, npz_hash)
        if not DOC_PATH.is_file() or DOC_PATH.read_text(encoding="utf-8") != expected_doc:
            raise RuntimeError("Stored epsilon sensitivity report is stale")
        intersections = sum(row["moon_body_intersection"] == "true" for row in rows)
        print(
            "chapter4_epsilon_state_sensitivity_check: "
            f"rows={len(rows)}, moon_intersections={intersections}, "
            "projection=not_run"
        )
        return 0

    DATA.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ_PATH, **arrays)
    npz_hash = _sha256(NPZ_PATH)
    written_rows = [dict(row, evidence_npz_sha256=npz_hash) for row in rows]
    CSV_PATH.write_bytes(_csv_bytes(written_rows))
    DOCS.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(_render_doc(written_rows, npz_hash), encoding="utf-8")
    intersections = sum(row["moon_body_intersection"] == "true" for row in rows)
    print(f"wrote {_display(CSV_PATH)}")
    print(f"wrote {_display(NPZ_PATH)}")
    print(f"wrote {_display(DOC_PATH)}")
    print(
        "chapter4_epsilon_state_sensitivity: "
        f"rows={len(rows)}, moon_intersections={intersections}, projection=not_run"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
