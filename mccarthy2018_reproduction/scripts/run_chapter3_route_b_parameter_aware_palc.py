"""Route B parameter-aware PALC prototype.

This diagnostic promotes mapping time and mean Jacobi into the PALC unknown
vector:

    u = [curve states, rho, mapping_time_days, mean_jacobi]

The purpose is to test whether the PALC layer can reproduce known neighboring
tori when the continuation parameters are part of the tangent, and whether it
can make bounded diagnostic progress on the existing free-time quasi-DRO branch.

It does not update Figure 3.16, Figure 3.17, accepted fixed-time branch CSVs, or
Chapter 5 inputs.
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
import run_chapter3_route_b_bvp_palc_stabilization as stabilization
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import cr3bp_rhs, jacobi_constant


FREE_TIME_BRANCH_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_free_time_branch_states.npz"
)
OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_parameter_aware_palc.csv"
STATE_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_parameter_aware_palc_states.npz"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_route_b_parameter_aware_palc.md"

SYSTEM = SYSTEMS["earth_moon"]
AUDIT_TOLERANCE = 1.0e-8
MAX_NEWTON_STEPS = 8
CORRECTION_NORM_CAP = 2.0e-2

FIELDS = (
    "case_id",
    "family",
    "operation",
    "source_members",
    "target_member",
    "predictor_policy",
    "converged",
    "accepted",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "mean_jacobi_residual",
    "curve_jacobi_span",
    "phase_residual",
    "second_phase_residual",
    "palc_constraint_residual",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "target_max_abs_z_km",
    "amplitude_error_km",
    "rho",
    "delta_rho",
    "target_rho",
    "rho_error",
    "mapping_time_days",
    "delta_mapping_time_days",
    "target_mapping_time_days",
    "mapping_time_error_days",
    "mean_jacobi",
    "delta_mean_jacobi",
    "target_mean_jacobi",
    "mean_jacobi_error",
    "fourier_tail_energy_state",
    "ten_return_jacobi_span",
    "jacobian_shape",
    "rank_estimate",
    "condition_estimate",
    "newton_iterations",
    "max_correction_norm",
    "failure_reason",
    "diagnosis",
)


@dataclass(frozen=True)
class CurveMember:
    member: int
    family: str
    states: np.ndarray
    phases_rad: np.ndarray
    rotation_angle_rad: float
    mapping_time_days: float
    mean_jacobi: float
    max_abs_z_km: float


@dataclass(frozen=True)
class ParameterAssembly:
    case_id: str
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
    second_phase_residual: float
    palc_residual: float | None
    residual: np.ndarray
    jacobian: np.ndarray
    singular_values: np.ndarray
    rank_estimate: int
    fourier_tail_state: float
    fourier_tail_z: float
    max_abs_z_km: float


def _fmt(value: Any) -> str:
    return bvp._fmt(value)


def _mean_jacobi(states: np.ndarray) -> float:
    return float(np.mean(jacobi_constant(states, SYSTEM.mu)))


def _unknown_vector(
    states: np.ndarray,
    rho: float,
    mapping_time_days: float,
    target_jacobi: float,
) -> np.ndarray:
    return np.concatenate(
        [
            states.reshape(-1),
            np.array([rho, mapping_time_days, target_jacobi], dtype=float),
        ]
    )


def _unpack_unknown(vector: np.ndarray, sample_count: int) -> tuple[np.ndarray, float, float, float]:
    state_size = 6 * sample_count
    states = vector[:state_size].reshape(sample_count, 6)
    rho = float(vector[state_size])
    mapping_time_days = float(vector[state_size + 1])
    target_jacobi = float(vector[state_size + 2])
    return states, rho, mapping_time_days, target_jacobi


def _condition(singular_values: np.ndarray) -> float:
    return bvp._condition(singular_values)


def _assemble_parameter_bvp(
    *,
    case_id: str,
    states: np.ndarray,
    phases: np.ndarray,
    rho: float,
    mapping_time_days: float,
    target_jacobi: float,
    reference_states: np.ndarray,
    include_second_phase: bool,
    palc: bvp.PALCConstraint | None,
) -> ParameterAssembly:
    time_unit = SYSTEM.time_unit_days or 1.0
    length_unit = SYSTEM.length_unit_km or 1.0
    sample_count = states.shape[0]
    state_size = states.size
    mapping_time_nd = mapping_time_days / time_unit
    interpolation = bvp._trigonometric_interpolation_matrix(phases, phases + rho)
    interpolation_derivative = bvp._trigonometric_interpolation_derivative_matrix(
        phases,
        phases + rho,
    )
    mapped, stms = bvp._stroboscopic_map_and_stms(
        states,
        period=mapping_time_nd,
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
    palc_residual = None
    vector = _unknown_vector(states, rho, mapping_time_days, target_jacobi)
    if palc is not None:
        palc_residual = float(np.dot(vector - palc.predictor, palc.tangent))
        residual_parts.append(np.array([palc_residual], dtype=float))
    residual = np.concatenate(residual_parts)

    row_count = state_size + 2 + int(include_second_phase) + int(palc is not None)
    unknown_size = state_size + 3
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
    time_col = state_size + 1
    jacobi_col = state_size + 2
    jacobian[:state_size, rho_col] = -(interpolation_derivative @ states).reshape(-1)
    mapped_rhs = np.asarray([cr3bp_rhs(0.0, state, SYSTEM.mu) for state in mapped])
    jacobian[:state_size, time_col] = (mapped_rhs / time_unit).reshape(-1)

    jacobi_row = state_size
    phase_row = state_size + 1
    jacobian[jacobi_row, :state_size] = (bvp._jacobi_gradient(states, SYSTEM.mu) / sample_count).reshape(-1)
    jacobian[jacobi_row, jacobi_col] = -1.0
    jacobian[phase_row, :state_size] = bvp._phase_direction(phases, reference_states).reshape(-1)
    next_row = state_size + 2
    if include_second_phase:
        jacobian[next_row, :state_size] = bvp._second_phase_direction(phases, reference_states).reshape(-1)
        next_row += 1
    if palc is not None:
        jacobian[next_row, :] = palc.tangent

    u, singular_values, _ = np.linalg.svd(jacobian, full_matrices=False)
    del u
    return ParameterAssembly(
        case_id=case_id,
        states=states.copy(),
        phases=phases.copy(),
        rho=float(rho),
        mapping_time_days=float(mapping_time_days),
        mapping_time_nd=float(mapping_time_nd),
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
        fourier_tail_z=bvp._fourier_tail_energy(states[:, 2:3]),
        max_abs_z_km=float(np.max(np.abs(states[:, 2])) * length_unit),
    )


def _solve_scaled_correction(jacobian: np.ndarray, residual: np.ndarray) -> np.ndarray:
    return bvp._solve_scaled_correction(jacobian, residual)


def _accepts(
    *,
    assembly: ParameterAssembly,
    converged: bool,
    endpoint_condition: float,
    target: CurveMember | None,
) -> tuple[bool, str]:
    failed: list[str] = []
    map_max = float(np.max(assembly.map_residual_norms))
    jacobi_span = float(np.ptp(assembly.jacobi_values))
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
    if assembly.palc_residual is not None and abs(assembly.palc_residual) > AUDIT_TOLERANCE:
        failed.append("PALC gate")
    if _condition(assembly.singular_values) > 100.0 * endpoint_condition:
        failed.append("condition gate")
    if target is not None:
        if abs(assembly.max_abs_z_km - target.max_abs_z_km) > stabilization.TARGET_AMPLITUDE_TOL_KM:
            failed.append("target amplitude gate")
        if abs(assembly.rho - target.rotation_angle_rad) > stabilization.TARGET_RHO_TOL:
            failed.append("target rho gate")
        if abs(assembly.mapping_time_days - target.mapping_time_days) > 1.0e-4:
            failed.append("target mapping-time gate")
        if abs(_mean_jacobi(assembly.states) - target.mean_jacobi) > stabilization.TARGET_MEAN_JACOBI_TOL:
            failed.append("target mean-Jacobi gate")
    return not failed, "; ".join(failed)


def _correct_parameter_palc(
    *,
    case_id: str,
    predictor: np.ndarray,
    tangent: np.ndarray,
    phases: np.ndarray,
    reference_states: np.ndarray,
    endpoint_condition: float,
    include_second_phase: bool,
) -> tuple[ParameterAssembly, list[float], bool, str]:
    sample_count = phases.size
    vector = predictor.copy()
    tangent = tangent / max(float(np.linalg.norm(tangent)), 1.0e-14)
    palc = bvp.PALCConstraint(predictor=predictor.copy(), tangent=tangent.copy())
    correction_norms: list[float] = []
    assembly: ParameterAssembly | None = None
    converged = False
    failure_reason = "maximum iterations reached"
    for _ in range(MAX_NEWTON_STEPS):
        states, rho, mapping_time_days, target_jacobi = _unpack_unknown(vector, sample_count)
        assembly = _assemble_parameter_bvp(
            case_id=case_id,
            states=states,
            phases=phases,
            rho=rho,
            mapping_time_days=mapping_time_days,
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
            and abs(assembly.second_phase_residual) < (1.0e-7 if include_second_phase else np.inf)
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
        states, rho, mapping_time_days, target_jacobi = _unpack_unknown(vector, sample_count)
        assembly = _assemble_parameter_bvp(
            case_id=case_id,
            states=states,
            phases=phases,
            rho=rho,
            mapping_time_days=mapping_time_days,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            include_second_phase=include_second_phase,
            palc=palc,
        )
    return assembly, correction_norms, converged, failure_reason


def _member_vector(member: CurveMember, phases: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    if phases is None:
        return member.states.copy(), member.phases_rad.copy()
    states = bvp._resample_states(member.states, member.phases_rad, phases)
    return states, phases.copy()


def _vector_from_member(member: CurveMember, phases: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    states, target_phases = _member_vector(member, phases)
    return _unknown_vector(
        states,
        member.rotation_angle_rad,
        member.mapping_time_days,
        member.mean_jacobi,
    ), target_phases


def _ten_return_jacobi_span(assembly: ParameterAssembly) -> float | None:
    try:
        return bvp._ten_return_jacobi_span(assembly)  # type: ignore[arg-type]
    except (RuntimeError, ValueError, FloatingPointError):
        return None


def _row(
    *,
    case_id: str,
    family: str,
    operation: str,
    source_members: str,
    target: CurveMember | None,
    current: CurveMember,
    predictor_policy: str,
    assembly: ParameterAssembly,
    converged: bool,
    accepted: bool,
    failure_reason: str,
    correction_norms: list[float],
    diagnosis: str,
) -> dict[str, Any]:
    mean_jacobi = _mean_jacobi(assembly.states)
    return {
        "case_id": case_id,
        "family": family,
        "operation": operation,
        "source_members": source_members,
        "target_member": target.member if target is not None else "predicted_forward",
        "predictor_policy": predictor_policy,
        "converged": converged,
        "accepted": accepted,
        "map_residual_max_norm": float(np.max(assembly.map_residual_norms)),
        "map_residual_rms_norm": float(np.sqrt(np.mean(assembly.map_residual_norms**2))),
        "mean_jacobi_residual": assembly.mean_jacobi_residual,
        "curve_jacobi_span": float(np.ptp(assembly.jacobi_values)),
        "phase_residual": assembly.phase_residual,
        "second_phase_residual": assembly.second_phase_residual,
        "palc_constraint_residual": assembly.palc_residual,
        "max_abs_z_km": assembly.max_abs_z_km,
        "delta_max_abs_z_km": assembly.max_abs_z_km - current.max_abs_z_km,
        "target_max_abs_z_km": target.max_abs_z_km if target is not None else None,
        "amplitude_error_km": None if target is None else assembly.max_abs_z_km - target.max_abs_z_km,
        "rho": assembly.rho,
        "delta_rho": assembly.rho - current.rotation_angle_rad,
        "target_rho": target.rotation_angle_rad if target is not None else None,
        "rho_error": None if target is None else assembly.rho - target.rotation_angle_rad,
        "mapping_time_days": assembly.mapping_time_days,
        "delta_mapping_time_days": assembly.mapping_time_days - current.mapping_time_days,
        "target_mapping_time_days": target.mapping_time_days if target is not None else None,
        "mapping_time_error_days": None if target is None else assembly.mapping_time_days - target.mapping_time_days,
        "mean_jacobi": mean_jacobi,
        "delta_mean_jacobi": mean_jacobi - current.mean_jacobi,
        "target_mean_jacobi": target.mean_jacobi if target is not None else None,
        "mean_jacobi_error": None if target is None else mean_jacobi - target.mean_jacobi,
        "fourier_tail_energy_state": assembly.fourier_tail_state,
        "ten_return_jacobi_span": _ten_return_jacobi_span(assembly) if accepted else None,
        "jacobian_shape": f"{assembly.jacobian.shape[0]}x{assembly.jacobian.shape[1]}",
        "rank_estimate": assembly.rank_estimate,
        "condition_estimate": _condition(assembly.singular_values),
        "newton_iterations": len(correction_norms),
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
        "failure_reason": failure_reason,
        "diagnosis": diagnosis,
    }


def _endpoint_case(member: CurveMember, endpoint_condition: float) -> dict[str, Any]:
    assembly = _assemble_parameter_bvp(
        case_id=f"{member.family}_endpoint_{member.member}",
        states=member.states,
        phases=member.phases_rad,
        rho=member.rotation_angle_rad,
        mapping_time_days=member.mapping_time_days,
        target_jacobi=member.mean_jacobi,
        reference_states=member.states,
        include_second_phase=True,
        palc=None,
    )
    accepted, failure = _accepts(
        assembly=assembly,
        converged=True,
        endpoint_condition=endpoint_condition,
        target=member,
    )
    return _row(
        case_id=f"{member.family}_endpoint_{member.member}",
        family=member.family,
        operation="parameter_endpoint_reproduction",
        source_members=str(member.member),
        target=member,
        current=member,
        predictor_policy="member_own_state_rho_T_J",
        assembly=assembly,
        converged=True,
        accepted=accepted,
        failure_reason=failure,
        correction_norms=[],
        diagnosis="Endpoint reproduction with states, rho, mapping time, and mean Jacobi in the unknown layout.",
    )


def _palc_case(
    *,
    case_id: str,
    previous: CurveMember,
    current: CurveMember,
    target: CurveMember | None,
    endpoint_condition: float,
    fraction: float,
    predictor_policy: str,
    include_second_phase: bool = True,
) -> tuple[dict[str, Any], ParameterAssembly]:
    phases = target.phases_rad if target is not None else current.phases_rad
    previous_vector, _ = _vector_from_member(previous, phases)
    current_vector, _ = _vector_from_member(current, phases)
    if predictor_policy == "target_state_control" and target is not None:
        predictor, _ = _vector_from_member(target, phases)
    else:
        predictor = current_vector + fraction * (current_vector - previous_vector)
    tangent = predictor - current_vector
    previous_states, _ = _member_vector(previous, phases)
    current_states, _ = _member_vector(current, phases)
    reference_states = current_states
    del previous_states
    assembly, correction_norms, converged, solver_failure = _correct_parameter_palc(
        case_id=case_id,
        predictor=predictor,
        tangent=tangent,
        phases=phases,
        reference_states=reference_states,
        endpoint_condition=endpoint_condition,
        include_second_phase=include_second_phase,
    )
    accepted, audit_failure = _accepts(
        assembly=assembly,
        converged=converged,
        endpoint_condition=endpoint_condition,
        target=target,
    )
    if target is None and assembly.max_abs_z_km >= 10500.0:
        # This is allowed only as a diagnostic free-time member, never as a
        # fixed-time figure source.
        pass
    failure = solver_failure or audit_failure
    if predictor_policy == "target_state_control":
        diagnosis = "Control case; target member is recovered when the full target vector is used as predictor."
    elif target is None:
        diagnosis = "Parameter-aware forward diagnostic; not a fixed-mapping-time figure source."
    else:
        diagnosis = "Parameter-aware PALC known-neighbor reproduction."
    return (
        _row(
            case_id=case_id,
            family=current.family,
            operation="parameter_aware_PALC",
            source_members=f"{previous.member},{current.member}",
            target=target,
            current=current,
            predictor_policy=predictor_policy,
            assembly=assembly,
            converged=converged,
            accepted=accepted,
            failure_reason=failure,
            correction_norms=correction_norms,
            diagnosis=diagnosis,
        ),
        assembly,
    )


def _load_small_members() -> list[CurveMember]:
    members, _ = stabilization._load_small_vertical_members()
    return [
        CurveMember(
            member=member.member,
            family="small_quasi_vertical",
            states=member.states,
            phases_rad=member.phases_rad,
            rotation_angle_rad=member.rotation_angle_rad,
            mapping_time_days=member.mapping_time_days,
            mean_jacobi=member.mean_jacobi,
            max_abs_z_km=member.max_abs_z_km,
        )
        for member in members
    ]


def _load_free_time_members() -> list[CurveMember]:
    if not FREE_TIME_BRANCH_PATH.exists():
        return []
    with np.load(FREE_TIME_BRANCH_PATH) as data:
        phases = np.asarray(data["phase_grid"], dtype=float)
        return [
            CurveMember(
                member=index,
                family="quasi_dro_free_time_diagnostic",
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


def _write_state_archive(records: list[tuple[dict[str, Any], ParameterAssembly]]) -> None:
    quasi_dro_records = [
        (row, assembly)
        for row, assembly in records
        if row["family"] == "quasi_dro_free_time_diagnostic" and bool(row["accepted"])
    ]
    if not quasi_dro_records:
        return
    STATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        STATE_OUTPUT,
        schema_version=np.array("1.1"),
        created_by_script=np.array(Path(__file__).name),
        case_ids=np.asarray([str(row["case_id"]) for row, _ in quasi_dro_records]),
        source_members=np.asarray([str(row["source_members"]) for row, _ in quasi_dro_records]),
        target_members=np.asarray([str(row["target_member"]) for row, _ in quasi_dro_records]),
        states=np.stack([assembly.states for _, assembly in quasi_dro_records]),
        phase_grid=quasi_dro_records[0][1].phases,
        mapping_time_days=np.asarray([assembly.mapping_time_days for _, assembly in quasi_dro_records], dtype=float),
        rho=np.asarray([assembly.rho for _, assembly in quasi_dro_records], dtype=float),
        mean_jacobi=np.asarray([_mean_jacobi(assembly.states) for _, assembly in quasi_dro_records], dtype=float),
        max_abs_z_km=np.asarray([assembly.max_abs_z_km for _, assembly in quasi_dro_records], dtype=float),
        map_residual_max_norm=np.asarray(
            [float(np.max(assembly.map_residual_norms)) for _, assembly in quasi_dro_records],
            dtype=float,
        ),
        map_residual_rms_norm=np.asarray(
            [
                float(np.sqrt(np.mean(assembly.map_residual_norms**2)))
                for _, assembly in quasi_dro_records
            ],
            dtype=float,
        ),
        curve_jacobi_span=np.asarray(
            [float(np.ptp(assembly.jacobi_values)) for _, assembly in quasi_dro_records],
            dtype=float,
        ),
        ten_return_jacobi_span=np.asarray(
            [
                float(row["ten_return_jacobi_span"])
                if row.get("ten_return_jacobi_span") is not None
                else np.nan
                for row, _ in quasi_dro_records
            ],
            dtype=float,
        ),
        condition_estimate=np.asarray(
            [
                float(row["condition_estimate"])
                if row.get("condition_estimate") is not None
                else np.nan
                for row, _ in quasi_dro_records
            ],
            dtype=float,
        ),
        accepted=np.asarray([bool(row["accepted"]) for row, _ in quasi_dro_records], dtype=bool),
    )


def _doc_text(rows: list[dict[str, Any]]) -> str:
    accepted = [row for row in rows if bool(row["accepted"])]
    small_known = next(row for row in rows if row["case_id"] == "small_parameter_aware_0_1_to_2")
    free_known = next(row for row in rows if row["case_id"] == "free_time_parameter_aware_4_5_to_6")
    free_forward = next(row for row in rows if row["case_id"] == "free_time_parameter_aware_forward_from_5_6")
    accepted_lines = "\n".join(
        (
            f"- `{row['case_id']}`: max z `{row['max_abs_z_km']:.6g}` km, "
            f"T `{row['mapping_time_days']:.12g}` d, map max `{row['map_residual_max_norm']:.6g}`"
        )
        for row in accepted
    )
    return f"""# Chapter 3 Route B Parameter-Aware PALC Prototype

## Scope

This diagnostic promotes mapping time and mean Jacobi into the PALC unknown
vector. It tests smaller-family known-neighbor reproduction and the existing
accepted free-time quasi-DRO diagnostic branch. It does not update Figure 3.16
or Figure 3.17 and does not write to accepted fixed-time branch CSV files.

## Accepted Cases

{accepted_lines}

## Key Results

- The smaller quasi-vertical known-neighbor case is accepted
  `{small_known['accepted']}` with map residual max
  `{small_known['map_residual_max_norm']:.6g}`.
- The free-time quasi-DRO known-neighbor case from members 4, 5 to 6 is
  accepted `{free_known['accepted']}` with map residual max
  `{free_known['map_residual_max_norm']:.6g}`.
- The bounded forward free-time diagnostic from members 5 and 6 is accepted
  `{free_forward['accepted']}` and reaches
  `{free_forward['max_abs_z_km']:.6g}` km, with map residual max
  `{free_forward['map_residual_max_norm']:.6g}`, curve Jacobi span
  `{free_forward['curve_jacobi_span']:.6g}`, and ten-return Jacobi span
  `{free_forward['ten_return_jacobi_span']:.6g}`.
- The accepted parameter-aware quasi-DRO state is archived in
  `data/computed/chapter3_route_b_parameter_aware_palc_states.npz`
  as schema `1.1`; this state archive is diagnostic only and is not an
  accepted fixed-time figure source.

## Interpretation

The parameter-aware PALC layout can reproduce known neighbors when mapping time
and mean Jacobi are included in the continuation vector. It can also take one
bounded free-time diagnostic step beyond the stored 11,107 km member. This is
not a McCarthy fixed-mapping-time reproduction and therefore still does not
allow any Fig. 3.16 / Fig. 3.17 source update.

The next fixed-time task is to use this parameter-aware layout to build a
projection or constrained-PALC variant that keeps the McCarthy mapping time
fixed while retaining the improved predictor and scaling information.
"""


def main() -> None:
    rows: list[dict[str, Any]] = []
    state_records: list[tuple[dict[str, Any], ParameterAssembly]] = []
    small = _load_small_members()
    if len(small) >= 3:
        endpoint_condition = max(
            _condition(
                _assemble_parameter_bvp(
                    case_id="small_endpoint_condition",
                    states=small[0].states,
                    phases=small[0].phases_rad,
                    rho=small[0].rotation_angle_rad,
                    mapping_time_days=small[0].mapping_time_days,
                    target_jacobi=small[0].mean_jacobi,
                    reference_states=small[0].states,
                    include_second_phase=True,
                    palc=None,
                ).singular_values
            ),
            1.0,
        )
        rows.extend(_endpoint_case(member, endpoint_condition) for member in small[:3])
        row, assembly = _palc_case(
            case_id="small_parameter_aware_0_1_to_2",
            previous=small[0],
            current=small[1],
            target=small[2],
            endpoint_condition=endpoint_condition,
            fraction=1.0,
            predictor_policy="full_parameter_secant",
        )
        rows.append(row)
        state_records.append((row, assembly))
        row, assembly = _palc_case(
            case_id="small_parameter_aware_target_control",
            previous=small[0],
            current=small[1],
            target=small[2],
            endpoint_condition=endpoint_condition,
            fraction=1.0,
            predictor_policy="target_state_control",
        )
        rows.append(row)
        state_records.append((row, assembly))

    free_time = _load_free_time_members()
    if len(free_time) >= 7:
        endpoint_condition = max(
            _condition(
                _assemble_parameter_bvp(
                    case_id="free_time_endpoint_condition",
                    states=free_time[0].states,
                    phases=free_time[0].phases_rad,
                    rho=free_time[0].rotation_angle_rad,
                    mapping_time_days=free_time[0].mapping_time_days,
                    target_jacobi=free_time[0].mean_jacobi,
                    reference_states=free_time[0].states,
                    include_second_phase=True,
                    palc=None,
                ).singular_values
            ),
            1.0,
        )
        rows.extend(_endpoint_case(member, endpoint_condition) for member in (free_time[0], free_time[6]))
        row, assembly = _palc_case(
            case_id="free_time_parameter_aware_0_1_to_2",
            previous=free_time[0],
            current=free_time[1],
            target=free_time[2],
            endpoint_condition=endpoint_condition,
            fraction=1.0,
            predictor_policy="full_parameter_secant",
        )
        rows.append(row)
        state_records.append((row, assembly))
        row, assembly = _palc_case(
            case_id="free_time_parameter_aware_4_5_to_6",
            previous=free_time[4],
            current=free_time[5],
            target=free_time[6],
            endpoint_condition=endpoint_condition,
            fraction=1.0,
            predictor_policy="full_parameter_secant",
        )
        rows.append(row)
        state_records.append((row, assembly))
        row, assembly = _palc_case(
            case_id="free_time_parameter_aware_forward_from_5_6",
            previous=free_time[5],
            current=free_time[6],
            target=None,
            endpoint_condition=endpoint_condition,
            fraction=1.0,
            predictor_policy="full_parameter_secant_forward",
        )
        rows.append(row)
        state_records.append((row, assembly))

    _write_rows(rows)
    _write_state_archive(state_records)
    DOC_OUTPUT.write_text(_doc_text(rows), encoding="utf-8")
    accepted = [row for row in rows if bool(row["accepted"])]
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}")
    if STATE_OUTPUT.exists():
        print(f"wrote {STATE_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(
        "parameter-aware PALC: "
        f"rows={len(rows)}, accepted={len(accepted)}, "
        f"max_accepted_z={max(float(row['max_abs_z_km']) for row in accepted):.6f} km"
    )


if __name__ == "__main__":
    main()
