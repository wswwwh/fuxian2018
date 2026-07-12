"""Propagate a two-angle stable-manifold periapsis scan for Figure 5.13."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import solve_ivp


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import cr3bp_rhs, jacobi_constant  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _trigonometric_interpolation_matrix,
    corrected_l1_vertical_lissajous_torus,
)
from qp_orbits.torus_stability import corrected_curve_dg, real_hyperbolic_eigen_index  # noqa: E402
from qp_orbits.variational import integrate_state_and_stm, unpack_augmented  # noqa: E402


DATA = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_lissajous_stable_manifold_scan.csv"
AUDIT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_lissajous_stable_manifold_audit.csv"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_lissajous_stable_manifold_audit.md"


def _periapsis(initial_state: np.ndarray, *, mu: float, duration: float, earth: np.ndarray, length_km: float) -> tuple[float, float, float]:
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
        max_step=0.02,
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
    system = SYSTEMS["sun_earth"]
    torus = corrected_l1_vertical_lissajous_torus(
        system.mu,
        vertical_orbit_amplitude=0.00628,
        samples=11,
        time_samples=24,
    )
    dg = corrected_curve_dg(torus.correction)
    stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
    stable_value = dg.eigenvalues[stable_index]
    native_count = torus.correction.corrected_states.shape[0]
    native_direction = np.real(dg.eigenvectors[:, stable_index]).reshape(native_count, 6)
    native_direction /= np.linalg.norm(native_direction[:, :3], axis=1)[:, None]

    theta0_degrees = np.unique(
        np.r_[np.arange(0.0, 360.0, 30.0), np.arange(210.0, 271.0, 1.0)]
    )
    time_phase_count = theta0_degrees.size
    curve_phase_count = 16
    phase_times = theta0_degrees / 360.0 * dg.mapping_time
    target_phases = np.linspace(0.0, 2.0 * np.pi, curve_phase_count, endpoint=False)
    transported_states = np.empty((time_phase_count, native_count, 6))
    transported_directions = np.empty_like(transported_states)
    for node, state in enumerate(torus.correction.corrected_states):
        solution = integrate_state_and_stm(
            state,
            (0.0, float(phase_times[-1])),
            system.mu,
            t_eval=phase_times,
            max_step=0.01,
        )
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
        interpolation = _trigonometric_interpolation_matrix(
            torus.correction.seed.phases,
            target_phases - fraction * dg.rotation_angle_rad,
        )
        states = interpolation @ transported_states[time_index]
        directions = interpolation @ transported_directions[time_index]
        directions /= np.linalg.norm(directions[:, :3], axis=1)[:, None]
        for curve_index in range(curve_phase_count):
            candidates = []
            for sign in (-1.0, 1.0):
                initial = states[curve_index] + sign * perturbation_scale * directions[curve_index]
                radius, time, drift = _periapsis(
                    initial,
                    mu=system.mu,
                    duration=8.0,
                    earth=earth,
                    length_km=float(system.length_unit_km),
                )
                candidates.append((radius, time, drift, sign))
            radius, time, drift, sign = min(candidates)
            rows.append(
                {
                    "theta0_index": time_index,
                    "theta1_index": curve_index,
                    "theta0_deg": theta0_degrees[time_index],
                    "theta1_deg": 360.0 * curve_index / curve_phase_count,
                    "periapsis_radius_km": radius,
                    "periapsis_time_days": time * system.time_unit_days,
                    "selected_half_manifold_sign": sign,
                    "jacobi_drift": drift,
                }
            )

    with DATA.open("w", newline="", encoding="utf-8") as stream:
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
        "source_model": "corrected Sun-Earth L1 Lissajous torus DG stable manifold",
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
    with AUDIT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(audit))
        writer.writeheader()
        writer.writerow(audit)
    source_audit = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_lissajous_torus_audit.csv"
    if source_audit.exists():
        with source_audit.open(newline="", encoding="utf-8") as stream:
            source_rows = list(csv.DictReader(stream))
        if source_rows:
            source_rows[0]["stable_manifold_map_acceptance"] = (
                "numerical_map_pass"
                if accepted and time_phase_count >= 60 and curve_phase_count >= 16
                else "target_gate_pass_resolution_pending"
                if accepted
                else "fail"
            )
            with source_audit.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(source_rows[0]))
                writer.writeheader()
                writer.writerows(source_rows)
    REPORT.write_text(
        f"""# Chapter 5 Lissajous stable-manifold two-angle audit

- Two-angle grid: `{time_phase_count} x {curve_phase_count}`
- Propagated half-manifold trajectories: `{len(rows) * 2}`
- Stable multiplier: `{stable_value}`
- Periapsis range: `{np.min(radii):.6f}` to `{np.max(radii):.6f}` km
- Best 7033-km candidate: `{radii[best_index]:.6f}` km
- Best target error: `{target_error[best_index]:.6f}` km
- Maximum Jacobi drift: `{max_drift:.6e}`
- Acceptance: `{'pass' if accepted else 'fail'}`

Each grid cell starts on the corrected two-frequency Lissajous torus. The real
stable DG eigenvector is transported along the first torus phase, interpolated
in the invariant-curve phase, and both half-manifold signs are propagated
backward. The recorded radius is therefore a numerical CR3BP result rather
than a thesis-shaped display function. This first grid is an acceptance scan;
resolution refinement remains required for pointwise paper comparison.
""",
        encoding="utf-8",
    )
    print(AUDIT)
    print(DATA)
    print(REPORT)
    print(f"acceptance={accepted}")


if __name__ == "__main__":
    main()
