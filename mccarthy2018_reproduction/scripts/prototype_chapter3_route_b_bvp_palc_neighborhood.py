"""Route B local BVP/PALC neighborhood diagnostics for quasi-DRO members.

This script is intentionally bounded. It compares BVP residual scaling and
solve conventions, reproduces accepted neighbors near the current endpoint, and
attempts only local pseudo-arclength diagnostic steps. It does not chase the
10,500 km or 11,000 km targets and does not modify accepted branch CSV files.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    CorrectedDROFamilyMember,
    load_corrected_dro_family_csv,
    propagate_corrected_dro_phase,
)
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    _jacobi_gradient,
    _stroboscopic_map_and_stms,
    _trigonometric_interpolation_derivative_matrix,
    _trigonometric_interpolation_matrix,
)


FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
VALIDATION_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_validation.csv"
ENDPOINT_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_endpoint_residual.csv"

SCALING_OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_scaling_experiments.csv"
NEIGHBOR_OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_neighbor_reproduction.csv"
PALC_OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_palc_neighborhood.csv"
SINGULAR_OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_singular_values.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_route_b_bvp_palc_neighborhood.md"

INTEGRATION_MAX_STEP = 0.02
TINY_FORWARD_FRACTION = 0.25
MAX_NEWTON_STEPS = 5
CORRECTION_NORM_CAP = 2.5e-3
AUDIT_TOLERANCE = 1.0e-8


SCALING_FIELDS = (
    "variant",
    "solve_convention",
    "residual_scaling",
    "column_scaling",
    "phase_condition",
    "active_residual_size",
    "unknown_size",
    "jacobian_shape",
    "rank_estimate",
    "condition_estimate",
    "min_singular_value",
    "max_singular_value",
    "endpoint_total_residual_norm",
    "endpoint_map_residual_max_norm",
    "endpoint_jacobi_residual",
    "endpoint_phase_residual",
    "curve_jacobi_span",
    "fourier_tail_energy_state",
    "fourier_tail_energy_z",
    "classification",
    "interpretation",
)

NEIGHBOR_FIELDS = (
    "member_id",
    "curve_samples",
    "max_abs_z_km",
    "mapping_time_days",
    "rho",
    "mean_jacobi",
    "total_residual_norm",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "mean_jacobi_residual",
    "phase_residual",
    "curve_jacobi_span",
    "fourier_tail_energy_state",
    "fourier_tail_energy_z",
    "jacobian_rank_estimate",
    "condition_estimate",
    "min_singular_value",
    "max_singular_value",
    "matches_existing_audit",
    "classification",
    "diagnosis",
)

PALC_FIELDS = (
    "case_id",
    "case_type",
    "source_members",
    "target_or_predicted_member",
    "step_size",
    "palc_constraint_residual",
    "converged",
    "accepted",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "rho",
    "delta_rho",
    "mean_jacobi",
    "delta_mean_jacobi",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "curve_jacobi_span",
    "phase_residual",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "fourier_tail_energy_state",
    "fourier_tail_energy_z",
    "condition_estimate",
    "min_singular_value",
    "max_correction_norm",
    "mean_correction_norm",
    "failure_reason",
    "classification",
    "diagnosis",
)

SINGULAR_FIELDS = (
    "case_id",
    "variant",
    "member_id",
    "singular_value_rank",
    "singular_value",
    "normalized_value",
    "component_diagnosis",
    "state_component_norm",
    "rho_component_norm",
    "jacobi_residual_sensitivity",
    "phase_residual_sensitivity",
    "interpretation",
)


@dataclass(frozen=True)
class BVPAssembly:
    """Experimental local BVP residual assembly for one invariant curve."""

    case_id: str
    member_id: int | None
    states: np.ndarray
    phases: np.ndarray
    rho: float
    mapping_time_days: float
    mapping_time_nd: float
    target_jacobi: float
    reference_states: np.ndarray
    mapped_states: np.ndarray
    target_states: np.ndarray
    map_residuals: np.ndarray
    map_residual_norms: np.ndarray
    jacobi_values: np.ndarray
    mean_jacobi_residual: float
    phase_residual: float
    second_phase_diagnostic: float
    palc_residual: float | None
    residual: np.ndarray
    jacobian: np.ndarray
    singular_values: np.ndarray
    vh: np.ndarray
    rank_estimate: int
    fourier_tail_state: float
    fourier_tail_z: float
    max_abs_z_km: float


@dataclass(frozen=True)
class PALCConstraint:
    predictor: np.ndarray
    tangent: np.ndarray


def _fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    number = float(value)
    if not np.isfinite(number):
        return "N/A"
    return f"{number:.16g}"


def _write_rows(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in fields})


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _read_endpoint_condition() -> float:
    rows = _read_csv_rows(ENDPOINT_PATH)
    if not rows:
        raise RuntimeError(f"missing endpoint residual row in {ENDPOINT_PATH}")
    return float(rows[0]["condition_estimate"])


def _phase_direction(phases: np.ndarray, reference: np.ndarray) -> np.ndarray:
    derivative = _trigonometric_interpolation_derivative_matrix(phases, phases) @ reference
    norm = float(np.linalg.norm(derivative))
    if norm <= 1.0e-14:
        raise RuntimeError("degenerate curve phase direction")
    return derivative / norm


def _second_phase_direction(phases: np.ndarray, reference: np.ndarray) -> np.ndarray:
    first = _trigonometric_interpolation_derivative_matrix(phases, phases) @ reference
    second = _trigonometric_interpolation_derivative_matrix(phases, phases) @ first
    norm = float(np.linalg.norm(second))
    if norm <= 1.0e-14:
        return np.zeros_like(second)
    return second / norm


def _fourier_tail_energy(values: np.ndarray, tail_fraction: float = 0.15) -> float:
    coefficients = np.fft.rfft(np.asarray(values, dtype=float), axis=0)
    energy = float(np.sum(np.abs(coefficients) ** 2))
    if energy <= 0.0:
        return 0.0
    tail_count = max(1, int(np.ceil(coefficients.shape[0] * tail_fraction)))
    return float(np.sum(np.abs(coefficients[-tail_count:]) ** 2) / energy)


def _rank_from_singular_values(singular_values: np.ndarray, shape: tuple[int, int]) -> int:
    if singular_values.size == 0:
        return 0
    tolerance = np.finfo(float).eps * max(shape) * float(singular_values[0])
    return int(np.sum(singular_values > tolerance))


def _condition(singular_values: np.ndarray) -> float:
    if singular_values.size == 0 or singular_values[-1] <= 0.0:
        return float("inf")
    return float(singular_values[0] / singular_values[-1])


def _classification(rank: int, shape: tuple[int, int], condition: float) -> str:
    if rank < shape[1]:
        return "rank_deficient"
    if condition < 1.0e9:
        return "full_column_rank_moderate"
    return "full_column_rank_ill_conditioned"


def _unknown_vector(states: np.ndarray, rho: float) -> np.ndarray:
    return np.concatenate([states.reshape(-1), np.array([rho], dtype=float)])


def _unpack_unknown(vector: np.ndarray, sample_count: int) -> tuple[np.ndarray, float]:
    state_size = 6 * sample_count
    return vector[:state_size].reshape(sample_count, 6), float(vector[state_size])


def _assemble_jacobian_blocks(
    *,
    states: np.ndarray,
    phases: np.ndarray,
    rho: float,
    stms: np.ndarray,
    reference_states: np.ndarray,
    mu: float,
    palc: PALCConstraint | None,
) -> tuple[np.ndarray, dict[str, int]]:
    sample_count = states.shape[0]
    state_size = states.size
    interpolation = _trigonometric_interpolation_matrix(phases, phases + rho)
    interpolation_derivative = _trigonometric_interpolation_derivative_matrix(phases, phases + rho)
    row_count = state_size + 3 + (1 if palc is not None else 0)
    jacobian = np.zeros((row_count, state_size + 1), dtype=float)

    for row in range(sample_count):
        row_slice = slice(6 * row, 6 * row + 6)
        for col in range(sample_count):
            col_slice = slice(6 * col, 6 * col + 6)
            block = -interpolation[row, col] * np.eye(6)
            if row == col:
                block = block + stms[row]
            jacobian[row_slice, col_slice] = block
    jacobian[:state_size, state_size] = -(interpolation_derivative @ states).reshape(-1)

    jacobi_row = state_size
    phase_row = state_size + 1
    second_phase_row = state_size + 2
    jacobian[jacobi_row, :state_size] = (_jacobi_gradient(states, mu) / sample_count).reshape(-1)
    jacobian[phase_row, :state_size] = _phase_direction(phases, reference_states).reshape(-1)
    jacobian[second_phase_row, :state_size] = _second_phase_direction(phases, reference_states).reshape(-1)
    rows = {
        "map_start": 0,
        "map_end": state_size,
        "jacobi": jacobi_row,
        "phase": phase_row,
        "second_phase": second_phase_row,
    }
    if palc is not None:
        palc_row = state_size + 3
        jacobian[palc_row, :] = palc.tangent
        rows["palc"] = palc_row
    return jacobian, rows


def _assemble_bvp(
    *,
    case_id: str,
    member_id: int | None,
    states: np.ndarray,
    phases: np.ndarray,
    rho: float,
    mapping_time_days: float,
    target_jacobi: float,
    reference_states: np.ndarray,
    system_name: str = "earth_moon",
    include_second_phase: bool = False,
    palc: PALCConstraint | None = None,
) -> BVPAssembly:
    system = SYSTEMS[system_name]
    time_unit = system.time_unit_days or 1.0
    length_unit = system.length_unit_km or 1.0
    mapping_time_nd = mapping_time_days / time_unit
    interpolation = _trigonometric_interpolation_matrix(phases, phases + rho)
    mapped, stms = _stroboscopic_map_and_stms(
        states,
        period=mapping_time_nd,
        mu=system.mu,
        max_step=INTEGRATION_MAX_STEP,
    )
    targets = interpolation @ states
    map_residuals = mapped - targets
    map_residual_norms = np.linalg.norm(map_residuals, axis=1)
    jacobi_values = np.asarray(jacobi_constant(states, system.mu), dtype=float)
    mean_jacobi_residual = float(np.mean(jacobi_values) - target_jacobi)
    delta = states - reference_states
    phase_residual = float(np.sum(delta * _phase_direction(phases, reference_states)))
    second_phase = float(np.sum(delta * _second_phase_direction(phases, reference_states)))
    palc_residual = None

    residual_parts = [
        map_residuals.reshape(-1),
        np.array([mean_jacobi_residual, phase_residual], dtype=float),
    ]
    if include_second_phase:
        residual_parts.append(np.array([second_phase], dtype=float))
    if palc is not None:
        vector = _unknown_vector(states, rho)
        palc_residual = float(np.dot(vector - palc.predictor, palc.tangent))
        residual_parts.append(np.array([palc_residual], dtype=float))
    residual = np.concatenate(residual_parts)

    full_jacobian, rows = _assemble_jacobian_blocks(
        states=states,
        phases=phases,
        rho=rho,
        stms=stms,
        reference_states=reference_states,
        mu=system.mu,
        palc=palc,
    )
    active_rows = list(range(rows["map_start"], rows["map_end"])) + [rows["jacobi"], rows["phase"]]
    if include_second_phase:
        active_rows.append(rows["second_phase"])
    if palc is not None:
        active_rows.append(rows["palc"])
    jacobian = full_jacobian[active_rows]
    u, singular_values, vh = np.linalg.svd(jacobian, full_matrices=False)
    del u
    return BVPAssembly(
        case_id=case_id,
        member_id=member_id,
        states=states.copy(),
        phases=phases.copy(),
        rho=float(rho),
        mapping_time_days=float(mapping_time_days),
        mapping_time_nd=float(mapping_time_nd),
        target_jacobi=float(target_jacobi),
        reference_states=reference_states.copy(),
        mapped_states=mapped,
        target_states=targets,
        map_residuals=map_residuals,
        map_residual_norms=map_residual_norms,
        jacobi_values=jacobi_values,
        mean_jacobi_residual=mean_jacobi_residual,
        phase_residual=phase_residual,
        second_phase_diagnostic=second_phase,
        palc_residual=palc_residual,
        residual=residual,
        jacobian=jacobian,
        singular_values=singular_values,
        vh=vh,
        rank_estimate=_rank_from_singular_values(singular_values, jacobian.shape),
        fourier_tail_state=_fourier_tail_energy(states),
        fourier_tail_z=_fourier_tail_energy(states[:, 2:3]),
        max_abs_z_km=float(np.max(np.abs(states[:, 2])) * length_unit),
    )


def _resample_states(states: np.ndarray, old_phases: np.ndarray, new_phases: np.ndarray) -> np.ndarray:
    return _trigonometric_interpolation_matrix(old_phases, new_phases) @ states


def _member_like(
    *,
    member_id: int,
    states: np.ndarray,
    phases: np.ndarray,
    rho: float,
    mapping_time_days: float,
    map_residual_norm: float,
    phase_residual: float,
) -> CorrectedDROFamilyMember:
    system = SYSTEMS["earth_moon"]
    length_unit = system.length_unit_km or 1.0
    jacobi_values = np.asarray(jacobi_constant(states, system.mu), dtype=float)
    z_amplitude = float(np.sqrt(2.0 * np.mean(states[:, 2] ** 2)))
    return CorrectedDROFamilyMember(
        member=member_id,
        curve_indices=np.arange(states.shape[0]),
        phases_rad=phases.copy(),
        states=states.copy(),
        jacobi_values=jacobi_values,
        target_vertical_amplitude_nd=z_amplitude,
        target_vertical_amplitude_km=z_amplitude * length_unit,
        max_abs_z_km=float(np.max(np.abs(states[:, 2])) * length_unit),
        rotation_angle_rad=float(rho),
        mapping_time_days=float(mapping_time_days),
        map_residual_norm=float(map_residual_norm),
        amplitude_residual=0.0,
        phase_residual=float(phase_residual),
        curve_jacobi_span=float(np.ptp(jacobi_values)),
    )


def _scaled_svd(
    jacobian: np.ndarray,
    *,
    residual_scaling: str,
    column_scaling: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str, str]:
    scaled = jacobian.copy()
    residual_note = "none"
    column_note = "none"
    if residual_scaling == "row_equilibrated":
        row_norms = np.linalg.norm(scaled, axis=1)
        row_scale = 1.0 / np.maximum(row_norms, 1.0e-14)
        scaled = row_scale[:, None] * scaled
        residual_note = "row_norm_equilibration"
    if column_scaling == "column_equilibrated":
        column_norms = np.linalg.norm(scaled, axis=0)
        column_scale = 1.0 / np.maximum(column_norms, 1.0e-14)
        scaled = scaled * column_scale[None, :]
        column_note = "state_and_rho_column_norm_equilibration"
    u, singular_values, vh = np.linalg.svd(scaled, full_matrices=False)
    del u
    return scaled, singular_values, vh, residual_note, column_note


def _scaling_rows(endpoint: CorrectedDROFamilyMember) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    base = _assemble_bvp(
        case_id="endpoint_unscaled_base",
        member_id=endpoint.member,
        states=endpoint.states,
        phases=endpoint.phases_rad,
        rho=endpoint.rotation_angle_rad,
        mapping_time_days=endpoint.mapping_time_days,
        target_jacobi=endpoint.mean_jacobi,
        reference_states=endpoint.states,
    )
    second = _assemble_bvp(
        case_id="endpoint_two_phase_base",
        member_id=endpoint.member,
        states=endpoint.states,
        phases=endpoint.phases_rad,
        rho=endpoint.rotation_angle_rad,
        mapping_time_days=endpoint.mapping_time_days,
        target_jacobi=endpoint.mean_jacobi,
        reference_states=endpoint.states,
        include_second_phase=True,
    )
    square_jacobian = np.vstack([base.jacobian[: endpoint.states.size], base.jacobian[endpoint.states.size + 1]])
    square_residual = np.concatenate([base.map_residuals.reshape(-1), np.array([base.phase_residual])])
    square_u, square_s, square_vh = np.linalg.svd(square_jacobian, full_matrices=False)
    del square_u

    variants = [
        (
            "unscaled_overdetermined",
            "least_squares_overdetermined",
            base.jacobian,
            base.residual,
            base.singular_values,
            base.vh,
            "none",
            "none",
            "curve_tangent",
            "baseline overdetermined endpoint linearization",
        ),
        (
            "residual_scaled_overdetermined",
            "least_squares_overdetermined",
            base.jacobian,
            base.residual,
            None,
            None,
            "row_equilibrated",
            "none",
            "curve_tangent",
            "row scaling improves numerical balancing but changes the displayed spectrum",
        ),
        (
            "column_scaled_overdetermined",
            "least_squares_overdetermined",
            base.jacobian,
            base.residual,
            None,
            None,
            "none",
            "column_equilibrated",
            "curve_tangent",
            "column scaling tests whether state/rho units dominate conditioning",
        ),
        (
            "residual_and_column_scaled",
            "least_squares_overdetermined",
            base.jacobian,
            base.residual,
            None,
            None,
            "row_equilibrated",
            "column_equilibrated",
            "curve_tangent",
            "combined row/column equilibration for the diagnostic solve convention",
        ),
        (
            "two_phase_overdetermined",
            "least_squares_overdetermined",
            second.jacobian,
            second.residual,
            second.singular_values,
            second.vh,
            "none",
            "none",
            "curve_tangent_plus_second_phase",
            "adding the second phase as an active residual increases overdetermination",
        ),
        (
            "square_reduced_convention",
            "square_map_plus_phase",
            square_jacobian,
            square_residual,
            square_s,
            square_vh,
            "none",
            "none",
            "curve_tangent_without_mean_jacobi",
            "feasible square diagnostic drops the mean-Jacobi row, so Jacobi is diagnostic only",
        ),
    ]

    rows: list[dict[str, Any]] = []
    singular_rows: list[dict[str, Any]] = []
    for (
        variant,
        solve_convention,
        jacobian,
        residual,
        singular_values,
        vh,
        residual_scaling,
        column_scaling,
        phase_condition,
        interpretation,
    ) in variants:
        residual_note = residual_scaling
        column_note = column_scaling
        if singular_values is None or vh is None:
            _, singular_values, vh, residual_note, column_note = _scaled_svd(
                jacobian,
                residual_scaling=residual_scaling,
                column_scaling=column_scaling,
            )
        rank = _rank_from_singular_values(singular_values, jacobian.shape)
        cond = _condition(singular_values)
        rows.append(
            {
                "variant": variant,
                "solve_convention": solve_convention,
                "residual_scaling": residual_note,
                "column_scaling": column_note,
                "phase_condition": phase_condition,
                "active_residual_size": jacobian.shape[0],
                "unknown_size": jacobian.shape[1],
                "jacobian_shape": f"{jacobian.shape[0]}x{jacobian.shape[1]}",
                "rank_estimate": rank,
                "condition_estimate": cond,
                "min_singular_value": float(singular_values[-1]),
                "max_singular_value": float(singular_values[0]),
                "endpoint_total_residual_norm": float(np.linalg.norm(residual)),
                "endpoint_map_residual_max_norm": float(np.max(base.map_residual_norms)),
                "endpoint_jacobi_residual": base.mean_jacobi_residual,
                "endpoint_phase_residual": base.phase_residual,
                "curve_jacobi_span": float(np.ptp(base.jacobi_values)),
                "fourier_tail_energy_state": base.fourier_tail_state,
                "fourier_tail_energy_z": base.fourier_tail_z,
                "classification": _classification(rank, jacobian.shape, cond),
                "interpretation": interpretation,
            }
        )
        singular_rows.extend(
            _singular_rows(
                case_id=f"scaling_{variant}",
                variant=variant,
                member_id=endpoint.member,
                jacobian=jacobian,
                singular_values=singular_values,
                vh=vh,
                sample_count=endpoint.states.shape[0],
                interpretation=interpretation,
            )
        )
    return rows, singular_rows


def _singular_rows(
    *,
    case_id: str,
    variant: str,
    member_id: int | None,
    jacobian: np.ndarray,
    singular_values: np.ndarray,
    vh: np.ndarray,
    sample_count: int,
    interpretation: str,
) -> list[dict[str, Any]]:
    normalized = singular_values / singular_values[0] if singular_values.size else singular_values
    min_index = singular_values.size - 1
    rows: list[dict[str, Any]] = []
    state_size = 6 * sample_count
    for idx, value in enumerate(singular_values):
        row: dict[str, Any] = {
            "case_id": case_id,
            "variant": variant,
            "member_id": member_id,
            "singular_value_rank": idx + 1,
            "singular_value": float(value),
            "normalized_value": float(normalized[idx]),
            "component_diagnosis": "",
            "state_component_norm": None,
            "rho_component_norm": None,
            "jacobi_residual_sensitivity": None,
            "phase_residual_sensitivity": None,
            "interpretation": interpretation,
        }
        if idx == min_index and vh.size:
            vector = vh[-1]
            state_vector = vector[:state_size]
            rho_component = float(abs(vector[-1]))
            state_component = float(np.linalg.norm(state_vector))
            high_mode_tail = _fourier_tail_energy(state_vector.reshape(sample_count, 6))
            jacobi_row = state_size if jacobian.shape[0] > state_size else None
            phase_row = state_size + 1 if jacobian.shape[0] > state_size + 1 else None
            jacobi_sensitivity = (
                float(abs(jacobian[jacobi_row] @ vector)) if jacobi_row is not None else None
            )
            phase_sensitivity = (
                float(abs(jacobian[phase_row] @ vector)) if phase_row is not None else None
            )
            if rho_component > 0.5 * max(state_component, 1.0e-14):
                diagnosis = "rho_column_coupled"
            elif high_mode_tail > 0.25:
                diagnosis = "high_fourier_mode_state_component"
            else:
                diagnosis = "distributed_state_component"
            row.update(
                {
                    "component_diagnosis": diagnosis,
                    "state_component_norm": state_component,
                    "rho_component_norm": rho_component,
                    "jacobi_residual_sensitivity": jacobi_sensitivity,
                    "phase_residual_sensitivity": phase_sensitivity,
                }
            )
        rows.append(row)
    return rows


def _select_neighbors(family: tuple[CorrectedDROFamilyMember, ...]) -> tuple[CorrectedDROFamilyMember, ...]:
    by_id = {member.member: member for member in family}
    preferred = [by_id[idx] for idx in (7, 8, 9, 10) if idx in by_id]
    if len(preferred) >= 3:
        return tuple(preferred)
    return tuple(family[-4:])


def _neighbor_rows(
    family: tuple[CorrectedDROFamilyMember, ...],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, BVPAssembly]]:
    rows: list[dict[str, Any]] = []
    singular_rows: list[dict[str, Any]] = []
    assemblies: dict[int, BVPAssembly] = {}
    for member in _select_neighbors(family):
        assembly = _assemble_bvp(
            case_id=f"neighbor_member_{member.member}",
            member_id=member.member,
            states=member.states,
            phases=member.phases_rad,
            rho=member.rotation_angle_rad,
            mapping_time_days=member.mapping_time_days,
            target_jacobi=member.mean_jacobi,
            reference_states=member.states,
        )
        assemblies[member.member] = assembly
        condition = _condition(assembly.singular_values)
        classification = _classification(assembly.rank_estimate, assembly.jacobian.shape, condition)
        map_max = float(np.max(assembly.map_residual_norms))
        jacobi_span = float(np.ptp(assembly.jacobi_values))
        matches = bool(
            map_max <= max(10.0 * member.map_residual_norm, 1.0e-12)
            and jacobi_span <= max(10.0 * member.curve_jacobi_span, 1.0e-12)
        )
        peak_index = int(np.argmax(assembly.map_residual_norms))
        rows.append(
            {
                "member_id": member.member,
                "curve_samples": member.states.shape[0],
                "max_abs_z_km": member.max_abs_z_km,
                "mapping_time_days": member.mapping_time_days,
                "rho": member.rotation_angle_rad,
                "mean_jacobi": float(np.mean(assembly.jacobi_values)),
                "total_residual_norm": float(np.linalg.norm(assembly.residual)),
                "map_residual_max_norm": map_max,
                "map_residual_rms_norm": float(np.sqrt(np.mean(assembly.map_residual_norms**2))),
                "mean_jacobi_residual": assembly.mean_jacobi_residual,
                "phase_residual": assembly.phase_residual,
                "curve_jacobi_span": jacobi_span,
                "fourier_tail_energy_state": assembly.fourier_tail_state,
                "fourier_tail_energy_z": assembly.fourier_tail_z,
                "jacobian_rank_estimate": assembly.rank_estimate,
                "condition_estimate": condition,
                "min_singular_value": float(assembly.singular_values[-1]),
                "max_singular_value": float(assembly.singular_values[0]),
                "matches_existing_audit": matches,
                "classification": classification,
                "diagnosis": (
                    f"peak_index={peak_index}; peak_phase={member.phases_rad[peak_index]:.6g}; "
                    f"conditioning={classification}"
                ),
            }
        )
        singular_rows.extend(
            _singular_rows(
                case_id=f"neighbor_member_{member.member}",
                variant="neighbor_reproduction",
                member_id=member.member,
                jacobian=assembly.jacobian,
                singular_values=assembly.singular_values,
                vh=assembly.vh,
                sample_count=member.states.shape[0],
                interpretation="accepted-neighbor endpoint-style BVP reproduction",
            )
        )
    return rows, singular_rows, assemblies


def _solve_scaled_correction(jacobian: np.ndarray, residual: np.ndarray) -> np.ndarray:
    row_norms = np.linalg.norm(jacobian, axis=1)
    row_scale = 1.0 / np.maximum(row_norms, 1.0e-14)
    row_scaled_jacobian = row_scale[:, None] * jacobian
    row_scaled_residual = row_scale * residual
    column_norms = np.linalg.norm(row_scaled_jacobian, axis=0)
    column_scale = 1.0 / np.maximum(column_norms, 1.0e-14)
    scaled_jacobian = row_scaled_jacobian * column_scale[None, :]
    correction_scaled, *_ = np.linalg.lstsq(scaled_jacobian, -row_scaled_residual, rcond=None)
    return column_scale * correction_scaled


def _palc_correct(
    *,
    case_id: str,
    member_id: int | None,
    predictor: np.ndarray,
    tangent: np.ndarray,
    phases: np.ndarray,
    mapping_time_days: float,
    target_jacobi: float,
    reference_states: np.ndarray,
    endpoint_condition: float,
) -> tuple[BVPAssembly, list[float], bool, str]:
    sample_count = phases.size
    vector = predictor.copy()
    tangent = tangent / max(float(np.linalg.norm(tangent)), 1.0e-14)
    palc = PALCConstraint(predictor=predictor.copy(), tangent=tangent.copy())
    correction_norms: list[float] = []
    failure_reason = "maximum iterations reached"
    converged = False
    assembly: BVPAssembly | None = None
    for _ in range(MAX_NEWTON_STEPS):
        states, rho = _unpack_unknown(vector, sample_count)
        assembly = _assemble_bvp(
            case_id=case_id,
            member_id=member_id,
            states=states,
            phases=phases,
            rho=rho,
            mapping_time_days=mapping_time_days,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            palc=palc,
        )
        condition = _condition(assembly.singular_values)
        if condition > 100.0 * endpoint_condition:
            failure_reason = "condition estimate exceeded 100x endpoint prototype"
            break
        map_max = float(np.max(assembly.map_residual_norms))
        if (
            map_max < AUDIT_TOLERANCE
            and abs(assembly.mean_jacobi_residual) < AUDIT_TOLERANCE
            and abs(assembly.phase_residual) < AUDIT_TOLERANCE
            and abs(assembly.palc_residual or 0.0) < AUDIT_TOLERANCE
        ):
            converged = True
            failure_reason = ""
            break
        correction = _solve_scaled_correction(assembly.jacobian, assembly.residual)
        correction_norm = float(np.linalg.norm(correction))
        if correction_norm > CORRECTION_NORM_CAP:
            correction *= CORRECTION_NORM_CAP / correction_norm
            correction_norm = CORRECTION_NORM_CAP
        correction_norms.append(correction_norm)
        vector += correction
    if assembly is None:
        states, rho = _unpack_unknown(vector, sample_count)
        assembly = _assemble_bvp(
            case_id=case_id,
            member_id=member_id,
            states=states,
            phases=phases,
            rho=rho,
            mapping_time_days=mapping_time_days,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            palc=palc,
        )
    return assembly, correction_norms, converged, failure_reason


def _ten_return_jacobi_span(assembly: BVPAssembly) -> float | None:
    try:
        member = _member_like(
            member_id=-1,
            states=assembly.states,
            phases=assembly.phases,
            rho=assembly.rho,
            mapping_time_days=assembly.mapping_time_days,
            map_residual_norm=float(np.max(assembly.map_residual_norms)),
            phase_residual=assembly.phase_residual,
        )
        trajectory = propagate_corrected_dro_phase(
            member,
            SYSTEMS["earth_moon"],
            phase_rad=0.0,
            returns=10,
            samples=121,
            max_step=INTEGRATION_MAX_STEP,
        )
        return trajectory.jacobi_span
    except (RuntimeError, ValueError, FloatingPointError):
        return None


def _palc_case(
    *,
    case_id: str,
    case_type: str,
    previous: CorrectedDROFamilyMember,
    current: CorrectedDROFamilyMember,
    target: CorrectedDROFamilyMember | None,
    endpoint_condition: float,
    fraction: float = 1.0,
) -> tuple[dict[str, Any], list[dict[str, Any]], BVPAssembly]:
    if target is not None:
        phases = target.phases_rad
        previous_states = _resample_states(previous.states, previous.phases_rad, phases)
        current_states = _resample_states(current.states, current.phases_rad, phases)
        target_member_label = str(target.member)
    else:
        phases = current.phases_rad
        previous_states = _resample_states(previous.states, previous.phases_rad, phases)
        current_states = current.states
        target_member_label = "predicted_forward"

    secant_states = current_states - previous_states
    secant_rho = current.rotation_angle_rad - previous.rotation_angle_rad
    secant_jacobi = current.mean_jacobi - previous.mean_jacobi
    predictor_states = current_states + fraction * secant_states
    predictor_rho = current.rotation_angle_rad + fraction * secant_rho
    target_jacobi = current.mean_jacobi + fraction * secant_jacobi
    current_vector = _unknown_vector(current_states, current.rotation_angle_rad)
    predictor = _unknown_vector(predictor_states, predictor_rho)
    tangent = predictor - current_vector
    step_size = float(np.linalg.norm(tangent))
    if step_size <= 1.0e-14:
        raise RuntimeError(f"{case_id} has a degenerate PALC tangent")

    assembly, correction_norms, converged, failure_reason = _palc_correct(
        case_id=case_id,
        member_id=None,
        predictor=predictor,
        tangent=tangent,
        phases=phases,
        mapping_time_days=current.mapping_time_days,
        target_jacobi=target_jacobi,
        reference_states=current_states,
        endpoint_condition=endpoint_condition,
    )
    condition = _condition(assembly.singular_values)
    classification = _classification(assembly.rank_estimate, assembly.jacobian.shape, condition)
    map_max = float(np.max(assembly.map_residual_norms))
    jacobi_span = float(np.ptp(assembly.jacobi_values))
    one_map_phase_return_error = float(assembly.map_residual_norms[0])
    ten_return_jacobi_span = _ten_return_jacobi_span(assembly)
    endpoint_tail_limit = 1.0e-12
    accepted = bool(
        converged
        and map_max < AUDIT_TOLERANCE
        and jacobi_span < AUDIT_TOLERANCE
        and abs(assembly.phase_residual) < AUDIT_TOLERANCE
        and assembly.fourier_tail_state < endpoint_tail_limit
        and condition <= 100.0 * endpoint_condition
    )
    if not accepted and not failure_reason:
        failure_reason = "failed residual/Jacobi/phase/tail audit gates"
    delta_z = assembly.max_abs_z_km - current.max_abs_z_km
    delta_rho = assembly.rho - current.rotation_angle_rad
    delta_jacobi = float(np.mean(assembly.jacobi_values) - current.mean_jacobi)
    if target is not None:
        target_states = _resample_states(target.states, target.phases_rad, phases)
        target_error = float(
            np.sqrt(np.mean((assembly.states - target_states) ** 2))
            + abs(assembly.rho - target.rotation_angle_rad)
        )
        diagnosis = f"target_rms_plus_rho_error={target_error:.6g}; conditioning={classification}"
    else:
        diagnosis = f"bounded tiny forward diagnostic; conditioning={classification}"
    row = {
        "case_id": case_id,
        "case_type": case_type,
        "source_members": f"{previous.member},{current.member}",
        "target_or_predicted_member": target_member_label,
        "step_size": step_size,
        "palc_constraint_residual": assembly.palc_residual,
        "converged": converged,
        "accepted": accepted,
        "max_abs_z_km": assembly.max_abs_z_km,
        "delta_max_abs_z_km": delta_z,
        "rho": assembly.rho,
        "delta_rho": delta_rho,
        "mean_jacobi": float(np.mean(assembly.jacobi_values)),
        "delta_mean_jacobi": delta_jacobi,
        "map_residual_max_norm": map_max,
        "map_residual_rms_norm": float(np.sqrt(np.mean(assembly.map_residual_norms**2))),
        "curve_jacobi_span": jacobi_span,
        "phase_residual": assembly.phase_residual,
        "one_map_phase_return_error": one_map_phase_return_error,
        "ten_return_jacobi_span": ten_return_jacobi_span,
        "fourier_tail_energy_state": assembly.fourier_tail_state,
        "fourier_tail_energy_z": assembly.fourier_tail_z,
        "condition_estimate": condition,
        "min_singular_value": float(assembly.singular_values[-1]),
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
        "mean_correction_norm": float(np.mean(correction_norms)) if correction_norms else 0.0,
        "failure_reason": failure_reason,
        "classification": classification,
        "diagnosis": diagnosis,
    }
    singular_rows = _singular_rows(
        case_id=case_id,
        variant="palc_neighborhood",
        member_id=None,
        jacobian=assembly.jacobian,
        singular_values=assembly.singular_values,
        vh=assembly.vh,
        sample_count=assembly.states.shape[0],
        interpretation=diagnosis,
    )
    return row, singular_rows, assembly


def _palc_rows(
    family: tuple[CorrectedDROFamilyMember, ...],
    endpoint_condition: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {member.member: member for member in family}
    rows: list[dict[str, Any]] = []
    singular_rows: list[dict[str, Any]] = []
    cases = [
        ("reproduce_known_neighbor_8_to_9", "known_neighbor_reproduction", 7, 8, 9, 1.0),
        ("reproduce_known_neighbor_9_to_10", "known_neighbor_reproduction", 8, 9, 10, 1.0),
        ("tiny_forward_from_10_step_1", "tiny_forward_diagnostic", 9, 10, None, TINY_FORWARD_FRACTION),
    ]
    for case_id, case_type, prev_id, curr_id, target_id, fraction in cases:
        if prev_id not in by_id or curr_id not in by_id or (target_id is not None and target_id not in by_id):
            rows.append(
                {
                    "case_id": case_id,
                    "case_type": case_type,
                    "source_members": f"{prev_id},{curr_id}",
                    "target_or_predicted_member": target_id,
                    "converged": False,
                    "accepted": False,
                    "failure_reason": "required source or target member missing",
                    "classification": "not_attempted",
                    "diagnosis": "case skipped before correction",
                }
            )
            continue
        row, case_singular_rows, assembly = _palc_case(
            case_id=case_id,
            case_type=case_type,
            previous=by_id[prev_id],
            current=by_id[curr_id],
            target=by_id[target_id] if target_id is not None else None,
            endpoint_condition=endpoint_condition,
            fraction=fraction,
        )
        rows.append(row)
        singular_rows.extend(case_singular_rows)
        if case_id.startswith("tiny_forward") and not row["accepted"]:
            break
        if _condition(assembly.singular_values) > 100.0 * endpoint_condition:
            break
    return rows, singular_rows


def _document_text(
    scaling_rows: list[dict[str, Any]],
    neighbor_rows: list[dict[str, Any]],
    palc_rows: list[dict[str, Any]],
) -> str:
    best = min(
        scaling_rows,
        key=lambda row: (
            row["classification"] != "full_column_rank_moderate",
            float(row["condition_estimate"]),
        ),
    )
    unscaled = next(row for row in scaling_rows if row["variant"] == "unscaled_overdetermined")
    neighbor_ok = all(str(row["matches_existing_audit"]) == "True" or row["matches_existing_audit"] is True for row in neighbor_rows)
    known_rows = [row for row in palc_rows if row["case_type"] == "known_neighbor_reproduction"]
    known_ok = all(str(row.get("accepted")) == "True" or row.get("accepted") is True for row in known_rows)
    tiny_rows = [row for row in palc_rows if row["case_type"] == "tiny_forward_diagnostic"]
    tiny_accepted = any(str(row.get("accepted")) == "True" or row.get("accepted") is True for row in tiny_rows)
    condition_improved = float(best["condition_estimate"]) < float(unscaled["condition_estimate"])
    neighbor_lines = "\n".join(
        (
            f"- member {row['member_id']}: map max `{row['map_residual_max_norm']:.6g}`, "
            f"condition `{row['condition_estimate']:.6g}`, audit match `{row['matches_existing_audit']}`"
        )
        for row in neighbor_rows
    )
    palc_lines = "\n".join(
        (
            f"- `{row['case_id']}`: converged `{row.get('converged')}`, accepted `{row.get('accepted')}`, "
            f"map max `{row.get('map_residual_max_norm')}`, condition `{row.get('condition_estimate')}`, "
            f"reason `{row.get('failure_reason') or 'none'}`"
        )
        for row in palc_rows
    )
    scaling_lines = "\n".join(
        (
            f"- `{row['variant']}`: shape `{row['jacobian_shape']}`, rank `{row['rank_estimate']}`, "
            f"condition `{row['condition_estimate']:.6g}`, class `{row['classification']}`"
        )
        for row in scaling_rows
    )
    continue_route = "yes, but only as bounded local BVP/PALC refinement" if tiny_accepted else "not beyond bounded local diagnostics yet"
    return f"""# Chapter 3 Route B BVP/PALC Neighborhood Diagnostics

## Scope

This is a local diagnostic layer around the existing accepted quasi-DRO
endpoint. It compares residual/column scaling, checks nearby accepted members,
and attempts only known-neighbor and tiny-forward PALC diagnostics. It does not
target 10,500 km or 11,000 km, does not update Figure 3.16 or Figure 3.17, and
does not write any candidate into the accepted branch.

## Scaling And Solve Conventions

{scaling_lines}

The best diagnostic conditioning in this run is
`{best['variant']}` with condition estimate `{best['condition_estimate']:.6g}`.
The unscaled endpoint condition estimate is
`{unscaled['condition_estimate']:.6g}`. Condition estimate improved under the
best scaling convention: `{condition_improved}`.

## Accepted Neighbor Reproduction

{neighbor_lines}

Endpoint-style BVP residual reproduction held across the selected accepted
neighborhood: `{neighbor_ok}`. The formulation is therefore not only an endpoint
artifact at the residual-evaluation level, although all selected systems remain
ill-conditioned.

## PALC Neighborhood Diagnostics

{palc_lines}

Known-neighbor PALC reproduction accepted all attempted known cases:
`{known_ok}`. A tiny forward step from the endpoint was accepted:
`{tiny_accepted}`.

## Required Answers

1. The BVP residual endpoint prototype also holds on the accepted neighborhood:
   `{neighbor_ok}`.
2. The most stable scaling/solve convention is `{best['variant']}`.
3. The condition estimate improves under scaling: `{condition_improved}`. This
   is a scaled linear-algebra improvement, not proof that the physical Newton
   basin is fixed.
4. Full column rank is retained for the selected scaling and neighbor cases
   where the classification is not rank deficient.
5. PALC known-neighbor reproduction holds: `{known_ok}`.
6. The tiny forward step is accepted: `{tiny_accepted}`.
7. A fixed-time BVP/PALC candidate worth the next bounded round exists:
   `{continue_route}`.
8. It is still not justified to discuss replacing Figure 3.16 or Figure 3.17
   data sources.
9. Next steps: refine BVP/PALC scaling, test a smaller-family sanity case, then
   run only limited fixed-time BVP continuation. Stop the high-amplitude Route B
   attempt if conditioning or Fourier-tail gates fail again.
"""


def main() -> None:
    family = load_corrected_dro_family_csv(FAMILY_PATH)
    endpoint = family[-1]
    endpoint_condition = _read_endpoint_condition()

    scaling_rows, singular_rows = _scaling_rows(endpoint)
    neighbor_rows, neighbor_singular_rows, _ = _neighbor_rows(family)
    singular_rows.extend(neighbor_singular_rows)

    prerequisite_ok = (
        len(scaling_rows) >= 4
        and len(neighbor_rows) >= 3
        and all(row["matches_existing_audit"] for row in neighbor_rows)
    )
    if prerequisite_ok:
        palc_rows, palc_singular_rows = _palc_rows(family, endpoint_condition)
        singular_rows.extend(palc_singular_rows)
    else:
        palc_rows = [
            {
                "case_id": "palc_neighborhood_skipped",
                "case_type": "not_attempted",
                "source_members": "",
                "target_or_predicted_member": "",
                "converged": False,
                "accepted": False,
                "failure_reason": "scaling or neighbor reproduction prerequisite failed",
                "classification": "not_attempted",
                "diagnosis": "PALC diagnostics skipped by hard gate",
            }
        ]

    _write_rows(SCALING_OUTPUT, SCALING_FIELDS, scaling_rows)
    _write_rows(NEIGHBOR_OUTPUT, NEIGHBOR_FIELDS, neighbor_rows)
    _write_rows(PALC_OUTPUT, PALC_FIELDS, palc_rows)
    _write_rows(SINGULAR_OUTPUT, SINGULAR_FIELDS, singular_rows)
    DOC_OUTPUT.write_text(_document_text(scaling_rows, neighbor_rows, palc_rows), encoding="utf-8")

    print(f"wrote {SCALING_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {NEIGHBOR_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {PALC_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {SINGULAR_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}")
    best = min(scaling_rows, key=lambda row: float(row["condition_estimate"]))
    print(
        "best scaling="
        f"{best['variant']}, condition={float(best['condition_estimate']):.6e}, "
        f"neighbors={len(neighbor_rows)}, palc_cases={len(palc_rows)}"
    )


if __name__ == "__main__":
    main()
