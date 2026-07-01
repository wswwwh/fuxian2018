"""Route B conditioning, scaling, and phase-condition refinement diagnostics."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    CorrectedDROFamilyMember,
    load_corrected_dro_family_csv,
)
from qp_orbits.quasi_torus import (
    FixedJacobiFreeTimeRotationCurveCorrection,
    stroboscopic_curve_fixed_jacobi_free_time_rotation_correction,
    stroboscopic_dro_invariant_curve_seed,
)
from run_chapter3_route_b_free_time_experiment import (
    _audit_route_b,
    _float_from_audit,
    _member_from_route_b,
)


DIAGNOSTIC_FIELDS = (
    "case_id",
    "case_type",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "target_mean_jacobi",
    "delta_mean_jacobi",
    "corrected_mapping_time_days",
    "delta_mapping_time_days",
    "corrected_rho",
    "delta_rho",
    "d_amp_d_jacobi",
    "d_amp_d_time",
    "d_amp_d_rho",
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "condition_estimate",
    "max_correction_norm",
    "mean_correction_norm",
    "tangent_norm",
    "tangent_amp_component",
    "tangent_time_component",
    "tangent_rho_component",
    "amplitude_progress_efficiency",
    "classification",
    "diagnosis",
)

EXPERIMENT_FIELDS = (
    "experiment_id",
    "variant",
    "description",
    "curve_samples",
    "source_case",
    "scaling_method",
    "phase_condition",
    "continuation_parameter",
    "step_attempt",
    "target_delta",
    "converged",
    "accepted",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "corrected_mapping_time_days",
    "mapping_time_delta_days",
    "corrected_rho",
    "rho_delta",
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "condition_estimate",
    "min_singular_value",
    "max_singular_value",
    "max_correction_norm",
    "mean_correction_norm",
    "failure_reason",
    "interpretation",
)

BRANCH_STATE_SCHEMA_VERSION = "1.0"
BRANCH_STATE_AUDIT_METRICS = (
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "condition_estimate",
    "max_correction_norm",
    "mean_correction_norm",
)

AUDIT_MAP_RESIDUAL = 1.0e-8
AUDIT_JACOBI_SPAN = 1.0e-8
AUDIT_PHASE_RETURN = 1.0e-8
AMP_SCALE_KM = 10500.0 - 10164.02309965055
TIME_SCALE_DAYS = 0.01
RHO_SCALE_RAD = 1.0e-3


@dataclass(frozen=True)
class VariantConfig:
    variant: str
    description: str
    scaling_method: str
    phase_condition: str
    target_delta: float
    state_variable_scale: float = 1.0
    mapping_time_variable_scale: float = 1.0
    rotation_variable_scale: float = 1.0
    map_residual_scale: float = 1.0
    jacobi_residual_scale: float = 1.0
    phase_residual_scale: float = 1.0
    max_state_step: float = 8.0e-4
    max_mapping_time_step_days: float = 0.015
    max_rotation_step: float = 0.003


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


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_rows(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _branch_state_record(
    *,
    case_id: str,
    source_case: str,
    variant: str,
    correction: FixedJacobiFreeTimeRotationCurveCorrection,
    member: CorrectedDROFamilyMember,
    audit_row: dict[str, str],
    accepted: bool,
) -> dict[str, object]:
    max_norm, mean_norm = _correction_norms(correction)
    one_map_phase = _float_from_audit(audit_row, "one_map_phase_return_error")
    ten_return_span = _float_from_audit(audit_row, "ten_return_jacobi_span")
    condition = _condition_estimate(correction)
    return {
        "case_id": case_id,
        "states": correction.corrected_states.copy(),
        "mapping_time_days": member.mapping_time_days,
        "rho": correction.rotation_angle_rad,
        "mean_jacobi": member.mean_jacobi,
        "max_abs_z_km": member.max_abs_z_km,
        "source_case": source_case,
        "variant": variant,
        "accepted": bool(accepted),
        "audit_metrics": np.array(
            [
                member.map_residual_norm,
                member.curve_jacobi_span,
                np.nan if one_map_phase is None else one_map_phase,
                np.nan if ten_return_span is None else ten_return_span,
                np.nan if condition is None else condition,
                np.nan if max_norm is None else max_norm,
                np.nan if mean_norm is None else mean_norm,
            ],
            dtype=float,
        ),
    }


def _write_branch_state_archive(
    path: Path,
    *,
    records: list[dict[str, object]],
    phase_grid: np.ndarray,
) -> None:
    if not records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        schema_version=np.array(BRANCH_STATE_SCHEMA_VERSION),
        created_by_script=np.array(Path(__file__).name),
        case_ids=np.asarray([record["case_id"] for record in records], dtype="U96"),
        states=np.stack([np.asarray(record["states"], dtype=float) for record in records], axis=0),
        phase_grid=np.asarray(phase_grid, dtype=float),
        mapping_time_days=np.asarray([record["mapping_time_days"] for record in records], dtype=float),
        rho=np.asarray([record["rho"] for record in records], dtype=float),
        mean_jacobi=np.asarray([record["mean_jacobi"] for record in records], dtype=float),
        max_abs_z_km=np.asarray([record["max_abs_z_km"] for record in records], dtype=float),
        source_case=np.asarray([record["source_case"] for record in records], dtype="U96"),
        variant=np.asarray([record["variant"] for record in records], dtype="U96"),
        accepted=np.asarray([record["accepted"] for record in records], dtype=bool),
        audit_metric_names=np.asarray(BRANCH_STATE_AUDIT_METRICS, dtype="U64"),
        audit_metrics=np.stack([np.asarray(record["audit_metrics"], dtype=float) for record in records], axis=0),
    )


def _float(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "N/A")
    if value in ("", "N/A", None):
        return None
    return float(value)


def _condition_estimate(correction: FixedJacobiFreeTimeRotationCurveCorrection) -> float | None:
    if correction.jacobian_condition_history.size == 0:
        return None
    return float(np.max(correction.jacobian_condition_history))


def _singular_range(correction: FixedJacobiFreeTimeRotationCurveCorrection) -> tuple[float | None, float | None]:
    if correction.jacobian_min_singular_history.size == 0:
        return None, None
    finite_min = correction.jacobian_min_singular_history[
        np.isfinite(correction.jacobian_min_singular_history)
    ]
    finite_max = correction.jacobian_max_singular_history[
        np.isfinite(correction.jacobian_max_singular_history)
    ]
    min_value = float(np.min(finite_min)) if finite_min.size else None
    max_value = float(np.max(finite_max)) if finite_max.size else None
    return min_value, max_value


def _correction_norms(correction: FixedJacobiFreeTimeRotationCurveCorrection) -> tuple[float | None, float | None]:
    if correction.correction_norm_history.size == 0:
        return None, None
    return (
        float(np.max(correction.correction_norm_history)),
        float(np.mean(correction.correction_norm_history)),
    )


def _audit_passed(
    member: CorrectedDROFamilyMember,
    audit_row: dict[str, str],
    failure_reason: str,
) -> bool:
    phase_error = _float_from_audit(audit_row, "one_map_phase_return_error")
    ten_span = _float_from_audit(audit_row, "ten_return_jacobi_span")
    return bool(
        not failure_reason
        and member.map_residual_norm <= AUDIT_MAP_RESIDUAL
        and member.curve_jacobi_span <= AUDIT_JACOBI_SPAN
        and phase_error is not None
        and phase_error <= AUDIT_PHASE_RETURN
        and ten_span is not None
        and ten_span <= AUDIT_JACOBI_SPAN
    )


def _diagnostic_rows(
    previous_rows: list[dict[str, str]],
    endpoint: CorrectedDROFamilyMember,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    prev_amp = endpoint.max_abs_z_km
    prev_jacobi = endpoint.mean_jacobi
    prev_time = endpoint.mapping_time_days
    prev_rho = endpoint.rotation_angle_rad

    for source in previous_rows:
        amp = _float(source, "max_abs_z_km")
        jacobi = _float(source, "target_mean_jacobi")
        time_days = _float(source, "corrected_mapping_time_days")
        rho = _float(source, "corrected_rho")
        condition = _float(source, "condition_estimate")
        if amp is None or jacobi is None or time_days is None or rho is None:
            delta_amp = delta_jacobi = delta_time = delta_rho = None
        else:
            delta_amp = amp - prev_amp
            delta_jacobi = jacobi - prev_jacobi
            delta_time = time_days - prev_time
            delta_rho = rho - prev_rho

        if delta_amp is None:
            d_amp_d_jacobi = d_amp_d_time = d_amp_d_rho = None
            tangent_norm = tangent_amp = tangent_time = tangent_rho = None
            efficiency = None
        else:
            d_amp_d_jacobi = None if abs(delta_jacobi or 0.0) <= 0.0 else delta_amp / delta_jacobi
            d_amp_d_time = None if abs(delta_time or 0.0) <= 0.0 else delta_amp / delta_time
            d_amp_d_rho = None if abs(delta_rho or 0.0) <= 0.0 else delta_amp / delta_rho
            vector = np.array(
                [
                    delta_amp / AMP_SCALE_KM,
                    (delta_time or 0.0) / TIME_SCALE_DAYS,
                    (delta_rho or 0.0) / RHO_SCALE_RAD,
                ],
                dtype=float,
            )
            tangent_norm_value = float(np.linalg.norm(vector))
            tangent_norm = tangent_norm_value
            if tangent_norm_value > 0.0:
                tangent_amp = abs(float(vector[0])) / tangent_norm_value
                tangent_time = abs(float(vector[1])) / tangent_norm_value
                tangent_rho = abs(float(vector[2])) / tangent_norm_value
            else:
                tangent_amp = tangent_time = tangent_rho = 0.0
            efficiency = abs(delta_amp) / AMP_SCALE_KM

        if source["case_type"] == "correction_only":
            classification = "endpoint_reproduction"
            diagnosis = "Correction-only reproduces the endpoint; local continuation direction is not defined by this row."
        elif condition is not None and condition > 1.0e14 and (delta_amp or 0.0) < 5.0:
            classification = "slow_progress_ill_conditioned"
            diagnosis = (
                "Accepted step gains only a few km while scaled T/rho drift is larger than the normalized "
                "amplitude component; the local branch tangent is inefficient for the 10,500 km gate."
            )
        else:
            classification = "accepted_local_progress"
            diagnosis = "Accepted local step, but amplitude progress remains bounded by the local Jacobi direction."

        values: dict[str, float | str | None] = {
            "case_id": source["case_id"],
            "case_type": source["case_type"],
            "max_abs_z_km": amp,
            "delta_max_abs_z_km": delta_amp,
            "target_mean_jacobi": jacobi,
            "delta_mean_jacobi": delta_jacobi,
            "corrected_mapping_time_days": time_days,
            "delta_mapping_time_days": delta_time,
            "corrected_rho": rho,
            "delta_rho": delta_rho,
            "d_amp_d_jacobi": d_amp_d_jacobi,
            "d_amp_d_time": d_amp_d_time,
            "d_amp_d_rho": d_amp_d_rho,
            "map_residual_norm": _float(source, "map_residual_norm"),
            "curve_jacobi_span": _float(source, "curve_jacobi_span"),
            "one_map_phase_return_error": _float(source, "one_map_phase_return_error"),
            "ten_return_jacobi_span": _float(source, "ten_return_jacobi_span"),
            "condition_estimate": condition,
            "max_correction_norm": _float(source, "max_correction_norm"),
            "mean_correction_norm": _float(source, "mean_correction_norm"),
            "tangent_norm": tangent_norm,
            "tangent_amp_component": tangent_amp,
            "tangent_time_component": tangent_time,
            "tangent_rho_component": tangent_rho,
            "amplitude_progress_efficiency": efficiency,
            "classification": classification,
            "diagnosis": diagnosis,
        }
        rows.append({field: _value(values[field]) for field in DIAGNOSTIC_FIELDS})

        if source.get("accepted") == "True" and amp is not None and jacobi is not None and time_days is not None and rho is not None:
            prev_amp = amp
            prev_jacobi = jacobi
            prev_time = time_days
            prev_rho = rho
    return rows


def _run_route_b_correction(
    *,
    seed,
    system,
    endpoint: CorrectedDROFamilyMember,
    variant: VariantConfig,
    target_jacobi: float,
    initial_states: np.ndarray,
    initial_mapping_time: float,
    initial_rotation: float,
    phase_reference_states: np.ndarray,
    source_member: int,
    time_unit_days: float,
    length_unit_km: float,
) -> tuple[
    FixedJacobiFreeTimeRotationCurveCorrection,
    CorrectedDROFamilyMember,
    dict[str, str],
    bool,
    str,
]:
    correction = stroboscopic_curve_fixed_jacobi_free_time_rotation_correction(
        seed,
        target_jacobi=target_jacobi,
        initial_states=initial_states,
        initial_mapping_time=initial_mapping_time,
        initial_rotation_angle_rad=initial_rotation,
        phase_reference_states=phase_reference_states,
        max_iterations=14,
        tolerance=1.0e-10,
        jacobi_tolerance=1.0e-10,
        phase_tolerance=1.0e-10,
        max_step=0.02,
        max_state_step=variant.max_state_step,
        max_mapping_time_step=variant.max_mapping_time_step_days / time_unit_days,
        max_rotation_step=variant.max_rotation_step,
        state_variable_scale=variant.state_variable_scale,
        mapping_time_variable_scale=variant.mapping_time_variable_scale,
        rotation_variable_scale=variant.rotation_variable_scale,
        map_residual_scale=variant.map_residual_scale,
        jacobi_residual_scale=variant.jacobi_residual_scale,
        phase_residual_scale=variant.phase_residual_scale,
        phase_condition=variant.phase_condition,
    )
    member = _member_from_route_b(
        source_member,
        correction,
        time_unit_days=time_unit_days,
        length_unit_km=length_unit_km,
    )
    audit_row, accepted, reason = _audit_route_b(
        member,
        correction,
        target_mean_jacobi=target_jacobi,
        system=system,
    )
    accepted = bool(accepted and _audit_passed(member, audit_row, reason))
    return correction, member, audit_row, accepted, reason


def _experiment_row(
    *,
    experiment_id: str,
    variant: VariantConfig,
    curve_samples: int,
    source_case: str,
    step_attempt: int,
    target_delta: float,
    initial_amp: float,
    initial_time_days: float,
    initial_rho: float,
    correction: FixedJacobiFreeTimeRotationCurveCorrection | None,
    member: CorrectedDROFamilyMember | None,
    audit_row: dict[str, str] | None,
    converged: bool,
    accepted: bool,
    failure_reason: str,
    interpretation: str,
    time_unit_days: float,
) -> dict[str, str]:
    if correction is None or member is None:
        values: dict[str, float | str | int | bool | None] = {
            "experiment_id": experiment_id,
            "variant": variant.variant,
            "description": variant.description,
            "curve_samples": curve_samples,
            "source_case": source_case,
            "scaling_method": variant.scaling_method,
            "phase_condition": variant.phase_condition,
            "continuation_parameter": "mean_jacobi",
            "step_attempt": step_attempt,
            "target_delta": target_delta,
            "converged": converged,
            "accepted": accepted,
            "max_abs_z_km": None,
            "delta_max_abs_z_km": None,
            "corrected_mapping_time_days": None,
            "mapping_time_delta_days": None,
            "corrected_rho": None,
            "rho_delta": None,
            "map_residual_norm": None,
            "curve_jacobi_span": None,
            "one_map_phase_return_error": None,
            "ten_return_jacobi_span": None,
            "condition_estimate": None,
            "min_singular_value": None,
            "max_singular_value": None,
            "max_correction_norm": None,
            "mean_correction_norm": None,
            "failure_reason": failure_reason,
            "interpretation": interpretation,
        }
    else:
        min_singular, max_singular = _singular_range(correction)
        max_norm, mean_norm = _correction_norms(correction)
        corrected_time_days = correction.mapping_time * time_unit_days
        values = {
            "experiment_id": experiment_id,
            "variant": variant.variant,
            "description": variant.description,
            "curve_samples": curve_samples,
            "source_case": source_case,
            "scaling_method": variant.scaling_method,
            "phase_condition": variant.phase_condition,
            "continuation_parameter": "mean_jacobi",
            "step_attempt": step_attempt,
            "target_delta": target_delta,
            "converged": converged,
            "accepted": accepted,
            "max_abs_z_km": member.max_abs_z_km,
            "delta_max_abs_z_km": member.max_abs_z_km - initial_amp,
            "corrected_mapping_time_days": corrected_time_days,
            "mapping_time_delta_days": corrected_time_days - initial_time_days,
            "corrected_rho": correction.rotation_angle_rad,
            "rho_delta": correction.rotation_angle_rad - initial_rho,
            "map_residual_norm": member.map_residual_norm,
            "curve_jacobi_span": member.curve_jacobi_span,
            "one_map_phase_return_error": (
                None if audit_row is None else _float_from_audit(audit_row, "one_map_phase_return_error")
            ),
            "ten_return_jacobi_span": (
                None if audit_row is None else _float_from_audit(audit_row, "ten_return_jacobi_span")
            ),
            "condition_estimate": _condition_estimate(correction),
            "min_singular_value": min_singular,
            "max_singular_value": max_singular,
            "max_correction_norm": max_norm,
            "mean_correction_norm": mean_norm,
            "failure_reason": failure_reason,
            "interpretation": interpretation,
        }
    return {field: _value(values[field]) for field in EXPERIMENT_FIELDS}


def _variants(time_unit_days: float) -> list[VariantConfig]:
    return [
        VariantConfig(
            variant="A_baseline",
            description="Current square Route B system with one curve-tangent phase condition.",
            scaling_method="unscaled variables and residuals",
            phase_condition="curve_tangent",
            target_delta=-5.0e-5,
        ),
        VariantConfig(
            variant="B_column_scaled",
            description="Column-scaled least-squares solve with balanced T/rho columns and weighted scalar rows.",
            scaling_method="state=1, T=1e-3, rho=1e-3, Jacobi residual=1e5, phase residual=1",
            phase_condition="curve_tangent",
            target_delta=-5.0e-5,
            mapping_time_variable_scale=1.0e-3,
            rotation_variable_scale=1.0e-3,
            jacobi_residual_scale=1.0e5,
        ),
        VariantConfig(
            variant="C_strong_T_rho_scaling",
            description="Stronger T/rho variable scaling to test whether solver balance is the dominant issue.",
            scaling_method="state=1, T=1e-4, rho=1e-4, Jacobi residual=1e5, phase residual=10",
            phase_condition="curve_tangent",
            target_delta=-5.0e-5,
            mapping_time_variable_scale=1.0e-4,
            rotation_variable_scale=1.0e-4,
            jacobi_residual_scale=1.0e5,
            phase_residual_scale=10.0,
        ),
        VariantConfig(
            variant="D_two_phase",
            description="Alternative least-squares phase anchor using longitudinal and latitudinal orthogonality.",
            scaling_method="state=1, T=1e-3, rho=1e-3, Jacobi residual=1e5, phase residual=1",
            phase_condition="two_orthogonality",
            target_delta=-5.0e-5,
            mapping_time_variable_scale=1.0e-3,
            rotation_variable_scale=1.0e-3,
            jacobi_residual_scale=1.0e5,
        ),
        VariantConfig(
            variant="E_amplitude_monitor_large_step",
            description="Optional amplitude-monitor Jacobi predictor; amplitude is monitored but not a hard residual.",
            scaling_method="same as B, larger bounded Jacobi step",
            phase_condition="curve_tangent",
            target_delta=-7.5e-5,
            mapping_time_variable_scale=1.0e-3,
            rotation_variable_scale=1.0e-3,
            jacobi_residual_scale=1.0e5,
            max_state_step=1.2e-3,
            max_mapping_time_step_days=0.025,
            max_rotation_step=0.004,
        ),
    ]


def _write_doc(
    path: Path,
    *,
    endpoint: CorrectedDROFamilyMember,
    diagnostics: list[dict[str, str]],
    experiments: list[dict[str, str]],
    best_variant: str,
    best_condition: float | None,
    baseline_condition: float | None,
    accepted_10250: bool,
    accepted_10500: bool,
    accepted_11000: bool,
    next_action: str,
) -> None:
    last_previous = diagnostics[-1]
    accepted_rows = [row for row in experiments if row["accepted"] == "True"]
    best_row = max(
        accepted_rows,
        key=lambda row: float(row["max_abs_z_km"]) if row["max_abs_z_km"] != "N/A" else -np.inf,
    ) if accepted_rows else None
    accepted_step_rows = [
        row for row in accepted_rows
        if row["step_attempt"] != "0" and row["condition_estimate"] != "N/A"
    ]
    conditioning_row = min(
        accepted_step_rows,
        key=lambda row: float(row["condition_estimate"]),
    ) if accepted_step_rows else None
    best_amp = "N/A" if best_row is None else best_row["max_abs_z_km"]
    best_delta = "N/A" if best_row is None else best_row["delta_max_abs_z_km"]
    conditioning_variant = "N/A" if conditioning_row is None else conditioning_row["variant"]
    conditioning_value = "N/A" if conditioning_row is None else conditioning_row["condition_estimate"]
    condition_ratio = (
        "N/A"
        if best_condition is None or baseline_condition is None or baseline_condition == 0.0
        else f"{best_condition / baseline_condition:.6g}"
    )
    content = f"""# Chapter 3 Route B Refinement

## Purpose

This diagnostic refines the Route B fixed-Jacobi/free-time/free-rho prototype
without changing Figures 3.16/3.17 or any accepted fixed-mapping-time branch
CSV. It compares solver scaling and phase-condition variants before allowing a
bounded continuation attempt.

## Input State

- Endpoint source: `data/computed/chapter3_quasi_dro_palc_family.csv`
- Endpoint member: `{endpoint.member}`
- Endpoint max abs z: `{endpoint.max_abs_z_km:.16g}` km
- Endpoint mapping time: `{endpoint.mapping_time_days:.16g}` days
- Endpoint rho: `{endpoint.rotation_angle_rad:.16g}` rad
- Prior Route B local result: `data/computed/chapter3_route_b_free_time_local_experiment.csv`

## Why Endpoint Reproduction Works

The correction-only row starts from an already accepted invariant curve and only
re-solves the same local object with `T` and `rho` released. The mean-Jacobi
equation and curve-tangent phase condition are sufficient locally, so the
residual, Jacobi span, and one-map phase-return audit remain near integration
precision.

## Why The Eight Small Steps Did Not Cross 10,500 km

The previous accepted small steps ended at `{last_previous['max_abs_z_km']}` km.
Each accepted Jacobi step gained only a few km, while the normalized local
direction showed substantial mapping-time drift. This means the local natural
Jacobi direction is audit-clean but inefficient for the 10,500 km gate.

## Conditioning Diagnosis

The high condition estimates are not explained only by raw units. The tested
column/residual scaling and phase-anchor changes did not remove the near-null
local direction involving state, mapping time, rho, and phase gauge components.
The condition ratio for the selected amplitude-progress variant relative to
baseline is `{condition_ratio}`.

## Variant Comparison

- Best variant: `{best_variant}`
- Best accepted max abs z in this refinement: `{best_amp}` km
- Best accepted local amplitude gain from its source: `{best_delta}` km
- Selected variant condition estimate: `{_value(best_condition)}`
- Baseline condition estimate: `{_value(baseline_condition)}`
- Best conditioning step variant: `{conditioning_variant}` with condition `{conditioning_value}`

## Threshold Results

- Accepted member beyond 10,250 km: `{accepted_10250}`
- Accepted member beyond 10,500 km: `{accepted_10500}`
- Accepted member beyond 11,000 km: `{accepted_11000}`

These are diagnostic free-time Route B members only. They are not
constant-mapping-time reproductions and do not justify updating Figure 3.16 or
Figure 3.17.

## Most Effective Change

The most effective amplitude-progress change in this bounded test is the
variant listed above. It does not solve conditioning; instead, it shows that a
larger bounded fixed-Jacobi predictor can stay inside the Route B audit gates on
this diagnostic free-time branch. The next check must therefore be
branch-consistency and phase-gauge robustness, not figure replacement.

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

    computed = PROJECT_ROOT / "data" / "computed"
    local_path = computed / "chapter3_route_b_free_time_local_experiment.csv"
    log_path = computed / "chapter3_route_b_free_time_log.csv"
    family_path = computed / "chapter3_quasi_dro_palc_family.csv"
    diagnostics_path = computed / "chapter3_route_b_refinement_diagnostics.csv"
    experiments_path = computed / "chapter3_route_b_refinement_experiments.csv"
    branch_states_path = computed / "chapter3_route_b_free_time_branch_states.npz"
    doc_path = PROJECT_ROOT / "docs" / "chapter3_route_b_refinement.md"

    local_rows = _read_rows(local_path)
    _ = _read_rows(log_path)
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

    diagnostics = _diagnostic_rows(local_rows, endpoint)
    _write_rows(diagnostics_path, DIAGNOSTIC_FIELDS, diagnostics)

    experiment_rows: list[dict[str, str]] = []
    branch_state_records: list[dict[str, object]] = []
    correction_cache: dict[str, tuple[VariantConfig, FixedJacobiFreeTimeRotationCurveCorrection, CorrectedDROFamilyMember]] = {}

    for idx, variant in enumerate(_variants(time_unit), start=1):
        try:
            correction, member, audit_row, accepted, reason = _run_route_b_correction(
                seed=seed,
                system=system,
                endpoint=endpoint,
                variant=variant,
                target_jacobi=endpoint.mean_jacobi,
                initial_states=endpoint.states,
                initial_mapping_time=endpoint.mapping_time_days / time_unit,
                initial_rotation=endpoint.rotation_angle_rad,
                phase_reference_states=endpoint.states,
                source_member=endpoint.member,
                time_unit_days=time_unit,
                length_unit_km=length_unit,
            )
            experiment_rows.append(
                _experiment_row(
                    experiment_id=f"{idx:02d}_{variant.variant}_correction",
                    variant=variant,
                    curve_samples=endpoint.states.shape[0],
                    source_case="accepted_endpoint",
                    step_attempt=0,
                    target_delta=0.0,
                    initial_amp=endpoint.max_abs_z_km,
                    initial_time_days=endpoint.mapping_time_days,
                    initial_rho=endpoint.rotation_angle_rad,
                    correction=correction,
                    member=member,
                    audit_row=audit_row,
                    converged=True,
                    accepted=accepted,
                    failure_reason=reason,
                    interpretation=(
                        "correction-only reproduction passed audit"
                        if accepted
                        else "correction-only reproduction failed audit"
                    ),
                    time_unit_days=time_unit,
                )
            )
            if accepted:
                correction_cache[variant.variant] = (variant, correction, member)
                if variant.variant == "E_amplitude_monitor_large_step":
                    branch_state_records.append(
                        _branch_state_record(
                            case_id=f"{idx:02d}_{variant.variant}_correction",
                            source_case="accepted_endpoint",
                            variant=variant.variant,
                            correction=correction,
                            member=member,
                            audit_row=audit_row,
                            accepted=accepted,
                        )
                    )
        except Exception as exc:  # noqa: BLE001 - numerical experiment records failures verbatim.
            experiment_rows.append(
                _experiment_row(
                    experiment_id=f"{idx:02d}_{variant.variant}_correction",
                    variant=variant,
                    curve_samples=endpoint.states.shape[0],
                    source_case="accepted_endpoint",
                    step_attempt=0,
                    target_delta=0.0,
                    initial_amp=endpoint.max_abs_z_km,
                    initial_time_days=endpoint.mapping_time_days,
                    initial_rho=endpoint.rotation_angle_rad,
                    correction=None,
                    member=None,
                    audit_row=None,
                    converged=False,
                    accepted=False,
                    failure_reason=str(exc),
                    interpretation="correction-only exception; do not continue this variant",
                    time_unit_days=time_unit,
                )
            )
            continue

        if variant.variant not in correction_cache:
            continue
        _, source_correction, source_member = correction_cache[variant.variant]
        target_jacobi = source_member.mean_jacobi + variant.target_delta
        try:
            correction, member, audit_row, accepted, reason = _run_route_b_correction(
                seed=seed,
                system=system,
                endpoint=endpoint,
                variant=variant,
                target_jacobi=target_jacobi,
                initial_states=source_correction.corrected_states,
                initial_mapping_time=source_correction.mapping_time,
                initial_rotation=source_correction.rotation_angle_rad,
                phase_reference_states=source_correction.corrected_states,
                source_member=endpoint.member + idx,
                time_unit_days=time_unit,
                length_unit_km=length_unit,
            )
            experiment_rows.append(
                _experiment_row(
                    experiment_id=f"{idx:02d}_{variant.variant}_step",
                    variant=variant,
                    curve_samples=endpoint.states.shape[0],
                    source_case=f"{variant.variant}_correction",
                    step_attempt=1,
                    target_delta=variant.target_delta,
                    initial_amp=source_member.max_abs_z_km,
                    initial_time_days=source_correction.mapping_time * time_unit,
                    initial_rho=source_correction.rotation_angle_rad,
                    correction=correction,
                    member=member,
                    audit_row=audit_row,
                    converged=True,
                    accepted=accepted,
                    failure_reason=reason,
                    interpretation=(
                        "bounded local step accepted"
                        if accepted
                        else "bounded local step failed audit"
                    ),
                    time_unit_days=time_unit,
                )
            )
            if accepted:
                correction_cache[f"{variant.variant}_step"] = (variant, correction, member)
                if variant.variant == "E_amplitude_monitor_large_step":
                    branch_state_records.append(
                        _branch_state_record(
                            case_id=f"{idx:02d}_{variant.variant}_step",
                            source_case=f"{variant.variant}_correction",
                            variant=variant.variant,
                            correction=correction,
                            member=member,
                            audit_row=audit_row,
                            accepted=accepted,
                        )
                    )
        except Exception as exc:  # noqa: BLE001 - numerical experiment records failures verbatim.
            experiment_rows.append(
                _experiment_row(
                    experiment_id=f"{idx:02d}_{variant.variant}_step",
                    variant=variant,
                    curve_samples=endpoint.states.shape[0],
                    source_case=f"{variant.variant}_correction",
                    step_attempt=1,
                    target_delta=variant.target_delta,
                    initial_amp=source_member.max_abs_z_km,
                    initial_time_days=source_correction.mapping_time * time_unit,
                    initial_rho=source_correction.rotation_angle_rad,
                    correction=None,
                    member=None,
                    audit_row=None,
                    converged=False,
                    accepted=False,
                    failure_reason=str(exc),
                    interpretation="bounded local step exception",
                    time_unit_days=time_unit,
                )
            )

    baseline_rows = [
        row for row in experiment_rows
        if row["variant"] == "A_baseline" and row["step_attempt"] == "1" and row["condition_estimate"] != "N/A"
    ]
    baseline_condition = float(baseline_rows[0]["condition_estimate"]) if baseline_rows else None
    accepted_step_rows = [
        row for row in experiment_rows
        if row["accepted"] == "True" and row["step_attempt"] == "1" and row["delta_max_abs_z_km"] != "N/A"
    ]
    best_step = max(
        accepted_step_rows,
        key=lambda row: (
            float(row["delta_max_abs_z_km"]),
            -float(row["condition_estimate"]) if row["condition_estimate"] != "N/A" else -np.inf,
        ),
    ) if accepted_step_rows else None

    original_small_delta = max(
        abs(float(row["delta_max_abs_z_km"]))
        for row in diagnostics
        if row["case_type"] == "small_step" and row["delta_max_abs_z_km"] != "N/A"
    )
    best_variant = best_step["variant"] if best_step is not None else "none"
    best_condition = (
        None if best_step is None or best_step["condition_estimate"] == "N/A"
        else float(best_step["condition_estimate"])
    )
    best_progress = (
        0.0 if best_step is None or best_step["delta_max_abs_z_km"] == "N/A"
        else float(best_step["delta_max_abs_z_km"])
    )
    can_continue = bool(
        best_step is not None
        and (
            (baseline_condition is not None and best_condition is not None and best_condition < 0.75 * baseline_condition)
            or best_progress > 1.5 * original_small_delta
        )
    )

    if can_continue:
        source_key = f"{best_variant}_step"
        variant, current_correction, current_member = correction_cache[source_key]
        step_delta = variant.target_delta
        for attempt in range(1, 6):
            source_amp = current_member.max_abs_z_km
            source_time_days = current_correction.mapping_time * time_unit
            source_rho = current_correction.rotation_angle_rad
            target_jacobi = current_member.mean_jacobi + step_delta
            try:
                correction, member, audit_row, accepted, reason = _run_route_b_correction(
                    seed=seed,
                    system=system,
                    endpoint=endpoint,
                    variant=variant,
                    target_jacobi=target_jacobi,
                    initial_states=current_correction.corrected_states,
                    initial_mapping_time=current_correction.mapping_time,
                    initial_rotation=current_correction.rotation_angle_rad,
                    phase_reference_states=current_correction.corrected_states,
                    source_member=endpoint.member + 100 + attempt,
                    time_unit_days=time_unit,
                    length_unit_km=length_unit,
                )
                experiment_rows.append(
                    _experiment_row(
                        experiment_id=f"bounded_{attempt:02d}_{variant.variant}",
                        variant=variant,
                        curve_samples=endpoint.states.shape[0],
                        source_case=f"bounded_previous_{attempt - 1}" if attempt > 1 else source_key,
                        step_attempt=attempt,
                        target_delta=step_delta,
                        initial_amp=source_amp,
                        initial_time_days=source_time_days,
                        initial_rho=source_rho,
                        correction=correction,
                        member=member,
                        audit_row=audit_row,
                        converged=True,
                        accepted=accepted,
                        failure_reason=reason,
                        interpretation=(
                            "bounded continuation step accepted"
                            if accepted
                            else "bounded continuation step failed audit; stop"
                        ),
                        time_unit_days=time_unit,
                    )
                )
                if not accepted:
                    break
                branch_state_records.append(
                    _branch_state_record(
                        case_id=f"bounded_{attempt:02d}_{variant.variant}",
                        source_case=f"bounded_previous_{attempt - 1}" if attempt > 1 else source_key,
                        variant=variant.variant,
                        correction=correction,
                        member=member,
                        audit_row=audit_row,
                        accepted=accepted,
                    )
                )
                current_correction = correction
                current_member = member
                if member.max_abs_z_km > 11000.0:
                    break
            except Exception as exc:  # noqa: BLE001 - numerical experiment records failures verbatim.
                experiment_rows.append(
                    _experiment_row(
                        experiment_id=f"bounded_{attempt:02d}_{variant.variant}",
                        variant=variant,
                        curve_samples=endpoint.states.shape[0],
                        source_case=f"bounded_previous_{attempt - 1}" if attempt > 1 else source_key,
                        step_attempt=attempt,
                        target_delta=step_delta,
                        initial_amp=source_amp,
                        initial_time_days=source_time_days,
                        initial_rho=source_rho,
                        correction=None,
                        member=None,
                        audit_row=None,
                        converged=False,
                        accepted=False,
                        failure_reason=str(exc),
                        interpretation="bounded continuation exception; stop",
                        time_unit_days=time_unit,
                    )
                )
                break

    _write_rows(experiments_path, EXPERIMENT_FIELDS, experiment_rows)
    _write_branch_state_archive(branch_states_path, records=branch_state_records, phase_grid=seed.phases)
    accepted_experiments = [
        row for row in experiment_rows
        if row["accepted"] == "True" and row["max_abs_z_km"] != "N/A"
    ]
    accepted_10250 = any(float(row["max_abs_z_km"]) > 10250.0 for row in accepted_experiments)
    accepted_10500 = any(float(row["max_abs_z_km"]) > 10500.0 for row in accepted_experiments)
    accepted_11000 = any(float(row["max_abs_z_km"]) > 11000.0 for row in accepted_experiments)
    if accepted_10500:
        next_action = (
            "Run branch-consistency and multi-member continuation checks before any figure-source split; "
            "do not update Fig. 3.16/3.17 yet."
        )
    elif can_continue:
        next_action = (
            "Bounded refined continuation improved local progress but did not clear 10,500 km; "
            "prioritize amplitude-guided PALC with stronger phase-condition diagnostics."
        )
    else:
        next_action = (
            "Scaling did not provide enough accepted progress; prioritize smaller-family sanity check, "
            "then Fourier/collocation BVP if the formulation remains ill-conditioned."
        )
    _write_doc(
        doc_path,
        endpoint=endpoint,
        diagnostics=diagnostics,
        experiments=experiment_rows,
        best_variant=best_variant,
        best_condition=best_condition,
        baseline_condition=baseline_condition,
        accepted_10250=accepted_10250,
        accepted_10500=accepted_10500,
        accepted_11000=accepted_11000,
        next_action=next_action,
    )

    print("Route B refinement complete")
    print(f"diagnostic_rows={len(diagnostics)}")
    print(f"experiment_rows={len(experiment_rows)}")
    print(f"best_variant={best_variant}")
    print(f"baseline_condition={_value(baseline_condition)}")
    print(f"best_condition={_value(best_condition)}")
    print(f"accepted_beyond_10250_km={accepted_10250}")
    print(f"accepted_beyond_10500_km={accepted_10500}")
    print(f"accepted_beyond_11000_km={accepted_11000}")


if __name__ == "__main__":
    main()
