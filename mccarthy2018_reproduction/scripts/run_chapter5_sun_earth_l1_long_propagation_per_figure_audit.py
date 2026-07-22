"""Build and audit the Figure 5.1 active-geometry long-time trajectory.

The corrected two-frequency torus is an invariant parameterization rather than
an indefinitely stable floating-point initial-value trajectory.  A long-time
orbit on that torus is therefore reconstructed map interval by map interval:
each interval is propagated by the corrected CR3BP flow and the next interval
is phase-advanced by the accepted rotation number.  This is the standard
shadowing interpretation of the discrete invariant-torus equation.  It keeps
the three thesis durations tied to one initial phase without silently replacing
them by several unrelated torus curves.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
for search_path in (SRC, SCRIPTS):
    if str(search_path) not in sys.path:
        sys.path.insert(0, str(search_path))

from qp_orbits.artifact_fingerprints import artifact_fingerprint  # noqa: E402
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import jacobi_constant  # noqa: E402
from qp_orbits.libration_points import compute_libration_points  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _trigonometric_interpolation_matrix,
    resample_corrected_torus_surface,
    sweep_corrected_curve_correction,
)
from run_chapter5_active_geometry_stable_manifold_scan import (  # noqa: E402
    CHECKPOINT,
    SEED_SOURCE,
    _accepted_active_correction,
)


OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter5_sun_earth_l1_long_propagation_per_figure_audit.csv"
)
BUNDLE = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter5_sun_earth_l1_active_geometry_long_trajectory.npz"
)
DOC_OUTPUT = (
    PROJECT_ROOT
    / "docs"
    / "chapter5_sun_earth_l1_long_propagation_per_figure_audit.md"
)

DURATIONS_DAYS = (325.0, 1068.0, 2182.0)
TIME_SAMPLES_PER_MAP = 73
SURFACE_PHASE_SAMPLES = 97
INITIAL_PHASE_RAD = 0.0

CLOSURE_THRESHOLD_ND = 1.0e-7
SEAM_THRESHOLD_ND = 1.0e-7
JACOBI_SPAN_THRESHOLD = 5.0e-7
TRANSVERSE_SPAN_THRESHOLD = 2.0e-3
MAX_L1_DISTANCE_THRESHOLD_KM = 2.0e6
SAME_INITIAL_STATE_THRESHOLD_ND = 1.0e-12
DURATION_ERROR_THRESHOLD_DAYS = 1.0e-10

FIELDS = (
    "figure_id",
    "panel",
    "source_model",
    "reconstruction_method",
    "duration_days",
    "duration_error_days",
    "mapping_segments",
    "sample_count",
    "same_initial_state_error_nd",
    "max_seam_residual_nd",
    "closure_residual_nd",
    "x_min",
    "x_max",
    "y_span",
    "z_span",
    "transverse_span",
    "max_l1_distance_km",
    "jacobi_span",
    "source_checkpoint_sha256",
    "seed_source_sha256",
    "evidence_artifact",
    "acceptance",
    "threshold",
    "boundary",
    "notes",
)


def _fmt(value: Any) -> str:
    if isinstance(value, (bool, np.bool_)):
        return str(bool(value)).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return f"{number:.16g}" if np.isfinite(number) else str(number)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _artifact(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _duration_tag(duration_days: float) -> str:
    return f"{int(round(duration_days)):04d}_days"


def _states_at_local_times(member, local_times: np.ndarray) -> np.ndarray:
    """Interpolate the propagated native curve only in the map-time direction."""

    base_times = member.normalized_times
    result = np.empty((len(local_times), member.states.shape[1], 6), dtype=float)
    for index, value in enumerate(local_times):
        right = int(np.searchsorted(base_times, value, side="left"))
        if right == 0:
            result[index] = member.states[0]
        elif right == len(base_times):
            result[index] = member.states[-1]
        elif abs(base_times[right] - value) <= 2.0e-14:
            result[index] = member.states[right]
        else:
            left = right - 1
            weight = (value - base_times[left]) / (base_times[right] - base_times[left])
            result[index] = (1.0 - weight) * member.states[left] + weight * member.states[right]
    return result


def _reconstruct_trajectory(
    member,
    *,
    duration_days: float,
    time_unit_days: float,
    initial_phase_rad: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mapping_time = float(member.correction.mapping_time)
    rotation = float(member.correction.rotation_angle_rad)
    duration_nd = duration_days / time_unit_days
    elapsed_parts: list[np.ndarray] = []
    state_parts: list[np.ndarray] = []
    segment_parts: list[np.ndarray] = []
    seam_residuals: list[float] = []
    segment = 0
    previous_endpoint: np.ndarray | None = None

    while segment * mapping_time < duration_nd - 1.0e-14:
        segment_start = segment * mapping_time
        local_stop = min(mapping_time, duration_nd - segment_start)
        local_times = member.normalized_times[member.normalized_times <= local_stop + 2.0e-14]
        if local_times.size == 0 or abs(local_times[0]) > 2.0e-14:
            local_times = np.r_[0.0, local_times]
        if local_stop - local_times[-1] > 2.0e-14:
            local_times = np.r_[local_times, local_stop]
        else:
            local_times[-1] = local_stop

        native_states = _states_at_local_times(member, local_times)
        phase = (initial_phase_rad + segment * rotation) % (2.0 * np.pi)
        weights = _trigonometric_interpolation_matrix(
            member.correction.seed.phases,
            np.array([phase]),
        )[0]
        states = np.einsum("n,tnk->tk", weights, native_states)
        if previous_endpoint is not None:
            seam_residuals.append(float(np.linalg.norm(previous_endpoint - states[0])))
            local_times = local_times[1:]
            states = states[1:]
        if states.size:
            elapsed_parts.append((segment_start + local_times) * time_unit_days)
            state_parts.append(states)
            segment_parts.append(np.full(len(states), segment, dtype=int))
            previous_endpoint = states[-1]
        segment += 1

    elapsed_days = np.concatenate(elapsed_parts)
    states = np.concatenate(state_parts)
    segment_ids = np.concatenate(segment_parts)
    elapsed_days[-1] = duration_days
    return elapsed_days, states, segment_ids, np.asarray(seam_residuals, dtype=float)


def _build() -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    system = SYSTEMS["sun_earth"]
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Sun-Earth dimensional units are required")

    seed, correction = _accepted_active_correction(system)
    member = sweep_corrected_curve_correction(
        correction,
        time_samples=TIME_SAMPLES_PER_MAP,
        max_step=0.005,
    )
    surface, invariant_curve = resample_corrected_torus_surface(
        member,
        phase_samples=SURFACE_PHASE_SAMPLES,
    )
    surface_phases = np.linspace(0.0, 2.0 * np.pi, SURFACE_PHASE_SAMPLES, endpoint=True)
    checkpoint_hash = artifact_fingerprint(CHECKPOINT).sha256
    seed_hash = artifact_fingerprint(SEED_SOURCE).sha256
    closure_residual = float(member.closure_error_norms.max())
    l1_x = compute_libration_points(system.mu)["L1"].x
    l1 = np.array([l1_x, 0.0, 0.0], dtype=float)

    bundle: dict[str, np.ndarray] = {
        "figure_id": np.array("5.1"),
        "reconstruction_method": np.array(
            "segmentwise CR3BP invariant-torus shadowing with accepted phase rotation"
        ),
        "durations_days": np.asarray(DURATIONS_DAYS, dtype=float),
        "initial_phase_rad": np.array(INITIAL_PHASE_RAD),
        "mapping_time_nd": np.array(float(correction.mapping_time)),
        "mapping_time_days": np.array(float(correction.mapping_time) * system.time_unit_days),
        "rotation_angle_rad": np.array(float(correction.rotation_angle_rad)),
        "torus_surface_nd": surface,
        "invariant_curve_nd": invariant_curve,
        "surface_phase_rad": surface_phases,
        "source_checkpoint_sha256": np.array(checkpoint_hash),
        "seed_source_sha256": np.array(seed_hash),
        "closure_residual_nd": np.array(closure_residual),
        "torus_jacobi_span": np.array(float(member.jacobi_drift)),
    }
    trajectories: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []
    for duration in DURATIONS_DAYS:
        trajectory = _reconstruct_trajectory(
            member,
            duration_days=duration,
            time_unit_days=system.time_unit_days,
            initial_phase_rad=INITIAL_PHASE_RAD,
        )
        trajectories.append(trajectory)
        elapsed, states, segment_ids, seams = trajectory
        tag = _duration_tag(duration)
        bundle[f"elapsed_{tag}"] = elapsed
        bundle[f"trajectory_{tag}_states"] = states
        bundle[f"trajectory_{tag}_segment_id"] = segment_ids
        bundle[f"trajectory_{tag}_seam_residual_nd"] = seams

    reference_initial = trajectories[0][1][0]
    rows: list[dict[str, Any]] = []
    for panel_index, (duration, trajectory) in enumerate(zip(DURATIONS_DAYS, trajectories)):
        elapsed, states, segment_ids, seams = trajectory
        points = states[:, :3]
        y_span = float(np.ptp(points[:, 1]))
        z_span = float(np.ptp(points[:, 2]))
        transverse_span = float(np.hypot(y_span, z_span))
        max_l1_distance_km = float(
            np.linalg.norm(points - l1, axis=1).max() * system.length_unit_km
        )
        jacobi_span = float(np.ptp(jacobi_constant(states, system.mu)))
        seam_residual = float(seams.max()) if seams.size else 0.0
        same_initial_error = float(np.linalg.norm(states[0] - reference_initial))
        duration_error = abs(float(elapsed[-1]) - duration)
        accepted = (
            closure_residual <= CLOSURE_THRESHOLD_ND
            and seam_residual <= SEAM_THRESHOLD_ND
            and jacobi_span <= JACOBI_SPAN_THRESHOLD
            and transverse_span >= TRANSVERSE_SPAN_THRESHOLD
            and max_l1_distance_km <= MAX_L1_DISTANCE_THRESHOLD_KM
            and same_initial_error <= SAME_INITIAL_STATE_THRESHOLD_ND
            and duration_error <= DURATION_ERROR_THRESHOLD_DAYS
        )
        rows.append(
            {
                "figure_id": "5.1",
                "panel": chr(ord("a") + panel_index),
                "source_model": "accepted active-geometry Sun-Earth L1 CR3BP two-frequency torus",
                "reconstruction_method": "segmentwise invariant-torus shadowing with accepted phase rotation",
                "duration_days": duration,
                "duration_error_days": duration_error,
                "mapping_segments": int(segment_ids.max()) + 1,
                "sample_count": len(states),
                "same_initial_state_error_nd": same_initial_error,
                "max_seam_residual_nd": seam_residual,
                "closure_residual_nd": closure_residual,
                "x_min": float(points[:, 0].min()),
                "x_max": float(points[:, 0].max()),
                "y_span": y_span,
                "z_span": z_span,
                "transverse_span": transverse_span,
                "max_l1_distance_km": max_l1_distance_km,
                "jacobi_span": jacobi_span,
                "source_checkpoint_sha256": checkpoint_hash,
                "seed_source_sha256": seed_hash,
                "evidence_artifact": _artifact(BUNDLE),
                "acceptance": accepted,
                "threshold": (
                    f"closure <= {CLOSURE_THRESHOLD_ND}; seam <= {SEAM_THRESHOLD_ND}; "
                    f"Jacobi span <= {JACOBI_SPAN_THRESHOLD}; transverse span >= "
                    f"{TRANSVERSE_SPAN_THRESHOLD}; max L1 distance <= "
                    f"{MAX_L1_DISTANCE_THRESHOLD_KM} km; same initial state <= "
                    f"{SAME_INITIAL_STATE_THRESHOLD_ND}; duration error <= "
                    f"{DURATION_ERROR_THRESHOLD_DAYS} day"
                ),
                "boundary": (
                    "One invariant-torus shadowing trajectory reconstructed map interval by map interval; "
                    "this is not a claim of unconstrained 2182-day floating-point initial-value stability."
                ),
                "notes": "All three panels share one initial phase and differ only by truncation duration.",
            }
        )
    return bundle, rows


def _write_bundle(bundle: dict[str, np.ndarray]) -> None:
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(BUNDLE, **bundle)


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row[field]) for field in FIELDS})


def _write_doc(rows: list[dict[str, Any]]) -> None:
    table = [
        "| panel | duration days | map intervals | samples | seam residual | Jacobi span | same start error | accepted |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        table.append(
            f"| {row['panel']} | {_fmt(row['duration_days'])} | {row['mapping_segments']} | "
            f"{row['sample_count']} | {_fmt(row['max_seam_residual_nd'])} | "
            f"{_fmt(row['jacobi_span'])} | {_fmt(row['same_initial_state_error_nd'])} | "
            f"{_fmt(row['acceptance'])} |"
        )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 Figure 5.1 active-geometry long-time audit

Generated by `scripts/run_chapter5_sun_earth_l1_long_propagation_per_figure_audit.py`.

## Corrected semantics

The three panels use the same accepted active-geometry Sun-Earth L1 torus and
the same initial phase.  They show one invariant-torus trajectory truncated at
325, 1068, and 2182 days.  The trajectory is reconstructed map interval by map
interval using the corrected CR3BP flow and the accepted phase rotation.

## Evidence

- Numerical bundle: `{_artifact(BUNDLE)}`
- Source checkpoint: `{_artifact(CHECKPOINT)}`
- Source checkpoint SHA256: `{rows[0]['source_checkpoint_sha256']}`
- Seed source SHA256: `{rows[0]['seed_source_sha256']}`
- Corrected-torus closure residual: `{_fmt(rows[0]['closure_residual_nd'])}`
- Accepted panels: `{sum(bool(row['acceptance']) for row in rows)}` / `{len(rows)}`

## Rows

{chr(10).join(table)}

## Boundary

This construction is the numerical shadowing representation implied by the
discrete invariant-torus equation.  It is deliberately not described as an
unconstrained 2182-day initial-value propagation.  BCR4BP/ephemeris correction
and pointwise comparison against the thesis panels remain outside this gate.
The `{JACOBI_SPAN_THRESHOLD:.1e}` reconstruction tolerance records the finite
21-node Fourier phase discretization; the native swept torus Jacobi span is
stored separately in the NPZ bundle.
""",
        encoding="utf-8",
    )


def _check(bundle: dict[str, np.ndarray], rows: list[dict[str, Any]]) -> None:
    if not BUNDLE.exists() or not OUTPUT.exists() or not DOC_OUTPUT.exists():
        raise SystemExit("Figure 5.1 audit artifacts are missing")
    with np.load(BUNDLE) as saved:
        if set(saved.files) != set(bundle):
            raise SystemExit("Figure 5.1 bundle key drift")
        for key, expected in bundle.items():
            actual = saved[key]
            if np.issubdtype(expected.dtype, np.number):
                matches = np.allclose(actual, expected, rtol=0.0, atol=2.0e-13, equal_nan=True)
            else:
                matches = np.array_equal(actual, expected)
            if not matches:
                raise SystemExit(f"Figure 5.1 bundle drift: {key}")
    with OUTPUT.open(newline="", encoding="utf-8") as stream:
        saved_rows = list(csv.DictReader(stream))
    expected_rows = [{field: _fmt(row[field]) for field in FIELDS} for row in rows]
    if saved_rows != expected_rows:
        raise SystemExit("Figure 5.1 audit CSV drift")
    if not all(bool(row["acceptance"]) for row in rows):
        raise SystemExit("Figure 5.1 numerical acceptance failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    bundle, rows = _build()
    if args.check:
        _check(bundle, rows)
    else:
        _write_bundle(bundle)
        _write_rows(rows)
        _write_doc(rows)
    accepted = sum(bool(row["acceptance"]) for row in rows)
    print(
        "chapter5_fig51_active_geometry_long_time: "
        f"accepted={accepted}/{len(rows)}, max_duration={max(DURATIONS_DAYS):.0f} days, "
        f"max_seam={max(float(row['max_seam_residual_nd']) for row in rows):.6e}, "
        f"mode={'check' if args.check else 'write'}"
    )


if __name__ == "__main__":
    main()
