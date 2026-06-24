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
