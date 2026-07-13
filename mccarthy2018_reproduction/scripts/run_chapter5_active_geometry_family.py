"""Audit or extend the adaptive active-event geometry family."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import jacobi_constant  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _project_constraint_nullspace,
    _propagated_active_geometry_constraints,
    _propagated_dense_smooth_geometry_constraints,
    resample_corrected_torus_surface,
    stroboscopic_curve_dual_geometry_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)


SEED_SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz"
CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_family_checkpoint.npz"
OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_family_audit.csv"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_active_geometry_family_audit.md"


def metric(correction) -> float:
    return max(
        float(np.max(correction.final_residual_norms)),
        abs(float(correction.energy_residual_history[-1])),
        float(np.max(np.abs(correction.geometry_residual_history[-1]))),
        abs(float(correction.phase_residual_history[-1])),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--additional-members", type=int, default=0)
    parser.add_argument("--z-target-km", type=float, default=940000.0)
    parser.add_argument("--max-relative-y-step", type=float, default=1.5e-4)
    parser.add_argument("--time-slices", type=int, default=33)
    parser.add_argument("--phase-samples", type=int, default=128)
    parser.add_argument("--initial-relative-y-step", type=float)
    parser.add_argument("--max-z-correction-km", type=float, default=250.0)
    parser.add_argument("--max-correction-iterations", type=int, default=60)
    parser.add_argument("--min-y-progress-fraction", type=float, default=0.5)
    parser.add_argument("--min-z-progress-fraction", type=float, default=0.5)
    parser.add_argument("--predictor-scale-cap", type=float, default=2.0)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--regularization", type=float, default=1.0e-8)
    parser.add_argument("--energy-residual-scale", type=float, default=1.0)
    parser.add_argument("--geometry-residual-scale", type=float, default=10.0)
    parser.add_argument("--correction-damping", type=float, default=1.0)
    parser.add_argument("--retarget-current-jacobi", action="store_true")
    parser.add_argument("--jacobi-target-offset", type=float, default=0.0)
    parser.add_argument("--project-predictor-z", action="store_true")
    parser.add_argument("--smooth-preconditioner-sharpness", type=float, default=1.0e8)
    parser.add_argument("--validate-full-torus-progress", action="store_true")
    parser.add_argument("--min-full-y-progress-fraction", type=float, default=0.5)
    parser.add_argument("--min-full-z-progress-fraction", type=float, default=0.5)
    args = parser.parse_args()
    if args.additional_members < 0:
        raise ValueError("additional-members must be non-negative")
    if args.z_target_km <= 0.0:
        raise ValueError("z-target-km must be positive")
    if args.max_relative_y_step <= 0.0:
        raise ValueError("max-relative-y-step must be positive")
    if args.time_slices < 3 or args.phase_samples < 3:
        raise ValueError("time-slices and phase-samples must be at least three")
    if args.initial_relative_y_step is not None and args.initial_relative_y_step <= 0.0:
        raise ValueError("initial-relative-y-step must be positive")
    if args.max_z_correction_km < 0.0:
        raise ValueError("max-z-correction-km must be non-negative")
    if args.max_correction_iterations < 1:
        raise ValueError("max-correction-iterations must be positive")
    if not 0.0 < args.min_y_progress_fraction <= 1.0:
        raise ValueError("min-y-progress-fraction must be in (0, 1]")
    if not 0.0 < args.min_z_progress_fraction <= 1.0:
        raise ValueError("min-z-progress-fraction must be in (0, 1]")
    if args.predictor_scale_cap < 0.0:
        raise ValueError("predictor-scale-cap must be non-negative")
    if args.max_retries < 1:
        raise ValueError("max-retries must be positive")
    if args.regularization < 0.0:
        raise ValueError("regularization must be non-negative")
    if args.energy_residual_scale <= 0.0:
        raise ValueError("energy-residual-scale must be positive")
    if args.geometry_residual_scale <= 0.0:
        raise ValueError("geometry-residual-scale must be positive")
    if not 0.0 < args.correction_damping <= 1.0:
        raise ValueError("correction-damping must be in (0, 1]")
    if args.smooth_preconditioner_sharpness <= 0.0:
        raise ValueError("smooth-preconditioner-sharpness must be positive")
    if not 0.0 < args.min_full_y_progress_fraction <= 1.0:
        raise ValueError("min-full-y-progress-fraction must be in (0, 1]")
    if not 0.0 < args.min_full_z_progress_fraction <= 1.0:
        raise ValueError("min-full-z-progress-fraction must be in (0, 1]")
    system = SYSTEMS["sun_earth"]
    seed_data = np.load(SEED_SOURCE)
    data = np.load(CHECKPOINT)
    seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=float(seed_data["x_amplitude"]),
        vertical_amplitude=1.0e-5,
        samples=int(seed_data["samples"]),
        curve_samples=168,
    )
    states = data["states"].copy()
    mapping_time = float(data["mapping_time"])
    rotation = float(data["rotation"])
    target_jacobi = float(data["jacobi"])
    initial_checkpoint_jacobi = target_jacobi
    accepted = int(data["accepted"])
    previous_states = (
        data["previous_states"].copy() if "previous_states" in data.files else None
    )
    previous_mapping_time = (
        float(data["previous_mapping_time"])
        if "previous_mapping_time" in data.files
        else None
    )
    previous_rotation = (
        float(data["previous_rotation"])
        if "previous_rotation" in data.files
        else None
    )
    step = (
        min(args.max_relative_y_step, args.initial_relative_y_step)
        if args.initial_relative_y_step is not None
        else min(args.max_relative_y_step, float(data["step"]) * 1.05)
    )
    fractions = np.linspace(0.0, 1.0, args.time_slices)
    initial_residuals, _, _, _, _ = _propagated_active_geometry_constraints(
        states,
        source_phases=seed.phases,
        mapping_time=mapping_time,
        rotation_angle_rad=rotation,
        mu=system.mu,
        time_fractions=fractions,
        phase_samples=args.phase_samples,
        target_y_support=1.0,
        target_z_support=1.0,
        max_step=0.005,
    )
    initial_y_support, initial_z_support = 1.0 + initial_residuals
    identity = stroboscopic_curve_dual_geometry_correction(
        seed,
        target_jacobi=target_jacobi,
        target_y_support=initial_y_support,
        target_z_support=initial_z_support,
        initial_states=states,
        initial_mapping_time=mapping_time,
        initial_rotation_angle_rad=rotation,
        geometry_time_fractions=fractions,
        active_geometry_phase_samples=args.phase_samples,
        max_iterations=2,
        tolerance=1.0e-8,
        constraint_tolerance=1.0e-8,
        max_step=0.005,
    )
    initial_torus = sweep_corrected_curve_correction(
        identity, time_samples=128, max_step=0.0025
    )
    initial_surface, _ = resample_corrected_torus_surface(
        initial_torus, phase_samples=256
    )
    initial_full_z_km = float(
        np.max(np.abs(initial_surface[:, :, 2])) * system.length_unit_km
    )
    z_correction_km = float(
        np.clip(
            args.z_target_km - initial_full_z_km,
            -args.max_z_correction_km,
            args.max_z_correction_km,
        )
    )
    last = identity
    last_predictor_scale = 0.0
    last_full_y_progress = float("nan")
    last_full_z_progress = float("nan")
    for _ in range(args.additional_members):
        correction = None
        current_full_y_km = float("nan")
        current_full_z_km = float("nan")
        if args.validate_full_torus_progress:
            current_torus = sweep_corrected_curve_correction(
                last,
                time_samples=128,
                max_step=0.0025,
            )
            current_surface, _ = resample_corrected_torus_surface(
                current_torus,
                phase_samples=256,
            )
            current_full_y_km = float(
                np.max(np.abs(current_surface[:, :, 1])) * system.length_unit_km
            )
            current_full_z_km = float(
                np.max(np.abs(current_surface[:, :, 2])) * system.length_unit_km
            )
        if args.retarget_current_jacobi:
            target_jacobi = (
                float(np.mean(jacobi_constant(states, system.mu)))
                + args.jacobi_target_offset
            )
        previous_y_support = None
        if previous_states is not None:
            previous_residuals, _, _, _, _ = _propagated_active_geometry_constraints(
                previous_states,
                source_phases=seed.phases,
                mapping_time=previous_mapping_time,
                rotation_angle_rad=previous_rotation,
                mu=system.mu,
                time_fractions=fractions,
                phase_samples=args.phase_samples,
                target_y_support=1.0,
                target_z_support=1.0,
                max_step=0.005,
            )
            previous_y_support = 1.0 + float(previous_residuals[0])
        for retry in range(args.max_retries):
            (
                residuals,
                current_geometry_jacobian,
                current_geometry_time_jacobian,
                current_geometry_rotation_jacobian,
                _,
            ) = _propagated_active_geometry_constraints(
                states,
                source_phases=seed.phases,
                mapping_time=mapping_time,
                rotation_angle_rad=rotation,
                mu=system.mu,
                time_fractions=fractions,
                phase_samples=args.phase_samples,
                target_y_support=1.0,
                target_z_support=1.0,
                max_step=0.005,
            )
            y_support, z_support = 1.0 + residuals
            target_y_support = (1.0 - step) * y_support
            requested_y_decrease = y_support - target_y_support
            member_z_event_target = (
                z_support + z_correction_km / system.length_unit_km
            )
            requested_z_change = member_z_event_target - z_support
            adaptive_constraint_tolerance = min(
                1.0e-8,
                max(1.0e-12, 0.1 * requested_y_decrease),
            )
            predictor_scale = 0.0
            candidate_initial_states = states
            candidate_initial_mapping_time = mapping_time
            candidate_initial_rotation = rotation
            if previous_y_support is not None:
                historical_y_decrease = previous_y_support - y_support
                if args.project_predictor_z:
                    (
                        _,
                        predictor_geometry_jacobian,
                        predictor_geometry_time_jacobian,
                        predictor_geometry_rotation_jacobian,
                    ) = _propagated_dense_smooth_geometry_constraints(
                        states,
                        source_phases=seed.phases,
                        mapping_time=mapping_time,
                        rotation_angle_rad=rotation,
                        mu=system.mu,
                        time_fractions=fractions,
                        phase_samples=args.phase_samples,
                        target_y_support=1.0,
                        target_z_support=1.0,
                        sharpness=args.smooth_preconditioner_sharpness,
                        max_step=0.005,
                    )
                    rotation_delta = float(
                        np.angle(np.exp(1j * (rotation - previous_rotation)))
                    )
                    augmented_direction = np.concatenate(
                        [
                            (states - previous_states).reshape(-1),
                            np.array(
                                [
                                    mapping_time - previous_mapping_time,
                                    rotation_delta,
                                ]
                            ),
                        ]
                    )
                    z_gradient = np.concatenate(
                        [
                            predictor_geometry_jacobian[1],
                            np.array(
                                [
                                    predictor_geometry_time_jacobian[1],
                                    predictor_geometry_rotation_jacobian[1],
                                ]
                            ),
                        ]
                    )
                    augmented_direction = _project_constraint_nullspace(
                        augmented_direction,
                        z_gradient,
                    )
                    y_gradient = np.concatenate(
                        [
                            predictor_geometry_jacobian[0],
                            np.array(
                                [
                                    predictor_geometry_time_jacobian[0],
                                    predictor_geometry_rotation_jacobian[0],
                                ]
                            ),
                        ]
                    )
                    predicted_y_change = float(
                        np.dot(y_gradient, augmented_direction)
                    )
                    if predicted_y_change < -1.0e-14:
                        predictor_scale = min(
                            args.predictor_scale_cap,
                            -requested_y_decrease / predicted_y_change,
                        )
                        augmented_step = predictor_scale * augmented_direction
                        z_correction_direction = _project_constraint_nullspace(
                            z_gradient,
                            y_gradient,
                        )
                        z_denominator = float(
                            np.dot(z_gradient, z_correction_direction)
                        )
                        if abs(z_denominator) > 1.0e-30:
                            augmented_step += (
                                requested_z_change
                                * z_correction_direction
                                / z_denominator
                            )
                        state_size = states.size
                        candidate_initial_states = states + (
                            augmented_step[:state_size].reshape(states.shape)
                        )
                        candidate_initial_mapping_time = mapping_time + float(
                            augmented_step[state_size]
                        )
                        candidate_initial_rotation = rotation + float(
                            augmented_step[state_size + 1]
                        )
                elif historical_y_decrease > 1.0e-14:
                    predictor_scale = min(
                        args.predictor_scale_cap,
                        requested_y_decrease / historical_y_decrease,
                    )
                    candidate_initial_states = states + predictor_scale * (
                        states - previous_states
                    )
                    candidate_initial_mapping_time = mapping_time + predictor_scale * (
                        mapping_time - previous_mapping_time
                    )
                    rotation_delta = float(
                        np.angle(np.exp(1j * (rotation - previous_rotation)))
                    )
                    candidate_initial_rotation = rotation + predictor_scale * rotation_delta
            predictor_z_progress = float("nan")
            if args.project_predictor_z and abs(requested_z_change) > 1.0e-14:
                predictor_active_residuals = _propagated_active_geometry_constraints(
                    candidate_initial_states,
                    source_phases=seed.phases,
                    mapping_time=candidate_initial_mapping_time,
                    rotation_angle_rad=candidate_initial_rotation,
                    mu=system.mu,
                    time_fractions=fractions,
                    phase_samples=args.phase_samples,
                    target_y_support=target_y_support,
                    target_z_support=member_z_event_target,
                    max_step=0.005,
                )[0]
                predictor_z_support = (
                    member_z_event_target + float(predictor_active_residuals[1])
                )
                predictor_z_progress = (
                    predictor_z_support - z_support
                ) / requested_z_change
            candidate = stroboscopic_curve_dual_geometry_correction(
                seed,
                target_jacobi=target_jacobi,
                target_y_support=target_y_support,
                target_z_support=member_z_event_target,
                initial_states=candidate_initial_states,
                initial_mapping_time=candidate_initial_mapping_time,
                initial_rotation_angle_rad=candidate_initial_rotation,
                phase_reference_states=states,
                geometry_time_fractions=fractions,
                active_geometry_phase_samples=args.phase_samples,
                regularization=args.regularization,
                energy_residual_scale=args.energy_residual_scale,
                geometry_residual_scale=args.geometry_residual_scale,
                max_iterations=args.max_correction_iterations,
                tolerance=1.0e-8,
                constraint_tolerance=adaptive_constraint_tolerance,
                max_step=0.005,
                max_state_step=5.0e-6,
                max_mapping_time_step=5.0e-4,
                max_rotation_step=5.0e-4,
                correction_damping=args.correction_damping,
            )
            candidate_metric = metric(candidate)
            curve_metric = float(np.max(candidate.final_residual_norms))
            initial_curve_metric = float(np.max(candidate.residual_history[0]))
            energy_metric = abs(float(candidate.energy_residual_history[-1]))
            geometry_metric = float(
                np.max(np.abs(candidate.geometry_residual_history[-1]))
            )
            geometry_y_metric = float(candidate.geometry_residual_history[-1, 0])
            geometry_z_metric = float(candidate.geometry_residual_history[-1, 1])
            phase_metric = abs(float(candidate.phase_residual_history[-1]))
            candidate_y_support = (
                target_y_support
                + float(candidate.geometry_residual_history[-1, 0])
            )
            candidate_z_support = (
                member_z_event_target
                + float(candidate.geometry_residual_history[-1, 1])
            )
            achieved_y_decrease = y_support - candidate_y_support
            y_progress_fraction = achieved_y_decrease / requested_y_decrease
            if abs(requested_z_change) > 1.0e-14:
                z_progress_fraction = (
                    candidate_z_support - z_support
                ) / requested_z_change
            else:
                z_progress_fraction = 1.0
            full_y_progress_fraction = float("nan")
            full_z_progress_fraction = float("nan")
            event_candidate_passed = (
                candidate_metric < 1.0e-8
                and y_progress_fraction >= args.min_y_progress_fraction
                and z_progress_fraction >= args.min_z_progress_fraction
            )
            full_candidate_passed = True
            if event_candidate_passed and args.validate_full_torus_progress:
                candidate_torus = sweep_corrected_curve_correction(
                    candidate,
                    time_samples=128,
                    max_step=0.0025,
                )
                candidate_surface, _ = resample_corrected_torus_surface(
                    candidate_torus,
                    phase_samples=256,
                )
                candidate_full_y_km = float(
                    np.max(np.abs(candidate_surface[:, :, 1]))
                    * system.length_unit_km
                )
                candidate_full_z_km = float(
                    np.max(np.abs(candidate_surface[:, :, 2]))
                    * system.length_unit_km
                )
                requested_full_y_decrease_km = step * current_full_y_km
                full_y_progress_fraction = (
                    current_full_y_km - candidate_full_y_km
                ) / requested_full_y_decrease_km
                if abs(z_correction_km) > 1.0e-14:
                    full_z_progress_fraction = (
                        candidate_full_z_km - current_full_z_km
                    ) / z_correction_km
                else:
                    full_z_progress_fraction = 1.0
                full_candidate_passed = (
                    full_y_progress_fraction
                    >= args.min_full_y_progress_fraction
                    and full_z_progress_fraction
                    >= args.min_full_z_progress_fraction
                )
            if event_candidate_passed and full_candidate_passed:
                correction = candidate
                last_full_y_progress = full_y_progress_fraction
                last_full_z_progress = full_z_progress_fraction
                break
            print(
                f"rejected={accepted + 1} retry={retry + 1} "
                f"step={step:.3e} metric={candidate_metric:.3e} "
                f"y_progress={y_progress_fraction:.3f} "
                f"z_progress={z_progress_fraction:.3f} "
                f"predictor_z_progress={predictor_z_progress:.3f} "
                f"full_y_progress={full_y_progress_fraction:.3f} "
                f"full_z_progress={full_z_progress_fraction:.3f} "
                f"predictor={predictor_scale:.3e} curve={curve_metric:.3e} "
                f"initial_curve={initial_curve_metric:.3e} "
                f"energy={energy_metric:.3e} geometry={geometry_metric:.3e} "
                f"geometry_y={geometry_y_metric:+.3e} "
                f"geometry_z={geometry_z_metric:+.3e} phase={phase_metric:.3e}",
                flush=True,
            )
            step *= 0.5
        if correction is None:
            raise RuntimeError("Active-event continuation exhausted step retries")
        old_states = states.copy()
        old_mapping_time = mapping_time
        old_rotation = rotation
        states = correction.corrected_states.copy()
        mapping_time = correction.mapping_time
        rotation = correction.rotation_angle_rad
        previous_states = old_states
        previous_mapping_time = old_mapping_time
        previous_rotation = old_rotation
        accepted += 1
        last = correction
        last_predictor_scale = predictor_scale
        step = min(args.max_relative_y_step, step * 1.05)
        np.savez_compressed(
            CHECKPOINT,
            states=states,
            mapping_time=mapping_time,
            rotation=rotation,
            jacobi=target_jacobi,
            accepted=accepted,
            step=step / 1.05,
            previous_states=previous_states,
            previous_mapping_time=previous_mapping_time,
            previous_rotation=previous_rotation,
        )
        print(f"accepted={accepted} metric={metric(correction):.3e}", flush=True)

    torus = sweep_corrected_curve_correction(last, time_samples=128, max_step=0.0025)
    surface, _ = resample_corrected_torus_surface(torus, phase_samples=256)
    final_event_residuals = _propagated_active_geometry_constraints(
        states,
        source_phases=seed.phases,
        mapping_time=mapping_time,
        rotation_angle_rad=rotation,
        mu=system.mu,
        time_fractions=fractions,
        phase_samples=args.phase_samples,
        target_y_support=1.0,
        target_z_support=1.0,
        max_step=0.005,
    )[0]
    event_y_km = float((1.0 + final_event_residuals[0]) * system.length_unit_km)
    event_z_km = float((1.0 + final_event_residuals[1]) * system.length_unit_km)
    full_y_km = float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km)
    full_z_km = float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km)
    row = {
        "accepted_members": accepted,
        "last_step": float(np.load(CHECKPOINT)["step"]),
        "combined_metric": metric(last),
        "max_abs_y_km": full_y_km,
        "max_abs_z_km": full_z_km,
        "event_max_abs_y_km": event_y_km,
        "event_max_abs_z_km": event_z_km,
        "event_to_full_y_gap_km": full_y_km - event_y_km,
        "event_to_full_z_gap_km": full_z_km - event_z_km,
        "jacobi_span": float(np.ptp(torus.jacobi_values)),
        "closure_residual": float(np.max(np.linalg.norm(torus.closure_residuals, axis=1))),
        "z_target_km": args.z_target_km,
        "z_target_error_km": float(
            np.max(np.abs(surface[:, :, 2])) * system.length_unit_km
            - args.z_target_km
        ),
        "event_time_slices": args.time_slices,
        "event_phase_samples": args.phase_samples,
        "per_member_z_correction_km": z_correction_km,
        "correction_iteration_cap": args.max_correction_iterations,
        "min_y_progress_fraction": args.min_y_progress_fraction,
        "min_z_progress_fraction": args.min_z_progress_fraction,
        "last_predictor_scale": last_predictor_scale,
        "regularization": args.regularization,
        "energy_residual_scale": args.energy_residual_scale,
        "geometry_residual_scale": args.geometry_residual_scale,
        "correction_damping": args.correction_damping,
        "retarget_current_jacobi": args.retarget_current_jacobi,
        "project_predictor_z": args.project_predictor_z,
        "smooth_preconditioner_sharpness": args.smooth_preconditioner_sharpness,
        "validate_full_torus_progress": args.validate_full_torus_progress,
        "last_full_y_progress_fraction": last_full_y_progress,
        "last_full_z_progress_fraction": last_full_z_progress,
        "jacobi_target": target_jacobi,
        "jacobi_target_change": target_jacobi - initial_checkpoint_jacobi,
        "jacobi_target_offset": args.jacobi_target_offset,
    }
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    REPORT.write_text(
        f"""# Chapter 5 active-event geometry family audit

- Accepted family members: `{accepted}`
- Last relative y-event step: `{row['last_step']:.3e}`
- Combined metric: `{row['combined_metric']:.3e}`
- Full-torus max |y|: `{row['max_abs_y_km']:.3f}` km
- Full-torus max |z|: `{row['max_abs_z_km']:.3f}` km
- Event-grid max |y|: `{row['event_max_abs_y_km']:.3f}` km
- Event-grid max |z|: `{row['event_max_abs_z_km']:.3f}` km
- Event-to-full y gap: `{row['event_to_full_y_gap_km']:+.3f}` km
- Event-to-full z gap: `{row['event_to_full_z_gap_km']:+.3f}` km
- Jacobi span: `{row['jacobi_span']:.3e}`
- Closure residual: `{row['closure_residual']:.3e}`
- z target error: `{row['z_target_error_km']:+.3f}` km
- Event grid: `{args.time_slices} x {args.phase_samples}`
- Applied per-member z correction: `{z_correction_km:+.3f}` km
- Per-candidate correction iteration cap: `{args.max_correction_iterations}`
- Minimum realized y-progress fraction: `{args.min_y_progress_fraction:.3f}`
- Minimum realized z-progress fraction: `{args.min_z_progress_fraction:.3f}`
- Last tangent-predictor scale: `{last_predictor_scale:.3e}`
- Regularization: `{args.regularization:.3e}`
- Energy residual scale: `{args.energy_residual_scale:.3e}`
- Geometry residual scale: `{args.geometry_residual_scale:.3e}`
- Correction damping: `{args.correction_damping:.3f}`
- Retarget current mean Jacobi before each member: `{args.retarget_current_jacobi}`
- Project predictor into z-constraint nullspace: `{args.project_predictor_z}`
- Smooth preconditioner sharpness: `{args.smooth_preconditioner_sharpness:.3e}`
- Validate full-torus progress: `{args.validate_full_torus_progress}`
- Last full-torus y-progress fraction: `{last_full_y_progress:.3f}`
- Last full-torus z-progress fraction: `{last_full_z_progress:.3f}`
- Active Jacobi target: `{target_jacobi:.15f}`
- Batch Jacobi-target change: `{target_jacobi - initial_checkpoint_jacobi:+.3e}`
- Per-member Jacobi-target offset: `{args.jacobi_target_offset:+.3e}`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `{args.max_relative_y_step:.3e}`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(CHECKPOINT)
    print(REPORT)


if __name__ == "__main__":
    main()
