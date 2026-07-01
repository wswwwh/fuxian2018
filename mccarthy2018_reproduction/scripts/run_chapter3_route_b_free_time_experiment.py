"""Route B fixed-Jacobi/free-time/free-rho quasi-DRO experiment."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    CorrectedDROFamilyMember,
    chapter3_quasi_dro_validation_row,
    load_corrected_dro_family_csv,
)
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    FixedJacobiFreeTimeRotationCurveCorrection,
    stroboscopic_curve_fixed_jacobi_free_time_rotation_correction,
    stroboscopic_dro_invariant_curve_seed,
)


OUTPUT_FIELDS = (
    "case_id",
    "case_type",
    "status",
    "curve_samples",
    "source_member",
    "initial_mapping_time_days",
    "corrected_mapping_time_days",
    "mapping_time_delta_days",
    "initial_rho",
    "corrected_rho",
    "rho_delta",
    "target_mean_jacobi",
    "mean_jacobi",
    "max_abs_z_km",
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "newton_iterations",
    "condition_estimate",
    "max_correction_norm",
    "mean_correction_norm",
    "accepted",
    "failure_reason",
    "next_action",
)


def _value(value: float | int | str | bool | None) -> str:
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


def _float_from_audit(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "N/A")
    if value == "N/A":
        return None
    return float(value)


def _correction_norms(correction: FixedJacobiFreeTimeRotationCurveCorrection) -> tuple[float, float]:
    if correction.correction_norm_history.size == 0:
        return 0.0, 0.0
    return (
        float(np.max(correction.correction_norm_history)),
        float(np.mean(correction.correction_norm_history)),
    )


def _condition_estimate(correction: FixedJacobiFreeTimeRotationCurveCorrection) -> float | None:
    if correction.jacobian_condition_history.size == 0:
        return None
    return float(np.max(correction.jacobian_condition_history))


def _member_from_route_b(
    member_id: int,
    correction: FixedJacobiFreeTimeRotationCurveCorrection,
    *,
    time_unit_days: float,
    length_unit_km: float,
) -> CorrectedDROFamilyMember:
    jacobi = np.asarray(jacobi_constant(correction.corrected_states, correction.seed.mu), dtype=float)
    displacement = correction.corrected_states[:, 2] - correction.seed.orbit_state[2]
    vertical_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    return CorrectedDROFamilyMember(
        member=member_id,
        curve_indices=np.arange(correction.corrected_states.shape[0]),
        phases_rad=correction.seed.phases.copy(),
        states=correction.corrected_states.copy(),
        jacobi_values=jacobi,
        target_vertical_amplitude_nd=vertical_amplitude,
        target_vertical_amplitude_km=vertical_amplitude * length_unit_km,
        max_abs_z_km=float(np.max(np.abs(correction.corrected_states[:, 2])) * length_unit_km),
        rotation_angle_rad=correction.rotation_angle_rad,
        mapping_time_days=correction.mapping_time * time_unit_days,
        map_residual_norm=float(np.max(correction.final_residual_norms)),
        amplitude_residual=0.0,
        phase_residual=float(correction.phase_residual_history[-1]),
        curve_jacobi_span=float(np.ptp(jacobi)),
    )


def _audit_route_b(
    member: CorrectedDROFamilyMember,
    correction: FixedJacobiFreeTimeRotationCurveCorrection,
    *,
    target_mean_jacobi: float,
    system,
) -> tuple[dict[str, str], bool, str]:
    row = chapter3_quasi_dro_validation_row(
        member,
        system,
        one_map_time_samples=7,
        ten_return_samples=401,
        max_step=0.02,
    )
    map_residual = member.map_residual_norm
    jacobi_span = member.curve_jacobi_span
    phase_error = _float_from_audit(row, "one_map_phase_return_error")
    ten_span = _float_from_audit(row, "ten_return_jacobi_span")
    mean_error = abs(member.mean_jacobi - target_mean_jacobi)
    phase_residual = abs(float(correction.phase_residual_history[-1]))
    failures: list[str] = []
    if map_residual > 1.0e-8:
        failures.append(f"map residual {map_residual:.3e} exceeds 1e-8")
    if jacobi_span > 1.0e-8:
        failures.append(f"curve Jacobi span {jacobi_span:.3e} exceeds 1e-8")
    if phase_error is None or phase_error > 1.0e-8:
        failures.append(
            "one-map phase return unavailable or "
            f"{phase_error:.3e} exceeds 1e-8" if phase_error is not None else "one-map phase return unavailable"
        )
    if ten_span is None or ten_span > 1.0e-8:
        failures.append(
            "ten-return Jacobi span unavailable or "
            f"{ten_span:.3e} exceeds 1e-8" if ten_span is not None else "ten-return Jacobi span unavailable"
        )
    if mean_error > 1.0e-8:
        failures.append(f"mean Jacobi target error {mean_error:.3e} exceeds 1e-8")
    if phase_residual > 1.0e-8:
        failures.append(f"Newton phase residual {phase_residual:.3e} exceeds 1e-8")
    return row, not failures, "; ".join(failures)


def _row(
    *,
    case_id: str,
    case_type: str,
    status: str,
    curve_samples: int,
    source_member: int | str,
    initial_mapping_time_days: float,
    initial_rho: float,
    target_mean_jacobi: float,
    correction: FixedJacobiFreeTimeRotationCurveCorrection | None,
    member: CorrectedDROFamilyMember | None,
    audit_row: dict[str, str] | None,
    accepted: bool,
    failure_reason: str,
    next_action: str,
    time_unit_days: float,
) -> dict[str, str]:
    if correction is None or member is None:
        values: dict[str, float | int | str | bool | None] = {
            "case_id": case_id,
            "case_type": case_type,
            "status": status,
            "curve_samples": curve_samples,
            "source_member": source_member,
            "initial_mapping_time_days": initial_mapping_time_days,
            "corrected_mapping_time_days": None,
            "mapping_time_delta_days": None,
            "initial_rho": initial_rho,
            "corrected_rho": None,
            "rho_delta": None,
            "target_mean_jacobi": target_mean_jacobi,
            "mean_jacobi": None,
            "max_abs_z_km": None,
            "map_residual_norm": None,
            "curve_jacobi_span": None,
            "one_map_phase_return_error": None,
            "ten_return_jacobi_span": None,
            "newton_iterations": None,
            "condition_estimate": None,
            "max_correction_norm": None,
            "mean_correction_norm": None,
            "accepted": accepted,
            "failure_reason": failure_reason,
            "next_action": next_action,
        }
    else:
        max_norm, mean_norm = _correction_norms(correction)
        corrected_mapping_days = correction.mapping_time * time_unit_days
        values = {
            "case_id": case_id,
            "case_type": case_type,
            "status": status,
            "curve_samples": curve_samples,
            "source_member": source_member,
            "initial_mapping_time_days": initial_mapping_time_days,
            "corrected_mapping_time_days": corrected_mapping_days,
            "mapping_time_delta_days": corrected_mapping_days - initial_mapping_time_days,
            "initial_rho": initial_rho,
            "corrected_rho": correction.rotation_angle_rad,
            "rho_delta": correction.rotation_angle_rad - initial_rho,
            "target_mean_jacobi": target_mean_jacobi,
            "mean_jacobi": member.mean_jacobi,
            "max_abs_z_km": member.max_abs_z_km,
            "map_residual_norm": member.map_residual_norm,
            "curve_jacobi_span": member.curve_jacobi_span,
            "one_map_phase_return_error": (
                None if audit_row is None else _float_from_audit(audit_row, "one_map_phase_return_error")
            ),
            "ten_return_jacobi_span": (
                None if audit_row is None else _float_from_audit(audit_row, "ten_return_jacobi_span")
            ),
            "newton_iterations": int(correction.correction_norm_history.shape[0]),
            "condition_estimate": _condition_estimate(correction),
            "max_correction_norm": max_norm,
            "mean_correction_norm": mean_norm,
            "accepted": accepted,
            "failure_reason": failure_reason,
            "next_action": next_action,
        }
    return {field: _value(values[field]) for field in OUTPUT_FIELDS}


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(
    path: Path,
    *,
    endpoint: CorrectedDROFamilyMember,
    rows: list[dict[str, str]],
) -> None:
    accepted_rows = [row for row in rows if row["accepted"] == "True"]
    beyond_10500 = [
        row for row in accepted_rows if row["max_abs_z_km"] != "N/A" and float(row["max_abs_z_km"]) > 10500.0
    ]
    beyond_11000 = [
        row for row in accepted_rows if row["max_abs_z_km"] != "N/A" and float(row["max_abs_z_km"]) > 11000.0
    ]
    correction = rows[0]
    final_accepted = accepted_rows[-1] if accepted_rows else correction
    if correction["accepted"] == "True":
        correction_result = "passed the Route B audit gates"
    else:
        correction_result = f"failed: {correction['failure_reason']}"
    if beyond_10500:
        continuation_result = f"accepted member above 10,500 km: {beyond_10500[0]['case_id']}"
    elif len(rows) > 1:
        continuation_result = "no accepted member exceeded 10,500 km"
    else:
        continuation_result = "not attempted because correction-only reproduction failed"
    next_action = rows[-1]["next_action"]
    drift = final_accepted["mapping_time_delta_days"]
    rho_drift = final_accepted["rho_delta"]
    content = f"""# Chapter 3 Route B Free-Time Experiment

## Purpose

This file records the minimal Route B numerical prototype for the quasi-DRO
endpoint: fixed mean Jacobi, free mapping time, and free rotation angle. It is a
diagnostic branch experiment only; it does not update Figures 3.16 or 3.17 and
does not modify the accepted fixed-mapping-time CSV files.

## Relation To Route B Note

The implementation follows `docs/route_b_formulation_note.md`: unknowns are the
`N` curve states, mapping time `T`, and rotation angle `rho`; residuals are the
stroboscopic map equation, one mean-Jacobi residual, and one curve-tangent phase
condition. Amplitude is reported as an output metric, not enforced.

## Input Endpoint

- Source: `data/computed/chapter3_quasi_dro_palc_family.csv`
- Member: `{endpoint.member}`
- Curve samples: `{endpoint.states.shape[0]}`
- Endpoint mapping time: `{endpoint.mapping_time_days:.16g}` days
- Endpoint rho: `{endpoint.rotation_angle_rad:.16g}` rad
- Endpoint mean Jacobi: `{endpoint.mean_jacobi:.16g}`
- Endpoint max abs z: `{endpoint.max_abs_z_km:.16g}` km

## Correction-Only Result

The correction-only reproduction `{correction_result}`.

- Corrected mapping time: `{correction['corrected_mapping_time_days']}` days
- Mapping time drift: `{correction['mapping_time_delta_days']}` days
- Corrected rho: `{correction['corrected_rho']}` rad
- Rho drift: `{correction['rho_delta']}` rad
- Map residual norm: `{correction['map_residual_norm']}`
- Curve Jacobi span: `{correction['curve_jacobi_span']}`
- One-map phase return error: `{correction['one_map_phase_return_error']}`
- Ten-return Jacobi span: `{correction['ten_return_jacobi_span']}`

## Small-Step Continuation Result

{continuation_result}.

- Accepted member exceeds 10,500 km: `{bool(beyond_10500)}`
- Accepted member exceeds 11,000 km: `{bool(beyond_11000)}`
- Last accepted/diagnostic mapping-time drift: `{drift}` days
- Last accepted/diagnostic rho drift: `{rho_drift}` rad

## Interpretation

Any nonzero mapping-time drift means these rows are diagnostic free-time Route B
members, not constant-mapping-time reproductions. If correction-only passes but
small-step continuation does not cross 10,500 km, the local bottleneck remains
unresolved by this minimal mean-Jacobi/free-time/free-rho prototype.

This experiment neither imports rejected fixed-rotation candidates nor uses
digitized Figure 3.17 extrapolation.

## Next Action

{next_action}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    system = SYSTEMS["earth_moon"]
    length_unit = system.length_unit_km or 1.0
    time_unit = system.time_unit_days or 1.0
    x0 = 1.0 - system.mu - 73800.0 / length_unit
    initial_ydot = 0.53
    initial_half_period = 14.75 / (2.0 * time_unit)

    family_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
    local_path = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_free_time_local_experiment.csv"
    log_path = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_free_time_log.csv"
    doc_path = PROJECT_ROOT / "docs" / "chapter3_route_b_free_time_experiment.md"

    endpoint = load_corrected_dro_family_csv(family_path)[-1]
    seed = stroboscopic_dro_invariant_curve_seed(
        system.mu,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
        vertical_amplitude=endpoint.target_vertical_amplitude_nd,
        samples=endpoint.states.shape[0],
        curve_samples=max(4 * endpoint.states.shape[0], 120),
    )
    if not np.allclose(seed.phases, endpoint.phases_rad, rtol=0.0, atol=1.0e-12):
        raise RuntimeError("Route B endpoint phases do not match the reconstructed seed")

    rows: list[dict[str, str]] = []
    current_correction: FixedJacobiFreeTimeRotationCurveCorrection | None = None
    current_member: CorrectedDROFamilyMember | None = None
    current_source: int | str = endpoint.member

    try:
        correction = stroboscopic_curve_fixed_jacobi_free_time_rotation_correction(
            seed,
            target_jacobi=endpoint.mean_jacobi,
            initial_states=endpoint.states,
            initial_mapping_time=endpoint.mapping_time_days / time_unit,
            initial_rotation_angle_rad=endpoint.rotation_angle_rad,
            phase_reference_states=endpoint.states,
            max_iterations=10,
            tolerance=1.0e-10,
            jacobi_tolerance=1.0e-11,
            phase_tolerance=1.0e-10,
            max_step=0.02,
            max_state_step=5.0e-4,
            max_mapping_time_step=0.01 / time_unit,
            max_rotation_step=0.002,
        )
        member = _member_from_route_b(
            endpoint.member,
            correction,
            time_unit_days=time_unit,
            length_unit_km=length_unit,
        )
        audit_row, accepted, reason = _audit_route_b(
            member,
            correction,
            target_mean_jacobi=endpoint.mean_jacobi,
            system=system,
        )
        next_action = "run small-step fixed-Jacobi continuation" if accepted else "stop; debug formulation or phase condition"
        status = "accepted" if accepted else "failed_audit"
        rows.append(
            _row(
                case_id="route_b_correction_only",
                case_type="correction_only",
                status=status,
                curve_samples=endpoint.states.shape[0],
                source_member=endpoint.member,
                initial_mapping_time_days=endpoint.mapping_time_days,
                initial_rho=endpoint.rotation_angle_rad,
                target_mean_jacobi=endpoint.mean_jacobi,
                correction=correction,
                member=member,
                audit_row=audit_row,
                accepted=accepted,
                failure_reason=reason,
                next_action=next_action,
                time_unit_days=time_unit,
            )
        )
        if accepted:
            current_correction = correction
            current_member = member
    except Exception as exc:  # noqa: BLE001 - numerical experiment logs failures verbatim.
        rows.append(
            _row(
                case_id="route_b_correction_only",
                case_type="correction_only",
                status="exception",
                curve_samples=endpoint.states.shape[0],
                source_member=endpoint.member,
                initial_mapping_time_days=endpoint.mapping_time_days,
                initial_rho=endpoint.rotation_angle_rad,
                target_mean_jacobi=endpoint.mean_jacobi,
                correction=None,
                member=None,
                audit_row=None,
                accepted=False,
                failure_reason=str(exc),
                next_action="stop; debug formulation or phase condition",
                time_unit_days=time_unit,
            )
        )

    if current_correction is not None and current_member is not None:
        jacobi_step = 2.5e-6
        minimum_step = 2.0e-8
        accepted_above_11000 = False
        for attempt in range(1, 9):
            target_jacobi = current_member.mean_jacobi - jacobi_step
            case_id = f"route_b_small_step_{attempt:02d}"
            try:
                correction = stroboscopic_curve_fixed_jacobi_free_time_rotation_correction(
                    seed,
                    target_jacobi=target_jacobi,
                    initial_states=current_correction.corrected_states,
                    initial_mapping_time=current_correction.mapping_time,
                    initial_rotation_angle_rad=current_correction.rotation_angle_rad,
                    phase_reference_states=current_correction.corrected_states,
                    max_iterations=12,
                    tolerance=1.0e-10,
                    jacobi_tolerance=1.0e-10,
                    phase_tolerance=1.0e-10,
                    max_step=0.02,
                    max_state_step=8.0e-4,
                    max_mapping_time_step=0.015 / time_unit,
                    max_rotation_step=0.003,
                )
                member = _member_from_route_b(
                    endpoint.member + attempt,
                    correction,
                    time_unit_days=time_unit,
                    length_unit_km=length_unit,
                )
                audit_row, accepted, reason = _audit_route_b(
                    member,
                    correction,
                    target_mean_jacobi=target_jacobi,
                    system=system,
                )
                if accepted and member.max_abs_z_km > 11000.0:
                    accepted_above_11000 = True
                    next_action = "stop; accepted diagnostic free-time member exceeds 11,000 km"
                elif accepted and member.max_abs_z_km > 10500.0:
                    next_action = "continue branch consistency checks before figure updates"
                elif accepted:
                    next_action = "continue small fixed-Jacobi steps"
                else:
                    next_action = "halve Jacobi step and retry"
                status = "accepted" if accepted else "failed_audit"
                rows.append(
                    _row(
                        case_id=case_id,
                        case_type="small_step",
                        status=status,
                        curve_samples=endpoint.states.shape[0],
                        source_member=current_source,
                        initial_mapping_time_days=current_correction.mapping_time * time_unit,
                        initial_rho=current_correction.rotation_angle_rad,
                        target_mean_jacobi=target_jacobi,
                        correction=correction,
                        member=member,
                        audit_row=audit_row,
                        accepted=accepted,
                        failure_reason=reason,
                        next_action=next_action,
                        time_unit_days=time_unit,
                    )
                )
                if accepted:
                    current_correction = correction
                    current_member = member
                    current_source = case_id
                    if accepted_above_11000:
                        break
                else:
                    jacobi_step *= 0.5
            except Exception as exc:  # noqa: BLE001 - numerical experiment logs failures verbatim.
                rows.append(
                    _row(
                        case_id=case_id,
                        case_type="small_step",
                        status="exception",
                        curve_samples=endpoint.states.shape[0],
                        source_member=current_source,
                        initial_mapping_time_days=current_correction.mapping_time * time_unit,
                        initial_rho=current_correction.rotation_angle_rad,
                        target_mean_jacobi=target_jacobi,
                        correction=None,
                        member=None,
                        audit_row=None,
                        accepted=False,
                        failure_reason=str(exc),
                        next_action="halve Jacobi step and retry",
                        time_unit_days=time_unit,
                    )
                )
                jacobi_step *= 0.5
            if jacobi_step < minimum_step:
                rows[-1]["next_action"] = "stop; Jacobi step fell below minimum diagnostic size"
                break

    accepted_above_10500 = any(
        row["accepted"] == "True"
        and row["max_abs_z_km"] != "N/A"
        and float(row["max_abs_z_km"]) > 10500.0
        for row in rows
    )
    if current_correction is not None and len(rows) > 1 and not accepted_above_10500:
        rows[-1]["next_action"] = (
            "stop; finite Route B small-step budget did not reach 10,500 km; "
            "try phase-condition/scaling refinement or a smaller-family sanity check"
        )

    _write_rows(local_path, rows)
    _write_rows(log_path, rows)
    _write_doc(doc_path, endpoint=endpoint, rows=rows)

    correction_row = rows[0]
    accepted_rows = [row for row in rows if row["accepted"] == "True"]
    beyond_10500 = any(row["max_abs_z_km"] != "N/A" and float(row["max_abs_z_km"]) > 10500.0 for row in accepted_rows)
    beyond_11000 = any(row["max_abs_z_km"] != "N/A" and float(row["max_abs_z_km"]) > 11000.0 for row in accepted_rows)
    print("Route B free-time experiment complete")
    print(f"correction_only_accepted={correction_row['accepted']}")
    print(f"correction_mapping_time_delta_days={correction_row['mapping_time_delta_days']}")
    print(f"correction_rho_delta={correction_row['rho_delta']}")
    print(f"accepted_beyond_10500_km={beyond_10500}")
    print(f"accepted_beyond_11000_km={beyond_11000}")
    print(f"rows_written={len(rows)}")


if __name__ == "__main__":
    main()
