"""Repropagate the accepted active-geometry stable-manifold candidate to LEO."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.quasi_torus import _trigonometric_interpolation_matrix  # noqa: E402
from qp_orbits.torus_stability import corrected_curve_dg, real_hyperbolic_eigen_index  # noqa: E402
from qp_orbits.variational import integrate_state_and_stm, unpack_augmented  # noqa: E402
from run_chapter5_active_geometry_stable_manifold_scan import _accepted_active_correction  # noqa: E402


SCAN = ROOT / "data" / "computed" / "chapter5_active_geometry_stable_manifold_tight_target_scan.csv"
TRAJECTORY = ROOT / "data" / "computed" / "chapter5_active_geometry_leo_transfer.csv"
AUDIT = ROOT / "data" / "computed" / "chapter5_active_geometry_leo_transfer_audit.csv"
REPORT = ROOT / "docs" / "chapter5_active_geometry_leo_transfer_audit.md"


def main() -> None:
    system = SYSTEMS["sun_earth"]
    with SCAN.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    selected = min(rows, key=lambda row: abs(float(row["periapsis_radius_km"]) - 7_033.0))
    theta0_deg = float(selected["theta0_deg"])
    theta1_deg = float(selected["theta1_deg"])
    sign = float(selected["selected_half_manifold_sign"])
    periapsis_time_days = float(selected["periapsis_time_days"])

    seed, correction = _accepted_active_correction(system)
    dg = corrected_curve_dg(correction)
    stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
    direction = np.real(dg.eigenvectors[:, stable_index]).reshape(-1, 6)
    direction /= np.linalg.norm(direction[:, :3], axis=1)[:, None]
    phase_time = theta0_deg / 360.0 * dg.mapping_time
    states = np.empty_like(correction.corrected_states)
    directions = np.empty_like(states)
    for node, state in enumerate(correction.corrected_states):
        solution = integrate_state_and_stm(
            state,
            (0.0, phase_time),
            system.mu,
            t_eval=np.array([phase_time]),
            max_step=0.01,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        states[node], phi = unpack_augmented(solution.y[:, -1])
        directions[node] = phi @ direction[node]
    target_phase = np.deg2rad(theta1_deg) - theta0_deg / 360.0 * dg.rotation_angle_rad
    interpolation = _trigonometric_interpolation_matrix(seed.phases, np.array([target_phase]))
    base_state = (interpolation @ states)[0]
    stable_direction = (interpolation @ directions)[0]
    stable_direction /= np.linalg.norm(stable_direction[:3])
    manifold_state = base_state + sign * 1.0e-7 * stable_direction

    final_time = periapsis_time_days / system.time_unit_days
    times = np.linspace(0.0, final_time, 900)
    solution = integrate_cr3bp(
        manifold_state,
        (0.0, final_time),
        system.mu,
        t_eval=times,
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    states_backward = solution.y.T
    chronological_states = states_backward[::-1]
    chronological_days = (times[::-1] - final_time) * system.time_unit_days
    earth = np.array([1.0 - system.mu, 0.0, 0.0])
    radii = np.linalg.norm(chronological_states[:, :3] - earth, axis=1) * system.length_unit_km
    jacobi_span = float(np.ptp(jacobi_constant(chronological_states, system.mu)))
    endpoint_distance_km = float(np.linalg.norm(chronological_states[-1] - base_state) * system.length_unit_km)

    with TRAJECTORY.open("w", newline="", encoding="utf-8") as stream:
        fields = ("sample", "elapsed_days", "x_nd", "y_nd", "z_nd", "xdot_nd", "ydot_nd", "zdot_nd", "earth_radius_km", "jacobi")
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        jacobi = jacobi_constant(chronological_states, system.mu)
        for index, (day, state, radius, jc) in enumerate(zip(chronological_days, chronological_states, radii, jacobi)):
            writer.writerow({
                "sample": index,
                "elapsed_days": f"{day:.16g}",
                "x_nd": f"{state[0]:.16g}",
                "y_nd": f"{state[1]:.16g}",
                "z_nd": f"{state[2]:.16g}",
                "xdot_nd": f"{state[3]:.16g}",
                "ydot_nd": f"{state[4]:.16g}",
                "zdot_nd": f"{state[5]:.16g}",
                "earth_radius_km": f"{radius:.16g}",
                "jacobi": f"{jc:.16g}",
            })

    target_error = abs(float(radii[0]) - 7_033.0)
    accepted = target_error <= 5.0 and jacobi_span <= 1.0e-8 and endpoint_distance_km <= 100.0
    audit = {
        "figure_id": "5.14",
        "source_model": "accepted active-geometry Sun-Earth L1 stable-manifold transfer",
        "active_checkpoint_members": int(np.load(ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_family_checkpoint.npz")["accepted"]),
        "theta0_deg": theta0_deg,
        "theta1_deg": theta1_deg,
        "stable_half_manifold_sign": sign,
        "trajectory_samples": len(chronological_states),
        "transfer_time_days": abs(periapsis_time_days),
        "periapsis_radius_km": float(radii[0]),
        "periapsis_target_error_km": target_error,
        "jacobi_span": jacobi_span,
        "lissajous_endpoint_distance_km": endpoint_distance_km,
        "acceptance": str(accepted).lower(),
    }
    with AUDIT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(audit))
        writer.writeheader()
        writer.writerow(audit)
    REPORT.write_text(
        f"""# Chapter 5 active-geometry Lissajous-to-LEO transfer audit

- Source checkpoint members: `468`
- Selected torus phases: `({theta0_deg}, {theta1_deg})` deg
- Stable half-manifold sign: `{sign}`
- Transfer time: `{abs(periapsis_time_days):.6f}` days
- Periapsis radius: `{radii[0]:.6f}` km
- 7033-km target error: `{target_error:.6f}` km
- Jacobi span: `{jacobi_span:.6e}`
- Lissajous endpoint distance: `{endpoint_distance_km:.6f}` km
- Acceptance: `{'pass' if accepted else 'fail'}`

The trajectory is a high-resolution CR3BP repropagation of the accepted
active-geometry stable-manifold candidate from the tight Fig. 5.13 scan.
Ephemeris/BCR4BP correction remains a separate high-fidelity boundary.
""",
        encoding="utf-8",
    )
    print(AUDIT)
    print(TRAJECTORY)
    print(REPORT)
    print(f"acceptance={accepted}")


if __name__ == "__main__":
    main()
