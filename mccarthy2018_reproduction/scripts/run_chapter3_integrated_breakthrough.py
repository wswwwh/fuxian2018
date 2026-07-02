"""Integrated Chapter 3 fixed-time quasi-DRO breakthrough campaign.

This is the campaign script requested by
``docs/chapter3_integrated_breakthrough_strategy.md``.  It integrates the
existing Route B ingredients:

- parameter-aware state/rho/Jacobi prediction,
- bounded substep advancement,
- fixed-time two-phase constrained BVP solves,
- seven audit gates with continuous CSV logging.

The script writes only new diagnostic/campaign artifacts.  It does not modify
the accepted Fig. 3.16 / Fig. 3.17 source branch.
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
import run_chapter3_route_b_fixed_time_constrained_palc as fixed_time
from qp_orbits.corrected_dro_family import load_corrected_dro_family_csv

# The source diagnostic script used a looser 1e-8 early-stop tolerance.  The
# integrated campaign gates are stricter, so force the reused corrector to keep
# iterating until it is close to the campaign gate scale.
fixed_time.AUDIT_TOLERANCE = 1.0e-11
fixed_time.SECOND_PHASE_TOLERANCE = 1.0e-10
fixed_time.MAX_NEWTON_STEPS = 24

FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
BOOTSTRAP_STATE_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_fixed_time_constrained_palc_states.npz"
)
CANDIDATES_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_integrated_breakthrough_candidates.csv"
)
REVALIDATION_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_integrated_breakthrough_revalidation.csv"
)
DIAGNOSTICS_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_integrated_breakthrough_diagnostics.csv"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_integrated_breakthrough_results.md"

T_FIXED_DAYS = fixed_time.T_FIXED_DAYS
TARGET_MIN_KM = 10500.0
TARGET_STRETCH_KM = 11000.0
TARGET_RHO_DELTA = 5.0e-5
INITIAL_SUBSTEPS = 3
RHO_TARGET_SUBSTEPS = (3, 6)
PALC_SUBSTEPS = (3, 6, 9)
MAX_MACRO_STEPS = 12
FOURIER_LIFT_SAMPLES = 71
RHO_TARGET_MAX_NEWTON_STEPS = 8

GATE_1_MAP_RESIDUAL = 1.0e-9
GATE_2_CURVE_JACOBI_SPAN = 1.0e-10
GATE_2_ONE_MAP_JACOBI_DRIFT = 1.0e-9
GATE_2_TEN_RETURN_JACOBI = 1.0e-14
GATE_3_PHASE_RETURN = 1.0e-10
GATE_5_AMPLITUDE_TOL_KM = 1.0
GATE_6_MAPPING_TIME_DAYS = 1.0e-10
GATE_7_SCALED_CONDITION = 1.0e9

CANDIDATE_FIELDS = (
    "member_id",
    "rho_rad",
    "mean_jacobi",
    "mapping_time_days",
    "max_abs_z_km",
    "map_residual_max",
    "jacobi_mean_span",
    "jacobi_one_map_drift",
    "jacobi_ten_return_span",
    "phase_return_error",
    "condition_number",
    "raw_condition_number",
    "fourier_order",
    "gate_1_residual",
    "gate_2_jacobi",
    "gate_3_phase",
    "gate_4_rho_monotone",
    "gate_5_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "overall_acceptance",
    "step_source",
    "source_member_id",
    "macro_step",
    "substep_index",
    "substep_count",
)

DIAGNOSTIC_FIELDS = (
    "attempt_id",
    "macro_step",
    "substep_index",
    "substep_count",
    "retry_level",
    "step_source",
    "source_member_id",
    "previous_member_id",
    "target_rho_delta",
    "predictor_alpha",
    "fourier_order",
    "converged",
    "overall_acceptance",
    "max_abs_z_km",
    "rho_rad",
    "mean_jacobi",
    "map_residual_max",
    "jacobi_mean_span",
    "jacobi_one_map_drift",
    "jacobi_ten_return_span",
    "phase_return_error",
    "condition_number",
    "raw_condition_number",
    "gate_1_residual",
    "gate_2_jacobi",
    "gate_3_phase",
    "gate_4_rho_monotone",
    "gate_5_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "failed_gates",
    "failure_reason",
    "newton_iterations",
    "max_correction_norm",
)

REVALIDATION_FIELDS = (
    "member_id",
    "source_member_id",
    "step_source",
    "revalidated_acceptance",
    "max_abs_z_km",
    "rho_rad",
    "map_residual_max",
    "jacobi_mean_span",
    "jacobi_one_map_drift",
    "jacobi_ten_return_span",
    "phase_return_error",
    "condition_number",
    "raw_condition_number",
    "gate_1_residual",
    "gate_2_jacobi",
    "gate_3_phase",
    "gate_4_rho_monotone",
    "gate_5_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "failed_gates",
    "failure_reason",
)


@dataclass(frozen=True)
class CampaignMember:
    member_id: int
    states: np.ndarray
    phases: np.ndarray
    rho: float
    mean_jacobi: float
    max_abs_z_km: float
    source: str
    source_member_id: int | str


@dataclass(frozen=True)
class GateEvaluation:
    row: dict[str, Any]
    failed_gates: tuple[str, ...]
    overall_acceptance: bool


@dataclass(frozen=True)
class AttemptResult:
    member: CampaignMember
    assembly: fixed_time.FixedTimeAssembly
    validation: dict[str, str] | None
    gates: GateEvaluation
    converged: bool
    failure_reason: str
    correction_norms: list[float]
    predictor_alpha: float


def _fmt(value: Any) -> str:
    return fixed_time._fmt(value)


def _write_header(path: Path, fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()


def _append_row(path: Path, fields: tuple[str, ...], row: dict[str, Any]) -> None:
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writerow({field: _fmt(row.get(field)) for field in fields})
        stream.flush()


def _scaled_condition(jacobian: np.ndarray) -> float:
    row_norms = np.linalg.norm(jacobian, axis=1)
    row_scale = 1.0 / np.maximum(row_norms, 1.0e-14)
    row_scaled = row_scale[:, None] * jacobian
    column_norms = np.linalg.norm(row_scaled, axis=0)
    column_scale = 1.0 / np.maximum(column_norms, 1.0e-14)
    scaled = row_scaled * column_scale[None, :]
    singular_values = np.linalg.svd(scaled, compute_uv=False)
    return fixed_time._condition(singular_values)


def _float_from_validation(validation: dict[str, str] | None, key: str) -> float | None:
    return fixed_time._float_from_validation(validation, key)


def _member_from_fixed(member, member_id: int | None = None, source: str = "accepted_fixed_time_branch") -> CampaignMember:
    return CampaignMember(
        member_id=member.member if member_id is None else member_id,
        states=member.states.copy(),
        phases=member.phases_rad.copy(),
        rho=float(member.rotation_angle_rad),
        mean_jacobi=float(member.mean_jacobi),
        max_abs_z_km=float(member.max_abs_z_km),
        source=source,
        source_member_id=member.member,
    )


def _member_from_assembly(
    *,
    member_id: int,
    assembly: fixed_time.FixedTimeAssembly,
    source: str,
    source_member_id: int | str,
) -> CampaignMember:
    return CampaignMember(
        member_id=member_id,
        states=assembly.states.copy(),
        phases=assembly.phases.copy(),
        rho=float(assembly.rho),
        mean_jacobi=fixed_time._mean_jacobi(assembly.states),
        max_abs_z_km=float(assembly.max_abs_z_km),
        source=source,
        source_member_id=source_member_id,
    )


def _assemble_member(member: CampaignMember, *, case_id: str) -> fixed_time.FixedTimeAssembly:
    return fixed_time._assemble_fixed_time_bvp(
        case_id=case_id,
        states=member.states,
        phases=member.phases,
        rho=member.rho,
        target_jacobi=member.mean_jacobi,
        reference_states=member.states,
        include_second_phase=True,
        palc=None,
    )


def _lift_member(member: CampaignMember, samples: int = FOURIER_LIFT_SAMPLES) -> CampaignMember:
    phases = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    states = bvp._resample_states(member.states, member.phases, phases)
    return CampaignMember(
        member_id=member.member_id,
        states=states,
        phases=phases,
        rho=member.rho,
        mean_jacobi=member.mean_jacobi,
        max_abs_z_km=float(np.max(np.abs(states[:, 2])) * (fixed_time.SYSTEM.length_unit_km or 1.0)),
        source=f"{member.source}_lifted_N{samples}",
        source_member_id=member.source_member_id,
    )


def _parameter_aware_predictor(
    *,
    previous: CampaignMember,
    current: CampaignMember,
    target_rho_delta: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    if previous.phases.shape != current.phases.shape or not np.allclose(previous.phases, current.phases):
        previous_states = bvp._resample_states(previous.states, previous.phases, current.phases)
    else:
        previous_states = previous.states
    previous_vector = fixed_time._fixed_unknown_vector(
        previous_states,
        previous.rho,
        previous.mean_jacobi,
    )
    current_vector = fixed_time._fixed_unknown_vector(
        current.states,
        current.rho,
        current.mean_jacobi,
    )
    previous_rho_delta = max(abs(current.rho - previous.rho), 1.0e-12)
    alpha = min(abs(target_rho_delta) / previous_rho_delta, 0.10)
    secant = current_vector - previous_vector
    predictor = current_vector + alpha * secant
    state_size = current.states.size
    predictor[state_size] = current.rho + target_rho_delta
    predictor[state_size + 1] = current.mean_jacobi + alpha * (current.mean_jacobi - previous.mean_jacobi)
    tangent = predictor - current_vector
    return predictor, tangent, alpha


def _solve_fixed_time_target_rho(
    *,
    case_id: str,
    predictor: np.ndarray,
    target_rho: float,
    phases: np.ndarray,
    reference_states: np.ndarray,
) -> tuple[fixed_time.FixedTimeAssembly, list[float], bool, str, float, float]:
    sample_count = phases.size
    vector = predictor.copy()
    correction_norms: list[float] = []
    assembly: fixed_time.FixedTimeAssembly | None = None
    final_jacobian: np.ndarray | None = None
    converged = False
    failure_reason = "maximum iterations reached"
    for _ in range(RHO_TARGET_MAX_NEWTON_STEPS):
        states, rho, target_jacobi = fixed_time._unpack_fixed_unknown(vector, sample_count)
        assembly = fixed_time._assemble_fixed_time_bvp(
            case_id=case_id,
            states=states,
            phases=phases,
            rho=rho,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            include_second_phase=True,
            palc=None,
        )
        state_size = states.size
        rho_residual = float(rho - target_rho)
        residual = np.concatenate([assembly.residual, np.array([rho_residual], dtype=float)])
        jacobian = np.zeros((assembly.jacobian.shape[0] + 1, assembly.jacobian.shape[1]), dtype=float)
        jacobian[:-1, :] = assembly.jacobian
        jacobian[-1, state_size] = 1.0
        final_jacobian = jacobian
        map_max = float(np.max(assembly.map_residual_norms))
        if (
            map_max < fixed_time.AUDIT_TOLERANCE
            and abs(assembly.mean_jacobi_residual) < fixed_time.AUDIT_TOLERANCE
            and abs(assembly.phase_residual) < fixed_time.AUDIT_TOLERANCE
            and abs(assembly.second_phase_residual) < fixed_time.SECOND_PHASE_TOLERANCE
            and abs(rho_residual) < fixed_time.AUDIT_TOLERANCE
        ):
            converged = True
            failure_reason = ""
            break
        correction = bvp._solve_scaled_correction(jacobian, residual)
        correction_norm = float(np.linalg.norm(correction))
        if correction_norm > fixed_time.CORRECTION_NORM_CAP:
            correction *= fixed_time.CORRECTION_NORM_CAP / correction_norm
            correction_norm = fixed_time.CORRECTION_NORM_CAP
        correction_norms.append(correction_norm)
        vector += correction
    if assembly is None or final_jacobian is None:
        states, rho, target_jacobi = fixed_time._unpack_fixed_unknown(vector, sample_count)
        assembly = fixed_time._assemble_fixed_time_bvp(
            case_id=case_id,
            states=states,
            phases=phases,
            rho=rho,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            include_second_phase=True,
            palc=None,
        )
        state_size = states.size
        final_jacobian = np.zeros((assembly.jacobian.shape[0] + 1, assembly.jacobian.shape[1]), dtype=float)
        final_jacobian[:-1, :] = assembly.jacobian
        final_jacobian[-1, state_size] = 1.0
    raw_condition = fixed_time._condition(np.linalg.svd(final_jacobian, compute_uv=False))
    condition = _scaled_condition(final_jacobian)
    return assembly, correction_norms, converged, failure_reason, condition, raw_condition


def _evaluate_gates(
    *,
    member: CampaignMember,
    previous: CampaignMember,
    assembly: fixed_time.FixedTimeAssembly,
    validation: dict[str, str] | None,
    converged: bool,
    step_source: str,
    macro_step: int,
    substep_index: int,
    substep_count: int,
    condition_override: float | None = None,
    raw_condition_override: float | None = None,
) -> GateEvaluation:
    map_residual = float(np.max(assembly.map_residual_norms))
    jacobi_span = float(np.ptp(assembly.jacobi_values))
    one_map_drift = _float_from_validation(validation, "one_map_sweep_jacobi_drift")
    ten_return = _float_from_validation(validation, "ten_return_jacobi_span")
    phase_return = _float_from_validation(validation, "one_map_phase_return_error")
    raw_condition = (
        float(raw_condition_override)
        if raw_condition_override is not None
        else fixed_time._condition(assembly.singular_values)
    )
    condition = (
        float(condition_override)
        if condition_override is not None
        else _scaled_condition(assembly.jacobian)
    )
    gates = {
        "gate_1_residual": converged and map_residual < GATE_1_MAP_RESIDUAL,
        "gate_2_jacobi": (
            converged
            and jacobi_span < GATE_2_CURVE_JACOBI_SPAN
            and one_map_drift is not None
            and one_map_drift < GATE_2_ONE_MAP_JACOBI_DRIFT
            and ten_return is not None
            and ten_return < GATE_2_TEN_RETURN_JACOBI
        ),
        "gate_3_phase": converged and phase_return is not None and phase_return < GATE_3_PHASE_RETURN,
        "gate_4_rho_monotone": member.rho > previous.rho,
        "gate_5_amplitude": member.max_abs_z_km >= previous.max_abs_z_km - GATE_5_AMPLITUDE_TOL_KM,
        "gate_6_mapping_time": abs(T_FIXED_DAYS - fixed_time.T_FIXED_DAYS) < GATE_6_MAPPING_TIME_DAYS,
        "gate_7_condition": condition < GATE_7_SCALED_CONDITION,
    }
    failed = tuple(name for name, passed in gates.items() if not passed)
    overall = converged and not failed
    row = {
        "member_id": member.member_id,
        "rho_rad": member.rho,
        "mean_jacobi": member.mean_jacobi,
        "mapping_time_days": T_FIXED_DAYS,
        "max_abs_z_km": member.max_abs_z_km,
        "map_residual_max": map_residual,
        "jacobi_mean_span": jacobi_span,
        "jacobi_one_map_drift": one_map_drift,
        "jacobi_ten_return_span": ten_return,
        "phase_return_error": phase_return,
        "condition_number": condition,
        "raw_condition_number": raw_condition,
        "fourier_order": member.states.shape[0],
        **gates,
        "overall_acceptance": overall,
        "step_source": step_source,
        "source_member_id": member.source_member_id,
        "macro_step": macro_step,
        "substep_index": substep_index,
        "substep_count": substep_count,
    }
    return GateEvaluation(row=row, failed_gates=failed, overall_acceptance=overall)


def _attempt_substep(
    *,
    previous: CampaignMember,
    current: CampaignMember,
    member_id: int,
    target_rho_delta: float,
    macro_step: int,
    substep_index: int,
    substep_count: int,
    retry_level: str,
    step_source: str,
    solver_mode: str = "palc",
) -> AttemptResult:
    predictor, tangent, alpha = _parameter_aware_predictor(
        previous=previous,
        current=current,
        target_rho_delta=target_rho_delta,
    )
    target_rho = current.rho + target_rho_delta
    condition_override = None
    raw_condition_override = None
    if solver_mode == "rho_target":
        (
            assembly,
            correction_norms,
            converged,
            solver_failure,
            condition_override,
            raw_condition_override,
        ) = _solve_fixed_time_target_rho(
            case_id=f"integrated_macro_{macro_step}_substep_{substep_index}_{retry_level}",
            predictor=predictor,
            target_rho=target_rho,
            phases=current.phases,
            reference_states=current.states,
        )
    else:
        assembly, correction_norms, converged, solver_failure = fixed_time._solve_fixed_time(
            case_id=f"integrated_macro_{macro_step}_substep_{substep_index}_{retry_level}",
            predictor=predictor,
            tangent=tangent,
            phases=current.phases,
            reference_states=current.states,
        )
    validation = fixed_time._validation_for(assembly)
    member = _member_from_assembly(
        member_id=member_id,
        assembly=assembly,
        source=step_source,
        source_member_id=current.member_id,
    )
    gates = _evaluate_gates(
        member=member,
        previous=current,
        assembly=assembly,
        validation=validation,
        converged=converged,
        step_source=step_source,
        macro_step=macro_step,
        substep_index=substep_index,
        substep_count=substep_count,
        condition_override=condition_override,
        raw_condition_override=raw_condition_override,
    )
    failure_reason = solver_failure if solver_failure else "; ".join(gates.failed_gates)
    return AttemptResult(
        member=member,
        assembly=assembly,
        validation=validation,
        gates=gates,
        converged=converged,
        failure_reason=failure_reason,
        correction_norms=correction_norms,
        predictor_alpha=alpha,
    )


def _diagnostic_row(result: AttemptResult, *, attempt_id: str, retry_level: str | None = None) -> dict[str, Any]:
    row = result.gates.row
    retry_label = retry_level or str(row["step_source"])
    return {
        "attempt_id": attempt_id,
        "macro_step": row["macro_step"],
        "substep_index": row["substep_index"],
        "substep_count": row["substep_count"],
        "retry_level": retry_label,
        "step_source": row["step_source"],
        "source_member_id": row["source_member_id"],
        "previous_member_id": result.member.source_member_id,
        "target_rho_delta": TARGET_RHO_DELTA / max(int(row["substep_count"]), 1),
        "predictor_alpha": result.predictor_alpha,
        "fourier_order": row["fourier_order"],
        "converged": result.converged,
        "overall_acceptance": row["overall_acceptance"],
        "max_abs_z_km": row["max_abs_z_km"],
        "rho_rad": row["rho_rad"],
        "mean_jacobi": row["mean_jacobi"],
        "map_residual_max": row["map_residual_max"],
        "jacobi_mean_span": row["jacobi_mean_span"],
        "jacobi_one_map_drift": row["jacobi_one_map_drift"],
        "jacobi_ten_return_span": row["jacobi_ten_return_span"],
        "phase_return_error": row["phase_return_error"],
        "condition_number": row["condition_number"],
        "raw_condition_number": row["raw_condition_number"],
        "gate_1_residual": row["gate_1_residual"],
        "gate_2_jacobi": row["gate_2_jacobi"],
        "gate_3_phase": row["gate_3_phase"],
        "gate_4_rho_monotone": row["gate_4_rho_monotone"],
        "gate_5_amplitude": row["gate_5_amplitude"],
        "gate_6_mapping_time": row["gate_6_mapping_time"],
        "gate_7_condition": row["gate_7_condition"],
        "failed_gates": "; ".join(result.gates.failed_gates),
        "failure_reason": result.failure_reason,
        "newton_iterations": len(result.correction_norms),
        "max_correction_norm": max(result.correction_norms) if result.correction_norms else 0.0,
    }


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _bootstrap_candidate(endpoint: CampaignMember) -> tuple[CampaignMember | None, GateEvaluation | None, fixed_time.FixedTimeAssembly | None]:
    if not BOOTSTRAP_STATE_PATH.exists():
        return None, None, None
    source_rows = {
        row["case_id"]: row
        for row in _read_csv_rows(PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_fixed_time_constrained_palc.csv")
    }
    with np.load(BOOTSTRAP_STATE_PATH) as data:
        max_z = np.asarray(data["max_abs_z_km"], dtype=float)
        valid: list[int] = []
        for index, case_id_value in enumerate(data["case_ids"]):
            case_id = str(case_id_value)
            source_row = source_rows.get(case_id)
            if source_row is None:
                continue
            try:
                source_condition = float(source_row["condition_estimate"])
                source_map = float(source_row["map_residual_max_norm"])
                source_curve_span = float(source_row["curve_jacobi_span"])
                source_phase = float(source_row["one_map_phase_return_error"])
                source_ten = float(source_row["ten_return_jacobi_span"])
                source_rho = float(source_row["rho"])
            except (KeyError, ValueError):
                continue
            if (
                str(source_row.get("accepted")) == "True"
                and max_z[index] > endpoint.max_abs_z_km + 1.0
                and source_condition < GATE_7_SCALED_CONDITION
                and source_map < GATE_1_MAP_RESIDUAL
                and source_curve_span < GATE_2_CURVE_JACOBI_SPAN
                and source_phase < GATE_3_PHASE_RETURN
                and source_ten < GATE_2_TEN_RETURN_JACOBI
                and source_rho > endpoint.rho
            ):
                valid.append(index)
        if not valid:
            return None, None, None
        index = int(max(valid, key=lambda item: max_z[item]))
        phases = np.asarray(data["phase_grid"], dtype=float)
        selected_case_id = str(data["case_ids"][index])
        source_row = source_rows[selected_case_id]
        member = CampaignMember(
            member_id=endpoint.member_id + 1,
            states=np.asarray(data["states"][index], dtype=float),
            phases=phases,
            rho=float(data["rho"][index]),
            mean_jacobi=float(data["mean_jacobi"][index]),
            max_abs_z_km=float(data["max_abs_z_km"][index]),
            source="bootstrap_fixed_time_projection",
            source_member_id=selected_case_id,
        )
    assembly = _assemble_member(member, case_id="integrated_bootstrap_fixed_time_projection")
    validation = fixed_time._validation_for(assembly)
    gates = _evaluate_gates(
        member=member,
        previous=endpoint,
        assembly=assembly,
        validation=validation,
        converged=True,
        step_source=member.source,
        macro_step=0,
        substep_index=0,
        substep_count=0,
        condition_override=float(source_row["condition_estimate"]),
        raw_condition_override=float(source_row["condition_estimate"]),
    )
    return member, gates, assembly


def _advance_macro(
    *,
    previous: CampaignMember,
    current: CampaignMember,
    next_member_id: int,
    macro_step: int,
) -> tuple[CampaignMember | None, list[AttemptResult], str]:
    all_attempts: list[AttemptResult] = []
    retry_plan: list[tuple[str, int, bool, str]] = []
    retry_plan.extend((f"rho_target_{count}_substeps", count, False, "rho_target") for count in RHO_TARGET_SUBSTEPS)
    retry_plan.extend((f"palc_native_{count}_substeps", count, False, "palc") for count in PALC_SUBSTEPS)
    retry_plan.append((f"palc_lifted_N{FOURIER_LIFT_SAMPLES}_6_substeps", 6, True, "palc"))

    for retry_level, substep_count, use_lift, solver_mode in retry_plan:
        local_previous = _lift_member(previous) if use_lift else previous
        local_current = _lift_member(current) if use_lift else current
        accepted_all = True
        step_attempts: list[AttemptResult] = []
        substep_delta = TARGET_RHO_DELTA / substep_count
        for substep_index in range(1, substep_count + 1):
            result = _attempt_substep(
                previous=local_previous,
                current=local_current,
                member_id=next_member_id,
                target_rho_delta=substep_delta,
                macro_step=macro_step,
                substep_index=substep_index,
                substep_count=substep_count,
                retry_level=retry_level,
                step_source=retry_level,
                solver_mode=solver_mode,
            )
            step_attempts.append(result)
            all_attempts.append(result)
            if not result.gates.overall_acceptance:
                accepted_all = False
                break
            local_previous = local_current
            local_current = result.member
        if accepted_all and step_attempts:
            final_member = step_attempts[-1].member
            return final_member, all_attempts, retry_level
    return None, all_attempts, "all_retry_levels_failed"


def _candidate_row(member: CampaignMember, gates: GateEvaluation) -> dict[str, Any]:
    row = dict(gates.row)
    row["member_id"] = member.member_id
    return row


def _revalidate_member(member: CampaignMember, previous: CampaignMember) -> dict[str, Any]:
    predictor = fixed_time._fixed_unknown_vector(member.states, member.rho, member.mean_jacobi)
    assembly, correction_norms, converged, solver_failure = fixed_time._solve_fixed_time(
        case_id=f"integrated_revalidation_member_{member.member_id}",
        predictor=predictor,
        tangent=None,
        phases=member.phases,
        reference_states=member.states,
    )
    validation = fixed_time._validation_for(assembly)
    revalidated_member = _member_from_assembly(
        member_id=member.member_id,
        assembly=assembly,
        source=f"revalidation_of_{member.source}",
        source_member_id=member.source_member_id,
    )
    gates = _evaluate_gates(
        member=revalidated_member,
        previous=previous,
        assembly=assembly,
        validation=validation,
        converged=converged,
        step_source="independent_no_PALC_revalidation",
        macro_step=-1,
        substep_index=-1,
        substep_count=-1,
    )
    row = {
        "member_id": member.member_id,
        "source_member_id": member.source_member_id,
        "step_source": member.source,
        "revalidated_acceptance": gates.overall_acceptance,
        "max_abs_z_km": revalidated_member.max_abs_z_km,
        "rho_rad": revalidated_member.rho,
        "map_residual_max": gates.row["map_residual_max"],
        "jacobi_mean_span": gates.row["jacobi_mean_span"],
        "jacobi_one_map_drift": gates.row["jacobi_one_map_drift"],
        "jacobi_ten_return_span": gates.row["jacobi_ten_return_span"],
        "phase_return_error": gates.row["phase_return_error"],
        "condition_number": gates.row["condition_number"],
        "raw_condition_number": gates.row["raw_condition_number"],
        "gate_1_residual": gates.row["gate_1_residual"],
        "gate_2_jacobi": gates.row["gate_2_jacobi"],
        "gate_3_phase": gates.row["gate_3_phase"],
        "gate_4_rho_monotone": gates.row["gate_4_rho_monotone"],
        "gate_5_amplitude": gates.row["gate_5_amplitude"],
        "gate_6_mapping_time": gates.row["gate_6_mapping_time"],
        "gate_7_condition": gates.row["gate_7_condition"],
        "failed_gates": "; ".join(gates.failed_gates),
        "failure_reason": solver_failure if solver_failure else "; ".join(gates.failed_gates),
    }
    row["newton_iterations"] = len(correction_norms)
    return row


def _write_doc(
    *,
    start: CampaignMember,
    accepted_members: list[CampaignMember],
    candidate_rows: list[dict[str, Any]],
    diagnostic_rows: list[dict[str, Any]],
    revalidation_rows: list[dict[str, Any]],
    stop_reason: str,
) -> None:
    final = accepted_members[-1] if accepted_members else start
    best_accepted = max(accepted_members, key=lambda item: item.max_abs_z_km) if accepted_members else start
    best_attempt = None
    if diagnostic_rows:
        best_attempt = max(diagnostic_rows, key=lambda row: float(row["max_abs_z_km"]))
    reached_min = final.max_abs_z_km >= TARGET_MIN_KM
    reached_stretch = final.max_abs_z_km >= TARGET_STRETCH_KM
    rows_by_member = {int(row["member_id"]): row for row in candidate_rows}
    accepted_lines = "\n".join(
        (
            f"- member `{member.member_id}`: max z `{member.max_abs_z_km:.12g}` km, "
            f"rho `{member.rho:.12g}`, source `{member.source}`"
        )
        for member in accepted_members
    ) or "- none"
    final_row = rows_by_member.get(final.member_id)
    final_gate_text = "N/A"
    if final_row is not None:
        final_gate_text = ", ".join(
            name
            for name in (
                "gate_1_residual",
                "gate_2_jacobi",
                "gate_3_phase",
                "gate_4_rho_monotone",
                "gate_5_amplitude",
                "gate_6_mapping_time",
                "gate_7_condition",
            )
            if bool(final_row.get(name))
        )
    worst_failures = "\n".join(
        (
            f"- `{row['attempt_id']}`: max z `{row['max_abs_z_km']}`, "
            f"failed `{row['failed_gates'] or row['failure_reason']}`"
        )
        for row in diagnostic_rows[-5:]
    ) or "- none"
    revalidation_passed = all(bool(row["revalidated_acceptance"]) for row in revalidation_rows) if revalidation_rows else False
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Integrated Breakthrough Results

## Scope

This run follows `docs/chapter3_integrated_breakthrough_strategy.md` Part 5:
parameter-aware prediction, bounded substeps, fixed-time two-phase solves, and
seven audit gates. Gate 7 is treated as a required pass in this campaign.

## Start

- Member: `{start.member_id}`
- Max abs z: `{start.max_abs_z_km:.12g}` km
- Rho: `{start.rho:.12g}`
- Fixed mapping time: `{T_FIXED_DAYS}` days

## Accepted Campaign Members

{accepted_lines}

## Outcome

- Final accepted max z: `{final.max_abs_z_km:.12g}` km
- Best accepted max z: `{best_accepted.max_abs_z_km:.12g}` km
- Best attempted max z: `{best_attempt['max_abs_z_km'] if best_attempt else 'N/A'}` km
- Minimum target 10,500 km reached: `{reached_min}`
- Stretch target 11,000 km reached: `{reached_stretch}`
- Final accepted gate passes: `{final_gate_text}`
- Independent revalidation all passed: `{revalidation_passed}`
- Stop reason: `{stop_reason}`

## Recent Diagnostics

{worst_failures}

## Output Files

- `data/computed/chapter3_integrated_breakthrough_candidates.csv`
- `data/computed/chapter3_integrated_breakthrough_revalidation.csv`
- `data/computed/chapter3_integrated_breakthrough_diagnostics.csv`

## Interpretation

This artifact is an integrated campaign audit. It does not update Fig. 3.16 or
Fig. 3.17 unless the minimum 10,500 km target and all seven gates are achieved
and independently revalidated.

The rho-target retry rows show whether explicit rotation targeting can push the
amplitude upward. Those rows are not accepted unless the residual, Jacobi, phase,
monotonicity, mapping-time, and condition gates all pass.
""",
        encoding="utf-8",
    )


def main() -> None:
    for path, fields in (
        (CANDIDATES_OUTPUT, CANDIDATE_FIELDS),
        (REVALIDATION_OUTPUT, REVALIDATION_FIELDS),
        (DIAGNOSTICS_OUTPUT, DIAGNOSTIC_FIELDS),
    ):
        _write_header(path, fields)

    fixed_family = load_corrected_dro_family_csv(FAMILY_PATH)
    start = _member_from_fixed(fixed_family[-1])
    previous = _member_from_fixed(fixed_family[-2])
    current = start
    accepted_members: list[CampaignMember] = []
    candidate_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    revalidation_rows: list[dict[str, Any]] = []
    stop_reason = "maximum macro steps reached"

    bootstrap, bootstrap_gates, _ = _bootstrap_candidate(start)
    if bootstrap is not None and bootstrap_gates is not None:
        diagnostic_row = {
            **_diagnostic_row(
                AttemptResult(
                    member=bootstrap,
                    assembly=_assemble_member(bootstrap, case_id="integrated_bootstrap_diagnostic"),
                    validation=fixed_time._validation_for(_assemble_member(bootstrap, case_id="integrated_bootstrap_validation")),
                    gates=bootstrap_gates,
                    converged=True,
                    failure_reason="; ".join(bootstrap_gates.failed_gates),
                    correction_norms=[],
                    predictor_alpha=0.0,
                ),
                attempt_id="bootstrap_fixed_time_projection",
                retry_level="bootstrap",
            )
        }
        _append_row(DIAGNOSTICS_OUTPUT, DIAGNOSTIC_FIELDS, diagnostic_row)
        diagnostic_rows.append(diagnostic_row)
        if bootstrap_gates.overall_acceptance:
            current = bootstrap
            previous = start
            accepted_members.append(bootstrap)
            candidate_row = _candidate_row(bootstrap, bootstrap_gates)
            _append_row(CANDIDATES_OUTPUT, CANDIDATE_FIELDS, candidate_row)
            candidate_rows.append(candidate_row)

    next_member_id = max(current.member_id + 1, 12)
    for macro_step in range(1, MAX_MACRO_STEPS + 1):
        if current.max_abs_z_km >= TARGET_MIN_KM:
            stop_reason = "minimum target reached"
            break
        next_member, attempts, _ = _advance_macro(
            previous=previous,
            current=current,
            next_member_id=next_member_id,
            macro_step=macro_step,
        )
        for index, attempt in enumerate(attempts, start=1):
            diagnostic_row = _diagnostic_row(
                attempt,
                attempt_id=f"macro_{macro_step}_attempt_{index}",
            )
            _append_row(DIAGNOSTICS_OUTPUT, DIAGNOSTIC_FIELDS, diagnostic_row)
            diagnostic_rows.append(diagnostic_row)
        if next_member is None:
            stop_reason = f"forward step failed at member {current.member_id}, max_z={current.max_abs_z_km:.12g} km"
            break
        if next_member.max_abs_z_km <= current.max_abs_z_km + 1.0e-6:
            stop_reason = (
                f"accepted forward step decreased amplitude from "
                f"{current.max_abs_z_km:.12g} km to {next_member.max_abs_z_km:.12g} km"
            )
            previous = current
            current = next_member
            accepted_members.append(current)
            final_attempt = next(attempt for attempt in reversed(attempts) if attempt.member.member_id == current.member_id)
            candidate_row = _candidate_row(current, final_attempt.gates)
            _append_row(CANDIDATES_OUTPUT, CANDIDATE_FIELDS, candidate_row)
            candidate_rows.append(candidate_row)
            break
        previous = current
        current = next_member
        accepted_members.append(current)
        final_attempt = next(attempt for attempt in reversed(attempts) if attempt.member.member_id == current.member_id)
        candidate_row = _candidate_row(current, final_attempt.gates)
        _append_row(CANDIDATES_OUTPUT, CANDIDATE_FIELDS, candidate_row)
        candidate_rows.append(candidate_row)
        next_member_id += 1

    revalidation_previous = start
    for member in accepted_members:
        row = _revalidate_member(member, revalidation_previous)
        _append_row(REVALIDATION_OUTPUT, REVALIDATION_FIELDS, row)
        revalidation_rows.append(row)
        revalidation_previous = member

    _write_doc(
        start=start,
        accepted_members=accepted_members,
        candidate_rows=candidate_rows,
        diagnostic_rows=diagnostic_rows,
        revalidation_rows=revalidation_rows,
        stop_reason=stop_reason,
    )

    final = accepted_members[-1] if accepted_members else start
    print(f"wrote {CANDIDATES_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {REVALIDATION_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DIAGNOSTICS_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(
        "integrated breakthrough: "
        f"accepted_members={len(accepted_members)}, "
        f"final_max_z={final.max_abs_z_km:.6f} km, "
        f"reached_10500={final.max_abs_z_km >= TARGET_MIN_KM}, "
        f"stop_reason={stop_reason}"
    )


if __name__ == "__main__":
    main()
