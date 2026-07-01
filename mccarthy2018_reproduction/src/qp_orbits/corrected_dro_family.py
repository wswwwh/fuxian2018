"""Stored and propagated corrected quasi-DRO family data."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .constants import CR3BPSystem
from .cr3bp import integrate_cr3bp, jacobi_constant
from .quasi_torus import (
    FreeRotationCurveCorrection,
    corrected_dro_fixed_mapping_family,
    corrected_dro_fixed_mapping_full_corrections,
)


@dataclass(frozen=True)
class CorrectedDROFamilyMember:
    """One corrected invariant curve in a fixed-mapping-time quasi-DRO family."""

    member: int
    curve_indices: np.ndarray
    phases_rad: np.ndarray
    states: np.ndarray
    jacobi_values: np.ndarray
    target_vertical_amplitude_nd: float
    target_vertical_amplitude_km: float
    max_abs_z_km: float
    rotation_angle_rad: float
    mapping_time_days: float
    map_residual_norm: float
    amplitude_residual: float
    phase_residual: float
    curve_jacobi_span: float

    @property
    def points(self) -> np.ndarray:
        return self.states[:, :3]

    @property
    def mean_jacobi(self) -> float:
        return float(np.mean(self.jacobi_values))


@dataclass(frozen=True)
class CorrectedDROTorusSweep:
    """CR3BP trajectories swept from every point on one invariant curve."""

    normalized_times: np.ndarray
    states: np.ndarray

    @property
    def points(self) -> np.ndarray:
        return self.states[:, :, :3]


@dataclass(frozen=True)
class CorrectedDROTrajectory:
    """Long CR3BP propagation launched from an interpolated invariant-curve phase."""

    phase_rad: float
    returns: int
    normalized_times: np.ndarray
    states: np.ndarray
    jacobi_span: float

    @property
    def points(self) -> np.ndarray:
        return self.states[:, :3]


_SCALAR_FIELDS = (
    "target_vertical_amplitude_nd",
    "target_vertical_amplitude_km",
    "max_abs_z_km",
    "rotation_angle_rad",
    "mapping_time_days",
    "map_residual_norm",
    "amplitude_residual",
    "phase_residual",
    "curve_jacobi_span",
)

CORRECTED_DRO_FAMILY_FIELDS = (
    "member",
    "curve_index",
    "phase_rad",
    "x",
    "y",
    "z",
    "xdot",
    "ydot",
    "zdot",
    "jacobi",
    "target_vertical_amplitude_nd",
    "target_vertical_amplitude_km",
    "max_abs_z_km",
    "rotation_angle_rad",
    "mapping_time_days",
    "map_residual_norm",
    "amplitude_residual",
    "phase_residual",
    "curve_jacobi_span",
)

CHAPTER3_QUASI_DRO_VALIDATION_FIELDS = (
    "member",
    "curve_samples",
    "rotation_angle_rad",
    "mapping_time_days",
    "target_vertical_amplitude_km",
    "max_abs_z_km",
    "mean_jacobi",
    "curve_jacobi_span",
    "map_residual_norm",
    "amplitude_residual",
    "phase_residual",
    "one_map_sweep_jacobi_drift",
    "one_map_sweep_max_state_norm",
    "one_map_phase_return_error",
    "ten_return_phase",
    "ten_return_jacobi_span",
    "ten_return_final_distance_from_initial",
    "validation_status",
    "next_action",
)

CHAPTER3_QUASI_DRO_CONTINUATION_LOG_FIELDS = (
    "attempt_id",
    "source_member",
    "target_max_abs_z_km",
    "target_amplitude_km",
    "curve_samples",
    "initial_step",
    "final_step",
    "converged",
    "rotation_angle_rad",
    "mapping_time_days",
    "max_abs_z_km",
    "mean_jacobi",
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_jacobi_drift",
    "phase_return_error",
    "newton_iterations",
    "condition_estimate",
    "failure_reason",
    "next_action",
)


def _validation_value(value: float | int | str | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    number = float(value)
    if not np.isfinite(number):
        return "N/A"
    return f"{number:.16g}"


def _constant_column(rows: list[dict[str, str]], field: str) -> float:
    values = np.asarray([float(row[field]) for row in rows], dtype=float)
    if not np.all(np.isfinite(values)) or not np.allclose(values, values[0], rtol=1e-11, atol=1e-13):
        raise ValueError(f"column {field!r} is not constant within one family member")
    return float(values[0])


def load_corrected_dro_family_csv(path: str | Path) -> tuple[CorrectedDROFamilyMember, ...]:
    """Load and validate the corrected fixed-time quasi-DRO family CSV."""

    source = Path(path)
    with source.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"no corrected quasi-DRO rows found in {source}")

    required = {
        "member",
        "curve_index",
        "phase_rad",
        "x",
        "y",
        "z",
        "xdot",
        "ydot",
        "zdot",
        "jacobi",
        *_SCALAR_FIELDS,
    }
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"missing corrected quasi-DRO columns: {sorted(missing)}")

    grouped: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(int(row["member"]), []).append(row)
    member_ids = sorted(grouped)
    if member_ids != list(range(len(member_ids))):
        raise ValueError(f"family member ids must be contiguous from zero, got {member_ids}")

    family: list[CorrectedDROFamilyMember] = []
    for member_id in member_ids:
        member_rows = sorted(grouped[member_id], key=lambda row: int(row["curve_index"]))
        indices = np.asarray([int(row["curve_index"]) for row in member_rows], dtype=int)
        if not np.array_equal(indices, np.arange(indices.size)):
            raise ValueError(f"member {member_id} curve indices are not contiguous from zero")
        phases = np.asarray([float(row["phase_rad"]) for row in member_rows], dtype=float)
        states = np.asarray(
            [
                [float(row[field]) for field in ("x", "y", "z", "xdot", "ydot", "zdot")]
                for row in member_rows
            ],
            dtype=float,
        )
        jacobi = np.asarray([float(row["jacobi"]) for row in member_rows], dtype=float)
        if not np.all(np.isfinite(phases)) or not np.all(np.diff(phases) > 0.0):
            raise ValueError(f"member {member_id} phases must be finite and strictly increasing")
        if not np.all(np.isfinite(states)) or not np.all(np.isfinite(jacobi)):
            raise ValueError(f"member {member_id} contains non-finite states or Jacobi constants")
        scalars = {field: _constant_column(member_rows, field) for field in _SCALAR_FIELDS}
        family.append(
            CorrectedDROFamilyMember(
                member=member_id,
                curve_indices=indices,
                phases_rad=phases,
                states=states,
                jacobi_values=jacobi,
                **scalars,
            )
        )

    rotations = np.asarray([member.rotation_angle_rad for member in family])
    amplitudes = np.asarray([member.target_vertical_amplitude_nd for member in family])
    mapping_times = np.asarray([member.mapping_time_days for member in family])
    if not np.all(np.diff(rotations) > 0.0) or not np.all(np.diff(amplitudes) > 0.0):
        raise ValueError("corrected quasi-DRO family rotation and amplitude must increase monotonically")
    if not np.allclose(mapping_times, mapping_times[0], rtol=1e-11, atol=1e-12):
        raise ValueError("corrected quasi-DRO family does not have a fixed mapping time")
    return tuple(family)


def write_corrected_dro_family_csv(
    path: str | Path,
    family: tuple[CorrectedDROFamilyMember, ...],
) -> None:
    """Write a corrected fixed-time quasi-DRO family without changing member data."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CORRECTED_DRO_FAMILY_FIELDS)
        writer.writeheader()
        for member in family:
            for curve_index, state in enumerate(member.states):
                writer.writerow(
                    {
                        "member": member.member,
                        "curve_index": curve_index,
                        "phase_rad": f"{member.phases_rad[curve_index]:.16g}",
                        "x": f"{state[0]:.16g}",
                        "y": f"{state[1]:.16g}",
                        "z": f"{state[2]:.16g}",
                        "xdot": f"{state[3]:.16g}",
                        "ydot": f"{state[4]:.16g}",
                        "zdot": f"{state[5]:.16g}",
                        "jacobi": f"{member.jacobi_values[curve_index]:.16g}",
                        "target_vertical_amplitude_nd": (
                            f"{member.target_vertical_amplitude_nd:.16g}"
                        ),
                        "target_vertical_amplitude_km": (
                            f"{member.target_vertical_amplitude_km:.16g}"
                        ),
                        "max_abs_z_km": f"{member.max_abs_z_km:.16g}",
                        "rotation_angle_rad": f"{member.rotation_angle_rad:.16g}",
                        "mapping_time_days": f"{member.mapping_time_days:.16g}",
                        "map_residual_norm": f"{member.map_residual_norm:.16g}",
                        "amplitude_residual": f"{member.amplitude_residual:.16g}",
                        "phase_residual": f"{member.phase_residual:.16g}",
                        "curve_jacobi_span": f"{member.curve_jacobi_span:.16g}",
                    }
                )


def _member_from_correction(
    member_id: int,
    correction: FreeRotationCurveCorrection,
    system: CR3BPSystem,
) -> CorrectedDROFamilyMember:
    length_unit = system.length_unit_km or 1.0
    time_unit = system.time_unit_days or 1.0
    jacobi = np.asarray(jacobi_constant(correction.corrected_states, system.mu), dtype=float)
    displacement = correction.corrected_states[:, 2] - correction.seed.orbit_state[2]
    vertical_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    return CorrectedDROFamilyMember(
        member=member_id,
        curve_indices=np.arange(correction.corrected_states.shape[0]),
        phases_rad=correction.seed.phases.copy(),
        states=correction.corrected_states.copy(),
        jacobi_values=jacobi,
        target_vertical_amplitude_nd=vertical_amplitude,
        target_vertical_amplitude_km=vertical_amplitude * length_unit,
        max_abs_z_km=float(np.max(np.abs(correction.corrected_states[:, 2])) * length_unit),
        rotation_angle_rad=correction.rotation_angle_rad,
        mapping_time_days=correction.seed.orbit_period * time_unit,
        map_residual_norm=float(np.max(correction.final_residual_norms)),
        amplitude_residual=float(correction.amplitude_residual_history[-1]),
        phase_residual=float(correction.phase_residual_history[-1]),
        curve_jacobi_span=float(np.ptp(jacobi)),
    )


def _correction_condition_estimate(correction: FreeRotationCurveCorrection) -> float | None:
    if correction.jacobian_condition_history.size == 0:
        return None
    return float(np.max(correction.jacobian_condition_history))


def _is_tight_fixed_mapping_correction(
    correction: FreeRotationCurveCorrection,
    system: CR3BPSystem,
    *,
    map_tolerance: float = 1.0e-8,
    jacobi_span_tolerance: float = 1.0e-8,
    constraint_tolerance: float = 1.0e-10,
) -> bool:
    jacobi_span = float(np.ptp(jacobi_constant(correction.corrected_states, system.mu)))
    return bool(
        correction.final_residual_norms.max() < map_tolerance
        and jacobi_span < jacobi_span_tolerance
        and abs(correction.amplitude_residual_history[-1]) < constraint_tolerance
        and abs(correction.phase_residual_history[-1]) < constraint_tolerance
    )


def _continuation_log_row(
    *,
    attempt_id: str,
    source_member: int | str,
    target_max_abs_z_km: float,
    target_amplitude_km: float,
    curve_samples: int,
    initial_step: float,
    final_step: float,
    correction: FreeRotationCurveCorrection | None,
    system: CR3BPSystem,
    converged: bool,
    failure_reason: str,
    next_action: str,
) -> dict[str, str]:
    one_map_jacobi_drift: float | None = None
    phase_return_error: float | None = None
    if correction is not None:
        provisional = _member_from_correction(-1, correction, system)
        try:
            row = chapter3_quasi_dro_validation_row(
                provisional,
                system,
                returns=1,
                one_map_time_samples=5,
                ten_return_samples=11,
            )
            one_map_jacobi_drift = (
                None
                if row["one_map_sweep_jacobi_drift"] == "N/A"
                else float(row["one_map_sweep_jacobi_drift"])
            )
            phase_return_error = (
                None
                if row["one_map_phase_return_error"] == "N/A"
                else float(row["one_map_phase_return_error"])
            )
        except (RuntimeError, ValueError, FloatingPointError):
            pass
        values: dict[str, float | int | str | None] = {
            "attempt_id": attempt_id,
            "source_member": source_member,
            "target_max_abs_z_km": target_max_abs_z_km,
            "target_amplitude_km": target_amplitude_km,
            "curve_samples": curve_samples,
            "initial_step": initial_step,
            "final_step": final_step,
            "converged": str(bool(converged)),
            "rotation_angle_rad": correction.rotation_angle_rad,
            "mapping_time_days": correction.seed.orbit_period * (system.time_unit_days or 1.0),
            "max_abs_z_km": provisional.max_abs_z_km,
            "mean_jacobi": provisional.mean_jacobi,
            "map_residual_norm": provisional.map_residual_norm,
            "curve_jacobi_span": provisional.curve_jacobi_span,
            "one_map_jacobi_drift": one_map_jacobi_drift,
            "phase_return_error": phase_return_error,
            "newton_iterations": int(correction.correction_norm_history.shape[0]),
            "condition_estimate": _correction_condition_estimate(correction),
            "failure_reason": failure_reason,
            "next_action": next_action,
        }
    else:
        values = {
            "attempt_id": attempt_id,
            "source_member": source_member,
            "target_max_abs_z_km": target_max_abs_z_km,
            "target_amplitude_km": target_amplitude_km,
            "curve_samples": curve_samples,
            "initial_step": initial_step,
            "final_step": final_step,
            "converged": str(bool(converged)),
            "rotation_angle_rad": None,
            "mapping_time_days": None,
            "max_abs_z_km": None,
            "mean_jacobi": None,
            "map_residual_norm": None,
            "curve_jacobi_span": None,
            "one_map_jacobi_drift": None,
            "phase_return_error": None,
            "newton_iterations": None,
            "condition_estimate": None,
            "failure_reason": failure_reason,
            "next_action": next_action,
        }
    return {
        field: _validation_value(values[field])
        for field in CHAPTER3_QUASI_DRO_CONTINUATION_LOG_FIELDS
    }


def write_chapter3_quasi_dro_continuation_log(
    path: str | Path,
    rows: tuple[dict[str, str], ...],
) -> None:
    """Write the quasi-DRO continuation attempt log."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=CHAPTER3_QUASI_DRO_CONTINUATION_LOG_FIELDS,
        )
        writer.writeheader()
        writer.writerows(rows)


def compute_chapter3_extended_corrected_dro_family(
    base_family: tuple[CorrectedDROFamilyMember, ...],
    system: CR3BPSystem,
    *,
    curve_samples: int = 41,
) -> tuple[tuple[CorrectedDROFamilyMember, ...], tuple[dict[str, str], ...]]:
    """Attempt a larger fixed-mapping-time quasi-DRO branch for Chapter 3.

    The original five `N=21` members are preserved, while new candidates are
    accepted only if they pass the same map residual, constraint, and Jacobi
    span thresholds used by the validation table.
    """

    if not base_family:
        raise ValueError("base_family must contain the audited local branch")
    length_unit = system.length_unit_km or 1.0
    time_unit = system.time_unit_days or 1.0
    x0 = 1.0 - system.mu - 73800.0 / length_unit
    base_amplitudes = tuple(member.target_vertical_amplitude_nd for member in base_family)
    stage_targets_km = (8500.0, 9000.0, 9500.0, 10000.0, 11000.0, 12000.0, 14000.0)
    target_amplitudes = tuple(value / length_unit for value in stage_targets_km)
    all_amplitudes = base_amplitudes + target_amplitudes
    corrections = corrected_dro_fixed_mapping_family(
        system.mu,
        x0=x0,
        vertical_amplitudes=all_amplitudes,
        samples=curve_samples,
        initial_half_period=14.75 / (2.0 * time_unit),
        max_iterations=32,
    )

    accepted: list[CorrectedDROFamilyMember] = [
        member for member in base_family
    ]
    log_rows: list[dict[str, str]] = []
    source_member = base_family[-1].member
    source_amplitude_km = base_family[-1].target_vertical_amplitude_km
    for offset, target_km in enumerate(stage_targets_km, start=len(base_family)):
        correction = corrections[offset]
        converged = _is_tight_fixed_mapping_correction(correction, system)
        attempt_source_member = source_member
        attempt_source_amplitude_km = source_amplitude_km
        stage = (
            "stage1" if target_km <= 12000.0 else
            "stage2" if target_km <= 18000.0 else
            "stage3" if target_km <= 25000.0 else
            "stage4"
        )
        if converged:
            new_member = _member_from_correction(len(accepted), correction, system)
            accepted.append(new_member)
            source_member = new_member.member
            source_amplitude_km = new_member.target_vertical_amplitude_km
            failure_reason = ""
            next_action = "accepted into extended corrected family"
        else:
            failure_reason = "failed residual/Jacobi audit thresholds"
            next_action = (
                "increase curve samples or switch to pseudo-arclength/rotation continuation"
            )
        log_rows.append(
            _continuation_log_row(
                attempt_id=f"{stage}_target_{int(target_km)}km_N{curve_samples}",
                source_member=attempt_source_member,
                target_max_abs_z_km=target_km,
                target_amplitude_km=target_km,
                curve_samples=curve_samples,
                initial_step=target_km - attempt_source_amplitude_km,
                final_step=target_km - attempt_source_amplitude_km,
                correction=correction,
                system=system,
                converged=converged,
                failure_reason=failure_reason,
                next_action=next_action,
            )
        )
        if not converged and target_km >= 14000.0:
            break

    for target_km, stage in ((20000.0, "stage3"), (31000.0, "stage4")):
        log_rows.append(
            _continuation_log_row(
                attempt_id=f"{stage}_skipped_after_stage2_failure",
                source_member=accepted[-1].member,
                target_max_abs_z_km=target_km,
                target_amplitude_km=target_km,
                curve_samples=curve_samples,
                initial_step=target_km - source_amplitude_km,
                final_step=0.0,
                correction=None,
                system=system,
                converged=False,
                failure_reason="skipped because Stage 2 lower-bound correction failed",
                next_action="resolve the 11,000-14,000 km bottleneck before Stage 3/4",
            )
        )
    return tuple(accepted), tuple(log_rows)


def load_or_compute_extended_corrected_dro_family(
    base_path: str | Path,
    extended_path: str | Path,
    log_path: str | Path,
    system: CR3BPSystem,
) -> tuple[CorrectedDROFamilyMember, ...]:
    """Load or compute the Chapter 3 extended quasi-DRO family and log."""

    extended = Path(extended_path)
    if extended.exists():
        return load_corrected_dro_family_csv(extended)
    base_family = load_or_compute_corrected_dro_family(base_path, system)
    family, log_rows = compute_chapter3_extended_corrected_dro_family(base_family, system)
    write_corrected_dro_family_csv(extended, family)
    write_chapter3_quasi_dro_continuation_log(log_path, log_rows)
    return family


def load_or_compute_corrected_dro_family(
    path: str | Path,
    system: CR3BPSystem,
) -> tuple[CorrectedDROFamilyMember, ...]:
    """Load validated data, or recompute the thesis-scale fixed-time family."""

    source = Path(path)
    if source.exists():
        return load_corrected_dro_family_csv(source)
    length_unit = system.length_unit_km or 1.0
    time_unit = system.time_unit_days or 1.0
    corrections = corrected_dro_fixed_mapping_full_corrections(
        system.mu,
        x0=1.0 - system.mu - 73800.0 / length_unit,
        initial_samples=21,
        initial_half_period=14.75 / (2.0 * time_unit),
    )
    return tuple(
        _member_from_correction(member_id, correction, system)
        for member_id, correction in enumerate(corrections)
    )


def sweep_corrected_dro_member(
    member: CorrectedDROFamilyMember,
    system: CR3BPSystem,
    *,
    time_samples: int = 25,
    max_step: float = 0.02,
) -> CorrectedDROTorusSweep:
    """Propagate every invariant-curve state through one fixed mapping time."""

    if time_samples < 2:
        raise ValueError("time_samples must be at least two")
    if system.time_unit_days is None:
        raise ValueError("system time_unit_days is required for a stored mapping time")
    mapping_time = member.mapping_time_days / system.time_unit_days
    times = np.linspace(0.0, mapping_time, time_samples)
    swept_states = np.empty((time_samples, member.states.shape[0], 6), dtype=float)
    for curve_index, initial_state in enumerate(member.states):
        solution = integrate_cr3bp(
            initial_state,
            (0.0, mapping_time),
            system.mu,
            t_eval=times,
            rtol=2e-10,
            atol=2e-12,
            max_step=max_step,
        )
        if not solution.success or solution.y.shape[1] != time_samples:
            raise RuntimeError(
                f"failed to sweep corrected quasi-DRO member {member.member}, curve point {curve_index}"
            )
        swept_states[:, curve_index] = solution.y.T
    return CorrectedDROTorusSweep(normalized_times=times, states=swept_states)


def interpolate_corrected_dro_state(
    member: CorrectedDROFamilyMember,
    phase_rad: float,
) -> np.ndarray:
    """Trigonometric interpolation of a state on an odd, uniform invariant curve."""

    count = member.phases_rad.size
    if count < 3 or count % 2 == 0:
        raise ValueError("corrected quasi-DRO interpolation requires an odd number of points")
    expected = np.arange(count, dtype=float) * (2.0 * np.pi / count)
    if not np.allclose(member.phases_rad, expected, rtol=0.0, atol=1.0e-11):
        raise ValueError("corrected quasi-DRO phases must be uniformly spaced from zero")

    wrapped_phase = float(np.mod(phase_rad, 2.0 * np.pi))
    differences = wrapped_phase - member.phases_rad
    harmonics = np.arange(1, (count - 1) // 2 + 1, dtype=float)
    weights = (
        1.0
        + 2.0 * np.sum(np.cos(differences[:, None] * harmonics[None, :]), axis=1)
    ) / count
    return np.asarray(weights @ member.states, dtype=float)


def propagate_corrected_dro_phase(
    member: CorrectedDROFamilyMember,
    system: CR3BPSystem,
    *,
    phase_rad: float,
    returns: int = 10,
    samples: int = 1100,
    max_step: float = 0.01,
) -> CorrectedDROTrajectory:
    """Propagate a corrected quasi-DRO phase through several stroboscopic returns."""

    if returns < 1:
        raise ValueError("returns must be positive")
    if samples < 2:
        raise ValueError("samples must be at least two")
    if system.time_unit_days is None:
        raise ValueError("system time_unit_days is required for a stored mapping time")

    initial_state = interpolate_corrected_dro_state(member, phase_rad)
    mapping_time = member.mapping_time_days / system.time_unit_days
    times = np.linspace(0.0, returns * mapping_time, samples)
    solution = integrate_cr3bp(
        initial_state,
        (0.0, times[-1]),
        system.mu,
        t_eval=times,
        rtol=2.0e-11,
        atol=2.0e-13,
        max_step=max_step,
    )
    if not solution.success or solution.y.shape[1] != samples:
        raise RuntimeError("failed to propagate the interpolated corrected quasi-DRO phase")
    states = solution.y.T
    jacobi_span = float(np.ptp(jacobi_constant(states, system.mu)))
    return CorrectedDROTrajectory(
        phase_rad=float(np.mod(phase_rad, 2.0 * np.pi)),
        returns=returns,
        normalized_times=times,
        states=states,
        jacobi_span=jacobi_span,
    )


def chapter3_quasi_dro_validation_row(
    member: CorrectedDROFamilyMember,
    system: CR3BPSystem,
    *,
    phase_rad: float = 0.0,
    returns: int = 10,
    one_map_time_samples: int = 7,
    ten_return_samples: int = 401,
    max_step: float = 0.02,
) -> dict[str, str]:
    """Audit one corrected quasi-DRO member for the Chapter 3 figure records."""

    one_map_jacobi_drift: float | None = None
    one_map_max_state_norm: float | None = None
    one_map_phase_return_error: float | None = None
    ten_return_phase: float | None = None
    ten_return_jacobi_span: float | None = None
    ten_return_final_distance: float | None = None

    try:
        sweep = sweep_corrected_dro_member(
            member,
            system,
            time_samples=one_map_time_samples,
            max_step=max_step,
        )
        sweep_states = sweep.states.reshape(-1, 6)
        one_map_jacobi_drift = float(np.ptp(jacobi_constant(sweep_states, system.mu)))
        one_map_max_state_norm = float(np.max(np.linalg.norm(sweep_states, axis=1)))
        target_state = interpolate_corrected_dro_state(
            member,
            phase_rad + member.rotation_angle_rad,
        )
        if np.isclose(np.mod(phase_rad, 2.0 * np.pi), 0.0, rtol=0.0, atol=1.0e-13):
            one_map_final_state = sweep.states[-1, 0]
        else:
            one_map_trajectory = propagate_corrected_dro_phase(
                member,
                system,
                phase_rad=phase_rad,
                returns=1,
                samples=2,
                max_step=max_step,
            )
            one_map_final_state = one_map_trajectory.states[-1]
        one_map_phase_return_error = float(np.linalg.norm(one_map_final_state - target_state))
    except (RuntimeError, ValueError, FloatingPointError):
        pass

    try:
        trajectory = propagate_corrected_dro_phase(
            member,
            system,
            phase_rad=phase_rad,
            returns=returns,
            samples=ten_return_samples,
            max_step=max_step,
        )
        ten_return_phase = float(
            np.mod(phase_rad + returns * member.rotation_angle_rad, 2.0 * np.pi)
        )
        ten_return_jacobi_span = trajectory.jacobi_span
        ten_return_final_distance = float(
            np.linalg.norm(trajectory.states[-1] - trajectory.states[0])
        )
    except (RuntimeError, ValueError, FloatingPointError):
        pass

    audited = all(
        value is not None
        for value in (
            one_map_jacobi_drift,
            one_map_max_state_norm,
            one_map_phase_return_error,
            ten_return_phase,
            ten_return_jacobi_span,
            ten_return_final_distance,
        )
    )
    numerically_tight = bool(
        audited
        and member.map_residual_norm < 1.0e-8
        and member.curve_jacobi_span < 1.0e-8
        and (one_map_jacobi_drift or 0.0) < 1.0e-8
        and (one_map_phase_return_error or 0.0) < 1.0e-8
        and (ten_return_jacobi_span or 0.0) < 1.0e-8
    )
    extended_member = member.max_abs_z_km > 8000.0
    validation_status = (
        ("validated extended CR3BP member" if extended_member else "validated local CR3BP member")
        if numerically_tight
        else "incomplete or failed member audit"
    )
    next_action = (
        (
            "Use as extended corrected branch; retain proxy reference until Stage 2 continuation succeeds"
            if extended_member
            else "Use as local corrected branch only; extend fixed-mapping continuation before replacing proxy trend"
        )
        if numerically_tight
        else "Re-run the corrected quasi-DRO propagation and inspect failed audit metric"
    )

    values: dict[str, float | int | str | None] = {
        "member": member.member,
        "curve_samples": int(member.states.shape[0]),
        "rotation_angle_rad": member.rotation_angle_rad,
        "mapping_time_days": member.mapping_time_days,
        "target_vertical_amplitude_km": member.target_vertical_amplitude_km,
        "max_abs_z_km": member.max_abs_z_km,
        "mean_jacobi": member.mean_jacobi,
        "curve_jacobi_span": member.curve_jacobi_span,
        "map_residual_norm": member.map_residual_norm,
        "amplitude_residual": member.amplitude_residual,
        "phase_residual": member.phase_residual,
        "one_map_sweep_jacobi_drift": one_map_jacobi_drift,
        "one_map_sweep_max_state_norm": one_map_max_state_norm,
        "one_map_phase_return_error": one_map_phase_return_error,
        "ten_return_phase": ten_return_phase,
        "ten_return_jacobi_span": ten_return_jacobi_span,
        "ten_return_final_distance_from_initial": ten_return_final_distance,
        "validation_status": validation_status,
        "next_action": next_action,
    }
    return {field: _validation_value(values[field]) for field in CHAPTER3_QUASI_DRO_VALIDATION_FIELDS}


def write_chapter3_quasi_dro_validation(
    path: str | Path,
    family: tuple[CorrectedDROFamilyMember, ...],
    system: CR3BPSystem,
    *,
    phase_rad: float = 0.0,
    returns: int = 10,
    one_map_time_samples: int = 7,
    ten_return_samples: int = 401,
    max_step: float = 0.02,
) -> tuple[dict[str, str], ...]:
    """Write the dedicated Chapter 3 quasi-DRO audit table."""

    rows = tuple(
        chapter3_quasi_dro_validation_row(
            member,
            system,
            phase_rad=phase_rad,
            returns=returns,
            one_map_time_samples=one_map_time_samples,
            ten_return_samples=ten_return_samples,
            max_step=max_step,
        )
        for member in family
    )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CHAPTER3_QUASI_DRO_VALIDATION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows
