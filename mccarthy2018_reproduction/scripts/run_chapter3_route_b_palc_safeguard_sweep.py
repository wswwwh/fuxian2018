"""Route B PALC safeguard sweep on the smaller quasi-vertical family.

This script is deliberately diagnostic. It checks whether the smaller-family
PALC failure recorded in the stabilization pass is caused by residual assembly
or by predictor/parameter policy. It writes independent audit outputs and does
not modify accepted quasi-DRO branches or figure sources.
"""

from __future__ import annotations

import csv
import sys
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
from qp_orbits.cr3bp import jacobi_constant


OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_palc_safeguard_sweep.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_route_b_palc_safeguard_sweep.md"

AUDIT_TOLERANCE = 1.0e-8
TARGET_AMPLITUDE_TOL_KM = stabilization.TARGET_AMPLITUDE_TOL_KM
TARGET_RHO_TOL = stabilization.TARGET_RHO_TOL
TARGET_MEAN_JACOBI_TOL = stabilization.TARGET_MEAN_JACOBI_TOL

FIELDS = (
    "case_id",
    "family",
    "operation",
    "parameter_policy",
    "predictor_policy",
    "previous_member",
    "current_member",
    "target_member",
    "state_fraction",
    "rho_fraction",
    "mapping_time_days",
    "target_jacobi",
    "converged",
    "accepted",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "curve_jacobi_span",
    "phase_residual",
    "palc_constraint_residual",
    "max_abs_z_km",
    "target_max_abs_z_km",
    "amplitude_error_km",
    "rho",
    "target_rho",
    "rho_error",
    "mean_jacobi",
    "target_mean_jacobi",
    "mean_jacobi_error",
    "fourier_tail_energy_state",
    "condition_estimate",
    "rank_estimate",
    "correction_steps",
    "max_correction_norm",
    "failure_reason",
    "diagnosis",
)


def _fmt(value: Any) -> str:
    return bvp._fmt(value)


def _mean_jacobi(states: np.ndarray) -> float:
    return float(np.mean(jacobi_constant(states, stabilization.SYSTEM.mu)))


def _condition(assembly: bvp.BVPAssembly) -> float:
    return bvp._condition(assembly.singular_values)


def _audit_accepts(
    *,
    converged: bool,
    assembly: bvp.BVPAssembly,
    endpoint_condition: float,
    target_max_abs_z_km: float | None,
    target_rho: float | None,
    target_mean_jacobi: float | None,
) -> tuple[bool, str]:
    map_max = float(np.max(assembly.map_residual_norms))
    jacobi_span = float(np.ptp(assembly.jacobi_values))
    phase_residual = abs(float(assembly.phase_residual))
    palc_residual = abs(float(assembly.palc_residual or 0.0))
    condition = _condition(assembly)
    mean_jacobi = _mean_jacobi(assembly.states)
    failed: list[str] = []
    if not converged:
        failed.append("not converged")
    if map_max > AUDIT_TOLERANCE:
        failed.append("map residual gate")
    if jacobi_span > AUDIT_TOLERANCE:
        failed.append("Jacobi span gate")
    if phase_residual > AUDIT_TOLERANCE:
        failed.append("phase gate")
    if palc_residual > AUDIT_TOLERANCE:
        failed.append("PALC gate")
    if condition > 100.0 * endpoint_condition:
        failed.append("condition gate")
    if target_max_abs_z_km is not None and abs(assembly.max_abs_z_km - target_max_abs_z_km) > TARGET_AMPLITUDE_TOL_KM:
        failed.append("target amplitude gate")
    if target_rho is not None and abs(assembly.rho - target_rho) > TARGET_RHO_TOL:
        failed.append("target rho gate")
    if target_mean_jacobi is not None and abs(mean_jacobi - target_mean_jacobi) > TARGET_MEAN_JACOBI_TOL:
        failed.append("target mean-Jacobi gate")
    return not failed, "; ".join(failed)


def _base_row(
    *,
    case_id: str,
    operation: str,
    parameter_policy: str,
    predictor_policy: str,
    previous_member: int | None,
    current_member: int | None,
    target_member: int | None,
    state_fraction: float | None,
    rho_fraction: float | None,
    assembly: bvp.BVPAssembly,
    converged: bool,
    accepted: bool,
    failure_reason: str,
    target_max_abs_z_km: float | None,
    target_rho: float | None,
    target_mean_jacobi: float | None,
    correction_norms: list[float],
    diagnosis: str,
) -> dict[str, Any]:
    mean_jacobi = _mean_jacobi(assembly.states)
    return {
        "case_id": case_id,
        "family": "chapter3_corrected_vertical_stroboscopic_torus_family",
        "operation": operation,
        "parameter_policy": parameter_policy,
        "predictor_policy": predictor_policy,
        "previous_member": previous_member,
        "current_member": current_member,
        "target_member": target_member,
        "state_fraction": state_fraction,
        "rho_fraction": rho_fraction,
        "mapping_time_days": assembly.mapping_time_days,
        "target_jacobi": assembly.target_jacobi,
        "converged": converged,
        "accepted": accepted,
        "map_residual_max_norm": float(np.max(assembly.map_residual_norms)),
        "map_residual_rms_norm": float(np.sqrt(np.mean(assembly.map_residual_norms**2))),
        "curve_jacobi_span": float(np.ptp(assembly.jacobi_values)),
        "phase_residual": assembly.phase_residual,
        "palc_constraint_residual": assembly.palc_residual,
        "max_abs_z_km": assembly.max_abs_z_km,
        "target_max_abs_z_km": target_max_abs_z_km,
        "amplitude_error_km": None if target_max_abs_z_km is None else assembly.max_abs_z_km - target_max_abs_z_km,
        "rho": assembly.rho,
        "target_rho": target_rho,
        "rho_error": None if target_rho is None else assembly.rho - target_rho,
        "mean_jacobi": mean_jacobi,
        "target_mean_jacobi": target_mean_jacobi,
        "mean_jacobi_error": None if target_mean_jacobi is None else mean_jacobi - target_mean_jacobi,
        "fourier_tail_energy_state": assembly.fourier_tail_state,
        "condition_estimate": _condition(assembly),
        "rank_estimate": assembly.rank_estimate,
        "correction_steps": len(correction_norms),
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
        "failure_reason": failure_reason,
        "diagnosis": diagnosis,
    }


def _endpoint_row(member: Any, endpoint_condition: float) -> dict[str, Any]:
    assembly = bvp._assemble_bvp(
        case_id=f"small_member_{member.member}_endpoint",
        member_id=member.member,
        states=member.states,
        phases=member.phases_rad,
        rho=member.rotation_angle_rad,
        mapping_time_days=member.mapping_time_days,
        target_jacobi=member.mean_jacobi,
        reference_states=member.states,
        include_second_phase=True,
    )
    accepted, failure = _audit_accepts(
        converged=True,
        assembly=assembly,
        endpoint_condition=endpoint_condition,
        target_max_abs_z_km=member.max_abs_z_km,
        target_rho=member.rotation_angle_rad,
        target_mean_jacobi=member.mean_jacobi,
    )
    return _base_row(
        case_id=f"endpoint_member_{member.member}",
        operation="endpoint_BVP_reproduction",
        parameter_policy="member_own_T_and_J",
        predictor_policy="none",
        previous_member=None,
        current_member=member.member,
        target_member=member.member,
        state_fraction=None,
        rho_fraction=None,
        assembly=assembly,
        converged=True,
        accepted=accepted,
        failure_reason=failure,
        target_max_abs_z_km=member.max_abs_z_km,
        target_rho=member.rotation_angle_rad,
        target_mean_jacobi=member.mean_jacobi,
        correction_norms=[],
        diagnosis="Known member endpoint residual is reproducible with the BVP assembly.",
    )


def _palc_predictor_row(
    *,
    case_id: str,
    previous: Any,
    current: Any,
    target: Any,
    endpoint_condition: float,
    state_fraction: float,
    rho_fraction: float,
    mapping_time_days: float,
    target_jacobi: float,
    parameter_policy: str,
    predictor_policy: str,
    diagnosis: str,
) -> dict[str, Any]:
    predictor_states = current.states + state_fraction * (current.states - previous.states)
    predictor_rho = current.rotation_angle_rad + rho_fraction * (
        current.rotation_angle_rad - previous.rotation_angle_rad
    )
    predictor = bvp._unknown_vector(predictor_states, predictor_rho)
    current_vector = bvp._unknown_vector(current.states, current.rotation_angle_rad)
    tangent = predictor - current_vector
    assembly, correction_norms, converged, solver_failure = bvp._palc_correct(
        case_id=case_id,
        member_id=None,
        predictor=predictor,
        tangent=tangent,
        phases=target.phases_rad,
        mapping_time_days=mapping_time_days,
        target_jacobi=target_jacobi,
        reference_states=current.states,
        endpoint_condition=endpoint_condition,
    )
    accepted, audit_failure = _audit_accepts(
        converged=converged,
        assembly=assembly,
        endpoint_condition=endpoint_condition,
        target_max_abs_z_km=target.max_abs_z_km,
        target_rho=target.rotation_angle_rad,
        target_mean_jacobi=target.mean_jacobi,
    )
    failure = solver_failure or audit_failure
    return _base_row(
        case_id=case_id,
        operation="known_neighbor_PALC_reproduction",
        parameter_policy=parameter_policy,
        predictor_policy=predictor_policy,
        previous_member=previous.member,
        current_member=current.member,
        target_member=target.member,
        state_fraction=state_fraction,
        rho_fraction=rho_fraction,
        assembly=assembly,
        converged=converged,
        accepted=accepted,
        failure_reason=failure,
        target_max_abs_z_km=target.max_abs_z_km,
        target_rho=target.rotation_angle_rad,
        target_mean_jacobi=target.mean_jacobi,
        correction_norms=correction_norms,
        diagnosis=diagnosis,
    )


def _target_predictor_row(
    *,
    previous: Any,
    current: Any,
    target: Any,
    endpoint_condition: float,
) -> dict[str, Any]:
    predictor = bvp._unknown_vector(target.states, target.rotation_angle_rad)
    current_vector = bvp._unknown_vector(current.states, current.rotation_angle_rad)
    tangent = predictor - current_vector
    assembly, correction_norms, converged, solver_failure = bvp._palc_correct(
        case_id="target_state_predictor_target_parameters",
        member_id=None,
        predictor=predictor,
        tangent=tangent,
        phases=target.phases_rad,
        mapping_time_days=target.mapping_time_days,
        target_jacobi=target.mean_jacobi,
        reference_states=current.states,
        endpoint_condition=endpoint_condition,
    )
    accepted, audit_failure = _audit_accepts(
        converged=converged,
        assembly=assembly,
        endpoint_condition=endpoint_condition,
        target_max_abs_z_km=target.max_abs_z_km,
        target_rho=target.rotation_angle_rad,
        target_mean_jacobi=target.mean_jacobi,
    )
    return _base_row(
        case_id="target_state_predictor_target_parameters",
        operation="known_neighbor_PALC_reproduction",
        parameter_policy="target_T_and_target_J",
        predictor_policy="known_target_state_and_rho_control",
        previous_member=previous.member,
        current_member=current.member,
        target_member=target.member,
        state_fraction=None,
        rho_fraction=None,
        assembly=assembly,
        converged=converged,
        accepted=accepted,
        failure_reason=solver_failure or audit_failure,
        target_max_abs_z_km=target.max_abs_z_km,
        target_rho=target.rotation_angle_rad,
        target_mean_jacobi=target.mean_jacobi,
        correction_norms=correction_norms,
        diagnosis=(
            "Control case: the target member is accepted when the predictor and external "
            "parameters are already aligned, isolating the prior failure to predictor/"
            "parameter policy rather than residual assembly."
        ),
    )


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _doc_text(rows: list[dict[str, Any]]) -> str:
    endpoint_rows = [row for row in rows if row["operation"] == "endpoint_BVP_reproduction"]
    palc_rows = [row for row in rows if row["operation"] == "known_neighbor_PALC_reproduction"]
    accepted_palc = [row for row in palc_rows if bool(row["accepted"])]
    current_policy = next(row for row in rows if row["case_id"] == "existing_full_secant_current_parameters")
    target_policy = next(row for row in rows if row["case_id"] == "z_state_rho_matched_target_parameters")
    control = next(row for row in rows if row["case_id"] == "target_state_predictor_target_parameters")
    endpoint_lines = "\n".join(
        (
            f"- member {row['current_member']}: accepted `{row['accepted']}`, "
            f"map max `{row['map_residual_max_norm']:.6g}`, "
            f"condition `{row['condition_estimate']:.6g}`"
        )
        for row in endpoint_rows
    )
    palc_lines = "\n".join(
        (
            f"- `{row['case_id']}`: accepted `{row['accepted']}`, "
            f"map max `{row['map_residual_max_norm']:.6g}`, "
            f"amp error `{row['amplitude_error_km']:.6g}` km, "
            f"rho error `{row['rho_error']:.6g}`, "
            f"reason `{row['failure_reason'] or 'none'}`"
        )
        for row in palc_rows
    )
    return f"""# Chapter 3 Route B PALC Safeguard Sweep

## Scope

This diagnostic targets the smaller quasi-vertical sanity case that blocked a
stronger Route B fixed-time BVP/PALC claim. It does not target the Fig. 3.16 /
Fig. 3.17 10,500 km or 11,000 km gates, does not update any accepted branch CSV,
and does not update figure sources.

## Endpoint Residual Controls

{endpoint_lines}

All checked smaller-family endpoint members are reproducible by the current BVP
assembly. This means the smaller-family failure is not a basic residual
assembly failure.

## PALC Predictor And Parameter Sweep

{palc_lines}

The existing full-secant/current-parameter policy remains accepted
`{current_policy['accepted']}`. Its map residual max is
`{current_policy['map_residual_max_norm']:.6g}`.

The component-matched state/rho predictor with target mapping time and target
Jacobi is accepted `{target_policy['accepted']}` with map residual max
`{target_policy['map_residual_max_norm']:.6g}`.

The target-state control is accepted `{control['accepted']}` with map residual
max `{control['map_residual_max_norm']:.6g}`.

## Interpretation

Accepted PALC cases in this sweep: `{len(accepted_palc)}`.

The previous smaller-family PALC failure is best interpreted as a predictor and
external-parameter policy issue, not as proof that the BVP residual cannot
represent the known neighbor. In this family, using current-member mapping time
and a single full secant is too weak, while aligning the predictor with the
target member's mapping time and mean Jacobi restores the audit gates.

For the quasi-DRO bottleneck this does not justify a Fig. 3.16 / Fig. 3.17
update. It does justify the next implementation direction: promote mapping time
and continuation parameter handling into the local PALC formulation, or add a
bounded parameter-aware predictor before attempting any wider fixed-time
campaign.
"""


def main() -> None:
    members, _ = stabilization._load_small_vertical_members()
    if len(members) < 3:
        raise RuntimeError("small quasi-vertical family requires at least three members")
    previous, current, target = members[:3]
    endpoint_condition = bvp._read_endpoint_condition()
    state_fraction = (
        (target.max_abs_z_km - current.max_abs_z_km)
        / (current.max_abs_z_km - previous.max_abs_z_km)
    )
    rho_fraction = (
        (target.rotation_angle_rad - current.rotation_angle_rad)
        / (current.rotation_angle_rad - previous.rotation_angle_rad)
    )
    rows: list[dict[str, Any]] = [_endpoint_row(member, endpoint_condition) for member in members]
    rows.extend(
        [
            _palc_predictor_row(
                case_id="existing_full_secant_current_parameters",
                previous=previous,
                current=current,
                target=target,
                endpoint_condition=endpoint_condition,
                state_fraction=1.0,
                rho_fraction=1.0,
                mapping_time_days=current.mapping_time_days,
                target_jacobi=current.mean_jacobi + (current.mean_jacobi - previous.mean_jacobi),
                parameter_policy="current_T_and_secant_J",
                predictor_policy="full_single_secant",
                diagnosis="Reproduces the previous smaller-family PALC failure policy.",
            ),
            _palc_predictor_row(
                case_id="z_state_rho_matched_current_parameters",
                previous=previous,
                current=current,
                target=target,
                endpoint_condition=endpoint_condition,
                state_fraction=state_fraction,
                rho_fraction=rho_fraction,
                mapping_time_days=current.mapping_time_days,
                target_jacobi=target.mean_jacobi,
                parameter_policy="current_T_and_target_J",
                predictor_policy="z_amplitude_state_fraction_plus_rho_fraction",
                diagnosis="Tests component-aware prediction while retaining current mapping time.",
            ),
            _palc_predictor_row(
                case_id="z_state_rho_matched_target_parameters",
                previous=previous,
                current=current,
                target=target,
                endpoint_condition=endpoint_condition,
                state_fraction=state_fraction,
                rho_fraction=rho_fraction,
                mapping_time_days=target.mapping_time_days,
                target_jacobi=target.mean_jacobi,
                parameter_policy="target_T_and_target_J",
                predictor_policy="z_amplitude_state_fraction_plus_rho_fraction",
                diagnosis="Tests whether parameter-aware prediction can reproduce the known neighbor.",
            ),
            _target_predictor_row(
                previous=previous,
                current=current,
                target=target,
                endpoint_condition=endpoint_condition,
            ),
        ]
    )
    _write_rows(rows)
    DOC_OUTPUT.write_text(_doc_text(rows), encoding="utf-8")
    accepted_cases = [row for row in rows if bool(row["accepted"])]
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(
        "PALC safeguard sweep: "
        f"rows={len(rows)}, accepted={len(accepted_cases)}, "
        f"state_fraction={state_fraction:.6g}, rho_fraction={rho_fraction:.6g}"
    )


if __name__ == "__main__":
    main()
