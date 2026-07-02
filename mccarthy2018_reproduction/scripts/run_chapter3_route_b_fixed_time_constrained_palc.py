"""Route B fixed-time constrained PALC diagnostic.

This script takes the parameter-aware PALC evidence one step closer to the
McCarthy Figure 3.16 / Figure 3.17 requirement by fixing the mapping time back
to the accepted McCarthy value while retaining the improved state/rho/Jacobi
predictor layout.

It writes diagnostic artifacts only. It does not update accepted branch CSVs,
figures, Chapter 4 inputs, or Chapter 5 inputs.
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
SCRIPTS = PROJECT_ROOT / "scripts"
for candidate in (SRC, SCRIPTS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import prototype_chapter3_route_b_bvp_palc_neighborhood as bvp
import run_chapter3_route_b_parameter_aware_palc as parameter_aware
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    CorrectedDROFamilyMember,
    chapter3_quasi_dro_validation_row,
    load_corrected_dro_family_csv,
)
from qp_orbits.cr3bp import jacobi_constant


SYSTEM = SYSTEMS["earth_moon"]
FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
PARAMETER_AWARE_STATE_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_parameter_aware_palc_states.npz"
)
OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_fixed_time_constrained_palc.csv"
STATE_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_fixed_time_constrained_palc_states.npz"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_route_b_fixed_time_constrained_palc.md"

T_FIXED_DAYS = 14.74932760227518
AUDIT_TOLERANCE = 1.0e-8
SECOND_PHASE_TOLERANCE = 1.0e-7
MAX_NEWTON_STEPS = 12
CORRECTION_NORM_CAP = 2.0e-2

FIELDS = (
    "case_id",
    "source_family",
    "operation",
    "source_members",
    "target_member",
    "predictor_policy",
    "fixed_mapping_time_days",
    "converged",
    "accepted",
    "passed_10500_gate",
    "passed_11000_gate",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "mean_jacobi_residual",
    "curve_jacobi_span",
    "phase_residual",
    "second_phase_residual",
    "palc_constraint_residual",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "target_max_abs_z_km",
    "amplitude_error_km",
    "rho",
    "delta_rho",
    "target_rho",
    "rho_error",
    "mean_jacobi",
    "delta_mean_jacobi",
    "target_mean_jacobi",
    "mean_jacobi_error",
    "fourier_tail_energy_state",
    "jacobian_shape",
    "rank_estimate",
    "condition_estimate",
    "newton_iterations",
    "max_correction_norm",
    "failure_reason",
    "diagnosis",
)


@dataclass(frozen=True)
class FixedTimeAssembly:
    case_id: str
    states: np.ndarray
    phases: np.ndarray
    rho: float
    target_jacobi: float
    reference_states: np.ndarray
    mapped_states: np.ndarray
    target_states: np.ndarray
    map_residuals: np.ndarray
    map_residual_norms: np.ndarray
    jacobi_values: np.ndarray
    mean_jacobi_residual: float
    phase_residual: float
    second_phase_residual: float
    palc_residual: float | None
    residual: np.ndarray
    jacobian: np.ndarray
    singular_values: np.ndarray
    rank_estimate: int
    fourier_tail_state: float
    max_abs_z_km: float


def _fmt(value: Any) -> str:
    return parameter_aware._fmt(value)


def _mean_jacobi(states: np.ndarray) -> float:
    return float(np.mean(jacobi_constant(states, SYSTEM.mu)))


def _fixed_unknown_vector(states: np.ndarray, rho: float, target_jacobi: float) -> np.ndarray:
    return np.concatenate([states.reshape(-1), np.array([rho, target_jacobi], dtype=float)])


def _unpack_fixed_unknown(vector: np.ndarray, sample_count: int) -> tuple[np.ndarray, float, float]:
    state_size = 6 * sample_count
    states = vector[:state_size].reshape(sample_count, 6)
    rho = float(vector[state_size])
    target_jacobi = float(vector[state_size + 1])
    return states, rho, target_jacobi


def _condition(singular_values: np.ndarray) -> float:
    return bvp._condition(singular_values)


def _assemble_fixed_time_bvp(
    *,
    case_id: str,
    states: np.ndarray,
    phases: np.ndarray,
    rho: float,
    target_jacobi: float,
    reference_states: np.ndarray,
    include_second_phase: bool,
    palc: bvp.PALCConstraint | None,
) -> FixedTimeAssembly:
    time_unit = SYSTEM.time_unit_days or 1.0
    length_unit = SYSTEM.length_unit_km or 1.0
    sample_count = states.shape[0]
    state_size = states.size
    fixed_mapping_time_nd = T_FIXED_DAYS / time_unit

    interpolation = bvp._trigonometric_interpolation_matrix(phases, phases + rho)
    interpolation_derivative = bvp._trigonometric_interpolation_derivative_matrix(
        phases,
        phases + rho,
    )
    mapped, stms = bvp._stroboscopic_map_and_stms(
        states,
        period=fixed_mapping_time_nd,
        mu=SYSTEM.mu,
        max_step=bvp.INTEGRATION_MAX_STEP,
    )
    target_states = interpolation @ states
    map_residuals = mapped - target_states
    map_residual_norms = np.linalg.norm(map_residuals, axis=1)
    jacobi_values = np.asarray(jacobi_constant(states, SYSTEM.mu), dtype=float)
    mean_jacobi_residual = float(np.mean(jacobi_values) - target_jacobi)
    delta = states - reference_states
    phase_residual = float(np.sum(delta * bvp._phase_direction(phases, reference_states)))
    second_phase_residual = float(np.sum(delta * bvp._second_phase_direction(phases, reference_states)))

    residual_parts = [
        map_residuals.reshape(-1),
        np.array([mean_jacobi_residual, phase_residual], dtype=float),
    ]
    if include_second_phase:
        residual_parts.append(np.array([second_phase_residual], dtype=float))
    vector = _fixed_unknown_vector(states, rho, target_jacobi)
    palc_residual = None
    if palc is not None:
        palc_residual = float(np.dot(vector - palc.predictor, palc.tangent))
        residual_parts.append(np.array([palc_residual], dtype=float))
    residual = np.concatenate(residual_parts)

    row_count = state_size + 2 + int(include_second_phase) + int(palc is not None)
    unknown_size = state_size + 2
    jacobian = np.zeros((row_count, unknown_size), dtype=float)
    for row in range(sample_count):
        row_slice = slice(6 * row, 6 * row + 6)
        for col in range(sample_count):
            col_slice = slice(6 * col, 6 * col + 6)
            block = -interpolation[row, col] * np.eye(6)
            if row == col:
                block = block + stms[row]
            jacobian[row_slice, col_slice] = block
    rho_col = state_size
    jacobi_col = state_size + 1
    jacobian[:state_size, rho_col] = -(interpolation_derivative @ states).reshape(-1)
    jacobi_row = state_size
    phase_row = state_size + 1
    jacobian[jacobi_row, :state_size] = (
        bvp._jacobi_gradient(states, SYSTEM.mu) / sample_count
    ).reshape(-1)
    jacobian[jacobi_row, jacobi_col] = -1.0
    jacobian[phase_row, :state_size] = bvp._phase_direction(phases, reference_states).reshape(-1)
    next_row = state_size + 2
    if include_second_phase:
        jacobian[next_row, :state_size] = bvp._second_phase_direction(
            phases,
            reference_states,
        ).reshape(-1)
        next_row += 1
    if palc is not None:
        jacobian[next_row, :] = palc.tangent

    _, singular_values, _ = np.linalg.svd(jacobian, full_matrices=False)
    return FixedTimeAssembly(
        case_id=case_id,
        states=states.copy(),
        phases=phases.copy(),
        rho=float(rho),
        target_jacobi=float(target_jacobi),
        reference_states=reference_states.copy(),
        mapped_states=mapped,
        target_states=target_states,
        map_residuals=map_residuals,
        map_residual_norms=map_residual_norms,
        jacobi_values=jacobi_values,
        mean_jacobi_residual=mean_jacobi_residual,
        phase_residual=phase_residual,
        second_phase_residual=second_phase_residual,
        palc_residual=palc_residual,
        residual=residual,
        jacobian=jacobian,
        singular_values=singular_values,
        rank_estimate=bvp._rank_from_singular_values(singular_values, jacobian.shape),
        fourier_tail_state=bvp._fourier_tail_energy(states),
        max_abs_z_km=float(np.max(np.abs(states[:, 2])) * length_unit),
    )


def _solve_fixed_time(
    *,
    case_id: str,
    predictor: np.ndarray,
    tangent: np.ndarray | None,
    phases: np.ndarray,
    reference_states: np.ndarray,
    include_second_phase: bool = True,
) -> tuple[FixedTimeAssembly, list[float], bool, str]:
    sample_count = phases.size
    vector = predictor.copy()
    palc = None
    if tangent is not None:
        tangent_norm = max(float(np.linalg.norm(tangent)), 1.0e-14)
        palc = bvp.PALCConstraint(predictor=predictor.copy(), tangent=tangent / tangent_norm)

    correction_norms: list[float] = []
    assembly: FixedTimeAssembly | None = None
    converged = False
    failure_reason = "maximum iterations reached"
    for _ in range(MAX_NEWTON_STEPS):
        states, rho, target_jacobi = _unpack_fixed_unknown(vector, sample_count)
        assembly = _assemble_fixed_time_bvp(
            case_id=case_id,
            states=states,
            phases=phases,
            rho=rho,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            include_second_phase=include_second_phase,
            palc=palc,
        )
        map_max = float(np.max(assembly.map_residual_norms))
        if (
            map_max < AUDIT_TOLERANCE
            and abs(assembly.mean_jacobi_residual) < AUDIT_TOLERANCE
            and abs(assembly.phase_residual) < AUDIT_TOLERANCE
            and abs(assembly.second_phase_residual) < (SECOND_PHASE_TOLERANCE if include_second_phase else np.inf)
            and abs(assembly.palc_residual or 0.0) < AUDIT_TOLERANCE
        ):
            converged = True
            failure_reason = ""
            break
        correction = bvp._solve_scaled_correction(assembly.jacobian, assembly.residual)
        correction_norm = float(np.linalg.norm(correction))
        if correction_norm > CORRECTION_NORM_CAP:
            correction *= CORRECTION_NORM_CAP / correction_norm
            correction_norm = CORRECTION_NORM_CAP
        correction_norms.append(correction_norm)
        vector += correction

    if assembly is None:
        states, rho, target_jacobi = _unpack_fixed_unknown(vector, sample_count)
        assembly = _assemble_fixed_time_bvp(
            case_id=case_id,
            states=states,
            phases=phases,
            rho=rho,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            include_second_phase=include_second_phase,
            palc=palc,
        )
    return assembly, correction_norms, converged, failure_reason


def _member_from_assembly(member_id: int, assembly: FixedTimeAssembly) -> CorrectedDROFamilyMember:
    return bvp._member_like(
        member_id=member_id,
        states=assembly.states,
        phases=assembly.phases,
        rho=assembly.rho,
        mapping_time_days=T_FIXED_DAYS,
        map_residual_norm=float(np.max(assembly.map_residual_norms)),
        phase_residual=assembly.phase_residual,
    )


def _float_from_validation(row: dict[str, str] | None, key: str) -> float | None:
    if row is None:
        return None
    value = row.get(key)
    if value is None or value == "N/A":
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if np.isfinite(number) else None


def _validation_for(assembly: FixedTimeAssembly) -> dict[str, str] | None:
    try:
        member = _member_from_assembly(999, assembly)
        return chapter3_quasi_dro_validation_row(
            member,
            SYSTEM,
            one_map_time_samples=7,
            ten_return_samples=401,
            max_step=bvp.INTEGRATION_MAX_STEP,
        )
    except (RuntimeError, ValueError, FloatingPointError):
        return None


def _target_failure(assembly: FixedTimeAssembly, target: parameter_aware.CurveMember | None) -> list[str]:
    if target is None:
        return []
    failed: list[str] = []
    if abs(assembly.max_abs_z_km - target.max_abs_z_km) > 1.0:
        failed.append("target amplitude gate")
    if abs(assembly.rho - target.rotation_angle_rad) > 1.0e-4:
        failed.append("target rho gate")
    if abs(_mean_jacobi(assembly.states) - target.mean_jacobi) > 1.0e-8:
        failed.append("target mean-Jacobi gate")
    return failed


def _acceptance(
    *,
    assembly: FixedTimeAssembly,
    converged: bool,
    validation: dict[str, str] | None,
    target: parameter_aware.CurveMember | None,
    enforce_target: bool,
) -> tuple[bool, str]:
    failed: list[str] = []
    map_max = float(np.max(assembly.map_residual_norms))
    jacobi_span = float(np.ptp(assembly.jacobi_values))
    phase_return = _float_from_validation(validation, "one_map_phase_return_error")
    ten_span = _float_from_validation(validation, "ten_return_jacobi_span")
    if not converged:
        failed.append("not converged")
    if map_max > AUDIT_TOLERANCE:
        failed.append("map residual gate")
    if abs(assembly.mean_jacobi_residual) > AUDIT_TOLERANCE:
        failed.append("mean-Jacobi residual gate")
    if jacobi_span > AUDIT_TOLERANCE:
        failed.append("Jacobi span gate")
    if abs(assembly.phase_residual) > AUDIT_TOLERANCE:
        failed.append("phase gate")
    if abs(assembly.second_phase_residual) > SECOND_PHASE_TOLERANCE:
        failed.append("second phase gate")
    if assembly.palc_residual is not None and abs(assembly.palc_residual) > AUDIT_TOLERANCE:
        failed.append("PALC gate")
    if phase_return is None or phase_return > AUDIT_TOLERANCE:
        failed.append("one-map phase-return gate")
    if ten_span is None or ten_span > AUDIT_TOLERANCE:
        failed.append("ten-return Jacobi gate")
    if enforce_target:
        failed.extend(_target_failure(assembly, target))
    return not failed, "; ".join(failed)


def _row(
    *,
    case_id: str,
    source_family: str,
    operation: str,
    source_members: str,
    target: parameter_aware.CurveMember | None,
    current: parameter_aware.CurveMember,
    predictor_policy: str,
    assembly: FixedTimeAssembly,
    converged: bool,
    accepted: bool,
    validation: dict[str, str] | None,
    failure_reason: str,
    correction_norms: list[float],
    diagnosis: str,
) -> tuple[dict[str, Any], FixedTimeAssembly]:
    mean_jacobi = _mean_jacobi(assembly.states)
    return {
        "case_id": case_id,
        "source_family": source_family,
        "operation": operation,
        "source_members": source_members,
        "target_member": target.member if target is not None else "predicted_forward",
        "predictor_policy": predictor_policy,
        "fixed_mapping_time_days": T_FIXED_DAYS,
        "converged": converged,
        "accepted": accepted,
        "passed_10500_gate": accepted and assembly.max_abs_z_km > 10500.0,
        "passed_11000_gate": accepted and assembly.max_abs_z_km > 11000.0,
        "map_residual_max_norm": float(np.max(assembly.map_residual_norms)),
        "map_residual_rms_norm": float(np.sqrt(np.mean(assembly.map_residual_norms**2))),
        "mean_jacobi_residual": assembly.mean_jacobi_residual,
        "curve_jacobi_span": float(np.ptp(assembly.jacobi_values)),
        "phase_residual": assembly.phase_residual,
        "second_phase_residual": assembly.second_phase_residual,
        "palc_constraint_residual": assembly.palc_residual,
        "one_map_phase_return_error": _float_from_validation(validation, "one_map_phase_return_error"),
        "ten_return_jacobi_span": _float_from_validation(validation, "ten_return_jacobi_span"),
        "max_abs_z_km": assembly.max_abs_z_km,
        "delta_max_abs_z_km": assembly.max_abs_z_km - current.max_abs_z_km,
        "target_max_abs_z_km": target.max_abs_z_km if target is not None else None,
        "amplitude_error_km": None if target is None else assembly.max_abs_z_km - target.max_abs_z_km,
        "rho": assembly.rho,
        "delta_rho": assembly.rho - current.rotation_angle_rad,
        "target_rho": target.rotation_angle_rad if target is not None else None,
        "rho_error": None if target is None else assembly.rho - target.rotation_angle_rad,
        "mean_jacobi": mean_jacobi,
        "delta_mean_jacobi": mean_jacobi - current.mean_jacobi,
        "target_mean_jacobi": target.mean_jacobi if target is not None else None,
        "mean_jacobi_error": None if target is None else mean_jacobi - target.mean_jacobi,
        "fourier_tail_energy_state": assembly.fourier_tail_state,
        "jacobian_shape": f"{assembly.jacobian.shape[0]}x{assembly.jacobian.shape[1]}",
        "rank_estimate": assembly.rank_estimate,
        "condition_estimate": _condition(assembly.singular_values),
        "newton_iterations": len(correction_norms),
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
        "failure_reason": failure_reason,
        "diagnosis": diagnosis,
    }


def _curve_from_fixed_member(member: CorrectedDROFamilyMember) -> parameter_aware.CurveMember:
    return parameter_aware.CurveMember(
        member=member.member,
        family="quasi_dro_fixed_time_accepted",
        states=member.states,
        phases_rad=member.phases_rad,
        rotation_angle_rad=member.rotation_angle_rad,
        mapping_time_days=T_FIXED_DAYS,
        mean_jacobi=member.mean_jacobi,
        max_abs_z_km=member.max_abs_z_km,
    )


def _curve_from_assembly(
    *,
    member_id: int,
    family: str,
    assembly: FixedTimeAssembly,
) -> parameter_aware.CurveMember:
    return parameter_aware.CurveMember(
        member=member_id,
        family=family,
        states=assembly.states,
        phases_rad=assembly.phases,
        rotation_angle_rad=assembly.rho,
        mapping_time_days=T_FIXED_DAYS,
        mean_jacobi=_mean_jacobi(assembly.states),
        max_abs_z_km=assembly.max_abs_z_km,
    )


def _vector_from_member(member: parameter_aware.CurveMember, phases: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    states, target_phases = parameter_aware._member_vector(member, phases)
    return _fixed_unknown_vector(states, member.rotation_angle_rad, member.mean_jacobi), target_phases


def _endpoint_row(endpoint: parameter_aware.CurveMember) -> dict[str, Any]:
    assembly = _assemble_fixed_time_bvp(
        case_id="fixed_time_endpoint_reproduction",
        states=endpoint.states,
        phases=endpoint.phases_rad,
        rho=endpoint.rotation_angle_rad,
        target_jacobi=endpoint.mean_jacobi,
        reference_states=endpoint.states,
        include_second_phase=True,
        palc=None,
    )
    validation = _validation_for(assembly)
    accepted, audit_failure = _acceptance(
        assembly=assembly,
        converged=True,
        validation=validation,
        target=endpoint,
        enforce_target=True,
    )
    return _row(
        case_id="fixed_time_endpoint_reproduction",
        source_family=endpoint.family,
        operation="fixed_time_endpoint_reproduction",
        source_members=str(endpoint.member),
        target=endpoint,
        current=endpoint,
        predictor_policy="accepted_endpoint_state_rho_J_fixed_T",
        assembly=assembly,
        converged=True,
        accepted=accepted,
        validation=validation,
        failure_reason=audit_failure,
        correction_norms=[],
        diagnosis="Authoritative accepted fixed-time endpoint reproduced in the constrained unknown layout.",
    )


def _palc_case(
    *,
    case_id: str,
    previous: parameter_aware.CurveMember,
    current: parameter_aware.CurveMember,
    target: parameter_aware.CurveMember | None,
    source_family: str,
    fraction: float,
    predictor_policy: str,
    enforce_target: bool,
) -> dict[str, Any]:
    phases = target.phases_rad if target is not None else current.phases_rad
    previous_vector, _ = _vector_from_member(previous, phases)
    current_vector, _ = _vector_from_member(current, phases)
    if predictor_policy == "target_state_control" and target is not None:
        predictor, _ = _vector_from_member(target, phases)
    else:
        predictor = current_vector + fraction * (current_vector - previous_vector)
    tangent = predictor - current_vector
    current_states, _ = parameter_aware._member_vector(current, phases)
    assembly, correction_norms, converged, solver_failure = _solve_fixed_time(
        case_id=case_id,
        predictor=predictor,
        tangent=tangent,
        phases=phases,
        reference_states=current_states,
    )
    validation = _validation_for(assembly)
    accepted, audit_failure = _acceptance(
        assembly=assembly,
        converged=converged,
        validation=validation,
        target=target,
        enforce_target=enforce_target,
    )
    failure = solver_failure or audit_failure
    if target is None:
        diagnosis = "Fixed-time constrained PALC forward diagnostic; candidate only if accepted and amplitude gates pass."
    elif enforce_target:
        diagnosis = "Strict fixed-time known-neighbor reproduction under constrained PALC."
    else:
        diagnosis = "Fixed-time constrained replay of a free-time predictor; target closeness is reported but not required."
    row = _row(
        case_id=case_id,
        source_family=source_family,
        operation="fixed_time_constrained_PALC",
        source_members=f"{previous.member},{current.member}",
        target=target,
        current=current,
        predictor_policy=predictor_policy,
        assembly=assembly,
        converged=converged,
        accepted=accepted,
        validation=validation,
        failure_reason=failure,
        correction_norms=correction_norms,
        diagnosis=diagnosis,
    )
    return row, assembly


def _no_palc_projection_case(
    *,
    case_id: str,
    initial: parameter_aware.CurveMember,
    source_family: str,
    reference: parameter_aware.CurveMember,
    predictor_policy: str,
) -> tuple[dict[str, Any], FixedTimeAssembly]:
    predictor, phases = _vector_from_member(initial, reference.phases_rad)
    reference_states, _ = parameter_aware._member_vector(reference, phases)
    assembly, correction_norms, converged, solver_failure = _solve_fixed_time(
        case_id=case_id,
        predictor=predictor,
        tangent=None,
        phases=phases,
        reference_states=reference_states,
    )
    validation = _validation_for(assembly)
    accepted, audit_failure = _acceptance(
        assembly=assembly,
        converged=converged,
        validation=validation,
        target=None,
        enforce_target=False,
    )
    row = _row(
        case_id=case_id,
        source_family=source_family,
        operation="fixed_time_no_PALC_projection",
        source_members=str(initial.member),
        target=None,
        current=reference,
        predictor_policy=predictor_policy,
        assembly=assembly,
        converged=converged,
        accepted=accepted,
        validation=validation,
        failure_reason=solver_failure or audit_failure,
        correction_norms=correction_norms,
        diagnosis="Fixed-time Newton projection from a high-amplitude diagnostic state without a PALC arclength row.",
    )
    return row, assembly


def _load_parameter_aware_state() -> list[parameter_aware.CurveMember]:
    if not PARAMETER_AWARE_STATE_PATH.exists():
        return []
    with np.load(PARAMETER_AWARE_STATE_PATH) as data:
        phases = np.asarray(data["phase_grid"], dtype=float)
        return [
            parameter_aware.CurveMember(
                member=100 + index,
                family="quasi_dro_parameter_aware_free_time_forward",
                states=np.asarray(data["states"][index], dtype=float),
                phases_rad=phases,
                rotation_angle_rad=float(data["rho"][index]),
                mapping_time_days=float(data["mapping_time_days"][index]),
                mean_jacobi=float(data["mean_jacobi"][index]),
                max_abs_z_km=float(data["max_abs_z_km"][index]),
            )
            for index in range(data["states"].shape[0])
            if bool(data["accepted"][index])
        ]


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _write_state_archive(records: list[tuple[dict[str, Any], FixedTimeAssembly]]) -> None:
    accepted = [(row, assembly) for row, assembly in records if bool(row["accepted"])]
    if not accepted:
        return
    STATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        STATE_OUTPUT,
        schema_version=np.array("1.0"),
        created_by_script=np.array(Path(__file__).name),
        case_ids=np.asarray([str(row["case_id"]) for row, _ in accepted]),
        states=np.stack([assembly.states for _, assembly in accepted]),
        phase_grid=accepted[0][1].phases,
        fixed_mapping_time_days=np.asarray([T_FIXED_DAYS for _ in accepted], dtype=float),
        rho=np.asarray([assembly.rho for _, assembly in accepted], dtype=float),
        mean_jacobi=np.asarray([_mean_jacobi(assembly.states) for _, assembly in accepted], dtype=float),
        max_abs_z_km=np.asarray([assembly.max_abs_z_km for _, assembly in accepted], dtype=float),
        map_residual_max_norm=np.asarray(
            [float(row["map_residual_max_norm"]) for row, _ in accepted],
            dtype=float,
        ),
        curve_jacobi_span=np.asarray(
            [float(row["curve_jacobi_span"]) for row, _ in accepted],
            dtype=float,
        ),
        one_map_phase_return_error=np.asarray(
            [float(row["one_map_phase_return_error"]) for row, _ in accepted],
            dtype=float,
        ),
        ten_return_jacobi_span=np.asarray(
            [float(row["ten_return_jacobi_span"]) for row, _ in accepted],
            dtype=float,
        ),
        passed_10500_gate=np.asarray([bool(row["passed_10500_gate"]) for row, _ in accepted], dtype=bool),
        passed_11000_gate=np.asarray([bool(row["passed_11000_gate"]) for row, _ in accepted], dtype=bool),
    )


def _doc_text(rows: list[dict[str, Any]]) -> str:
    accepted = [row for row in rows if bool(row["accepted"])]
    high = [row for row in accepted if bool(row["passed_10500_gate"])]
    best = max(rows, key=lambda item: float(item["max_abs_z_km"]))
    best_accepted = max(accepted, key=lambda item: float(item["max_abs_z_km"])) if accepted else None
    accepted_lines = "\n".join(
        (
            f"- `{row['case_id']}`: max z `{row['max_abs_z_km']:.6g}` km, "
            f"map max `{row['map_residual_max_norm']:.6g}`, "
            f"ten-return Jacobi `{_fmt(row['ten_return_jacobi_span'])}`"
        )
        for row in accepted
    ) or "- none"
    high_lines = "\n".join(
        (
            f"- `{row['case_id']}`: max z `{row['max_abs_z_km']:.6g}` km"
        )
        for row in high
    ) or "- none"
    return f"""# Chapter 3 Route B Fixed-Time Constrained PALC

## Scope

This diagnostic fixes the mapping time at `{T_FIXED_DAYS}` days while retaining
the state/rho/mean-Jacobi continuation layout from the parameter-aware PALC
prototype. It is a Route B audit artifact only and does not update Figure 3.16,
Figure 3.17, accepted branch CSVs, Chapter 4, or Chapter 5.

## Accepted Cases

{accepted_lines}

## Accepted High-Amplitude Fixed-Time Cases

{high_lines}

## Key Results

- Total cases: `{len(rows)}`.
- Accepted cases: `{len(accepted)}`.
- Accepted cases above 10,500 km: `{len(high)}`.
- Highest accepted fixed-time case:
  `{best_accepted['case_id'] if best_accepted else 'none'}`, max z
  `{best_accepted['max_abs_z_km'] if best_accepted else 'N/A'}` km.
- Highest evaluated case: `{best['case_id']}`, max z
  `{best['max_abs_z_km']:.6g}` km, accepted `{best['accepted']}`, failure
  reason `{best['failure_reason'] or 'none'}`.
- Accepted fixed-time states from this diagnostic are archived in
  `data/computed/chapter3_route_b_fixed_time_constrained_palc_states.npz`.

## Interpretation

The endpoint and local controls show whether the constrained unknown layout
preserves the existing fixed-time accepted branch. The free-time replay and
projection cases test whether the parameter-aware high-amplitude diagnostic can
survive when the McCarthy mapping time is fixed again.

An accepted row above 10,500 km would be a fixed-time candidate for further
multi-member continuation and figure-source review. A rejected high-amplitude
row is diagnostic only and must not be used to update Fig. 3.16 / Fig. 3.17.

The accepted fixed-time projections above the old 10,164 km endpoint are useful
candidate evidence, but the 10,500 km and 11,000 km gates remain unpassed. The
next fixed-time task should either stabilize continuation from the 10,275 km
candidate or document this as the current bounded fixed-time continuation
frontier.
"""


def _write_doc(rows: list[dict[str, Any]]) -> None:
    DOC_OUTPUT.write_text(_doc_text(rows), encoding="utf-8")


def main() -> None:
    fixed_family = tuple(_curve_from_fixed_member(member) for member in load_corrected_dro_family_csv(FAMILY_PATH))
    free_time_family = parameter_aware._load_free_time_members()
    parameter_forward = _load_parameter_aware_state()
    rows: list[dict[str, Any]] = []
    state_records: list[tuple[dict[str, Any], FixedTimeAssembly]] = []
    fixed_time_candidates: list[parameter_aware.CurveMember] = []

    def add_case(result: tuple[dict[str, Any], FixedTimeAssembly]) -> None:
        row, assembly = result
        rows.append(row)
        state_records.append((row, assembly))
        if bool(row["accepted"]) and float(row["max_abs_z_km"]) > fixed_family[-1].max_abs_z_km + 1.0:
            fixed_time_candidates.append(
                _curve_from_assembly(
                    member_id=200 + len(fixed_time_candidates),
                    family="quasi_dro_fixed_time_candidate",
                    assembly=assembly,
                )
            )

    endpoint = fixed_family[-1]
    rows.append(_endpoint_row(endpoint))

    if len(fixed_family) >= 11:
        add_case(
            _palc_case(
                case_id="fixed_time_known_neighbor_8_9_to_10",
                previous=fixed_family[8],
                current=fixed_family[9],
                target=fixed_family[10],
                source_family="quasi_dro_fixed_time_accepted",
                fraction=1.0,
                predictor_policy="fixed_time_secant_8_9_to_10",
                enforce_target=True,
            )
        )
        for fraction in (0.10, 0.25, 0.50, 1.00):
            add_case(
                _palc_case(
                    case_id=f"fixed_time_forward_9_10_fraction_{fraction:.2f}".replace(".", "p"),
                    previous=fixed_family[9],
                    current=fixed_family[10],
                    target=None,
                    source_family="quasi_dro_fixed_time_accepted",
                    fraction=fraction,
                    predictor_policy="fixed_time_endpoint_secant_forward",
                    enforce_target=False,
                )
            )

    if len(free_time_family) >= 7:
        add_case(
            _palc_case(
                case_id="free_time_tangent_fixed_T_known_4_5_to_6",
                previous=free_time_family[4],
                current=free_time_family[5],
                target=free_time_family[6],
                source_family="quasi_dro_free_time_diagnostic",
                fraction=1.0,
                predictor_policy="free_time_state_rho_J_secant_with_T_fixed",
                enforce_target=False,
            )
        )
        for fraction in (0.25, 0.50, 1.00):
            add_case(
                _palc_case(
                    case_id=f"free_time_tangent_fixed_T_forward_5_6_fraction_{fraction:.2f}".replace(".", "p"),
                    previous=free_time_family[5],
                    current=free_time_family[6],
                    target=None,
                    source_family="quasi_dro_free_time_diagnostic",
                    fraction=fraction,
                    predictor_policy="free_time_high_amplitude_tangent_with_T_fixed",
                    enforce_target=False,
                )
            )
        add_case(
            _no_palc_projection_case(
                case_id="free_time_member_6_no_palc_projection_to_fixed_T",
                initial=free_time_family[6],
                source_family="quasi_dro_free_time_diagnostic",
                reference=free_time_family[6],
                predictor_policy="free_time_member_6_state_rho_J_fixed_T_no_PALC",
            )
        )
        if parameter_forward:
            add_case(
                _no_palc_projection_case(
                    case_id="parameter_aware_forward_no_palc_projection_to_fixed_T",
                    initial=parameter_forward[0],
                    source_family="quasi_dro_parameter_aware_free_time_forward",
                    reference=free_time_family[6],
                    predictor_policy="parameter_aware_forward_state_rho_J_fixed_T_no_PALC",
                )
            )

    if fixed_time_candidates:
        candidate = max(fixed_time_candidates, key=lambda member: member.max_abs_z_km)
        for fraction in (0.25, 0.50, 1.00):
            add_case(
                _palc_case(
                    case_id=f"fixed_time_candidate_forward_endpoint_candidate_fraction_{fraction:.2f}".replace(".", "p"),
                    previous=endpoint,
                    current=candidate,
                    target=None,
                    source_family="quasi_dro_fixed_time_candidate",
                    fraction=fraction,
                    predictor_policy="accepted_fixed_time_candidate_secant_forward",
                    enforce_target=False,
                )
            )

    _write_rows(rows)
    _write_state_archive(state_records)
    _write_doc(rows)
    accepted = sum(1 for row in rows if bool(row["accepted"]))
    high = sum(1 for row in rows if bool(row["passed_10500_gate"]))
    best = max(rows, key=lambda item: float(item["max_abs_z_km"]))
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}")
    if STATE_OUTPUT.exists():
        print(f"wrote {STATE_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(
        "fixed-time constrained PALC: "
        f"rows={len(rows)}, accepted={accepted}, "
        f"accepted_gt_10500={high}, max_evaluated_z={best['max_abs_z_km']:.6f} km"
    )


if __name__ == "__main__":
    main()
