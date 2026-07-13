"""Scan stable manifolds from the accepted active-geometry torus (Fig. 5.13)."""

from __future__ import annotations

import csv
import argparse
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import solve_ivp


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import cr3bp_rhs, jacobi_constant  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _propagated_active_geometry_constraints,
    _trigonometric_interpolation_matrix,
    stroboscopic_curve_dual_geometry_correction,
    stroboscopic_invariant_curve_seed,
)
from qp_orbits.torus_stability import corrected_curve_dg, real_hyperbolic_eigen_index  # noqa: E402
from qp_orbits.variational import integrate_state_and_stm, unpack_augmented  # noqa: E402


SEED_SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz"
CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_family_checkpoint.npz"
DATA = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_stable_manifold_scan.csv"
AUDIT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_stable_manifold_audit.csv"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_active_geometry_stable_manifold_audit.md"


def _accepted_active_correction(system):
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
    fractions = np.linspace(0.0, 1.0, 129)
    residuals, _, _, _, _ = _propagated_active_geometry_constraints(
        states,
        source_phases=seed.phases,
        mapping_time=mapping_time,
        rotation_angle_rad=rotation,
        mu=system.mu,
        time_fractions=fractions,
        phase_samples=256,
        target_y_support=1.0,
        target_z_support=1.0,
        max_step=0.005,
    )
    correction = stroboscopic_curve_dual_geometry_correction(
        seed,
        target_jacobi=float(data["jacobi"]),
        target_y_support=1.0 + float(residuals[0]),
        target_z_support=1.0 + float(residuals[1]),
        initial_states=states,
        initial_mapping_time=mapping_time,
        initial_rotation_angle_rad=rotation,
        phase_reference_states=states,
        geometry_time_fractions=fractions,
        active_geometry_phase_samples=256,
        regularization=1.0e-7,
        energy_residual_scale=1.0,
        geometry_residual_scale=1.0,
        max_iterations=2,
        tolerance=1.0e-8,
        constraint_tolerance=1.0e-8,
        max_step=0.005,
        max_state_step=5.0e-6,
        max_mapping_time_step=5.0e-4,
        max_rotation_step=5.0e-4,
        correction_damping=1.0,
    )
    return seed, correction


def _periapsis(initial_state: np.ndarray, *, mu: float, duration: float, earth: np.ndarray, length_km: float, max_step: float) -> tuple[float, float, float]:
    def radial_velocity(_time: float, state: np.ndarray) -> float:
        position = state[:3] - earth
        return float(np.dot(position, state[3:]) / np.linalg.norm(position))

    radial_velocity.terminal = False
    radial_velocity.direction = 0
    solution = solve_ivp(
        lambda time, state: cr3bp_rhs(time, state, mu),
        (0.0, -abs(duration)),
        initial_state,
        method="DOP853",
        rtol=2.0e-10,
        atol=2.0e-12,
        max_step=max_step,
        events=radial_velocity,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    candidates = [(solution.y[:, 0], 0.0), (solution.y[:, -1], float(solution.t[-1]))]
    candidates.extend((state, float(time)) for time, state in zip(solution.t_events[0], solution.y_events[0]))
    state, time = min(candidates, key=lambda item: np.linalg.norm(item[0][:3] - earth))
    radius_km = float(np.linalg.norm(state[:3] - earth) * length_km)
    drift = float(abs(jacobi_constant(state, mu) - jacobi_constant(initial_state, mu)))
    return radius_km, time, drift


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theta0-start", type=float, default=0.0)
    parser.add_argument("--theta0-stop", type=float, default=360.0)
    parser.add_argument("--theta0-step", type=float, default=30.0)
    parser.add_argument("--theta1-start", type=float, default=0.0)
    parser.add_argument("--theta1-stop", type=float, default=360.0)
    parser.add_argument("--theta1-step", type=float, default=22.5)
    parser.add_argument("--output-stem", default="chapter5_active_geometry_stable_manifold")
    parser.add_argument("--propagation-max-step", type=float, default=0.02)
    args = parser.parse_args()
    if args.theta0_step <= 0.0 or args.theta1_step <= 0.0:
        raise ValueError("phase steps must be positive")
    if args.propagation_max_step <= 0.0:
        raise ValueError("propagation-max-step must be positive")
    if args.theta0_stop <= args.theta0_start or args.theta1_stop <= args.theta1_start:
        raise ValueError("phase stop must exceed phase start")
    data_path = ROOT / "data" / "computed" / f"{args.output_stem}_scan.csv"
    audit_path = ROOT / "data" / "computed" / f"{args.output_stem}_audit.csv"
    report_path = ROOT / "docs" / f"{args.output_stem}_audit.md"
    system = SYSTEMS["sun_earth"]
    seed, correction = _accepted_active_correction(system)
    dg = corrected_curve_dg(correction)
    stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
    stable_value = dg.eigenvalues[stable_index]
    native_count = correction.corrected_states.shape[0]
    native_direction = np.real(dg.eigenvectors[:, stable_index]).reshape(native_count, 6)
    native_direction /= np.linalg.norm(native_direction[:, :3], axis=1)[:, None]

    if args.theta0_start == 0.0 and args.theta0_stop == 360.0 and args.theta0_step == 30.0:
        theta0_degrees = np.unique(
            np.r_[np.arange(0.0, 360.0, 30.0), np.arange(210.0, 271.0, 1.0)]
        )
    else:
        theta0_degrees = np.arange(args.theta0_start, args.theta0_stop, args.theta0_step)
    theta1_degrees = np.arange(args.theta1_start, args.theta1_stop, args.theta1_step)
    curve_phase_count = 16
    phase_times = theta0_degrees / 360.0 * dg.mapping_time
    target_phases = np.deg2rad(theta1_degrees)
    time_phase_count = theta0_degrees.size
    curve_phase_count = theta1_degrees.size
    transported_states = np.empty((time_phase_count, native_count, 6))
    transported_directions = np.empty_like(transported_states)
    for node, state in enumerate(correction.corrected_states):
        solution = integrate_state_and_stm(state, (0.0, float(phase_times[-1])), system.mu, t_eval=phase_times, max_step=0.01)
        if not solution.success:
            raise RuntimeError(solution.message)
        for time_index in range(time_phase_count):
            base, phi = unpack_augmented(solution.y[:, time_index])
            transported_states[time_index, node] = base
            transported_directions[time_index, node] = phi @ native_direction[node]

    earth = np.array([1.0 - system.mu, 0.0, 0.0])
    rows: list[dict[str, object]] = []
    perturbation_scale = 1.0e-7
    for time_index, phase_time in enumerate(phase_times):
        fraction = phase_time / dg.mapping_time
        interpolation = _trigonometric_interpolation_matrix(seed.phases, target_phases - fraction * dg.rotation_angle_rad)
        states = interpolation @ transported_states[time_index]
        directions = interpolation @ transported_directions[time_index]
        directions /= np.linalg.norm(directions[:, :3], axis=1)[:, None]
        for curve_index in range(curve_phase_count):
            candidates = []
            for sign in (-1.0, 1.0):
                initial = states[curve_index] + sign * perturbation_scale * directions[curve_index]
                radius, time, drift = _periapsis(initial, mu=system.mu, duration=8.0, earth=earth, length_km=float(system.length_unit_km), max_step=args.propagation_max_step)
                candidates.append((radius, time, drift, sign))
            radius, time, drift, sign = min(candidates)
            rows.append({
                "theta0_index": time_index,
                "theta1_index": curve_index,
                "theta0_deg": theta0_degrees[time_index],
                "theta1_deg": theta1_degrees[curve_index],
                "periapsis_radius_km": radius,
                "periapsis_time_days": time * system.time_unit_days,
                "selected_half_manifold_sign": sign,
                "jacobi_drift": drift,
            })

    with data_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    radii = np.array([float(row["periapsis_radius_km"]) for row in rows])
    target_error = np.abs(radii - 7_033.0)
    best_index = int(np.argmin(target_error))
    max_drift = max(float(row["jacobi_drift"]) for row in rows)
    accepted = (
        len(rows) == time_phase_count * curve_phase_count
        and abs(stable_value.imag) <= 1.0e-8
        and abs(stable_value) < 1.0
        and max_drift <= 1.0e-8
        and target_error[best_index] <= 500.0
    )
    audit = {
        "figure_id": "5.13",
        "source_model": "accepted active-geometry Sun-Earth L1 two-frequency torus DG stable manifold",
        "active_checkpoint_members": int(np.load(CHECKPOINT)["accepted"]),
        "theta0_samples": time_phase_count,
        "theta1_samples": curve_phase_count,
        "manifold_trajectories": len(rows) * 2,
        "stable_eigenvalue_real": stable_value.real,
        "stable_eigenvalue_imag": stable_value.imag,
        "stable_eigenvalue_abs": abs(stable_value),
        "minimum_periapsis_radius_km": float(np.min(radii)),
        "maximum_periapsis_radius_km": float(np.max(radii)),
        "best_7033_radius_km": float(radii[best_index]),
        "best_7033_error_km": float(target_error[best_index]),
        "best_theta0_deg": rows[best_index]["theta0_deg"],
        "best_theta1_deg": rows[best_index]["theta1_deg"],
        "maximum_jacobi_drift": max_drift,
        "acceptance": str(accepted).lower(),
    }
    with audit_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(audit))
        writer.writeheader()
        writer.writerow(audit)
    report_path.write_text(
        f"""# Chapter 5 active-geometry Lissajous stable-manifold audit

- Source checkpoint members: `{int(np.load(CHECKPOINT)['accepted'])}`
- Two-angle grid: `{time_phase_count} x {curve_phase_count}`
- Propagated half-manifold trajectories: `{len(rows) * 2}`
- Stable multiplier: `{stable_value}`
- Periapsis range: `{np.min(radii):.6f}` to `{np.max(radii):.6f}` km
- Best 7033-km candidate: `{radii[best_index]:.6f}` km
- Best target error: `{target_error[best_index]:.6f}` km
- Maximum Jacobi drift: `{max_drift:.6e}`
- Acceptance: `{'pass' if accepted else 'fail'}`

Every grid cell starts from the independently accepted active-geometry
checkpoint (member 468). The real stable DG eigenvector is transported along
the first torus phase, interpolated in the invariant-curve phase, and both
half-manifold signs are propagated backward in the CR3BP. The scan is therefore
an auditable numerical application of the accepted high-amplitude torus.
""",
        encoding="utf-8",
    )
    print(audit_path)
    print(data_path)
    print(report_path)
    print(f"acceptance={accepted}")


if __name__ == "__main__":
    main()
