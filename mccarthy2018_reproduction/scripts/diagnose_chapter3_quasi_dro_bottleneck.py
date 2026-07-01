"""Diagnose the Chapter 3 quasi-DRO continuation bottleneck.

This script is intentionally bounded. It does not extend the production family
or regenerate figures; it reconstructs the 10-11 Mm failure neighborhood and
writes diagnostic CSV tables for the accepted and rejected candidates.
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
from qp_orbits.cr3bp import cr3bp_rhs, jacobi_constant, potential_gradient
from qp_orbits.corrected_dro_family import (
    CorrectedDROFamilyMember,
    _audit_values,
    _correction_from_member,
    _is_tight_fixed_mapping_correction,
    _member_from_correction,
    _palc_candidate_status,
    load_corrected_dro_family_csv,
)
from qp_orbits.quasi_torus import (
    FixedMappingPseudoArclengthCorrection,
    FixedRotationCurveCorrection,
    FreeEnergyCurveCorrection,
    FreeMappingTimeCurveCorrection,
    FreeRotationCurveCorrection,
    _fixed_mapping_pseudo_arclength_geometry,
    _lift_dro_fixed_mapping_correction,
    _stroboscopic_map_and_stms,
    _trigonometric_interpolation_derivative_matrix,
    _trigonometric_interpolation_matrix,
    corrected_dro_fixed_mapping_family,
    stroboscopic_curve_fixed_mapping_pseudo_arclength_correction,
    stroboscopic_curve_fixed_rotation_correction,
    stroboscopic_curve_free_energy_correction,
    stroboscopic_curve_free_mapping_time_correction,
    stroboscopic_dro_invariant_curve_seed,
)


DIAGNOSTIC_FIELDS = (
    "case_id",
    "case_type",
    "source",
    "curve_samples",
    "rho",
    "max_abs_z_km",
    "mean_jacobi",
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_jacobi_drift",
    "phase_return_error",
    "amplitude_residual",
    "phase_residual",
    "arclength_residual",
    "newton_iterations",
    "condition_estimate",
    "min_singular_value",
    "max_singular_value",
    "singular_value_ratio",
    "max_correction_norm",
    "mean_correction_norm",
    "fourier_tail_energy_z",
    "fourier_tail_energy_state",
    "max_pointwise_residual",
    "residual_peak_phase",
    "max_pointwise_jacobi_error",
    "jacobi_peak_phase",
    "classification",
    "diagnosis",
)

EXPERIMENT_FIELDS = (
    "experiment_id",
    "method",
    "source_member",
    "target",
    "curve_samples",
    "step_size",
    "max_iterations",
    "converged",
    "accepted",
    "rho",
    "max_abs_z_km",
    "mean_jacobi",
    "map_residual_norm",
    "curve_jacobi_span",
    "phase_return_error",
    "failure_reason",
    "interpretation",
)


@dataclass(frozen=True)
class Context:
    length_unit: float
    time_unit: float
    x0: float
    initial_ydot: float
    initial_half_period: float
    source_mapping_time_days: float


def _fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    number = float(value)
    if not np.isfinite(number):
        return "N/A"
    return f"{number:.16g}"


def _correction_mapping_time(correction: object) -> float:
    return float(getattr(correction, "mapping_time", correction.seed.orbit_period))


def _pointwise_metrics(
    correction: object,
    *,
    max_step: float = 0.03,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mapping_time = _correction_mapping_time(correction)
    states = correction.corrected_states
    mapped, _ = _stroboscopic_map_and_stms(
        states,
        period=mapping_time,
        mu=correction.seed.mu,
        max_step=max_step,
    )
    interpolation = _trigonometric_interpolation_matrix(
        correction.seed.phases,
        correction.seed.phases + correction.rotation_angle_rad,
    )
    targets = interpolation @ states
    residuals = mapped - targets
    residual_norms = np.linalg.norm(residuals, axis=1)
    jacobi_values = np.asarray(jacobi_constant(states, correction.seed.mu), dtype=float)
    jacobi_errors = jacobi_values - float(np.mean(jacobi_values))
    return mapped, targets, residual_norms, jacobi_values, jacobi_errors


def _jacobi_gradient(states: np.ndarray, mu: float) -> np.ndarray:
    gradients = np.empty_like(states)
    for idx, state in enumerate(states):
        gradients[idx, :3] = 2.0 * potential_gradient(state[:3], mu)
        gradients[idx, 3:] = -2.0 * state[3:]
    return gradients


def _phase_direction(reference: np.ndarray) -> np.ndarray:
    direction = np.roll(reference, -1, axis=0) - np.roll(reference, 1, axis=0)
    norm = float(np.linalg.norm(direction))
    if norm <= 1.0e-14:
        raise RuntimeError("degenerate phase direction")
    return direction / norm


def _amplitude_gradient(states: np.ndarray, correction: object) -> np.ndarray:
    component = int(correction.seed.mode_component)
    displacement = states[:, component] - correction.seed.orbit_state[component]
    amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    gradient = np.zeros_like(states)
    if amplitude > 1.0e-15:
        gradient[:, component] = 2.0 * displacement / (states.shape[0] * amplitude)
    return gradient


def _singular_values(correction: object) -> np.ndarray:
    states = correction.corrected_states
    seed = correction.seed
    sample_count = states.shape[0]
    state_size = states.size
    mapping_time = _correction_mapping_time(correction)
    rotation = float(correction.rotation_angle_rad)
    interpolation = _trigonometric_interpolation_matrix(seed.phases, seed.phases + rotation)
    mapped, stms = _stroboscopic_map_and_stms(
        states,
        period=mapping_time,
        mu=seed.mu,
        max_step=0.03,
    )

    if isinstance(correction, FixedRotationCurveCorrection):
        jacobian = np.zeros((state_size + 1, state_size), dtype=float)
    elif isinstance(correction, FreeMappingTimeCurveCorrection):
        jacobian = np.zeros((state_size + 2, state_size + 1), dtype=float)
    elif isinstance(correction, FreeEnergyCurveCorrection):
        jacobian = np.zeros((state_size + 3, state_size + 2), dtype=float)
    else:
        jacobian = np.zeros((state_size + 2, state_size + 1), dtype=float)

    for row in range(sample_count):
        for col in range(sample_count):
            block = -interpolation[row, col] * np.eye(6)
            if row == col:
                block = block + stms[row]
            jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block

    reference = getattr(correction, "predictor_variables", None)
    reference_states = states
    phase = _phase_direction(reference_states)

    if isinstance(correction, FixedRotationCurveCorrection):
        jacobian[state_size, :] = phase.reshape(-1)
    elif isinstance(correction, FreeMappingTimeCurveCorrection):
        for row in range(sample_count):
            jacobian[6 * row : 6 * row + 6, state_size] = cr3bp_rhs(
                mapping_time,
                mapped[row],
                seed.mu,
            )
        jacobian[state_size, :state_size] = _amplitude_gradient(states, correction).reshape(-1)
        jacobian[state_size + 1, :state_size] = phase.reshape(-1)
    elif isinstance(correction, FreeEnergyCurveCorrection):
        derivative = _trigonometric_interpolation_derivative_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        for row in range(sample_count):
            jacobian[6 * row : 6 * row + 6, state_size] = cr3bp_rhs(
                mapping_time,
                mapped[row],
                seed.mu,
            )
        jacobian[:state_size, state_size + 1] = -(derivative @ states).reshape(-1)
        jacobian[state_size, :state_size] = (_jacobi_gradient(states, seed.mu) / sample_count).reshape(-1)
        jacobian[state_size + 1, :state_size] = _amplitude_gradient(states, correction).reshape(-1)
        jacobian[state_size + 2, :state_size] = phase.reshape(-1)
    else:
        derivative = _trigonometric_interpolation_derivative_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        jacobian[:state_size, -1] = -(derivative @ states).reshape(-1)
        jacobian[state_size, :state_size] = phase.reshape(-1)
        if isinstance(correction, FixedMappingPseudoArclengthCorrection):
            jacobian[state_size + 1, :] = correction.continuation_tangent
        else:
            jacobian[state_size + 1, :state_size] = _amplitude_gradient(states, correction).reshape(-1)

    if reference is None:
        pass
    return np.linalg.svd(jacobian, compute_uv=False)


def _fourier_tail_energy(values: np.ndarray) -> float:
    data = np.asarray(values, dtype=float)
    coeffs = np.fft.rfft(data, axis=0)
    energy_by_mode = np.sum(np.abs(coeffs) ** 2, axis=tuple(range(1, coeffs.ndim)))
    total = float(np.sum(energy_by_mode[1:]))
    if total <= 0.0:
        return 0.0
    tail_start = max(2, int(np.ceil(0.67 * (energy_by_mode.size - 1))))
    return float(np.sum(energy_by_mode[tail_start:]) / total)


def _correction_stats(correction: object) -> tuple[int | None, float | None, float | None]:
    history = getattr(correction, "correction_norm_history", np.empty((0, 0)))
    if history.size == 0:
        return 0, None, None
    return int(history.shape[0]), float(np.max(history)), float(np.mean(history))


def _constraint_residual(correction: object, name: str) -> float | None:
    history = getattr(correction, name, None)
    if history is None or np.asarray(history).size == 0:
        return None
    return float(np.asarray(history)[-1])


def _classify(
    *,
    accepted: bool,
    residual_norms: np.ndarray,
    jacobi_errors: np.ndarray,
    tail_state: float,
    condition: float | None,
    phase: float,
) -> tuple[str, str]:
    peak = float(np.max(residual_norms))
    median = float(np.median(residual_norms))
    concentration = peak / max(median, 1.0e-16)
    jac_peak = float(np.max(np.abs(jacobi_errors)))
    near_wrap = phase < 0.25 or phase > (2.0 * np.pi - 0.25)

    if accepted:
        return "accepted_audited", "accepted; residual and Jacobi errors stay below audit thresholds"
    if tail_state > 1.0e-3 and concentration > 8.0:
        return "localized_spectral_ringing", "rejected; high-mode tail and localized residual peak indicate spectral ringing"
    if concentration > 8.0:
        if near_wrap:
            return "localized_phase_wrapping", "rejected; residual peak is localized near the periodic wrap"
        return "localized_phase_failure", "rejected; residual is dominated by a narrow phase sector"
    if condition is not None and condition > 1.0e9:
        return "ill_conditioned_parameterization", "rejected; Jacobian is ill-conditioned before residual audit passes"
    if peak > 1.0e-6 and jac_peak > 1.0e-6:
        return "global_consistency_loss", "rejected; map residual and Jacobi error rise across the curve"
    return "parameterization_or_newton_failure", "rejected; spectral tail is modest but Newton residual remains above audit thresholds"


def _diagnostic_row(
    *,
    case_id: str,
    case_type: str,
    source: str,
    correction: object,
    accepted: bool,
    system_length_unit: float,
) -> dict[str, str]:
    _, _, residual_norms, jacobi_values, jacobi_errors = _pointwise_metrics(correction)
    singular_values = _singular_values(correction)
    iterations, max_corr, mean_corr = _correction_stats(correction)
    condition_history = getattr(correction, "jacobian_condition_history", np.empty(0))
    condition = (
        float(np.max(condition_history))
        if np.asarray(condition_history).size
        else float(singular_values[0] / singular_values[-1])
    )
    max_residual_idx = int(np.argmax(residual_norms))
    max_jacobi_idx = int(np.argmax(np.abs(jacobi_errors)))
    residual_peak_phase = float(correction.seed.phases[max_residual_idx] % (2.0 * np.pi))
    jacobi_peak_phase = float(correction.seed.phases[max_jacobi_idx] % (2.0 * np.pi))
    one_map_jacobi_drift = float(np.ptp(jacobi_values))
    phase_return_error = float(residual_norms[0])
    max_abs_z_km = float(np.max(np.abs(correction.corrected_states[:, 2])) * system_length_unit)
    target_amplitude = getattr(correction, "target_amplitude", None)
    mean_jacobi = float(np.mean(jacobi_values))
    map_residual_norm = float(np.max(residual_norms))
    curve_jacobi_span = float(np.ptp(jacobi_values))
    tail_z = _fourier_tail_energy(correction.corrected_states[:, 2])
    tail_state = _fourier_tail_energy(correction.corrected_states)
    classification, diagnosis = _classify(
        accepted=accepted,
        residual_norms=residual_norms,
        jacobi_errors=jacobi_errors,
        tail_state=tail_state,
        condition=condition,
        phase=residual_peak_phase,
    )
    amplitude_residual = _constraint_residual(correction, "amplitude_residual_history")
    if amplitude_residual is None and target_amplitude is not None:
        component = int(correction.seed.mode_component)
        displacement = correction.corrected_states[:, component] - correction.seed.orbit_state[component]
        amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        amplitude_residual = amplitude - float(target_amplitude)
    if isinstance(correction, FreeEnergyCurveCorrection):
        energy_residual = _constraint_residual(correction, "energy_residual_history")
        if energy_residual is not None:
            diagnosis += f"; fixed-mean-Jacobi residual={energy_residual:.3e}"

    values = {
        "case_id": case_id,
        "case_type": case_type,
        "source": source,
        "curve_samples": correction.corrected_states.shape[0],
        "rho": correction.rotation_angle_rad,
        "max_abs_z_km": max_abs_z_km,
        "mean_jacobi": mean_jacobi,
        "map_residual_norm": map_residual_norm,
        "curve_jacobi_span": curve_jacobi_span,
        "one_map_jacobi_drift": one_map_jacobi_drift,
        "phase_return_error": phase_return_error,
        "amplitude_residual": amplitude_residual,
        "phase_residual": _constraint_residual(correction, "phase_residual_history"),
        "arclength_residual": _constraint_residual(correction, "arclength_residual_history"),
        "newton_iterations": iterations,
        "condition_estimate": condition,
        "min_singular_value": float(singular_values[-1]),
        "max_singular_value": float(singular_values[0]),
        "singular_value_ratio": float(singular_values[0] / singular_values[-1]),
        "max_correction_norm": max_corr,
        "mean_correction_norm": mean_corr,
        "fourier_tail_energy_z": tail_z,
        "fourier_tail_energy_state": tail_state,
        "max_pointwise_residual": float(np.max(residual_norms)),
        "residual_peak_phase": residual_peak_phase,
        "max_pointwise_jacobi_error": float(np.max(np.abs(jacobi_errors))),
        "jacobi_peak_phase": jacobi_peak_phase,
        "classification": classification,
        "diagnosis": diagnosis,
    }
    return {field: _fmt(values[field]) for field in DIAGNOSTIC_FIELDS}


def _experiment_row(
    *,
    experiment_id: str,
    method: str,
    source_member: str,
    target: str,
    step_size: float | None,
    max_iterations: int,
    correction: object | None,
    accepted: bool,
    failure_reason: str,
    interpretation: str,
    length_unit: float,
) -> dict[str, str]:
    values: dict[str, Any] = {
        "experiment_id": experiment_id,
        "method": method,
        "source_member": source_member,
        "target": target,
        "curve_samples": None,
        "step_size": step_size,
        "max_iterations": max_iterations,
        "converged": correction is not None,
        "accepted": accepted,
        "rho": None,
        "max_abs_z_km": None,
        "mean_jacobi": None,
        "map_residual_norm": None,
        "curve_jacobi_span": None,
        "phase_return_error": None,
        "failure_reason": failure_reason,
        "interpretation": interpretation,
    }
    if correction is not None:
        _, _, residuals, jacobi_values, _ = _pointwise_metrics(correction)
        values.update(
            {
                "curve_samples": correction.corrected_states.shape[0],
                "rho": correction.rotation_angle_rad,
                "max_abs_z_km": float(np.max(np.abs(correction.corrected_states[:, 2])) * length_unit),
                "mean_jacobi": float(np.mean(jacobi_values)),
                "map_residual_norm": float(np.max(residuals)),
                "curve_jacobi_span": float(np.ptp(jacobi_values)),
                "phase_return_error": float(residuals[0]),
            }
        )
    return {field: _fmt(values[field]) for field in EXPERIMENT_FIELDS}


def _quick_accept(correction: object) -> tuple[bool, str]:
    _, _, residuals, jacobi_values, _ = _pointwise_metrics(correction)
    residual = float(np.max(residuals))
    jacobi_span = float(np.ptp(jacobi_values))
    phase_error = float(residuals[0])
    accepted = residual <= 1.0e-8 and jacobi_span <= 1.0e-8 and phase_error <= 1.0e-8
    if accepted:
        return True, ""
    return False, (
        f"residual={residual:.3e}, jacobi_span={jacobi_span:.3e}, "
        f"phase_error={phase_error:.3e}"
    )


def _recompute_amplitude_candidates(
    base_family: tuple[CorrectedDROFamilyMember, ...],
    ctx: Context,
    mu: float,
) -> dict[float, FreeRotationCurveCorrection]:
    base_amplitudes = tuple(member.target_vertical_amplitude_nd for member in base_family[:5])
    targets_km = (8500.0, 9000.0, 9500.0, 10000.0, 11000.0, 12000.0, 14000.0)
    amplitudes = base_amplitudes + tuple(value / ctx.length_unit for value in targets_km)
    corrections = corrected_dro_fixed_mapping_family(
        mu,
        x0=ctx.x0,
        vertical_amplitudes=amplitudes,
        samples=41,
        initial_half_period=ctx.initial_half_period,
        max_iterations=32,
    )
    return {target: corrections[5 + idx] for idx, target in enumerate(targets_km)}


def _recompute_palc_neighborhood(
    extended_family: tuple[CorrectedDROFamilyMember, ...],
    ctx: Context,
    mu: float,
) -> tuple[
    FreeRotationCurveCorrection,
    FixedMappingPseudoArclengthCorrection,
    FreeRotationCurveCorrection,
    FreeRotationCurveCorrection,
    FixedMappingPseudoArclengthCorrection,
]:
    previous_member = extended_family[-2]
    current_member = extended_family[-1]
    previous = _correction_from_member(
        previous_member,
        SYSTEMS["earth_moon"],
        x0=ctx.x0,
        initial_ydot=ctx.initial_ydot,
        initial_half_period=ctx.initial_half_period,
    )
    current = _correction_from_member(
        current_member,
        SYSTEMS["earth_moon"],
        x0=ctx.x0,
        initial_ydot=ctx.initial_ydot,
        initial_half_period=ctx.initial_half_period,
    )
    _, _, _, natural = _fixed_mapping_pseudo_arclength_geometry(previous, current)
    palc_41 = stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
        previous,
        current,
        step_size=0.15 * natural,
        max_iterations=4,
        tolerance=1.0e-8,
        constraint_tolerance=1.0e-10,
        max_step=0.03,
        max_rotation_step=0.003,
    )
    lifted_previous = _lift_dro_fixed_mapping_correction(
        current,
        x0=ctx.x0,
        samples=61,
        initial_ydot=ctx.initial_ydot,
        initial_half_period=ctx.initial_half_period,
        max_iterations=4,
        map_tolerance=1.0e-8,
        max_step=0.03,
    )
    lifted_current = _lift_dro_fixed_mapping_correction(
        palc_41,
        x0=ctx.x0,
        samples=61,
        initial_ydot=ctx.initial_ydot,
        initial_half_period=ctx.initial_half_period,
        max_iterations=4,
        map_tolerance=1.0e-8,
        max_step=0.03,
    )
    _, _, _, natural_61 = _fixed_mapping_pseudo_arclength_geometry(
        lifted_previous,
        lifted_current,
    )
    palc_61 = stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
        lifted_previous,
        lifted_current,
        step_size=0.10 * natural_61,
        max_iterations=3,
        tolerance=1.0e-8,
        constraint_tolerance=1.0e-10,
        max_step=0.03,
        max_rotation_step=0.002,
    )
    return current, palc_41, lifted_previous, lifted_current, palc_61


def _fixed_rotation_candidate(
    previous: object,
    current: object,
    target_rho: float,
    ctx: Context,
    *,
    max_iterations: int = 3,
) -> FixedRotationCurveCorrection:
    seed = stroboscopic_dro_invariant_curve_seed(
        current.seed.mu,
        x0=ctx.x0,
        initial_ydot=ctx.initial_ydot,
        initial_half_period=ctx.initial_half_period,
        vertical_amplitude=1.0e-4,
        samples=current.corrected_states.shape[0],
        curve_samples=max(4 * current.corrected_states.shape[0], 120),
    )
    fraction = (target_rho - current.rotation_angle_rad) / (
        current.rotation_angle_rad - previous.rotation_angle_rad
    )
    interpolation = _trigonometric_interpolation_matrix(previous.seed.phases, current.seed.phases)
    previous_states = interpolation @ previous.corrected_states
    initial_states = current.corrected_states + fraction * (current.corrected_states - previous_states)
    return stroboscopic_curve_fixed_rotation_correction(
        seed,
        target_rotation_angle_rad=target_rho,
        initial_states=initial_states,
        phase_reference_states=initial_states,
        max_iterations=max_iterations,
        tolerance=1.0e-8,
        phase_tolerance=1.0e-10,
        max_step=0.03,
        max_state_step=1.0e-3,
    )


def _run_experiments(
    *,
    ctx: Context,
    lifted_current: FreeRotationCurveCorrection,
    palc_61: FixedMappingPseudoArclengthCorrection,
    length_unit: float,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    _, _, _, natural = _fixed_mapping_pseudo_arclength_geometry(lifted_current, palc_61)

    for idx, frac in enumerate((0.25, 0.50), start=1):
        step = frac * natural
        correction = None
        accepted = False
        reason = ""
        try:
            correction = stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
                lifted_current,
                palc_61,
                step_size=step,
                max_iterations=5,
                tolerance=1.0e-8,
                constraint_tolerance=1.0e-10,
                max_step=0.03,
                max_rotation_step=0.002,
            )
            accepted, reason = _quick_accept(correction)
        except Exception as exc:  # noqa: BLE001 - numerical probe table should capture failure text.
            reason = str(exc)
        rows.append(
            _experiment_row(
                experiment_id=f"A_palc_trust_N61_frac_{frac:.2f}",
                method="fixed-mapping PALC smaller trust region",
                source_member="N61 lifted 10.164 Mm PALC anchor",
                target="test accepted candidate beyond 10,500 km",
                step_size=step,
                max_iterations=5,
                correction=correction,
                accepted=accepted,
                failure_reason=reason,
                interpretation=(
                    "PALC remains local; accept only if full residual/Jacobi audit passes"
                ),
                length_unit=length_unit,
            )
        )

    for target_rho in (1.4440, 1.4442, 1.4445):
        correction = None
        accepted = False
        reason = ""
        try:
            correction = _fixed_rotation_candidate(
                lifted_current,
                palc_61,
                target_rho,
                ctx,
                max_iterations=5,
            )
            accepted, reason = _quick_accept(correction)
        except Exception as exc:  # noqa: BLE001
            reason = str(exc)
        rows.append(
            _experiment_row(
                experiment_id=f"B_fixed_rotation_rho_{target_rho:.4f}",
                method="fixed-rotation correction",
                source_member="N61 lifted 10.164 Mm PALC anchor",
                target=f"rho={target_rho:.4f}",
                step_size=target_rho - palc_61.rotation_angle_rad,
                max_iterations=5,
                correction=correction,
                accepted=accepted,
                failure_reason=reason,
                interpretation=(
                    "Fixed rho can increase amplitude, but rejected candidates are not invariant curves"
                ),
                length_unit=length_unit,
            )
        )

    target_rho = 1.4445
    seed = stroboscopic_dro_invariant_curve_seed(
        palc_61.seed.mu,
        x0=ctx.x0,
        initial_ydot=ctx.initial_ydot,
        initial_half_period=ctx.initial_half_period,
        vertical_amplitude=1.0e-4,
        samples=palc_61.corrected_states.shape[0],
        curve_samples=max(4 * palc_61.corrected_states.shape[0], 120),
    )
    fixed_guess = None
    try:
        fixed_guess = _fixed_rotation_candidate(lifted_current, palc_61, target_rho, ctx, max_iterations=3)
    except Exception:
        fixed_guess = None
    initial_states = palc_61.corrected_states if fixed_guess is None else fixed_guess.corrected_states
    target_amp = float(
        np.sqrt(
            2.0
            * np.mean(
                (initial_states[:, seed.mode_component] - seed.orbit_state[seed.mode_component]) ** 2
            )
        )
    )
    for label, runner in (
        ("C_free_mapping_time", stroboscopic_curve_free_mapping_time_correction),
        ("C_fixed_mean_jacobi_free_rho", stroboscopic_curve_free_energy_correction),
    ):
        correction = None
        accepted = False
        reason = ""
        try:
            if label == "C_free_mapping_time":
                correction = runner(
                    seed,
                    target_rotation_angle_rad=target_rho,
                    target_amplitude=target_amp,
                    initial_states=initial_states,
                    initial_mapping_time=palc_61.seed.orbit_period,
                    phase_reference_states=initial_states,
                    max_iterations=6,
                    tolerance=1.0e-8,
                    constraint_tolerance=1.0e-10,
                    max_step=0.03,
                    max_state_step=1.0e-3,
                    max_mapping_time_step=0.015,
                )
            else:
                correction = runner(
                    seed,
                    target_jacobi=float(np.mean(jacobi_constant(palc_61.corrected_states, seed.mu))),
                    target_amplitude=target_amp,
                    initial_states=initial_states,
                    initial_mapping_time=palc_61.seed.orbit_period,
                    initial_rotation_angle_rad=target_rho,
                    phase_reference_states=initial_states,
                    max_iterations=6,
                    tolerance=1.0e-8,
                    constraint_tolerance=1.0e-10,
                    max_step=0.03,
                    max_state_step=1.0e-3,
                    max_mapping_time_step=0.015,
                    max_rotation_step=0.002,
                )
            accepted, reason = _quick_accept(correction)
        except Exception as exc:  # noqa: BLE001
            reason = str(exc)
        rows.append(
            _experiment_row(
                experiment_id=label,
                method=(
                    "free-mapping-time local correction"
                    if label == "C_free_mapping_time"
                    else "fixed-mean-Jacobi free-rho/free-time local correction"
                ),
                source_member="N61 lifted 10.164 Mm PALC anchor plus fixed-rho predictor",
                target="near rho=1.4445 / 10.5-11.0 Mm neighborhood",
                step_size=target_rho - palc_61.rotation_angle_rad,
                max_iterations=6,
                correction=correction,
                accepted=accepted,
                failure_reason=reason,
                interpretation=(
                    "Alternative local parameterization; success here would not upgrade fixed-mapping figures"
                ),
                length_unit=length_unit,
            )
        )
    return rows


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _log_row_value(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "N/A")
    if value in {"", "N/A", None}:
        return None
    return float(value)


def _diagnostic_row_from_log(
    *,
    case_id: str,
    case_type: str,
    source: str,
    log_row: dict[str, str],
    diagnosis: str,
) -> dict[str, str]:
    residual = _log_row_value(log_row, "map_residual_norm")
    jacobi_span = _log_row_value(log_row, "curve_jacobi_span")
    one_map_drift = _log_row_value(log_row, "one_map_jacobi_drift")
    phase_error = _log_row_value(log_row, "phase_return_error")
    condition = _log_row_value(log_row, "condition_estimate")
    classification = "log_only_global_consistency_loss"
    if residual is not None and jacobi_span is not None and residual > 1.0e-6 and jacobi_span > 1.0e-6:
        classification = "log_only_residual_and_jacobi_failure"
    values: dict[str, Any] = {
        "case_id": case_id,
        "case_type": case_type,
        "source": source,
        "curve_samples": _log_row_value(log_row, "curve_samples"),
        "rho": _log_row_value(log_row, "rotation_angle_rad"),
        "max_abs_z_km": _log_row_value(log_row, "max_abs_z_km"),
        "mean_jacobi": _log_row_value(log_row, "mean_jacobi"),
        "map_residual_norm": residual,
        "curve_jacobi_span": jacobi_span,
        "one_map_jacobi_drift": one_map_drift,
        "phase_return_error": phase_error,
        "amplitude_residual": None,
        "phase_residual": None,
        "arclength_residual": None,
        "newton_iterations": _log_row_value(log_row, "newton_iterations"),
        "condition_estimate": condition,
        "min_singular_value": None,
        "max_singular_value": None,
        "singular_value_ratio": None,
        "max_correction_norm": None,
        "mean_correction_norm": None,
        "fourier_tail_energy_z": None,
        "fourier_tail_energy_state": None,
        "max_pointwise_residual": residual,
        "residual_peak_phase": None,
        "max_pointwise_jacobi_error": None if jacobi_span is None else 0.5 * jacobi_span,
        "jacobi_peak_phase": None,
        "classification": classification,
        "diagnosis": diagnosis,
    }
    return {field: _fmt(values[field]) for field in DIAGNOSTIC_FIELDS}


def _make_member_correction(
    member: CorrectedDROFamilyMember,
    ctx: Context,
) -> FreeRotationCurveCorrection:
    return _correction_from_member(
        member,
        SYSTEMS["earth_moon"],
        x0=ctx.x0,
        initial_ydot=ctx.initial_ydot,
        initial_half_period=ctx.initial_half_period,
    )


def main() -> None:
    system = SYSTEMS["earth_moon"]
    length_unit = system.length_unit_km or 1.0
    time_unit = system.time_unit_days or 1.0
    ctx = Context(
        length_unit=length_unit,
        time_unit=time_unit,
        x0=1.0 - system.mu - 73800.0 / length_unit,
        initial_ydot=0.53,
        initial_half_period=14.75 / (2.0 * time_unit),
        source_mapping_time_days=14.74932760227518,
    )

    extended_path = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family_extended.csv"
    palc_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
    continuation_log_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_continuation_log.csv"
    palc_log_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_log.csv"
    diagnostics_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_bottleneck_diagnostics.csv"
    experiments_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_bottleneck_experiments.csv"

    extended_family = load_corrected_dro_family_csv(extended_path)
    palc_family = load_corrected_dro_family_csv(palc_path)
    continuation_log = {row["attempt_id"]: row for row in _read_csv(continuation_log_path)}
    palc_log = {row["attempt_id"]: row for row in _read_csv(palc_log_path)}

    accepted_10k = _make_member_correction(extended_family[-1], ctx)
    accepted_palc = _make_member_correction(palc_family[-1], ctx)

    rows: list[dict[str, str]] = []
    rows.append(
        _diagnostic_row(
            case_id="accepted_amplitude_10000km",
            case_type="accepted",
            source="amplitude_stepping_N41",
            correction=accepted_10k,
            accepted=True,
            system_length_unit=length_unit,
        )
    )
    rows.append(
        _diagnostic_row(
            case_id="accepted_palc_10164km",
            case_type="accepted",
            source="fixed_mapping_PALC_N61",
            correction=accepted_palc,
            accepted=True,
            system_length_unit=length_unit,
        )
    )

    for attempt_id, target in (
        ("stage1_target_11000km_N41", 11000),
        ("stage1_target_12000km_N41", 12000),
        ("stage2_target_14000km_N41", 14000),
    ):
        rows.append(
            _diagnostic_row_from_log(
                case_id=f"rejected_amplitude_{target}km",
                case_type="rejected",
                source="amplitude_stepping_N41",
                log_row=continuation_log[attempt_id],
                diagnosis=(
                    "rejected amplitude-stepping candidate; full states are not persisted in the CSV, "
                    "so this bounded diagnostic uses continuation-log metrics instead of rerunning the slow full branch"
                ),
            )
        )

    lifted_current: FreeRotationCurveCorrection | None = None
    fixed_rotation_cases: dict[float, FixedRotationCurveCorrection | None] = {}
    try:
        previous_41 = _make_member_correction(palc_family[-2], ctx)
        current_61 = _make_member_correction(palc_family[-1], ctx)
        lifted_previous = _lift_dro_fixed_mapping_correction(
            previous_41,
            x0=ctx.x0,
            samples=current_61.corrected_states.shape[0],
            initial_ydot=ctx.initial_ydot,
            initial_half_period=ctx.initial_half_period,
            max_iterations=2,
            map_tolerance=1.0e-8,
            max_step=0.03,
        )
        lifted_current = current_61
    except Exception:
        lifted_previous = None
        lifted_current = None

    for target_rho in (1.4445, 1.4455, 1.4465, 1.4480, 1.4500):
        candidate: FixedRotationCurveCorrection | None = None
        if lifted_previous is not None and lifted_current is not None:
            try:
                candidate = _fixed_rotation_candidate(
                    lifted_previous,
                    lifted_current,
                    target_rho,
                    ctx,
                    max_iterations=3,
                )
            except Exception:
                candidate = None
        fixed_rotation_cases[target_rho] = candidate
        if candidate is None:
            rows.append(
                _diagnostic_row_from_log(
                    case_id=f"rejected_fixed_rotation_rho_{target_rho:.4f}",
                    case_type="rejected",
                    source="fixed_rotation_fallback_N61",
                    log_row=palc_log[f"fixed_rotation_rho_{target_rho:.4f}"],
                    diagnosis=(
                        "rejected fixed-rotation candidate; reconstruction failed in bounded run, "
                        "so metrics are read from the PALC log"
                    ),
                )
            )
        else:
            rows.append(
                _diagnostic_row(
                    case_id=f"rejected_fixed_rotation_rho_{target_rho:.4f}",
                    case_type="rejected",
                    source="fixed_rotation_fallback_N61",
                    correction=candidate,
                    accepted=False,
                    system_length_unit=length_unit,
                )
            )

    if palc_family[-1].max_abs_z_km > 11000.0:
        raise RuntimeError("PALC family unexpectedly exceeds 11,000 km; re-run figure audits before updating docs")

    experiment_rows: list[dict[str, str]] = []
    for attempt_id in ("palc_N41_small_step_1", "palc_N61_lifted_small_step_1"):
        log_row = palc_log[attempt_id]
        experiment_rows.append(
            _experiment_row(
                experiment_id=f"A_{attempt_id}",
                method="fixed-mapping PALC smaller trust region",
                source_member=f"{log_row['source_previous_member']}->{log_row['source_current_member']}",
                target="bounded PALC step near 10-11 Mm",
                step_size=_log_row_value(log_row, "step_size"),
                max_iterations=int(_log_row_value(log_row, "newton_iterations") or 0),
                correction=None,
                accepted=log_row["accepted"] == "True",
                failure_reason=log_row["failure_reason"],
                interpretation="accepted only as very small local step; did not approach 10,500 km",
                length_unit=length_unit,
            )
        )
        experiment_rows[-1].update(
            {
                "converged": log_row["converged"],
                "curve_samples": log_row["target_samples"],
                "rho": log_row["rotation_angle_rad"],
                "max_abs_z_km": log_row["max_abs_z_km"],
                "mean_jacobi": log_row["mean_jacobi"],
                "map_residual_norm": log_row["map_residual_norm"],
                "curve_jacobi_span": log_row["curve_jacobi_span"],
                "phase_return_error": log_row["phase_return_error"],
            }
        )

    for target_rho in (1.4445, 1.4455, 1.4465):
        log_row = palc_log[f"fixed_rotation_rho_{target_rho:.4f}"]
        experiment_rows.append(
            _experiment_row(
                experiment_id=f"B_fixed_rotation_rho_{target_rho:.4f}",
                method="fixed-rotation correction",
                source_member=f"{log_row['source_previous_member']}->{log_row['source_current_member']}",
                target=f"rho={target_rho:.4f}",
                step_size=_log_row_value(log_row, "step_size"),
                max_iterations=int(_log_row_value(log_row, "newton_iterations") or 0),
                correction=None,
                accepted=log_row["accepted"] == "True",
                failure_reason=log_row["failure_reason"],
                interpretation="reaches higher amplitude but fails residual/Jacobi audit",
                length_unit=length_unit,
            )
        )
        experiment_rows[-1].update(
            {
                "converged": log_row["converged"],
                "curve_samples": log_row["target_samples"],
                "rho": log_row["rotation_angle_rad"],
                "max_abs_z_km": log_row["max_abs_z_km"],
                "mean_jacobi": log_row["mean_jacobi"],
                "map_residual_norm": log_row["map_residual_norm"],
                "curve_jacobi_span": log_row["curve_jacobi_span"],
                "phase_return_error": log_row["phase_return_error"],
            }
        )

    alternative = None
    alternative_accepted = False
    alternative_reason = ""
    try:
        seed = stroboscopic_dro_invariant_curve_seed(
            system.mu,
            x0=ctx.x0,
            initial_ydot=ctx.initial_ydot,
            initial_half_period=ctx.initial_half_period,
            vertical_amplitude=1.0e-4,
            samples=accepted_palc.corrected_states.shape[0],
            curve_samples=max(4 * accepted_palc.corrected_states.shape[0], 120),
        )
        target_amp = float(
            np.sqrt(
                2.0
                * np.mean(
                    (
                        accepted_palc.corrected_states[:, seed.mode_component]
                        - seed.orbit_state[seed.mode_component]
                    )
                    ** 2
                )
            )
        )
        alternative = stroboscopic_curve_free_energy_correction(
            seed,
            target_jacobi=float(np.mean(jacobi_constant(accepted_palc.corrected_states, seed.mu))),
            target_amplitude=1.02 * target_amp,
            initial_states=accepted_palc.corrected_states,
            initial_mapping_time=accepted_palc.seed.orbit_period,
            initial_rotation_angle_rad=accepted_palc.rotation_angle_rad + 2.0e-4,
            phase_reference_states=accepted_palc.corrected_states,
            max_iterations=2,
            tolerance=1.0e-8,
            constraint_tolerance=1.0e-10,
            max_step=0.03,
            max_state_step=8.0e-4,
            max_mapping_time_step=0.01,
            max_rotation_step=0.001,
        )
        alternative_accepted, alternative_reason = _quick_accept(alternative)
    except Exception as exc:  # noqa: BLE001
        alternative_reason = str(exc)
    experiment_rows.append(
        _experiment_row(
            experiment_id="C_fixed_mean_jacobi_free_rho",
            method="fixed-mean-Jacobi free-rho/free-time local correction",
            source_member="accepted_palc_10164km",
            target="2 percent local amplitude increase with fixed mean Jacobi",
            step_size=2.0e-4,
            max_iterations=2,
            correction=alternative,
            accepted=alternative_accepted,
            failure_reason=alternative_reason,
            interpretation="tests whether freeing rho/time improves the local Newton basin",
            length_unit=length_unit,
        )
    )

    _write_csv(diagnostics_path, DIAGNOSTIC_FIELDS, rows)
    _write_csv(experiments_path, EXPERIMENT_FIELDS, experiment_rows)

    print(
        "wrote",
        diagnostics_path.relative_to(PROJECT_ROOT),
        len(rows),
        "rows;",
        experiments_path.relative_to(PROJECT_ROOT),
        len(experiment_rows),
        "rows;",
        "max accepted z",
        f"{max(float(row['max_abs_z_km']) for row in rows if row['case_type'] == 'accepted'):.3f}",
        "km",
    )


if __name__ == "__main__":
    main()
