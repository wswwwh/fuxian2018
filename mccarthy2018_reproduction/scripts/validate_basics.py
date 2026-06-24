"""Numerical smoke tests for the CR3BP foundation layer."""

from __future__ import annotations

import csv

import numpy as np

from _paths import PROJECT_ROOT
from qp_orbits.application_scenarios import (
    converged_transfer_pair,
    dro_ephemeris_trajectory,
    earth_moon_halo_to_lyapunov_transfer_baseline,
    earth_moon_nrho_transfer_baseline,
    halo_to_lyapunov_scene,
    leo_to_l1_transfer,
    periapsis_radius_map,
    quasi_dro_return_scene,
    quasi_dro_cr3bp_return_scene,
    rendezvous_delta_v_curve,
    sun_earth_l1_cr3bp_long_propagation,
    sun_earth_l1_stable_manifold_baseline,
    sun_earth_l1_long_propagation,
)
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    interpolate_corrected_dro_state,
    load_corrected_dro_family_csv,
    sweep_corrected_dro_member,
)
from qp_orbits.cr3bp import integrate_cr3bp, jacobi_constant
from qp_orbits.ephemeris import (
    de421_quasi_dro_epoch_scenes,
    de421_quasi_dro_phase_scenes,
)
from qp_orbits.linear_modes import center_modes
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.manifolds import (
    hyperbolic_eigenvectors,
    lyapunov_family_stability,
    monodromy,
    periodic_halo_manifold_sample,
    spatial_symmetric_folded_family_stability,
)
from qp_orbits.periodic_orbits import (
    constant_energy_periodic_boundaries,
    correct_planar_lyapunov,
    period_q_halo_examples,
    planar_lyapunov_family,
    planar_lyapunov_linear_guess,
    propagate_periodic_orbit,
    spatial_symmetric_family,
    vertical_symmetric_family,
)
from qp_orbits.quasi_torus import (
    PseudoArclengthCurveCorrection,
    constant_frequency_halo_curve,
    constant_frequency_vertical_curve,
    central_periodic_orbit_scene,
    corrected_l1_constant_energy_halo_family,
    corrected_l1_constant_energy_halo_high_order_corrections,
    corrected_l1_constant_energy_halo_pseudo_arclength_family,
    corrected_l1_constant_energy_vertical_family,
    corrected_l1_constant_energy_vertical_staged_corrections,
    corrected_stroboscopic_torus_family,
    corrected_l2_constant_frequency_halo_energy_corrections,
    corrected_l2_constant_frequency_vertical_pseudo_arclength_corrections,
    corrected_stroboscopic_torus,
    corrected_dro_fixed_mapping_family,
    corrected_vertical_stroboscopic_torus_family,
    dro_parameter_curve,
    frequency_ratio_curves,
    l2_quasi_halo_family,
    l2_quasi_vertical_family,
    linear_quasi_halo_family,
    linear_quasi_vertical_family,
    quasi_dro_family,
    quasi_halo_parameter_curve,
    quasi_vertical_parameter_curve,
    resample_corrected_torus_surface,
    stroboscopic_curve_newton_correction,
    stroboscopic_fixed_target_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)
from qp_orbits.torus_stability import (
    base_torus,
    chapter4_quasi_halo_orbit,
    corrected_l1_constant_energy_halo_dg_family,
    corrected_l1_constant_energy_halo_high_order_dg_family,
    corrected_l1_constant_energy_halo_high_order_stability_family,
    corrected_l1_constant_energy_halo_pseudo_arclength_dg_family,
    corrected_l1_constant_energy_halo_pseudo_arclength_stability_family,
    corrected_l1_constant_energy_halo_stability_family,
    corrected_l1_constant_energy_halo_unstable_manifolds,
    corrected_curve_stable_manifold,
    corrected_curve_stability_family,
    corrected_curve_unstable_manifold,
    corrected_stroboscopic_curve_dg,
    corrected_vertical_curve_unstable_manifold,
    corrected_vertical_global_unstable_manifold,
    corrected_vertical_stroboscopic_curve_dg,
    display_scaled_corrected_dg_spectrum,
    dg_eigenvalue_loops,
    manifold_sheet,
    quasi_halo_stability_curve,
    real_hyperbolic_eigen_index,
)


def write_libration_points() -> None:
    output = PROJECT_ROOT / "data" / "computed" / "libration_points.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["system", "mu", "label", "x", "y", "z", "jacobi"],
        )
        writer.writeheader()
        for system in SYSTEMS.values():
            points = compute_libration_points(system.mu)
            for point in points.values():
                writer.writerow(
                    {
                        "system": system.key,
                        "mu": system.mu,
                        "label": point.label,
                        "x": f"{point.x:.16g}",
                        "y": f"{point.y:.16g}",
                        "z": f"{point.z:.16g}",
                        "jacobi": f"{point.jacobi:.16g}",
                    }
                )
    print(f"Wrote {output}")


def assert_earth_moon_points() -> None:
    points = compute_libration_points(SYSTEMS["earth_moon"].mu)
    assert 0.83 < points["L1"].x < 0.85, points["L1"]
    assert 1.14 < points["L2"].x < 1.17, points["L2"]
    assert -1.02 < points["L3"].x < -0.99, points["L3"]
    assert np.isclose(points["L4"].y, np.sqrt(3.0) / 2.0)
    assert np.isclose(points["L5"].y, -np.sqrt(3.0) / 2.0)
    print("Earth-Moon libration point bounds: ok")


def assert_jacobi_conservation() -> None:
    mu = SYSTEMS["earth_moon"].mu
    state0 = np.array([0.85, 0.08, 0.02, 0.0, 0.18, -0.01], dtype=float)
    c0 = float(jacobi_constant(state0, mu))
    t_eval = np.linspace(0.0, 2.0, 300)
    sol = integrate_cr3bp(state0, (t_eval[0], t_eval[-1]), mu, t_eval=t_eval, max_step=0.01)
    if not sol.success:
        raise RuntimeError(sol.message)
    c = jacobi_constant(sol.y.T, mu)
    drift = float(np.max(np.abs(c - c0)))
    assert drift < 1e-9, drift
    print(f"Jacobi drift over test arc: {drift:.3e}")


def assert_planar_lyapunov_correction() -> None:
    mu = SYSTEMS["earth_moon"].mu
    guess = planar_lyapunov_linear_guess(mu, point="L2", x_amplitude=-1.15e-3)
    orbit = correct_planar_lyapunov(mu, guess)
    final_residual = orbit.iterations[-1].residual_norm
    assert final_residual < 1e-10, final_residual
    assert 1.68 < orbit.half_period < 1.69, orbit.half_period

    output = PROJECT_ROOT / "data" / "computed" / "lyapunov_l2_summary.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "x0_guess",
                "ydot0_guess",
                "half_period_guess",
                "x0_corrected",
                "ydot0_corrected",
                "half_period_corrected",
                "period_corrected",
                "jacobi_corrected",
                "iterations",
                "final_residual_norm",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "system": "earth_moon",
                "point": "L2",
                "x0_guess": f"{guess.initial_state[0]:.16g}",
                "ydot0_guess": f"{guess.initial_state[4]:.16g}",
                "half_period_guess": f"{guess.half_period:.16g}",
                "x0_corrected": f"{orbit.initial_state[0]:.16g}",
                "ydot0_corrected": f"{orbit.initial_state[4]:.16g}",
                "half_period_corrected": f"{orbit.half_period:.16g}",
                "period_corrected": f"{orbit.period:.16g}",
                "jacobi_corrected": f"{orbit.jacobi:.16g}",
                "iterations": len(orbit.iterations),
                "final_residual_norm": f"{final_residual:.16g}",
            }
        )
    print(f"L2 Lyapunov correction residual: {final_residual:.3e}")
    print(f"Wrote {output}")


def assert_l1_manifold_foundation() -> None:
    mu = SYSTEMS["earth_moon"].mu
    guess = planar_lyapunov_linear_guess(mu, point="L1", x_amplitude=0.0111)
    orbit = correct_planar_lyapunov(mu, guess, max_iterations=20)
    data = monodromy(orbit)
    unstable, stable, lambda_u, lambda_s = hyperbolic_eigenvectors(data)

    assert abs(orbit.jacobi - 3.1827) < 1e-4, orbit.jacobi
    assert data.periodicity_error < 1e-8, data.periodicity_error
    assert abs(abs(lambda_u * lambda_s) - 1.0) < 1e-4, (lambda_u, lambda_s)
    assert data.stability_index > 10.0, data.stability_index
    assert np.linalg.norm(unstable[:3]) > 0.0
    assert np.linalg.norm(stable[:3]) > 0.0

    output = PROJECT_ROOT / "data" / "computed" / "lyapunov_l1_manifold_summary.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "x0",
                "ydot0",
                "period",
                "jacobi",
                "periodicity_error",
                "lambda_unstable_abs",
                "lambda_stable_abs",
                "stability_index",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "system": "earth_moon",
                "point": "L1",
                "x0": f"{orbit.initial_state[0]:.16g}",
                "ydot0": f"{orbit.initial_state[4]:.16g}",
                "period": f"{orbit.period:.16g}",
                "jacobi": f"{orbit.jacobi:.16g}",
                "periodicity_error": f"{data.periodicity_error:.16g}",
                "lambda_unstable_abs": f"{abs(lambda_u):.16g}",
                "lambda_stable_abs": f"{abs(lambda_s):.16g}",
                "stability_index": f"{data.stability_index:.16g}",
            }
        )
    print(
        "L1 Lyapunov monodromy: "
        f"|lambda_u|={abs(lambda_u):.3e}, |lambda_s|={abs(lambda_s):.3e}, "
        f"nu={data.stability_index:.3e}"
    )
    print(f"Wrote {output}")


def assert_jupiter_europa_lyapunov_family() -> None:
    mu = SYSTEMS["jupiter_europa"].mu
    amplitudes = [0.001, 0.002, 0.003, 0.004, 0.005, 0.006]
    family = planar_lyapunov_family(mu, amplitudes, point="L2", tolerance=1e-10, max_iterations=20)
    assert len(family) == len(amplitudes)
    assert all(orbit.iterations[-1].residual_norm < 1e-8 for orbit in family)

    ranges = []
    for amplitude, orbit in zip(amplitudes, family):
        states = propagate_periodic_orbit(orbit, samples=160)
        ranges.append(
            {
                "system": "jupiter_europa",
                "point": "L2",
                "x_amplitude_input": amplitude,
                "x0": orbit.initial_state[0],
                "ydot0": orbit.initial_state[4],
                "period": orbit.period,
                "jacobi": orbit.jacobi,
                "x_min": float(states[:, 0].min()),
                "x_max": float(states[:, 0].max()),
                "y_abs_max": float(np.max(np.abs(states[:, 1]))),
                "final_residual_norm": orbit.iterations[-1].residual_norm,
            }
        )

    assert max(row["y_abs_max"] for row in ranges) > 0.003
    output = PROJECT_ROOT / "data" / "computed" / "jupiter_europa_lyapunov_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "x_amplitude_input",
                "x0",
                "ydot0",
                "period",
                "jacobi",
                "x_min",
                "x_max",
                "y_abs_max",
                "final_residual_norm",
            ],
        )
        writer.writeheader()
        for row in ranges:
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in row.items()})
    print(f"Jupiter-Europa L2 Lyapunov family members: {len(family)}")
    print(f"Wrote {output}")


def assert_jupiter_europa_halo_like_family() -> None:
    mu = SYSTEMS["jupiter_europa"].mu
    z_amplitudes = [0.001, 0.002, 0.003, 0.004, 0.005, 0.006]
    family = spatial_symmetric_family(
        mu,
        z_amplitudes,
        point="L2",
        seed_x_amplitude=-0.001,
        family_label="halo",
    )
    assert len(family) == len(z_amplitudes)

    ranges = []
    for orbit in family:
        states = propagate_periodic_orbit(orbit, samples=180)
        data = monodromy(orbit)
        ranges.append(
            {
                "system": "jupiter_europa",
                "point": "L2",
                "z0": orbit.fixed_z0,
                "x0": orbit.initial_state[0],
                "ydot0": orbit.initial_state[4],
                "period": orbit.period,
                "jacobi": orbit.jacobi,
                "x_min": float(states[:, 0].min()),
                "x_max": float(states[:, 0].max()),
                "y_abs_max": float(np.max(np.abs(states[:, 1]))),
                "z_abs_max": float(np.max(np.abs(states[:, 2]))),
                "periodicity_error": data.periodicity_error,
                "stability_index": data.stability_index,
                "final_residual_norm": orbit.iterations[-1].residual_norm,
            }
        )

    assert all(row["final_residual_norm"] < 1e-10 for row in ranges)
    assert all(row["periodicity_error"] < 1e-8 for row in ranges)
    assert ranges[-1]["z_abs_max"] > ranges[0]["z_abs_max"]
    assert ranges[-1]["z_abs_max"] > 0.008
    assert max(row["stability_index"] for row in ranges) > 10.0

    output = PROJECT_ROOT / "data" / "computed" / "jupiter_europa_l2_halo_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "z0",
                "x0",
                "ydot0",
                "period",
                "jacobi",
                "x_min",
                "x_max",
                "y_abs_max",
                "z_abs_max",
                "periodicity_error",
                "stability_index",
                "final_residual_norm",
            ],
        )
        writer.writeheader()
        for row in ranges:
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in row.items()})
    print(f"Jupiter-Europa L2 halo-like family members: {len(family)}")
    print(f"Wrote {output}")


def assert_jupiter_europa_vertical_seed_family() -> None:
    mu = SYSTEMS["jupiter_europa"].mu
    z_amplitudes = np.r_[
        np.arange(0.0005, 0.0061, 0.0005),
        np.arange(0.010, 0.0501, 0.004),
    ]
    family = vertical_symmetric_family(
        mu,
        z_amplitudes,
        point="L2",
        max_iterations=32,
        secant_predictor=True,
    )
    assert len(family) == len(z_amplitudes)

    ranges = []
    for orbit in family:
        states = propagate_periodic_orbit(orbit, samples=180)
        data = monodromy(orbit)
        ranges.append(
            {
                "system": "jupiter_europa",
                "point": "L2",
                "z0": orbit.fixed_z0,
                "x0": orbit.initial_state[0],
                "ydot0": orbit.initial_state[4],
                "period": orbit.period,
                "jacobi": orbit.jacobi,
                "x_min": float(states[:, 0].min()),
                "x_max": float(states[:, 0].max()),
                "y_abs_max": float(np.max(np.abs(states[:, 1]))),
                "z_abs_max": float(np.max(np.abs(states[:, 2]))),
                "periodicity_error": data.periodicity_error,
                "stability_index": data.stability_index,
                "final_residual_norm": orbit.iterations[-1].residual_norm,
            }
        )

    assert all(row["final_residual_norm"] < 1e-10 for row in ranges)
    assert all(row["periodicity_error"] < 1e-8 for row in ranges)
    assert ranges[-1]["z_abs_max"] > ranges[0]["z_abs_max"]
    assert ranges[-1]["x0"] < 1.0
    assert ranges[-1]["ydot0"] > 0.015
    assert ranges[-1]["z_abs_max"] > 0.0499
    assert ranges[-1]["period"] > 5.0

    output = PROJECT_ROOT / "data" / "computed" / "jupiter_europa_l2_vertical_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "z0",
                "x0",
                "ydot0",
                "period",
                "jacobi",
                "x_min",
                "x_max",
                "y_abs_max",
                "z_abs_max",
                "periodicity_error",
                "stability_index",
                "final_residual_norm",
            ],
        )
        writer.writeheader()
        for row in ranges:
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in row.items()})
    print(f"Jupiter-Europa L2 corrected vertical family members: {len(family)}")
    print(f"Wrote {output}")


def assert_earth_moon_stability_curve() -> None:
    system = SYSTEMS["earth_moon"]
    amplitudes = [-0.001, -0.006, -0.012, -0.020, -0.030, -0.040, -0.045]
    rows = lyapunov_family_stability(system.mu, system.length_unit_km or 1.0, amplitudes, point="L2")
    assert len(rows) == len(amplitudes)
    assert max(row["stability_index"] for row in rows) > 500.0
    assert min(row["perilune_radius_km"] for row in rows) > 4.0e4
    assert all(row["periodicity_error"] < 1e-7 for row in rows)

    output = PROJECT_ROOT / "data" / "computed" / "earth_moon_l2_lyapunov_stability.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "x_amplitude_input",
                "x0",
                "ydot0",
                "period",
                "jacobi",
                "perilune_radius_km",
                "stability_index",
                "periodicity_error",
                "final_residual_norm",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = {"system": "earth_moon", "point": "L2"}
            out.update(row)
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in out.items()})
    print(f"Earth-Moon L2 Lyapunov stability samples: {len(rows)}")
    print(f"Wrote {output}")


def assert_earth_moon_halo_stability_curve() -> None:
    system = SYSTEMS["earth_moon"]
    rows = spatial_symmetric_folded_family_stability(
        system.mu,
        system.length_unit_km or 1.0,
        point="L2",
        seed_x_amplitude=-0.002,
    )
    assert len(rows) >= 60
    assert all(float(row["periodicity_error"]) < 2e-9 for row in rows)
    assert all(row["final_residual_norm"] < 1e-10 for row in rows)
    assert rows[0]["perilune_radius_km"] < 1_800.0
    assert rows[-1]["perilune_radius_km"] > 50_000.0
    assert rows[0]["stability_index"] < 1.01
    assert rows[-1]["stability_index"] > 600.0
    target_4800 = min(rows, key=lambda row: abs(float(row["perilune_radius_km"]) - 4_800.0))
    target_12610 = min(rows, key=lambda row: abs(float(row["perilune_radius_km"]) - 12_610.0))
    assert abs(float(target_4800["perilune_radius_km"]) - 4_800.0) < 0.1
    assert abs(float(target_12610["perilune_radius_km"]) - 12_610.0) < 0.1
    assert abs(float(target_4800["stability_index"]) - 1.5425) < 0.01
    assert abs(float(target_12610["stability_index"]) - 1.1762) < 0.01

    output = PROJECT_ROOT / "data" / "computed" / "earth_moon_l2_halo_stability.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "branch_method",
                "continuation_index",
                "z0",
                "x0",
                "ydot0",
                "period",
                "jacobi",
                "perilune_radius_km",
                "z_amplitude_km",
                "stability_index",
                "periodicity_error",
                "final_residual_norm",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = {"system": "earth_moon", "point": "L2"}
            out.update(row)
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in out.items()})
    print(
        "Earth-Moon L2 folded halo/NRHO stability branch: "
        f"{len(rows)} samples, "
        f"rp={rows[0]['perilune_radius_km']:.1f}..{rows[-1]['perilune_radius_km']:.1f} km, "
        f"nu={rows[0]['stability_index']:.6f}..{rows[-1]['stability_index']:.6f}"
    )
    print(f"Wrote {output}")


def assert_linear_quasi_halo_family() -> None:
    system = SYSTEMS["earth_moon"]
    rows = quasi_halo_parameter_curve(system, samples=16)
    family = linear_quasi_halo_family(system, samples=4, n_major=48, n_minor=16)

    assert len(rows) == 16
    assert len(family) == 4
    assert 3.2e4 < rows[0]["y_amplitude_km"] < 3.3e4
    assert 4.1e4 < rows[-1]["y_amplitude_km"] < 4.3e4
    assert 2.5e4 < rows[0]["z_amplitude_km"] < 2.7e4
    assert 3.5e4 < rows[-1]["z_amplitude_km"] < 3.7e4

    combined = np.concatenate([member.surface.reshape(-1, 3) for member in family], axis=0)
    assert 0.80 < combined[:, 0].min() < 0.83
    assert 0.86 < combined[:, 0].max() < 0.89
    assert np.max(np.abs(combined[:, 1])) > 0.08
    assert np.max(np.abs(combined[:, 2])) > 0.09

    output = PROJECT_ROOT / "data" / "computed" / "linear_quasi_halo_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "mapping_time_days",
                "y_amplitude_km",
                "z_amplitude_km",
                "y_amplitude_nd",
                "z_amplitude_nd",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = {"system": "earth_moon", "point": "L1"}
            out.update(row)
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in out.items()})

    print(f"Linear quasi-halo proxy samples: {len(rows)}")
    print(f"Wrote {output}")


def assert_linear_quasi_vertical_family() -> None:
    system = SYSTEMS["earth_moon"]
    rows = quasi_vertical_parameter_curve(system, samples=16)
    family = linear_quasi_vertical_family(system, samples=4, n_major=48, n_minor=16)

    assert len(rows) == 16
    assert len(family) == 4
    assert rows[0]["y_amplitude_km"] > 4.0e4
    assert rows[-1]["y_amplitude_km"] < 3.0e3
    assert max(row["z_amplitude_km"] for row in rows) > 3.8e4

    combined = np.concatenate([member.surface.reshape(-1, 3) for member in family], axis=0)
    assert 0.80 < combined[:, 0].min() < 0.84
    assert 0.86 < combined[:, 0].max() < 0.90
    assert np.max(np.abs(combined[:, 1])) > 0.07
    assert np.max(np.abs(combined[:, 2])) > 0.09

    output = PROJECT_ROOT / "data" / "computed" / "linear_quasi_vertical_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "system",
                "point",
                "mapping_time_days",
                "y_amplitude_km",
                "z_amplitude_km",
                "y_amplitude_nd",
                "z_amplitude_nd",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = {"system": "earth_moon", "point": "L1"}
            out.update(row)
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in out.items()})

    print(f"Linear quasi-vertical proxy samples: {len(rows)}")
    print(f"Wrote {output}")


def write_frequency_ratio_curves() -> None:
    curves = frequency_ratio_curves(samples=32)
    assert curves["quasi_halo"][0]["frequency_ratio"] < curves["quasi_halo"][-1]["frequency_ratio"]
    assert curves["quasi_vertical"][0]["frequency_ratio"] > curves["quasi_vertical"][-1]["frequency_ratio"]

    output = PROJECT_ROOT / "data" / "computed" / "frequency_ratio_curves.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["family", "mapping_time_days", "frequency_ratio"])
        writer.writeheader()
        for family, rows in curves.items():
            for row in rows:
                out = {"family": family}
                out.update(row)
                writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in out.items()})

    print(f"Wrote {output}")


def assert_constant_energy_periodic_boundaries() -> None:
    system = SYSTEMS["earth_moon"]
    points = constant_energy_periodic_boundaries(system, target_jacobi=3.1389)
    by_family = {point.family_label: point for point in points}
    halo = by_family["quasi_halo"]
    vertical = by_family["quasi_vertical"]

    assert set(by_family) == {"quasi_halo", "quasi_vertical"}
    assert max(abs(point.targeted.jacobi_error) for point in points) < 1.0e-10
    assert max(point.periodicity_error for point in points) < 1.0e-9
    assert max(point.targeted.orbit.iterations[-1].residual_norm for point in points) < 1.0e-10
    assert all(abs(abs(point.rotation_eigenvalue) - 1.0) < 1.0e-8 for point in points)
    assert 12.0 < halo.mapping_time_days < 12.1
    assert 9.0 < halo.frequency_ratio < 11.0
    assert 12.8 < vertical.mapping_time_days < 12.9
    assert 15.0 < vertical.frequency_ratio < 17.0

    output = PROJECT_ROOT / "data" / "computed" / "chapter3_constant_energy_periodic_boundaries.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "family",
        "target_jacobi",
        "z0",
        "x0",
        "ydot0",
        "period_nd",
        "mapping_time_days",
        "jacobi",
        "jacobi_error",
        "rotation_eigenvalue_real",
        "rotation_eigenvalue_imag",
        "rotation_angle_rad",
        "frequency_ratio",
        "periodicity_error",
        "shooting_residual",
        "target_history_size",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for point in points:
            orbit = point.targeted.orbit
            row = {
                "family": point.family_label,
                "target_jacobi": point.targeted.target_jacobi,
                "z0": orbit.fixed_z0,
                "x0": orbit.initial_state[0],
                "ydot0": orbit.initial_state[4],
                "period_nd": orbit.period,
                "mapping_time_days": point.mapping_time_days,
                "jacobi": orbit.jacobi,
                "jacobi_error": point.targeted.jacobi_error,
                "rotation_eigenvalue_real": point.rotation_eigenvalue.real,
                "rotation_eigenvalue_imag": point.rotation_eigenvalue.imag,
                "rotation_angle_rad": point.rotation_angle_rad,
                "frequency_ratio": point.frequency_ratio,
                "periodicity_error": point.periodicity_error,
                "shooting_residual": orbit.iterations[-1].residual_norm,
                "target_history_size": point.targeted.z0_history.size,
            }
            writer.writerow(
                {key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value for key, value in row.items()}
            )

    print(
        "JC=3.1389 periodic torus boundaries: "
        f"halo T={halo.mapping_time_days:.6f} d, ratio={halo.frequency_ratio:.6f}; "
        f"vertical T={vertical.mapping_time_days:.6f} d, ratio={vertical.frequency_ratio:.6f}"
    )
    print(f"Wrote {output}")


def assert_period_q_halo_examples() -> None:
    system = SYSTEMS["earth_moon"]
    examples = period_q_halo_examples(system.mu)
    by_resonance = {example.resonance: example for example in examples}
    assert set(by_resonance) == {2, 3, 8}
    assert 2.0 < by_resonance[2].bifurcation.frequency_ratio < 2.01
    assert abs(by_resonance[3].bifurcation.frequency_ratio - 3.0) < 1.0e-6
    assert abs(by_resonance[8].bifurcation.frequency_ratio - 8.0) < 1.0e-6

    for resonance, example in by_resonance.items():
        corrected = example.corrected
        assert corrected.orbit.family_label == f"period{resonance}"
        assert corrected.orbit.iterations[-1].residual_norm < 1.0e-9
        assert np.max(corrected.continuity_errors) < 1.0e-9
        assert np.linalg.norm(corrected.terminal_symmetry_error) < 1.0e-9
        assert np.linalg.norm(example.trajectory[-1] - example.trajectory[0]) < 1.0e-12
        jacobi = np.asarray([jacobi_constant(state, system.mu) for state in example.trajectory])
        assert np.ptp(jacobi) < 1.0e-9
        assert np.ptp(example.trajectory[:, 1]) > 0.20
        assert np.ptp(example.trajectory[:, 2]) > 0.15

    output = PROJECT_ROOT / "data" / "computed" / "chapter3_period_q_halo_orbits.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "resonance",
        "sample_index",
        "x",
        "y",
        "z",
        "xdot",
        "ydot",
        "zdot",
        "base_z0",
        "base_period_nd",
        "base_jacobi",
        "base_frequency_ratio",
        "base_periodicity_error",
        "corrected_z0",
        "corrected_period_nd",
        "corrected_jacobi",
        "shooting_residual",
        "max_continuity_error",
        "terminal_symmetry_error",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for example in examples:
            base = example.bifurcation
            corrected = example.corrected
            metadata = {
                "resonance": example.resonance,
                "base_z0": base.orbit.fixed_z0,
                "base_period_nd": base.orbit.period,
                "base_jacobi": base.orbit.jacobi,
                "base_frequency_ratio": base.frequency_ratio,
                "base_periodicity_error": base.periodicity_error,
                "corrected_z0": corrected.orbit.fixed_z0,
                "corrected_period_nd": corrected.orbit.period,
                "corrected_jacobi": corrected.orbit.jacobi,
                "shooting_residual": corrected.orbit.iterations[-1].residual_norm,
                "max_continuity_error": np.max(corrected.continuity_errors),
                "terminal_symmetry_error": np.linalg.norm(corrected.terminal_symmetry_error),
            }
            for sample_index, state in enumerate(example.trajectory):
                row = dict(metadata)
                row.update(
                    {
                        "sample_index": sample_index,
                        "x": state[0],
                        "y": state[1],
                        "z": state[2],
                        "xdot": state[3],
                        "ydot": state[4],
                        "zdot": state[5],
                    }
                )
                writer.writerow(
                    {
                        key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value
                        for key, value in row.items()
                    }
                )

    print(
        "Corrected period-q halo examples: "
        + ", ".join(
            f"q={example.resonance} T={example.corrected.orbit.period:.6f} nd"
            for example in examples
        )
    )
    print(f"Wrote {output}")


def assert_l2_constant_frequency_families() -> None:
    system = SYSTEMS["earth_moon"]
    halo_rows = constant_frequency_halo_curve(system, samples=20)
    vertical_rows = constant_frequency_vertical_curve(system, samples=20)
    halo_family = l2_quasi_halo_family(system, samples=4, n_major=48, n_minor=16)
    vertical_family = l2_quasi_vertical_family(system, samples=4, n_major=48, n_minor=14)

    assert halo_rows[0]["y_amplitude_km"] < halo_rows[-1]["y_amplitude_km"]
    assert halo_rows[0]["jacobi"] > halo_rows[-1]["jacobi"]
    assert vertical_rows[0]["jacobi"] > vertical_rows[-1]["jacobi"]
    assert vertical_rows[0]["mapping_time_days"] < vertical_rows[-1]["mapping_time_days"]

    halo_points = np.concatenate([member.surface.reshape(-1, 3) for member in halo_family], axis=0)
    vertical_points = np.concatenate([member.surface.reshape(-1, 3) for member in vertical_family], axis=0)
    assert 1.00 < halo_points[:, 0].min() < 1.15
    assert np.max(np.abs(halo_points[:, 1])) > 0.20
    assert np.max(np.abs(halo_points[:, 2])) > 0.20
    assert 1.08 < vertical_points[:, 0].max() < 1.18
    assert np.max(np.abs(vertical_points[:, 2])) > 0.18

    output = PROJECT_ROOT / "data" / "computed" / "constant_frequency_l2_families.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "family",
                "mapping_time_days",
                "y_amplitude_km",
                "z_amplitude_km",
                "y_amplitude_nd",
                "z_amplitude_nd",
                "jacobi",
                "orbit_index",
            ],
        )
        writer.writeheader()
        for row in halo_rows:
            out = {"family": "quasi_halo", "orbit_index": ""}
            out.update(row)
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in out.items()})
        for row in vertical_rows:
            out = {
                "family": "quasi_vertical",
                "y_amplitude_km": "",
                "z_amplitude_km": "",
                "y_amplitude_nd": "",
                "z_amplitude_nd": "",
            }
            out.update(row)
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in out.items()})
    print(f"Wrote {output}")


def assert_corrected_l2_constant_frequency_families() -> None:
    system = SYSTEMS["earth_moon"]
    families = {
        "quasi_halo": corrected_l2_constant_frequency_halo_energy_corrections(
            system.mu
        ),
        "quasi_vertical": (
            corrected_l2_constant_frequency_vertical_pseudo_arclength_corrections(
                system.mu
            )
        ),
    }
    assert len(families["quasi_halo"]) == 30
    assert len(families["quasi_vertical"]) == 25

    rows: list[dict[str, float | int | str]] = []
    for family_name, family in families.items():
        mapping_times = []
        jacobi_values = []
        for orbit_index, correction in enumerate(family):
            frequency_ratio = 2.0 * np.pi / correction.rotation_angle_rad
            mapping_time_days = correction.mapping_time * system.time_unit_days
            curve_jacobi = jacobi_constant(correction.corrected_states, system.mu)
            jacobi = float(np.mean(curve_jacobi))
            member = sweep_corrected_curve_correction(correction, time_samples=20)
            map_limit = 1.0e-7 if family_name == "quasi_halo" else 3.0e-9
            energy_limit = 5.0e-8 if family_name == "quasi_halo" else 1.2e-8
            mapping_times.append(correction.mapping_time)
            jacobi_values.append(jacobi)
            assert abs(frequency_ratio - 9.441) < 1.0e-12
            assert np.max(member.closure_error_norms) < map_limit
            assert member.jacobi_drift < energy_limit
            assert np.max(correction.final_residual_norms) < map_limit
            assert np.ptp(curve_jacobi) < energy_limit
            rows.append(
                {
                    "family": family_name,
                    "orbit_index": orbit_index,
                    "correction_type": type(correction).__name__,
                    "spectral_samples": correction.corrected_states.shape[0],
                    "target_frequency_ratio": 9.441,
                    "rotation_angle_rad": correction.rotation_angle_rad,
                    "target_jacobi": getattr(correction, "target_jacobi", ""),
                    "base_z0": correction.seed.base_orbit_amplitude,
                    "base_jacobi": correction.seed.orbit_jacobi,
                    "mapping_time_nd": correction.mapping_time,
                    "mapping_time_days": mapping_time_days,
                    "jacobi": jacobi,
                    "y_amplitude_km": 0.5 * np.ptp(member.surface[:, :, 1]) * system.length_unit_km,
                    "z_amplitude_km": 0.5 * np.ptp(member.surface[:, :, 2]) * system.length_unit_km,
                    "closure_error": np.max(member.closure_error_norms),
                    "jacobi_span": member.jacobi_drift,
                    "curve_residual": np.max(correction.final_residual_norms),
                    "curve_jacobi_span": np.ptp(curve_jacobi),
                    "max_jacobian_condition": np.max(correction.jacobian_condition_history),
                }
            )
        assert np.all(np.diff(mapping_times) > 0.0)
        assert np.all(np.diff(jacobi_values) < 0.0)

    halo = [row for row in rows if row["family"] == "quasi_halo"]
    vertical = [row for row in rows if row["family"] == "quasi_vertical"]
    assert abs(halo[0]["jacobi"] - 3.1182) < 1.0e-10
    assert abs(halo[-1]["jacobi"] - 3.0011) < 1.0e-10
    for target in (3.1182, 3.0876, 3.0364, 3.0011):
        assert min(abs(row["jacobi"] - target) for row in halo) < 1.0e-10
    assert 14.5 < halo[0]["mapping_time_days"] < 14.7
    assert 17.5 < halo[-1]["mapping_time_days"] < 17.8
    assert 16.8 < vertical[0]["mapping_time_days"] < 17.0
    assert 3.04 < vertical[0]["jacobi"] < 3.05
    assert abs(vertical[-1]["jacobi"] - 3.02868) < 1.0e-4
    assert abs(vertical[-1]["mapping_time_days"] - 17.256) < 0.01

    output = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_constant_frequency_families.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value
                    for key, value in row.items()
                }
            )

    print(
        "Corrected L2 constant-frequency families: "
        f"halo JC={halo[0]['jacobi']:.7f}->{halo[-1]['jacobi']:.7f}, "
        f"T={halo[0]['mapping_time_days']:.6f}->{halo[-1]['mapping_time_days']:.6f} d; "
        f"vertical endpoint JC={vertical[-1]['jacobi']:.9f}, "
        f"T={vertical[-1]['mapping_time_days']:.6f} d"
    )
    print(f"Wrote {output}")


def assert_corrected_l1_constant_energy_families() -> None:
    system = SYSTEMS["earth_moon"]
    target_jacobi = 3.1389
    families = {
        "quasi_halo": corrected_l1_constant_energy_halo_family(system.mu),
        "quasi_vertical": corrected_l1_constant_energy_vertical_family(system.mu),
    }
    assert all(len(family) == 4 for family in families.values())

    rows: list[dict[str, float | int | str]] = []
    for family_name, family in families.items():
        mapping_times = []
        frequency_ratios = []
        y_amplitudes = []
        for orbit_index, member in enumerate(family):
            correction = member.correction
            mapping_time_days = correction.mapping_time * system.time_unit_days
            frequency_ratio = 2.0 * np.pi / correction.rotation_angle_rad
            jacobi = float(np.mean(member.jacobi_values))
            y_amplitude = 0.5 * np.ptp(member.surface[:, :, 1]) * system.length_unit_km
            z_amplitude = 0.5 * np.ptp(member.surface[:, :, 2]) * system.length_unit_km
            mapping_times.append(correction.mapping_time)
            frequency_ratios.append(frequency_ratio)
            y_amplitudes.append(y_amplitude)
            assert abs(jacobi - target_jacobi) < 1.0e-10
            assert np.max(member.closure_error_norms) < 1.0e-9
            assert member.jacobi_drift < 1.0e-10
            assert np.max(correction.final_residual_norms) < 1.0e-9
            assert abs(correction.energy_residual_history[-1]) < 1.0e-10
            assert abs(correction.amplitude_residual_history[-1]) < 1.0e-10
            assert abs(correction.phase_residual_history[-1]) < 1.0e-10
            rows.append(
                {
                    "family": family_name,
                    "orbit_index": orbit_index,
                    "target_jacobi": target_jacobi,
                    "target_mode_amplitude_nd": correction.target_amplitude,
                    "base_z0": correction.seed.base_orbit_amplitude,
                    "base_jacobi": correction.seed.orbit_jacobi,
                    "mapping_time_nd": correction.mapping_time,
                    "mapping_time_days": mapping_time_days,
                    "rotation_angle_rad": correction.rotation_angle_rad,
                    "frequency_ratio": frequency_ratio,
                    "jacobi": jacobi,
                    "y_amplitude_km": y_amplitude,
                    "z_amplitude_km": z_amplitude,
                    "closure_error": np.max(member.closure_error_norms),
                    "jacobi_span": member.jacobi_drift,
                    "curve_residual": np.max(correction.final_residual_norms),
                    "energy_residual": correction.energy_residual_history[-1],
                    "amplitude_residual": correction.amplitude_residual_history[-1],
                    "phase_residual": correction.phase_residual_history[-1],
                    "max_jacobian_condition": np.max(correction.jacobian_condition_history),
                }
            )
        assert np.all(np.diff(frequency_ratios) > 0.0)
        assert np.all(np.diff(y_amplitudes) > 0.0)
        if family_name == "quasi_halo":
            assert np.all(np.diff(mapping_times) > 0.0)
        else:
            assert np.all(np.diff(mapping_times) < 0.0)

    halo = [row for row in rows if row["family"] == "quasi_halo"]
    vertical = [row for row in rows if row["family"] == "quasi_vertical"]
    assert 12.0 < halo[0]["mapping_time_days"] < 12.1
    assert 9.8 < halo[0]["frequency_ratio"] < 9.9
    assert 12.8 < vertical[0]["mapping_time_days"] < 12.9
    assert 16.2 < vertical[0]["frequency_ratio"] < 16.4

    output = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_constant_energy_families.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value
                    for key, value in row.items()
                }
            )

    print(
        "Corrected L1 constant-energy families: "
        f"halo T={halo[0]['mapping_time_days']:.6f} d, ratio={halo[0]['frequency_ratio']:.6f}; "
        f"vertical T={vertical[0]['mapping_time_days']:.6f} d, ratio={vertical[0]['frequency_ratio']:.6f}"
    )
    print(f"Wrote {output}")


def assert_corrected_l1_constant_energy_halo_pseudo_arclength_family() -> None:
    system = SYSTEMS["earth_moon"]
    target_jacobi = 3.1389
    family = corrected_l1_constant_energy_halo_pseudo_arclength_family(
        system.mu,
        members=27,
        time_samples=16,
    )
    assert len(family) == 27

    rows: list[dict[str, float | int | str]] = []
    mapping_times: list[float] = []
    mode_amplitudes: list[float] = []
    y_amplitudes: list[float] = []
    z_amplitudes: list[float] = []
    curve_jacobi_spans: list[float] = []
    temporal_jacobi_drifts: list[float] = []
    for member_index, member in enumerate(family):
        correction = member.correction
        component = correction.seed.mode_component
        displacement = (
            correction.corrected_states[:, component]
            - correction.seed.orbit_state[component]
        )
        mode_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        points = member.surface.reshape(-1, 3)
        y_amplitude = float(0.5 * np.ptp(points[:, 1]) * system.length_unit_km)
        z_amplitude = float(0.5 * np.ptp(points[:, 2]) * system.length_unit_km)
        mapping_time_days = float(correction.mapping_time * system.time_unit_days)
        mapping_times.append(mapping_time_days)
        mode_amplitudes.append(mode_amplitude)
        y_amplitudes.append(y_amplitude)
        z_amplitudes.append(z_amplitude)

        assert member.closure_error_norms.max() < 2.1e-9
        curve_jacobi_span = float(np.ptp(member.jacobi_values[0]))
        max_temporal_jacobi_drift = float(
            np.max(np.ptp(member.jacobi_values, axis=0))
        )
        curve_jacobi_spans.append(curve_jacobi_span)
        temporal_jacobi_drifts.append(max_temporal_jacobi_drift)
        assert curve_jacobi_span < 2.5e-7
        assert max_temporal_jacobi_drift < 2.0e-12
        assert abs(float(np.mean(member.jacobi_values)) - target_jacobi) < 1.0e-10
        assert correction.final_residual_norms.max() < 2.1e-9
        if isinstance(correction, PseudoArclengthCurveCorrection):
            assert abs(correction.energy_residual_history[-1]) < 1.0e-10
            assert abs(correction.longitudinal_phase_residual_history[-1]) < 1.0e-10
            assert abs(correction.latitudinal_phase_residual_history[-1]) < 1.0e-10
            assert abs(correction.arclength_residual_history[-1]) < 1.0e-10

        rows.append(
            {
                "member_index": member_index,
                "method": "pseudo-arclength"
                if isinstance(correction, PseudoArclengthCurveCorrection)
                else "natural-amplitude",
                "target_jacobi": target_jacobi,
                "mode_amplitude_nd": mode_amplitude,
                "mapping_time_nd": correction.mapping_time,
                "mapping_time_days": mapping_time_days,
                "rotation_angle_rad": correction.rotation_angle_rad,
                "frequency_ratio": 2.0 * np.pi / correction.rotation_angle_rad,
                "y_amplitude_km": y_amplitude,
                "z_amplitude_km": z_amplitude,
                "curve_residual": correction.final_residual_norms.max(),
                "closure_error": member.closure_error_norms.max(),
                "curve_jacobi_span": curve_jacobi_span,
                "max_temporal_jacobi_drift": max_temporal_jacobi_drift,
                "continuation_step": getattr(correction, "step_size", np.nan),
                "newton_iterations": correction.residual_history.shape[0],
            }
        )

    assert np.all(np.diff(mapping_times) > 0.0)
    assert np.all(np.diff(mode_amplitudes) > 0.0)
    assert np.all(np.diff(y_amplitudes) > 0.0)
    assert np.all(np.diff(z_amplitudes) > 0.0)
    assert mapping_times[-1] > 12.09
    assert mode_amplitudes[-1] > 0.017
    assert y_amplitudes[-1] > 37_000.0
    assert z_amplitudes[-1] > 29_000.0
    assert z_amplitudes[-1] - z_amplitudes[0] > 5_000.0

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter3_corrected_constant_energy_halo_pseudo_arclength_family.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value
                    for key, value in row.items()
                }
            )
    print(
        "Corrected L1 constant-energy quasi-halo pseudo-arclength family: "
        f"{len(family)} members, T={mapping_times[0]:.6f}..{mapping_times[-1]:.6f} d, "
        f"Ay={y_amplitudes[-1]:.1f} km, Az={z_amplitudes[-1]:.1f} km, "
        f"curve dJC={max(curve_jacobi_spans):.3e}, "
        f"time dJC={max(temporal_jacobi_drifts):.3e}"
    )
    print(f"Wrote {output}")


def assert_corrected_l1_constant_energy_halo_high_order_family() -> None:
    system = SYSTEMS["earth_moon"]
    target_jacobi = 3.1389
    n15 = corrected_l1_constant_energy_halo_high_order_corrections(
        system.mu,
        members=27,
        samples=15,
        max_iterations=48,
        tolerance=5.0e-10,
    )
    n21 = corrected_l1_constant_energy_halo_high_order_corrections(
        system.mu,
        members=15,
        samples=21,
        max_iterations=48,
        tolerance=2.0e-10,
    )

    rows: list[dict[str, float | int | str]] = []
    for stage, samples, tolerance, family in (
        ("N9-to-N15", 15, 5.0e-10, n15),
        ("N15-to-N21", 21, 2.0e-10, n21),
    ):
        mapping_times = [
            correction.mapping_time * system.time_unit_days for correction in family
        ]
        mode_amplitudes: list[float] = []
        for member_index, correction in enumerate(family):
            component = correction.seed.mode_component
            displacement = (
                correction.corrected_states[:, component]
                - correction.seed.orbit_state[component]
            )
            mode_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
            mode_amplitudes.append(mode_amplitude)
            curve_jacobi = jacobi_constant(correction.corrected_states, system.mu)
            assert correction.final_residual_norms.max() < 1.01 * tolerance
            assert abs(float(np.mean(curve_jacobi)) - target_jacobi) < 1.0e-10
            assert float(np.ptp(curve_jacobi)) < 2.0e-6
            if isinstance(correction, PseudoArclengthCurveCorrection):
                assert abs(correction.energy_residual_history[-1]) < 1.0e-10
                assert abs(correction.longitudinal_phase_residual_history[-1]) < 1.0e-10
                assert abs(correction.latitudinal_phase_residual_history[-1]) < 1.0e-10
                assert abs(correction.arclength_residual_history[-1]) < 1.0e-10
            rows.append(
                {
                    "stage": stage,
                    "curve_samples": samples,
                    "member_index": member_index,
                    "target_jacobi": target_jacobi,
                    "mode_amplitude_nd": mode_amplitude,
                    "mapping_time_nd": correction.mapping_time,
                    "mapping_time_days": mapping_times[member_index],
                    "rotation_angle_rad": correction.rotation_angle_rad,
                    "frequency_ratio": 2.0 * np.pi / correction.rotation_angle_rad,
                    "curve_residual": correction.final_residual_norms.max(),
                    "curve_jacobi_span": np.ptp(curve_jacobi),
                    "continuation_step": getattr(correction, "step_size", np.nan),
                    "newton_iterations": correction.residual_history.shape[0],
                }
            )
        assert np.all(np.diff(mapping_times) > 0.0)
        assert np.all(np.diff(mode_amplitudes) > 0.0)

    n15_times = np.asarray(
        [correction.mapping_time * system.time_unit_days for correction in n15]
    )
    n21_times = np.asarray(
        [correction.mapping_time * system.time_unit_days for correction in n21]
    )
    n15_target = n15[int(np.argmin(np.abs(n15_times - 12.26)))]
    n21_target = n21[int(np.argmin(np.abs(n21_times - 12.40)))]
    assert abs(n15_target.mapping_time * system.time_unit_days - 12.26) < 0.01
    assert abs(n21_target.mapping_time * system.time_unit_days - 12.40) < 0.01
    assert n21_times[-1] > 12.40

    amplitudes: list[tuple[float, float]] = []
    for correction in (n15_target, n21_target):
        member = sweep_corrected_curve_correction(correction, time_samples=24)
        assert member.closure_error_norms.max() < 2.1e-9
        assert np.max(np.ptp(member.jacobi_values, axis=0)) < 2.0e-12
        surface, _ = resample_corrected_torus_surface(member, phase_samples=96)
        points = surface.reshape(-1, 3)
        amplitudes.append(
            (
                float(0.5 * np.ptp(points[:, 1]) * system.length_unit_km),
                float(0.5 * np.ptp(points[:, 2]) * system.length_unit_km),
            )
        )
    assert amplitudes[1][0] > amplitudes[0][0]
    assert amplitudes[1][1] > amplitudes[0][1]
    assert amplitudes[1][0] > 40_000.0
    assert amplitudes[1][1] > 33_000.0

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter3_corrected_constant_energy_halo_high_order_family.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value
                    for key, value in row.items()
                }
            )
    print(
        "High-order L1 constant-energy quasi-halo continuation: "
        f"N15 T={n15_times[0]:.6f}..{n15_times[-1]:.6f} d; "
        f"N21 T={n21_times[0]:.6f}..{n21_times[-1]:.6f} d; "
        f"12.40-d sample Ay={amplitudes[1][0]:.1f} km, "
        f"Az={amplitudes[1][1]:.1f} km"
    )
    print(f"Wrote {output}")


def assert_corrected_l1_constant_energy_vertical_staged_family() -> None:
    system = SYSTEMS["earth_moon"]
    target_jacobi = 3.1389
    family = corrected_l1_constant_energy_vertical_staged_corrections(system.mu)
    assert len(family) >= 100

    rows: list[dict[str, float | int | str]] = []
    mapping_times: list[float] = []
    frequency_ratios: list[float] = []
    for member_index, correction in enumerate(family):
        mapping_time_days = correction.mapping_time * system.time_unit_days
        frequency_ratio = 2.0 * np.pi / correction.rotation_angle_rad
        component = correction.seed.mode_component
        displacement = (
            correction.corrected_states[:, component]
            - correction.seed.orbit_state[component]
        )
        mode_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        curve_jacobi = jacobi_constant(correction.corrected_states, system.mu)
        curve_jacobi_span = float(np.ptp(curve_jacobi))
        mapping_times.append(mapping_time_days)
        frequency_ratios.append(frequency_ratio)
        assert correction.final_residual_norms.max() < 3.1e-9
        assert abs(float(np.mean(curve_jacobi)) - target_jacobi) < 1.0e-10
        assert curve_jacobi_span < 1.0e-5
        if isinstance(correction, PseudoArclengthCurveCorrection):
            assert abs(correction.energy_residual_history[-1]) < 1.0e-10
            assert abs(correction.longitudinal_phase_residual_history[-1]) < 1.0e-10
            assert abs(correction.latitudinal_phase_residual_history[-1]) < 1.0e-10
            assert abs(correction.arclength_residual_history[-1]) < 1.0e-10
        rows.append(
            {
                "member_index": member_index,
                "curve_samples": correction.corrected_states.shape[0],
                "target_jacobi": target_jacobi,
                "mode_amplitude_nd": mode_amplitude,
                "mapping_time_nd": correction.mapping_time,
                "mapping_time_days": mapping_time_days,
                "rotation_angle_rad": correction.rotation_angle_rad,
                "frequency_ratio": frequency_ratio,
                "curve_residual": correction.final_residual_norms.max(),
                "curve_jacobi_span": curve_jacobi_span,
                "continuation_step": getattr(correction, "step_size", np.nan),
                "newton_iterations": correction.residual_history.shape[0],
            }
        )
    assert np.all(np.diff(mapping_times) < 0.0)
    assert np.all(np.diff(frequency_ratios) > 0.0)
    assert mapping_times[-1] < 12.67
    assert frequency_ratios[-1] > 39.0

    target_times = (12.87, 12.85, 12.78, 12.66)
    selected = [
        min(
            family,
            key=lambda correction: abs(
                correction.mapping_time * system.time_unit_days - target_time
            ),
        )
        for target_time in target_times
    ]
    amplitudes: list[tuple[float, float]] = []
    selected_times: list[float] = []
    for target_time, correction in zip(target_times, selected):
        selected_time = correction.mapping_time * system.time_unit_days
        selected_times.append(selected_time)
        assert abs(selected_time - target_time) < 0.01
        member = sweep_corrected_curve_correction(correction, time_samples=24)
        assert member.closure_error_norms.max() < 3.1e-9
        assert np.max(np.ptp(member.jacobi_values, axis=0)) < 2.0e-12
        surface, _ = resample_corrected_torus_surface(member, phase_samples=96)
        points = surface.reshape(-1, 3)
        amplitudes.append(
            (
                float(0.5 * np.ptp(points[:, 1]) * system.length_unit_km),
                float(0.5 * np.ptp(points[:, 2]) * system.length_unit_km),
            )
        )
    assert np.all(np.diff([amplitude[0] for amplitude in amplitudes]) > 0.0)
    assert amplitudes[-1][0] > 40_000.0
    assert 35_000.0 < amplitudes[-1][1] < 37_000.0

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter3_corrected_constant_energy_vertical_staged_family.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value
                    for key, value in row.items()
                }
            )
    print(
        "Staged L1 constant-energy quasi-vertical continuation: "
        f"{len(family)} members, N=9..33, "
        f"T={mapping_times[0]:.6f}..{mapping_times[-1]:.6f} d, "
        f"ratio={frequency_ratios[0]:.6f}..{frequency_ratios[-1]:.6f}; "
        f"12.66-d sample Ay={amplitudes[-1][0]:.1f} km, "
        f"Az={amplitudes[-1][1]:.1f} km"
    )
    print(f"Wrote {output}")


def assert_chapter3_central_periodic_scene() -> None:
    system = SYSTEMS["earth_moon"]
    scene = central_periodic_orbit_scene(system.mu, orbit_samples=260, map_samples=120)

    lyapunov_points = np.concatenate(scene.lyapunov_orbits, axis=0)
    upper_points = np.concatenate(scene.map_halo_upper, axis=0)
    lower_points = np.concatenate(scene.map_halo_lower, axis=0)

    assert len(scene.lyapunov_orbits) >= 10
    assert len(scene.map_halo_upper) >= 6
    assert len(scene.map_halo_upper) == len(scene.map_halo_lower)
    assert np.max(np.abs(lyapunov_points[:, 2])) < 1e-12
    assert lyapunov_points[:, 0].min() < 0.835
    assert lyapunov_points[:, 1].max() > 0.065
    assert scene.halo_orbit[:, 2].max() > 0.065
    assert scene.halo_orbit[:, 2].min() < -0.090
    assert scene.vertical_orbit[:, 2].max() > 0.095
    assert scene.vertical_orbit[:, 1].max() > 0.095
    assert upper_points[:, 1].max() > 0.105
    assert lower_points[:, 1].min() < -0.105
    assert np.all(scene.halo_section_centers[::2, 1] > 0.05)
    assert np.all(scene.halo_section_centers[1::2, 1] < -0.05)

    output = PROJECT_ROOT / "data" / "computed" / "earth_moon_l1_central_periodic_scene.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["kind", "curve_index", "x_min", "x_max", "y_min", "y_max", "z_min", "z_max"],
        )
        writer.writeheader()

        def write_curve(kind: str, curve_index: int | str, points: np.ndarray) -> None:
            writer.writerow(
                {
                    "kind": kind,
                    "curve_index": curve_index,
                    "x_min": f"{points[:, 0].min():.16g}",
                    "x_max": f"{points[:, 0].max():.16g}",
                    "y_min": f"{points[:, 1].min():.16g}",
                    "y_max": f"{points[:, 1].max():.16g}",
                    "z_min": f"{points[:, 2].min():.16g}",
                    "z_max": f"{points[:, 2].max():.16g}",
                }
            )

        for idx, curve in enumerate(scene.lyapunov_orbits):
            write_curve("lyapunov_orbit", idx, curve)
        write_curve("central_halo_orbit", "", scene.halo_orbit)
        write_curve("central_vertical_orbit", "", scene.vertical_orbit)
        for idx, point in enumerate(scene.halo_section_centers):
            write_curve("halo_z0_section_center", idx, point.reshape(1, 3))

    print(
        "Earth-Moon L1 central periodic scene: "
        f"{len(scene.lyapunov_orbits)} Lyapunov curves, "
        f"{len(scene.map_halo_upper)} halo section islands"
    )
    print(f"Wrote {output}")


def assert_stroboscopic_invariant_curve_seed() -> None:
    system = SYSTEMS["earth_moon"]
    seed = stroboscopic_invariant_curve_seed(system.mu, samples=7, curve_samples=120)
    correction = stroboscopic_fixed_target_correction(seed, iterations=3)
    curve_newton = stroboscopic_curve_newton_correction(seed)
    residual_norms = seed.residual_norms
    jacobi_initial = jacobi_constant(seed.initial_states, system.mu)
    jacobi_mapped = jacobi_constant(seed.mapped_states, system.mu)
    jacobi_drift = np.max(np.abs(jacobi_mapped - jacobi_initial))
    stm_determinants = np.linalg.det(seed.map_stms)

    assert seed.initial_states.shape == (7, 6)
    assert seed.map_stms.shape == (7, 6, 6)
    assert 0.15 < seed.rotation_angle_rad < 0.20, seed.rotation_angle_rad
    assert abs(abs(seed.monodromy_eigenvalue) - 1.0) < 1e-10
    assert residual_norms.max() < 2.0e-6, residual_norms.max()
    assert correction.final_residual_norms.max() < 1.0e-9, correction.final_residual_norms.max()
    assert curve_newton.final_residual_norms.max() < 1.0e-9, curve_newton.final_residual_norms.max()
    assert curve_newton.final_residual_norms.max() < 1e-3 * curve_newton.initial_residual_norms.max()
    assert np.allclose(curve_newton.interpolation_matrix.sum(axis=1), 1.0, atol=1e-12)
    assert correction.correction_norm_history[0].max() < seed.vertical_amplitude
    assert curve_newton.correction_norm_history[0].max() < seed.vertical_amplitude
    assert correction.final_residual_norms.max() < 1e-3 * residual_norms.max()
    assert jacobi_drift < 1e-11, jacobi_drift
    assert np.allclose(stm_determinants, 1.0, atol=1e-8), stm_determinants
    assert np.max(np.linalg.norm(seed.mapped_points, axis=1)) < 1.2

    output = PROJECT_ROOT / "data" / "computed" / "earth_moon_l1_stroboscopic_curve_seed.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "sample",
                "phase_rad",
                "rotation_angle_rad",
                "orbit_period",
                "orbit_jacobi",
                "vertical_amplitude",
                "initial_q0",
                "initial_q1",
                "mapped_q0",
                "mapped_q1",
                "predicted_q0",
                "predicted_q1",
                "residual_norm",
                "corrected_initial_q0",
                "corrected_initial_q1",
                "corrected_mapped_q0",
                "corrected_mapped_q1",
                "corrected_residual_norm",
                "first_correction_norm",
                "curve_newton_initial_q0",
                "curve_newton_initial_q1",
                "curve_newton_mapped_q0",
                "curve_newton_mapped_q1",
                "curve_newton_target_q0",
                "curve_newton_target_q1",
                "curve_newton_residual_norm",
                "curve_newton_first_correction_norm",
                "jacobi_drift",
                "map_stm_determinant",
                "curve_newton_first_jacobian_condition",
            ],
        )
        writer.writeheader()
        for idx in range(seed.initial_states.shape[0]):
            writer.writerow(
                {
                    "sample": idx,
                    "phase_rad": f"{seed.phases[idx]:.16g}",
                    "rotation_angle_rad": f"{seed.rotation_angle_rad:.16g}",
                    "orbit_period": f"{seed.orbit_period:.16g}",
                    "orbit_jacobi": f"{seed.orbit_jacobi:.16g}",
                    "vertical_amplitude": f"{seed.vertical_amplitude:.16g}",
                    "initial_q0": f"{seed.initial_points[idx, 0]:.16g}",
                    "initial_q1": f"{seed.initial_points[idx, 1]:.16g}",
                    "mapped_q0": f"{seed.mapped_points[idx, 0]:.16g}",
                    "mapped_q1": f"{seed.mapped_points[idx, 1]:.16g}",
                    "predicted_q0": f"{seed.predicted_points[idx, 0]:.16g}",
                    "predicted_q1": f"{seed.predicted_points[idx, 1]:.16g}",
                    "residual_norm": f"{residual_norms[idx]:.16g}",
                    "corrected_initial_q0": f"{correction.corrected_initial_points[idx, 0]:.16g}",
                    "corrected_initial_q1": f"{correction.corrected_initial_points[idx, 1]:.16g}",
                    "corrected_mapped_q0": f"{correction.corrected_mapped_points[idx, 0]:.16g}",
                    "corrected_mapped_q1": f"{correction.corrected_mapped_points[idx, 1]:.16g}",
                    "corrected_residual_norm": f"{correction.final_residual_norms[idx]:.16g}",
                    "first_correction_norm": f"{correction.correction_norm_history[0, idx]:.16g}",
                    "curve_newton_initial_q0": f"{curve_newton.corrected_points[idx, 0]:.16g}",
                    "curve_newton_initial_q1": f"{curve_newton.corrected_points[idx, 1]:.16g}",
                    "curve_newton_mapped_q0": f"{curve_newton.corrected_mapped_points[idx, 0]:.16g}",
                    "curve_newton_mapped_q1": f"{curve_newton.corrected_mapped_points[idx, 1]:.16g}",
                    "curve_newton_target_q0": f"{curve_newton.corrected_target_points[idx, 0]:.16g}",
                    "curve_newton_target_q1": f"{curve_newton.corrected_target_points[idx, 1]:.16g}",
                    "curve_newton_residual_norm": f"{curve_newton.final_residual_norms[idx]:.16g}",
                    "curve_newton_first_correction_norm": f"{curve_newton.correction_norm_history[0, idx]:.16g}",
                    "jacobi_drift": f"{(jacobi_mapped[idx] - jacobi_initial[idx]):.16g}",
                    "map_stm_determinant": f"{stm_determinants[idx]:.16g}",
                    "curve_newton_first_jacobian_condition": (
                        f"{curve_newton.jacobian_condition_history[0]:.16g}"
                        if curve_newton.jacobian_condition_history.size
                        else ""
                    ),
                }
            )

    print(
        "Earth-Moon L1 stroboscopic invariant-curve seed/correction: "
        f"rho={seed.rotation_angle_rad:.6f}, "
        f"seed max residual={residual_norms.max():.3e}, "
        f"fixed-target max residual={correction.final_residual_norms.max():.3e}, "
        f"curve-Newton max residual={curve_newton.final_residual_norms.max():.3e}"
    )
    print(f"Wrote {output}")


def assert_corrected_stroboscopic_torus() -> None:
    system = SYSTEMS["earth_moon"]
    torus = corrected_stroboscopic_torus(system.mu, samples=15, time_samples=36)
    seed = torus.correction.seed
    surface_points = torus.surface.reshape(-1, 3)
    xyz_span = np.ptp(surface_points, axis=0)
    mapping_time_days = seed.orbit_period * (system.time_unit_days or 1.0)

    assert torus.surface.shape == (36, 15, 3)
    assert torus.states.shape == (36, 15, 6)
    assert torus.closure_error_norms.max() < 1.0e-9, torus.closure_error_norms.max()
    assert torus.jacobi_drift < 1.0e-11, torus.jacobi_drift
    assert xyz_span[0] > 1.0e-3, xyz_span
    assert xyz_span[1] > 5.0e-3, xyz_span
    assert xyz_span[2] > 1.0e-5, xyz_span

    output = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_stroboscopic_torus.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "time_index",
                "curve_index",
                "time_nd",
                "time_days",
                "phase_rad",
                "x",
                "y",
                "z",
                "xdot",
                "ydot",
                "zdot",
                "jacobi",
                "terminal_closure_norm",
                "rotation_angle_rad",
                "orbit_period_nd",
                "mapping_time_days",
            ],
        )
        writer.writeheader()
        for time_idx, time_value in enumerate(torus.normalized_times):
            for curve_idx, state in enumerate(torus.states[time_idx]):
                writer.writerow(
                    {
                        "time_index": time_idx,
                        "curve_index": curve_idx,
                        "time_nd": f"{time_value:.16g}",
                        "time_days": f"{time_value * (system.time_unit_days or 1.0):.16g}",
                        "phase_rad": f"{seed.phases[curve_idx]:.16g}",
                        "x": f"{state[0]:.16g}",
                        "y": f"{state[1]:.16g}",
                        "z": f"{state[2]:.16g}",
                        "xdot": f"{state[3]:.16g}",
                        "ydot": f"{state[4]:.16g}",
                        "zdot": f"{state[5]:.16g}",
                        "jacobi": f"{torus.jacobi_values[time_idx, curve_idx]:.16g}",
                        "terminal_closure_norm": (
                            f"{torus.closure_error_norms[curve_idx]:.16g}"
                            if time_idx == torus.normalized_times.size - 1
                            else ""
                        ),
                        "rotation_angle_rad": f"{seed.rotation_angle_rad:.16g}",
                        "orbit_period_nd": f"{seed.orbit_period:.16g}",
                        "mapping_time_days": f"{mapping_time_days:.16g}",
                    }
                )

    print(
        "Corrected stroboscopic torus surface: "
        f"{torus.surface.shape[0]}x{torus.surface.shape[1]} samples, "
        f"closure={torus.closure_error_norms.max():.3e}, "
        f"Jacobi drift={torus.jacobi_drift:.3e}"
    )
    print(f"Wrote {output}")


def assert_corrected_stroboscopic_torus_family() -> None:
    system = SYSTEMS["earth_moon"]
    family = corrected_stroboscopic_torus_family(system.mu)
    rows: list[dict[str, float]] = []
    for idx, torus in enumerate(family):
        seed = torus.correction.seed
        surface_points = torus.surface.reshape(-1, 3)
        xyz_span = np.ptp(surface_points, axis=0)
        jacobi_min = float(np.min(torus.jacobi_values))
        jacobi_max = float(np.max(torus.jacobi_values))
        rows.append(
            {
                "member": float(idx),
                "vertical_amplitude_nd": float(seed.vertical_amplitude),
                "vertical_amplitude_km": float(seed.vertical_amplitude * (system.length_unit_km or 1.0)),
                "curve_samples": float(torus.surface.shape[1]),
                "time_samples": float(torus.surface.shape[0]),
                "mapping_time_days": float(seed.orbit_period * (system.time_unit_days or 1.0)),
                "rotation_angle_rad": float(seed.rotation_angle_rad),
                "orbit_jacobi": float(seed.orbit_jacobi),
                "jacobi_min": jacobi_min,
                "jacobi_max": jacobi_max,
                "jacobi_span": jacobi_max - jacobi_min,
                "closure_max": float(torus.closure_error_norms.max()),
                "curve_newton_residual": float(torus.correction.final_residual_norms.max()),
                "x_span": float(xyz_span[0]),
                "y_span": float(xyz_span[1]),
                "z_span": float(xyz_span[2]),
            }
        )

    closures = [row["closure_max"] for row in rows]
    z_spans = [row["z_span"] for row in rows]
    amplitudes = [row["vertical_amplitude_nd"] for row in rows]
    assert len(rows) == 4
    assert all(a < b for a, b in zip(amplitudes, amplitudes[1:]))
    assert max(closures) < 1.0e-8, closures
    assert all(a < b for a, b in zip(z_spans, z_spans[1:])), z_spans
    assert max(row["jacobi_span"] for row in rows) < 1.0e-11

    output = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_stroboscopic_torus_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: f"{value:.16g}" for key, value in row.items()})

    print(
        "Corrected stroboscopic torus family: "
        f"{len(rows)} members, "
        f"closure max={max(closures):.3e}, "
        f"z-span range={z_spans[0]:.3e}..{z_spans[-1]:.3e}"
    )
    print(f"Wrote {output}")


def assert_corrected_vertical_stroboscopic_torus_family() -> None:
    system = SYSTEMS["earth_moon"]
    family = corrected_vertical_stroboscopic_torus_family(system.mu)
    closures = [float(torus.closure_error_norms.max()) for torus in family]
    jacobi_spans = [float(torus.jacobi_drift) for torus in family]
    z_spans = [float(np.ptp(torus.surface.reshape(-1, 3)[:, 2])) for torus in family]
    base_amplitudes = [torus.correction.seed.base_orbit_amplitude for torus in family]
    rotations = [torus.correction.seed.rotation_angle_rad for torus in family]

    assert len(family) == 4
    assert all(torus.correction.seed.base_family == "vertical" for torus in family)
    assert all(torus.correction.seed.mode_component == 0 for torus in family)
    assert all(a < b for a, b in zip(base_amplitudes, base_amplitudes[1:])), base_amplitudes
    assert all(a < b for a, b in zip(z_spans, z_spans[1:])), z_spans
    assert max(closures) < 1.0e-8, closures
    assert max(jacobi_spans) < 1.0e-11, jacobi_spans
    assert all(0.17 < rotation < 0.20 for rotation in rotations), rotations

    output = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_vertical_stroboscopic_torus_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "member",
        "time_index",
        "curve_index",
        "time_nd",
        "time_days",
        "phase_rad",
        "x",
        "y",
        "z",
        "xdot",
        "ydot",
        "zdot",
        "jacobi",
        "base_vertical_amplitude_nd",
        "base_vertical_amplitude_km",
        "planar_mode_amplitude_nd",
        "rotation_angle_rad",
        "mapping_time_days",
        "terminal_closure_norm",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for member_idx, torus in enumerate(family):
            seed = torus.correction.seed
            for time_idx, time_value in enumerate(torus.normalized_times):
                for curve_idx, state in enumerate(torus.states[time_idx]):
                    writer.writerow(
                        {
                            "member": member_idx,
                            "time_index": time_idx,
                            "curve_index": curve_idx,
                            "time_nd": f"{time_value:.16g}",
                            "time_days": f"{time_value * (system.time_unit_days or 1.0):.16g}",
                            "phase_rad": f"{seed.phases[curve_idx]:.16g}",
                            "x": f"{state[0]:.16g}",
                            "y": f"{state[1]:.16g}",
                            "z": f"{state[2]:.16g}",
                            "xdot": f"{state[3]:.16g}",
                            "ydot": f"{state[4]:.16g}",
                            "zdot": f"{state[5]:.16g}",
                            "jacobi": f"{torus.jacobi_values[time_idx, curve_idx]:.16g}",
                            "base_vertical_amplitude_nd": f"{seed.base_orbit_amplitude:.16g}",
                            "base_vertical_amplitude_km": (
                                f"{seed.base_orbit_amplitude * (system.length_unit_km or 1.0):.16g}"
                            ),
                            "planar_mode_amplitude_nd": f"{seed.mode_amplitude:.16g}",
                            "rotation_angle_rad": f"{seed.rotation_angle_rad:.16g}",
                            "mapping_time_days": (
                                f"{seed.orbit_period * (system.time_unit_days or 1.0):.16g}"
                            ),
                            "terminal_closure_norm": (
                                f"{torus.closure_error_norms[curve_idx]:.16g}"
                                if time_idx == torus.normalized_times.size - 1
                                else ""
                            ),
                        }
                    )

    print(
        "Corrected quasi-vertical stroboscopic torus family: "
        f"{len(family)} members, closure max={max(closures):.3e}, "
        f"Jacobi span max={max(jacobi_spans):.3e}, "
        f"z-span range={z_spans[0]:.3e}..{z_spans[-1]:.3e}"
    )
    print(f"Wrote {output}")


def assert_corrected_dro_fixed_mapping_family() -> None:
    system = SYSTEMS["earth_moon"]
    x0 = 1.0 - system.mu - 73800.0 / (system.length_unit_km or 1.0)
    amplitudes = (1e-3, 5e-3, 1e-2, 1.5e-2, 2e-2)
    family = corrected_dro_fixed_mapping_family(
        system.mu,
        x0=x0,
        vertical_amplitudes=amplitudes,
        samples=21,
        initial_half_period=14.75 / (2.0 * (system.time_unit_days or 1.0)),
        max_iterations=12,
    )
    rotations = [correction.rotation_angle_rad for correction in family]
    map_residuals = [float(correction.final_residual_norms.max()) for correction in family]
    jacobi_values = [jacobi_constant(correction.corrected_states, system.mu) for correction in family]
    jacobi_spans = [float(np.ptp(values)) for values in jacobi_values]
    max_z_km = [
        float(np.max(np.abs(correction.corrected_states[:, 2])) * (system.length_unit_km or 1.0))
        for correction in family
    ]

    assert len(family) == len(amplitudes)
    assert all(correction.seed.base_family == "planar_dro" for correction in family)
    assert all(a < b for a, b in zip(rotations, rotations[1:])), rotations
    assert max(map_residuals) < 1.0e-8, map_residuals
    assert max(jacobi_spans) < 1.0e-8, jacobi_spans
    assert max(abs(correction.amplitude_residual_history[-1]) for correction in family) < 1.0e-10
    assert max(abs(correction.phase_residual_history[-1]) for correction in family) < 1.0e-10
    assert max_z_km[1] > 1737.4, max_z_km
    assert max_z_km[-1] > 7000.0, max_z_km
    mapping_time_days = family[0].seed.orbit_period * (system.time_unit_days or 1.0)
    assert 14.74 < mapping_time_days < 14.76, mapping_time_days

    output = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "member",
        "curve_index",
        "phase_rad",
        "x",
        "y",
        "z",
        "xdot",
        "ydot",
        "zdot",
        "jacobi",
        "target_vertical_amplitude_nd",
        "target_vertical_amplitude_km",
        "max_abs_z_km",
        "rotation_angle_rad",
        "mapping_time_days",
        "map_residual_norm",
        "amplitude_residual",
        "phase_residual",
        "curve_jacobi_span",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for member_idx, correction in enumerate(family):
            for curve_idx, state in enumerate(correction.corrected_states):
                writer.writerow(
                    {
                        "member": member_idx,
                        "curve_index": curve_idx,
                        "phase_rad": f"{correction.seed.phases[curve_idx]:.16g}",
                        "x": f"{state[0]:.16g}",
                        "y": f"{state[1]:.16g}",
                        "z": f"{state[2]:.16g}",
                        "xdot": f"{state[3]:.16g}",
                        "ydot": f"{state[4]:.16g}",
                        "zdot": f"{state[5]:.16g}",
                        "jacobi": f"{jacobi_values[member_idx][curve_idx]:.16g}",
                        "target_vertical_amplitude_nd": f"{amplitudes[member_idx]:.16g}",
                        "target_vertical_amplitude_km": (
                            f"{amplitudes[member_idx] * (system.length_unit_km or 1.0):.16g}"
                        ),
                        "max_abs_z_km": f"{max_z_km[member_idx]:.16g}",
                        "rotation_angle_rad": f"{rotations[member_idx]:.16g}",
                        "mapping_time_days": f"{mapping_time_days:.16g}",
                        "map_residual_norm": f"{map_residuals[member_idx]:.16g}",
                        "amplitude_residual": (
                            f"{correction.amplitude_residual_history[-1]:.16g}"
                        ),
                        "phase_residual": f"{correction.phase_residual_history[-1]:.16g}",
                        "curve_jacobi_span": f"{jacobi_spans[member_idx]:.16g}",
                    }
                )

    stored_family = load_corrected_dro_family_csv(output)
    assert len(stored_family) == len(family)
    assert all(member.states.shape == (21, 6) for member in stored_family)
    assert np.allclose(
        [member.rotation_angle_rad for member in stored_family],
        rotations,
        rtol=0.0,
        atol=1.0e-13,
    )
    for curve_index in (0, 7, 20):
        assert np.allclose(
            interpolate_corrected_dro_state(
                stored_family[-1],
                stored_family[-1].phases_rad[curve_index],
            ),
            stored_family[-1].states[curve_index],
            rtol=0.0,
            atol=1.0e-12,
        )
    sample_sweep = sweep_corrected_dro_member(stored_family[0], system, time_samples=5)
    assert sample_sweep.states.shape == (5, 21, 6)
    assert np.allclose(sample_sweep.states[0], stored_family[0].states, rtol=0.0, atol=1.0e-13)
    swept_jacobi = jacobi_constant(sample_sweep.states.reshape(-1, 6), system.mu)
    assert float(np.ptp(swept_jacobi)) < 1.0e-8
    print(
        "Corrected fixed-mapping-time quasi-DRO family: "
        f"{len(family)} members, mapping={mapping_time_days:.6f} days, "
        f"max residual={max(map_residuals):.3e}, "
        f"max Jacobi span={max(jacobi_spans):.3e}, "
        f"max |z|={max_z_km[-1]:.1f} km"
    )
    print(f"Wrote {output}")


def assert_quasi_dro_family() -> None:
    system = SYSTEMS["earth_moon"]
    rows = dro_parameter_curve(system, samples=20)
    family = quasi_dro_family(system, samples=4, n_major=64, n_minor=14)

    assert rows[0]["z_amplitude_km"] < rows[-1]["z_amplitude_km"]
    assert rows[0]["jacobi"] > rows[-1]["jacobi"]
    points = np.concatenate([member.surface.reshape(-1, 3) for member in family], axis=0)
    assert points[:, 0].min() < 0.85
    assert points[:, 0].max() > 1.15
    assert np.max(np.abs(points[:, 1])) > 0.25
    assert np.max(np.abs(points[:, 2])) > 0.05

    output = PROJECT_ROOT / "data" / "computed" / "quasi_dro_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["rotation_angle_rad", "z_amplitude_km", "z_amplitude_nd", "jacobi"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in row.items()})
    print(f"Wrote {output}")


def assert_chapter4_proxy_foundation() -> None:
    system = SYSTEMS["earth_moon"]
    loops = dg_eigenvalue_loops(samples=24)
    curve = quasi_halo_stability_curve(samples=24)
    halo_orbit = chapter4_quasi_halo_orbit(system, n_major=48, n_minor=10)
    halo_torus = base_torus(system, "halo", n_major=48, n_minor=12)
    plus_sheet = manifold_sheet(system, family="halo", direction="plus", stage_fraction=1.0, n_curve=36, n_steps=18)
    minus_sheet = manifold_sheet(system, family="vertical", direction="minus", stage_fraction=1.0, n_curve=36, n_steps=18)

    assert np.isclose(np.mean(np.abs(loops["middle"])), 1.0, atol=1e-12)
    assert np.mean(np.abs(loops["outer"])) > 2.0
    assert np.mean(np.abs(loops["inner"])) < 0.5
    assert curve[0]["stability_index"] < curve[-1]["stability_index"]
    assert 600.0 < curve[0]["stability_index"] < 650.0
    assert curve[-1]["stability_index"] > 780.0
    assert halo_orbit.surface[:, :, 2].max() > 0.16
    assert halo_torus.surface[:, :, 0].min() > 0.80
    assert plus_sheet.surface[:, :, 0].max() > 1.0
    assert minus_sheet.surface[:, :, 0].min() < 0.40

    output = PROJECT_ROOT / "data" / "computed" / "chapter4_torus_stability_proxy.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["kind", "mapping_time_days", "stability_index", "real", "imag"])
        writer.writeheader()
        for row in curve:
            writer.writerow(
                {
                    "kind": "stability_curve",
                    "mapping_time_days": f"{row['mapping_time_days']:.16g}",
                    "stability_index": f"{row['stability_index']:.16g}",
                    "real": "",
                    "imag": "",
                }
            )
        for name, values in loops.items():
            for value in values:
                writer.writerow(
                    {
                        "kind": f"dg_{name}",
                        "mapping_time_days": "",
                        "stability_index": "",
                        "real": f"{value.real:.16g}",
                        "imag": f"{value.imag:.16g}",
                    }
                )
    print(f"Wrote {output}")


def assert_chapter4_corrected_curve_dg() -> None:
    system = SYSTEMS["earth_moon"]
    dg = corrected_stroboscopic_curve_dg(system.mu, samples=15)
    seed = dg.correction.seed
    magnitudes = np.abs(dg.eigenvalues)
    row_sum_error = np.max(np.abs(dg.interpolation_to_base.sum(axis=1) - 1.0))
    mapping_time_days = seed.orbit_period * (system.time_unit_days or 1.0)

    assert dg.map_jacobian.shape == (90, 90)
    assert dg.stms.shape == (15, 6, 6)
    assert dg.correction.final_residual_norms.max() < 1.0e-9
    assert row_sum_error < 1.0e-12, row_sum_error
    assert abs(dg.determinant - 1.0) < 1.0e-6, dg.determinant
    assert 1.0e3 < dg.stability_index < 2.0e3, dg.stability_index
    assert abs(dg.max_multiplier * dg.min_multiplier - 1.0) < 1.0e-5
    assert dg.unit_multiplier_count >= 4 * seed.initial_states.shape[0] - 2
    scaled_spectrum = display_scaled_corrected_dg_spectrum(dg)
    assert len(scaled_spectrum["unstable"]) == seed.initial_states.shape[0]
    assert len(scaled_spectrum["stable"]) == seed.initial_states.shape[0]
    assert len(scaled_spectrum["unit"]) >= 4 * seed.initial_states.shape[0] - 2
    assert np.allclose(np.abs(scaled_spectrum["unstable"]), 2.35)
    assert np.allclose(np.abs(scaled_spectrum["stable"]), 0.38)

    output = PROJECT_ROOT / "data" / "computed" / "chapter4_corrected_curve_dg.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "index",
                "classification",
                "real",
                "imag",
                "magnitude",
                "angle_rad",
                "mapping_time_days",
                "rotation_angle_rad",
                "curve_residual_norm",
                "determinant",
                "stability_index",
            ],
        )
        writer.writeheader()
        for idx, value in enumerate(dg.eigenvalues):
            magnitude = abs(value)
            if magnitude > 1.0 + 1.0e-3:
                classification = "unstable"
            elif magnitude < 1.0 - 1.0e-3:
                classification = "stable"
            else:
                classification = "unit"
            writer.writerow(
                {
                    "index": idx,
                    "classification": classification,
                    "real": f"{value.real:.16g}",
                    "imag": f"{value.imag:.16g}",
                    "magnitude": f"{magnitude:.16g}",
                    "angle_rad": f"{np.angle(value):.16g}",
                    "mapping_time_days": f"{mapping_time_days:.16g}",
                    "rotation_angle_rad": f"{seed.rotation_angle_rad:.16g}",
                    "curve_residual_norm": f"{dg.correction.final_residual_norms.max():.16g}",
                    "determinant": f"{dg.determinant:.16g}",
                    "stability_index": f"{dg.stability_index:.16g}",
                }
            )
    print(
        "Chapter 4 corrected stroboscopic-curve DG: "
        f"N={seed.initial_states.shape[0]}, "
        f"nu={dg.stability_index:.3e}, "
        f"|det(DG)-1|={abs(dg.determinant - 1.0):.3e}"
    )
    print(f"Wrote {output}")


def assert_chapter4_corrected_vertical_curve_dg() -> None:
    system = SYSTEMS["earth_moon"]
    dg = corrected_vertical_stroboscopic_curve_dg(system.mu, samples=9)
    seed = dg.correction.seed
    magnitudes = np.abs(dg.eigenvalues)
    row_sum_error = np.max(np.abs(dg.interpolation_to_base.sum(axis=1) - 1.0))
    mapping_time_days = seed.orbit_period * (system.time_unit_days or 1.0)

    assert dg.map_jacobian.shape == (54, 54)
    assert dg.stms.shape == (9, 6, 6)
    assert seed.base_family == "vertical"
    assert seed.mode_component == 0
    assert dg.correction.final_residual_norms.max() < 1.0e-9
    assert row_sum_error < 1.0e-12, row_sum_error
    assert abs(dg.determinant - 1.0) < 1.0e-6, dg.determinant
    assert 1.5e3 < dg.stability_index < 2.0e3, dg.stability_index
    assert abs(dg.max_multiplier * dg.min_multiplier - 1.0) < 1.0e-5
    assert dg.unit_multiplier_count >= 4 * seed.initial_states.shape[0] - 2
    assert np.count_nonzero(magnitudes > 1.0 + 1.0e-3) == seed.initial_states.shape[0]
    assert np.count_nonzero(magnitudes < 1.0 - 1.0e-3) == seed.initial_states.shape[0]

    output = PROJECT_ROOT / "data" / "computed" / "chapter4_corrected_vertical_curve_dg.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "index",
                "classification",
                "real",
                "imag",
                "magnitude",
                "angle_rad",
                "mapping_time_days",
                "rotation_angle_rad",
                "base_vertical_amplitude_nd",
                "planar_mode_amplitude_nd",
                "curve_residual_norm",
                "determinant",
                "stability_index",
            ],
        )
        writer.writeheader()
        for idx, value in enumerate(dg.eigenvalues):
            magnitude = abs(value)
            if magnitude > 1.0 + 1.0e-3:
                classification = "unstable"
            elif magnitude < 1.0 - 1.0e-3:
                classification = "stable"
            else:
                classification = "unit"
            writer.writerow(
                {
                    "index": idx,
                    "classification": classification,
                    "real": f"{value.real:.16g}",
                    "imag": f"{value.imag:.16g}",
                    "magnitude": f"{magnitude:.16g}",
                    "angle_rad": f"{np.angle(value):.16g}",
                    "mapping_time_days": f"{mapping_time_days:.16g}",
                    "rotation_angle_rad": f"{seed.rotation_angle_rad:.16g}",
                    "base_vertical_amplitude_nd": f"{seed.base_orbit_amplitude:.16g}",
                    "planar_mode_amplitude_nd": f"{seed.mode_amplitude:.16g}",
                    "curve_residual_norm": f"{dg.correction.final_residual_norms.max():.16g}",
                    "determinant": f"{dg.determinant:.16g}",
                    "stability_index": f"{dg.stability_index:.16g}",
                }
            )
    print(
        "Chapter 4 corrected quasi-vertical curve DG: "
        f"N={seed.initial_states.shape[0]}, nu={dg.stability_index:.3e}, "
        f"|det(DG)-1|={abs(dg.determinant - 1.0):.3e}"
    )
    print(f"Wrote {output}")


def assert_chapter4_corrected_curve_stability_family() -> None:
    system = SYSTEMS["earth_moon"]
    rows = corrected_curve_stability_family(system.mu)
    amplitudes = [row["vertical_amplitude_nd"] for row in rows]
    stability = [row["stability_index"] for row in rows]

    assert len(rows) == 4
    assert all(a < b for a, b in zip(amplitudes, amplitudes[1:]))
    assert all(1.0e3 < value < 2.0e3 for value in stability)
    assert stability[0] > stability[-1]
    assert max(row["curve_residual_norm"] for row in rows) < 1.0e-8
    assert max(abs(row["determinant"] - 1.0) for row in rows) < 1.0e-6
    assert max(abs(row["max_multiplier"] * row["min_multiplier"] - 1.0) for row in rows) < 1.0e-5

    output = PROJECT_ROOT / "data" / "computed" / "chapter4_corrected_curve_stability_family.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "vertical_amplitude_nd",
                "vertical_amplitude_km",
                "orbit_period_nd",
                "mapping_time_days",
                "rotation_angle_rad",
                "curve_residual_norm",
                "stability_index",
                "max_multiplier",
                "min_multiplier",
                "determinant",
                "unit_multiplier_count",
            ],
        )
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["vertical_amplitude_km"] = row["vertical_amplitude_nd"] * (system.length_unit_km or 1.0)
            out["mapping_time_days"] = row["orbit_period_nd"] * (system.time_unit_days or 1.0)
            writer.writerow({key: f"{out[key]:.16g}" for key in writer.fieldnames})

    print(
        "Chapter 4 corrected-curve stability family: "
        f"{len(rows)} members, "
        f"nu={min(stability):.6f}..{max(stability):.6f}"
    )
    print(f"Wrote {output}")


def assert_chapter4_corrected_l1_constant_energy_halo_dg_family() -> None:
    system = SYSTEMS["earth_moon"]
    family = corrected_l1_constant_energy_halo_dg_family(system.mu)
    rows = corrected_l1_constant_energy_halo_stability_family(system.mu)
    assert len(family) == len(rows) == 4

    mapping_times = [row["mapping_time_nd"] for row in rows]
    stability = [row["stability_index"] for row in rows]
    assert all(a < b for a, b in zip(mapping_times, mapping_times[1:]))
    assert all(a < b for a, b in zip(stability, stability[1:]))
    assert max(row["curve_residual_norm"] for row in rows) < 1.0e-9
    assert max(abs(row["determinant"] - 1.0) for row in rows) < 2.0e-8
    assert min(stability) > 600.0
    assert max(stability) < 650.0

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter4_corrected_l1_constant_energy_halo_dg_family.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "member_index",
        "eigen_index",
        "mode_amplitude_nd",
        "mapping_time_nd",
        "mapping_time_days",
        "rotation_angle_rad",
        "eigenvalue_real",
        "eigenvalue_imag",
        "eigenvalue_magnitude",
        "stability_index",
        "determinant",
        "curve_residual_norm",
        "real_unstable_index",
        "real_stable_index",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for member_index, (dg, row) in enumerate(zip(family, rows)):
            unstable_index = real_hyperbolic_eigen_index(dg, branch="unstable")
            stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
            assert abs(dg.eigenvalues[unstable_index].imag) < 1.0e-8
            assert abs(dg.eigenvalues[stable_index].imag) < 1.0e-10
            reciprocal_product = abs(dg.eigenvalues[unstable_index] * dg.eigenvalues[stable_index])
            assert abs(reciprocal_product - 1.0) < 2.0e-6
            for eigen_index, eigenvalue in enumerate(dg.eigenvalues):
                writer.writerow(
                    {
                        "member_index": member_index,
                        "eigen_index": eigen_index,
                        "mode_amplitude_nd": f'{row["mode_amplitude_nd"]:.16g}',
                        "mapping_time_nd": f'{row["mapping_time_nd"]:.16g}',
                        "mapping_time_days": f'{row["mapping_time_nd"] * system.time_unit_days:.16g}',
                        "rotation_angle_rad": f'{row["rotation_angle_rad"]:.16g}',
                        "eigenvalue_real": f"{eigenvalue.real:.16g}",
                        "eigenvalue_imag": f"{eigenvalue.imag:.16g}",
                        "eigenvalue_magnitude": f"{abs(eigenvalue):.16g}",
                        "stability_index": f'{row["stability_index"]:.16g}',
                        "determinant": f'{row["determinant"]:.16g}',
                        "curve_residual_norm": f'{row["curve_residual_norm"]:.16g}',
                        "real_unstable_index": unstable_index,
                        "real_stable_index": stable_index,
                    }
                )
    print(
        "Chapter 4 finite-amplitude constant-energy quasi-halo DG family: "
        f"{len(family)} members, nu={min(stability):.6f}..{max(stability):.6f}"
    )
    print(f"Wrote {output}")


def assert_chapter4_corrected_l1_constant_energy_halo_pseudo_arclength_dg() -> None:
    system = SYSTEMS["earth_moon"]
    family = corrected_l1_constant_energy_halo_pseudo_arclength_dg_family(system.mu)
    rows = corrected_l1_constant_energy_halo_pseudo_arclength_stability_family(system.mu)
    assert len(family) == len(rows) == 7

    mapping_times = [row["mapping_time_nd"] * system.time_unit_days for row in rows]
    stability = [row["stability_index"] for row in rows]
    assert np.all(np.diff(mapping_times) > 0.0)
    assert mapping_times[-1] > 12.09
    assert max(row["curve_residual_norm"] for row in rows) < 2.1e-9
    assert max(abs(row["determinant"] - 1.0) for row in rows) < 1.0e-6
    assert stability[-1] > stability[0]

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter4_corrected_l1_constant_energy_halo_pseudo_arclength_dg.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_index",
        "eigen_index",
        "mode_amplitude_nd",
        "mapping_time_days",
        "rotation_angle_rad",
        "eigenvalue_real",
        "eigenvalue_imag",
        "eigenvalue_magnitude",
        "stability_index",
        "determinant",
        "curve_residual_norm",
        "real_unstable_index",
        "real_stable_index",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for sample_index, (dg, row) in enumerate(zip(family, rows)):
            unstable_index = real_hyperbolic_eigen_index(dg, branch="unstable")
            stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
            assert abs(dg.eigenvalues[unstable_index].imag) < 1.0e-7
            assert abs(dg.eigenvalues[stable_index].imag) < 1.0e-9
            reciprocal_product = abs(dg.eigenvalues[unstable_index] * dg.eigenvalues[stable_index])
            assert abs(reciprocal_product - 1.0) < 2.0e-5
            for eigen_index, eigenvalue in enumerate(dg.eigenvalues):
                writer.writerow(
                    {
                        "sample_index": sample_index,
                        "eigen_index": eigen_index,
                        "mode_amplitude_nd": f'{row["mode_amplitude_nd"]:.16g}',
                        "mapping_time_days": f'{row["mapping_time_nd"] * system.time_unit_days:.16g}',
                        "rotation_angle_rad": f'{row["rotation_angle_rad"]:.16g}',
                        "eigenvalue_real": f"{eigenvalue.real:.16g}",
                        "eigenvalue_imag": f"{eigenvalue.imag:.16g}",
                        "eigenvalue_magnitude": f"{abs(eigenvalue):.16g}",
                        "stability_index": f'{row["stability_index"]:.16g}',
                        "determinant": f'{row["determinant"]:.16g}',
                        "curve_residual_norm": f'{row["curve_residual_norm"]:.16g}',
                        "real_unstable_index": unstable_index,
                        "real_stable_index": stable_index,
                    }
                )
    print(
        "Chapter 4 pseudo-arclength quasi-halo DG samples: "
        f"{len(family)} members, T={mapping_times[0]:.6f}..{mapping_times[-1]:.6f} d, "
        f"nu={stability[0]:.6f}..{stability[-1]:.6f}"
    )
    print(f"Wrote {output}")


def assert_chapter4_corrected_l1_constant_energy_halo_high_order_dg() -> None:
    system = SYSTEMS["earth_moon"]
    configurations = (
        {
            "samples": 15,
            "members": 27,
            "member_indices": (8, 16, 26),
            "tolerance": 5.0e-10,
        },
        {
            "samples": 21,
            "members": 15,
            "member_indices": (12,),
            "tolerance": 2.0e-10,
        },
    )
    family = []
    rows = []
    for configuration in configurations:
        family.extend(
            corrected_l1_constant_energy_halo_high_order_dg_family(
                system.mu,
                **configuration,
            )
        )
        rows.extend(
            corrected_l1_constant_energy_halo_high_order_stability_family(
                system.mu,
                **configuration,
            )
        )
    assert len(family) == len(rows) == 4

    mapping_times = [row["mapping_time_nd"] * system.time_unit_days for row in rows]
    stability = [row["stability_index"] for row in rows]
    assert np.all(np.diff(mapping_times) > 0.0)
    assert abs(mapping_times[1] - 12.26) < 0.01
    assert abs(mapping_times[-1] - 12.40) < 0.01
    assert np.all(np.diff(stability) > 0.0)
    assert max(row["curve_residual_norm"] for row in rows) < 5.1e-10
    assert max(abs(row["determinant"] - 1.0) for row in rows) < 2.0e-5

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter4_corrected_l1_constant_energy_halo_high_order_dg.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sample_index",
        "curve_samples",
        "eigen_index",
        "mode_amplitude_nd",
        "mapping_time_days",
        "rotation_angle_rad",
        "eigenvalue_real",
        "eigenvalue_imag",
        "eigenvalue_magnitude",
        "stability_index",
        "determinant",
        "curve_residual_norm",
        "real_unstable_index",
        "real_stable_index",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for sample_index, (dg, row) in enumerate(zip(family, rows)):
            unstable_index = real_hyperbolic_eigen_index(dg, branch="unstable")
            stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
            assert abs(dg.eigenvalues[unstable_index].imag) < 1.0e-6
            assert abs(dg.eigenvalues[stable_index].imag) < 1.0e-8
            reciprocal_product = abs(
                dg.eigenvalues[unstable_index] * dg.eigenvalues[stable_index]
            )
            assert abs(reciprocal_product - 1.0) < 5.0e-5
            for eigen_index, eigenvalue in enumerate(dg.eigenvalues):
                writer.writerow(
                    {
                        "sample_index": sample_index,
                        "curve_samples": int(row["curve_samples"]),
                        "eigen_index": eigen_index,
                        "mode_amplitude_nd": f'{row["mode_amplitude_nd"]:.16g}',
                        "mapping_time_days": f'{row["mapping_time_nd"] * system.time_unit_days:.16g}',
                        "rotation_angle_rad": f'{row["rotation_angle_rad"]:.16g}',
                        "eigenvalue_real": f"{eigenvalue.real:.16g}",
                        "eigenvalue_imag": f"{eigenvalue.imag:.16g}",
                        "eigenvalue_magnitude": f"{abs(eigenvalue):.16g}",
                        "stability_index": f'{row["stability_index"]:.16g}',
                        "determinant": f'{row["determinant"]:.16g}',
                        "curve_residual_norm": f'{row["curve_residual_norm"]:.16g}',
                        "real_unstable_index": unstable_index,
                        "real_stable_index": stable_index,
                    }
                )
    print(
        "Chapter 4 high-order quasi-halo DG samples: "
        f"T={mapping_times[0]:.6f}..{mapping_times[-1]:.6f} d, "
        f"nu={stability[0]:.6f}..{stability[-1]:.6f}"
    )
    print(f"Wrote {output}")


def assert_chapter4_corrected_l1_constant_energy_halo_manifolds() -> None:
    system = SYSTEMS["earth_moon"]
    snapshot_days = (7.79, 9.75, 11.39, 13.02)
    plus_x, minus_x = corrected_l1_constant_energy_halo_unstable_manifolds(
        system.mu,
        time_unit_days=system.time_unit_days,
        snapshot_times_days=snapshot_days,
    )
    sheets = {"plus_x": plus_x, "minus_x": minus_x}
    for sheet in sheets.values():
        assert sheet.dg.correction.seed.base_family == "halo"
        assert sheet.dg.mapping_time * system.time_unit_days > 12.09
        component = sheet.dg.correction.seed.mode_component
        displacement = (
            sheet.dg.correction.corrected_states[:, component]
            - sheet.dg.correction.seed.orbit_state[component]
        )
        mode_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        assert mode_amplitude > 0.017
        assert sheet.surface.shape[1:] == (9, 3)
        assert abs(sheet.eigenvalue.imag) < 1.0e-8
        assert abs(sheet.eigenvalue) > 1.0e3
        initial_separation = sheet.state_separation_norms[0]
        assert np.allclose(initial_separation, sheet.perturbation_scale, rtol=1.0e-9, atol=1.0e-12)
        jacobi_values = jacobi_constant(
            sheet.manifold_states.reshape(-1, 6),
            system.mu,
        ).reshape(sheet.manifold_states.shape[:2])
        assert np.max(np.ptp(jacobi_values, axis=0)) < 2.0e-8
        elapsed_days = sheet.times * system.time_unit_days
        for snapshot in snapshot_days:
            assert np.min(abs(elapsed_days - snapshot)) < 1.0e-10

    assert np.mean(plus_x.surface[-1, :, 0]) > np.mean(minus_x.surface[-1, :, 0])
    assert plus_x.surface[-1, :, 0].max() > 0.90
    assert minus_x.surface[-1, :, 0].min() < 0.85

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter4_corrected_l1_constant_energy_halo_unstable_manifolds.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "branch",
        "time_index",
        "curve_index",
        "elapsed_nd",
        "elapsed_days",
        "x",
        "y",
        "z",
        "xdot",
        "ydot",
        "zdot",
        "base_x",
        "base_y",
        "base_z",
        "state_separation_nd",
        "jacobi",
        "eigenvalue_real",
        "perturbation_sign",
        "perturbation_scale",
        "mapping_time_days",
        "mode_amplitude_nd",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for branch, sheet in sheets.items():
            component = sheet.dg.correction.seed.mode_component
            displacement = (
                sheet.dg.correction.corrected_states[:, component]
                - sheet.dg.correction.seed.orbit_state[component]
            )
            mode_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
            jacobi_values = jacobi_constant(
                sheet.manifold_states.reshape(-1, 6),
                system.mu,
            ).reshape(sheet.manifold_states.shape[:2])
            separations = sheet.state_separation_norms
            for time_index, elapsed in enumerate(sheet.times):
                for curve_index in range(sheet.surface.shape[1]):
                    state = sheet.manifold_states[time_index, curve_index]
                    base = sheet.base_states[time_index, curve_index]
                    writer.writerow(
                        {
                            "branch": branch,
                            "time_index": time_index,
                            "curve_index": curve_index,
                            "elapsed_nd": f"{elapsed:.16g}",
                            "elapsed_days": f"{elapsed * system.time_unit_days:.16g}",
                            "x": f"{state[0]:.16g}",
                            "y": f"{state[1]:.16g}",
                            "z": f"{state[2]:.16g}",
                            "xdot": f"{state[3]:.16g}",
                            "ydot": f"{state[4]:.16g}",
                            "zdot": f"{state[5]:.16g}",
                            "base_x": f"{base[0]:.16g}",
                            "base_y": f"{base[1]:.16g}",
                            "base_z": f"{base[2]:.16g}",
                            "state_separation_nd": f"{separations[time_index, curve_index]:.16g}",
                            "jacobi": f"{jacobi_values[time_index, curve_index]:.16g}",
                            "eigenvalue_real": f"{sheet.eigenvalue.real:.16g}",
                            "perturbation_sign": f"{sheet.perturbation_sign:.16g}",
                            "perturbation_scale": f"{sheet.perturbation_scale:.16g}",
                            "mapping_time_days": f"{sheet.dg.mapping_time * system.time_unit_days:.16g}",
                            "mode_amplitude_nd": f"{mode_amplitude:.16g}",
                        }
                    )
    print(
        "Chapter 4 finite-amplitude quasi-halo unstable manifolds: "
        f"+x terminal={np.mean(plus_x.surface[-1, :, 0]):.6f}, "
        f"-x terminal={np.mean(minus_x.surface[-1, :, 0]):.6f}"
    )
    print(f"Wrote {output}")


def _write_corrected_curve_manifold_csv(sheet, system, output) -> None:
    position_separation = sheet.position_separation_norms
    state_separation = sheet.state_separation_norms
    mapping_time_days = sheet.dg.correction.seed.orbit_period * (system.time_unit_days or 1.0)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "branch",
                "time_index",
                "curve_index",
                "time_nd",
                "time_days",
                "base_x",
                "base_y",
                "base_z",
                "manifold_x",
                "manifold_y",
                "manifold_z",
                "state_separation_norm",
                "position_separation_norm",
                "eigenvalue_real",
                "eigenvalue_imag",
                "eigenvalue_abs",
                "perturbation_scale",
                "mean_state_growth",
                "expected_growth",
                "mapping_time_days",
                "base_family",
                "base_orbit_amplitude_nd",
                "mode_amplitude_nd",
            ],
        )
        writer.writeheader()
        for time_idx, time_value in enumerate(sheet.times):
            for curve_idx in range(sheet.surface.shape[1]):
                writer.writerow(
                    {
                        "branch": sheet.branch,
                        "time_index": time_idx,
                        "curve_index": curve_idx,
                        "time_nd": f"{time_value:.16g}",
                        "time_days": f"{time_value * (system.time_unit_days or 1.0):.16g}",
                        "base_x": f"{sheet.base_surface[time_idx, curve_idx, 0]:.16g}",
                        "base_y": f"{sheet.base_surface[time_idx, curve_idx, 1]:.16g}",
                        "base_z": f"{sheet.base_surface[time_idx, curve_idx, 2]:.16g}",
                        "manifold_x": f"{sheet.surface[time_idx, curve_idx, 0]:.16g}",
                        "manifold_y": f"{sheet.surface[time_idx, curve_idx, 1]:.16g}",
                        "manifold_z": f"{sheet.surface[time_idx, curve_idx, 2]:.16g}",
                        "state_separation_norm": f"{state_separation[time_idx, curve_idx]:.16g}",
                        "position_separation_norm": f"{position_separation[time_idx, curve_idx]:.16g}",
                        "eigenvalue_real": f"{sheet.eigenvalue.real:.16g}",
                        "eigenvalue_imag": f"{sheet.eigenvalue.imag:.16g}",
                        "eigenvalue_abs": f"{abs(sheet.eigenvalue):.16g}",
                        "perturbation_scale": f"{sheet.perturbation_scale:.16g}",
                        "mean_state_growth": f"{sheet.mean_state_growth:.16g}",
                        "expected_growth": f"{sheet.expected_growth:.16g}",
                        "mapping_time_days": f"{mapping_time_days:.16g}",
                        "base_family": sheet.dg.correction.seed.base_family,
                        "base_orbit_amplitude_nd": (
                            f"{sheet.dg.correction.seed.base_orbit_amplitude:.16g}"
                        ),
                        "mode_amplitude_nd": f"{sheet.dg.correction.seed.mode_amplitude:.16g}",
                    }
                )


def _assert_corrected_curve_manifold(sheet) -> None:
    position_separation = sheet.position_separation_norms
    state_separation = sheet.state_separation_norms

    assert sheet.surface.shape == (24, 9, 3)
    assert sheet.base_surface.shape == (24, 9, 3)
    assert np.allclose(state_separation[0], sheet.perturbation_scale, rtol=1e-8, atol=1e-12)
    assert sheet.mean_state_growth > 1.0e3, sheet.mean_state_growth
    assert 0.5 * sheet.expected_growth < sheet.mean_state_growth < 1.5 * sheet.expected_growth
    assert position_separation[-1].max() > 5.0e-5, position_separation[-1].max()


def assert_chapter4_corrected_curve_unstable_manifold() -> None:
    system = SYSTEMS["earth_moon"]
    sheet = corrected_curve_unstable_manifold(system.mu, samples=9, time_samples=24)
    _assert_corrected_curve_manifold(sheet)
    eigen_index = real_hyperbolic_eigen_index(sheet.dg, branch="unstable")
    assert abs(sheet.eigenvalue - sheet.dg.eigenvalues[eigen_index]) < 1.0e-10
    assert abs(sheet.eigenvalue.imag) < 1.0e-8

    output = PROJECT_ROOT / "data" / "computed" / "chapter4_corrected_curve_unstable_manifold.csv"
    _write_corrected_curve_manifold_csv(sheet, system, output)

    print(
        "Chapter 4 corrected-curve unstable manifold: "
        f"{sheet.surface.shape[0]}x{sheet.surface.shape[1]} samples, "
        f"growth={sheet.mean_state_growth:.3e}, expected={sheet.expected_growth:.3e}"
    )
    print(f"Wrote {output}")


def assert_chapter4_corrected_curve_stable_manifold() -> None:
    system = SYSTEMS["earth_moon"]
    sheet = corrected_curve_stable_manifold(system.mu, samples=9, time_samples=24)
    _assert_corrected_curve_manifold(sheet)
    eigen_index = real_hyperbolic_eigen_index(sheet.dg, branch="stable")
    assert abs(sheet.eigenvalue - sheet.dg.eigenvalues[eigen_index]) < 1.0e-12
    assert abs(sheet.eigenvalue.imag) < 1.0e-10

    output = PROJECT_ROOT / "data" / "computed" / "chapter4_corrected_curve_stable_manifold.csv"
    _write_corrected_curve_manifold_csv(sheet, system, output)

    print(
        "Chapter 4 corrected-curve stable manifold: "
        f"{sheet.surface.shape[0]}x{sheet.surface.shape[1]} samples, "
        f"growth={sheet.mean_state_growth:.3e}, expected={sheet.expected_growth:.3e}"
    )
    print(f"Wrote {output}")


def assert_chapter4_corrected_vertical_curve_unstable_manifolds() -> None:
    system = SYSTEMS["earth_moon"]
    sheets = {
        "plus": corrected_vertical_curve_unstable_manifold(
            system.mu,
            samples=9,
            time_samples=24,
            perturbation_sign=1.0,
        ),
        "minus": corrected_vertical_curve_unstable_manifold(
            system.mu,
            samples=9,
            time_samples=24,
            perturbation_sign=-1.0,
        ),
    }
    for sheet in sheets.values():
        _assert_corrected_curve_manifold(sheet)
        assert sheet.dg.correction.seed.base_family == "vertical"
        eigen_index = real_hyperbolic_eigen_index(sheet.dg, branch="unstable")
        assert abs(sheet.eigenvalue - sheet.dg.eigenvalues[eigen_index]) < 1.0e-10
        assert abs(sheet.eigenvalue.imag) < 1.0e-8

    plus_x = float(np.mean(sheets["plus"].surface[-1, :, 0] - sheets["plus"].base_surface[-1, :, 0]))
    minus_x = float(np.mean(sheets["minus"].surface[-1, :, 0] - sheets["minus"].base_surface[-1, :, 0]))
    assert plus_x > 0.0, plus_x
    assert minus_x < 0.0, minus_x

    for name, sheet in sheets.items():
        output = (
            PROJECT_ROOT
            / "data"
            / "computed"
            / f"chapter4_corrected_vertical_curve_unstable_manifold_{name}.csv"
        )
        _write_corrected_curve_manifold_csv(sheet, system, output)
        print(f"Wrote {output}")
    print(
        "Chapter 4 corrected quasi-vertical unstable manifolds: "
        f"plus growth={sheets['plus'].mean_state_growth:.3e}, "
        f"minus growth={sheets['minus'].mean_state_growth:.3e}, "
        f"expected={sheets['plus'].expected_growth:.3e}"
    )


def assert_chapter4_corrected_vertical_global_unstable_manifold() -> None:
    system = SYSTEMS["earth_moon"]
    sheet = corrected_vertical_global_unstable_manifold(system.mu)
    points = sheet.surface.reshape(-1, 3)
    velocities = sheet.manifold_states[:, :, 3:]
    moon_position = np.array([1.0 - system.mu, 0.0, 0.0])
    moon_distances = np.linalg.norm(sheet.surface - moon_position, axis=2)
    jacobi_values = jacobi_constant(sheet.manifold_states.reshape(-1, 6), system.mu).reshape(
        sheet.manifold_states.shape[:2]
    )
    jacobi_spans = np.ptp(jacobi_values, axis=0)
    duration_periods = abs(sheet.times[-1]) / sheet.dg.correction.seed.orbit_period

    assert sheet.surface.shape == (240, 9, 3)
    assert sheet.dg.correction.seed.base_family == "vertical"
    assert abs(duration_periods - 2.5) < 1.0e-12
    assert np.isfinite(sheet.manifold_states).all()
    assert abs(sheet.eigenvalue.imag) < 1.0e-8
    assert points[:, 0].min() < -0.5, points[:, 0].min()
    assert 0.82 < points[:, 0].max() < 0.90, points[:, 0].max()
    assert points[:, 1].min() < -0.25, points[:, 1].min()
    assert points[:, 1].max() > 0.33, points[:, 1].max()
    assert np.max(np.abs(points[:, 2])) < 1.0e-3
    assert moon_distances.min() > 0.015, moon_distances.min()
    assert np.linalg.norm(velocities, axis=2).max() < 2.0
    assert jacobi_spans.max() < 1.0e-10, jacobi_spans.max()

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter4_corrected_vertical_global_unstable_manifold.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "curve_index",
        "time_index",
        "time_nd",
        "time_days",
        "x",
        "y",
        "z",
        "xdot",
        "ydot",
        "zdot",
        "jacobi",
        "curve_jacobi_span",
        "moon_distance_nd",
        "perturbation_sign",
        "perturbation_scale",
        "duration_periods",
        "eigenvalue_abs",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for time_idx, time_value in enumerate(sheet.times):
            for curve_idx, state in enumerate(sheet.manifold_states[time_idx]):
                writer.writerow(
                    {
                        "curve_index": curve_idx,
                        "time_index": time_idx,
                        "time_nd": f"{time_value:.16g}",
                        "time_days": f"{time_value * (system.time_unit_days or 1.0):.16g}",
                        "x": f"{state[0]:.16g}",
                        "y": f"{state[1]:.16g}",
                        "z": f"{state[2]:.16g}",
                        "xdot": f"{state[3]:.16g}",
                        "ydot": f"{state[4]:.16g}",
                        "zdot": f"{state[5]:.16g}",
                        "jacobi": f"{jacobi_values[time_idx, curve_idx]:.16g}",
                        "curve_jacobi_span": f"{jacobi_spans[curve_idx]:.16g}",
                        "moon_distance_nd": f"{moon_distances[time_idx, curve_idx]:.16g}",
                        "perturbation_sign": f"{sheet.perturbation_sign:.16g}",
                        "perturbation_scale": f"{sheet.perturbation_scale:.16g}",
                        "duration_periods": f"{duration_periods:.16g}",
                        "eigenvalue_abs": f"{abs(sheet.eigenvalue):.16g}",
                    }
                )
    print(
        "Chapter 4 corrected quasi-vertical global unstable manifold: "
        f"{sheet.surface.shape[0]}x{sheet.surface.shape[1]} samples, "
        f"x={points[:, 0].min():.3f}..{points[:, 0].max():.3f}, "
        f"min Moon distance={moon_distances.min():.3e}, "
        f"max Jacobi span={jacobi_spans.max():.3e}"
    )
    print(f"Wrote {output}")


def assert_chapter4_periodic_halo_manifold() -> None:
    system = SYSTEMS["earth_moon"]
    sample = periodic_halo_manifold_sample(
        system.mu,
        point="L1",
        include_stable=False,
        samples_on_orbit=8,
        duration=4.0,
        trajectory_samples=160,
    )
    selected = [
        curve
        for curve in sample.unstable
        if curve[:, 0].min() < 0.55 and curve[-1, 1] > 0.02
    ]
    selected_points = np.concatenate([curve[:, :3] for curve in selected], axis=0)

    assert sample.orbit.point == "L1"
    assert abs(sample.orbit.fixed_z0 - 0.040) < 1e-12
    assert sample.monodromy.periodicity_error < 1e-8, sample.monodromy.periodicity_error
    assert sample.monodromy.stability_index > 500.0, sample.monodromy.stability_index
    assert len(selected) >= 6
    assert 0.20 < selected_points[:, 0].min() < 0.35
    assert selected_points[:, 0].max() > 0.85
    assert selected_points[:, 1].max() > 0.30
    assert selected_points[:, 2].min() < -0.045
    assert selected_points[:, 2].max() > 0.040

    output = PROJECT_ROOT / "data" / "computed" / "earth_moon_l1_periodic_halo_manifold.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "kind",
        "curve_index",
        "point",
        "z0",
        "x0",
        "ydot0",
        "period",
        "jacobi",
        "stability_index",
        "periodicity_error",
        "x_min",
        "x_max",
        "y_min",
        "y_max",
        "z_min",
        "z_max",
    ]
    orbit_points = sample.orbit_curve[:, :3]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        base_row = {
            "kind": "corrected_periodic_halo",
            "curve_index": "",
            "point": sample.orbit.point,
            "z0": sample.orbit.fixed_z0,
            "x0": sample.orbit.initial_state[0],
            "ydot0": sample.orbit.initial_state[4],
            "period": sample.orbit.period,
            "jacobi": sample.orbit.jacobi,
            "stability_index": sample.monodromy.stability_index,
            "periodicity_error": sample.monodromy.periodicity_error,
            "x_min": float(orbit_points[:, 0].min()),
            "x_max": float(orbit_points[:, 0].max()),
            "y_min": float(orbit_points[:, 1].min()),
            "y_max": float(orbit_points[:, 1].max()),
            "z_min": float(orbit_points[:, 2].min()),
            "z_max": float(orbit_points[:, 2].max()),
        }
        writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in base_row.items()})
        for curve_index, curve in enumerate(selected):
            points = curve[:, :3]
            row = {
                "kind": "earthward_unstable",
                "curve_index": curve_index,
                "point": sample.orbit.point,
                "z0": sample.orbit.fixed_z0,
                "x0": sample.orbit.initial_state[0],
                "ydot0": sample.orbit.initial_state[4],
                "period": sample.orbit.period,
                "jacobi": sample.orbit.jacobi,
                "stability_index": sample.monodromy.stability_index,
                "periodicity_error": sample.monodromy.periodicity_error,
                "x_min": float(points[:, 0].min()),
                "x_max": float(points[:, 0].max()),
                "y_min": float(points[:, 1].min()),
                "y_max": float(points[:, 1].max()),
                "z_min": float(points[:, 2].min()),
                "z_max": float(points[:, 2].max()),
            }
            writer.writerow({key: f"{value:.16g}" if isinstance(value, float) else value for key, value in row.items()})

    print(
        "Earth-Moon L1 periodic halo manifold branches: "
        f"{len(selected)}, nu={sample.monodromy.stability_index:.3e}"
    )
    print(f"Wrote {output}")


def assert_chapter5_corrected_dro_scene() -> None:
    system = SYSTEMS["earth_moon"]
    scene = quasi_dro_cr3bp_return_scene(system)
    periodic_span = np.ptp(scene.periodic_states[:, :3], axis=0)
    quasi_span = np.ptp(scene.quasi_states[:, :3], axis=0)
    torus_span = np.ptp(scene.torus_surface.reshape(-1, 3), axis=0)

    assert scene.torus_surface.shape == (36, 15, 3)
    assert scene.torus_states.shape == (36, 15, 6)
    assert scene.periodic_states.shape == (420, 6)
    assert scene.quasi_states.shape == (1100, 6)
    assert 14.74 < scene.period_days < 14.76, scene.period_days
    assert 147.4 < scene.duration_days < 147.6, scene.duration_days
    assert abs(scene.periselene_radius_km - 73800.0) < 1.0, scene.periselene_radius_km
    assert scene.periodicity_error < 1.0e-10, scene.periodicity_error
    assert scene.periodic_jacobi_span < 1.0e-10, scene.periodic_jacobi_span
    assert scene.quasi_jacobi_span < 1.0e-10, scene.quasi_jacobi_span
    assert scene.torus_closure_error < 1.0e-7, scene.torus_closure_error
    assert abs(scene.target_vertical_amplitude - 1.0e-2) < 1.0e-14
    assert 1.432 < scene.rotation_angle_rad < 1.434, scene.rotation_angle_rad
    assert 0.39 < periodic_span[0] < 0.40, periodic_span
    assert 0.53 < periodic_span[1] < 0.54, periodic_span
    assert quasi_span[2] > 2.0e-4, quasi_span
    assert torus_span[2] > 2.0e-4, torus_span
    assert np.max(np.abs(scene.quasi_states[:, 2])) * (system.length_unit_km or 1.0) > 1737.4
    assert np.isfinite(scene.quasi_states).all()

    output = PROJECT_ROOT / "data" / "computed" / "chapter5_corrected_dro_quasi_dro_return.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "kind",
        "time_index",
        "curve_index",
        "time_nd",
        "time_days",
        "phase_rad",
        "x",
        "y",
        "z",
        "xdot",
        "ydot",
        "zdot",
        "jacobi",
        "period_days",
        "duration_days",
        "periselene_radius_km",
        "periodicity_error",
        "periodic_jacobi_span",
        "quasi_jacobi_span",
        "torus_closure_error",
        "rotation_angle_rad",
        "target_vertical_amplitude_nd",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()

        common = {
            "period_days": f"{scene.period_days:.16g}",
            "duration_days": f"{scene.duration_days:.16g}",
            "periselene_radius_km": f"{scene.periselene_radius_km:.16g}",
            "periodicity_error": f"{scene.periodicity_error:.16g}",
            "periodic_jacobi_span": f"{scene.periodic_jacobi_span:.16g}",
            "quasi_jacobi_span": f"{scene.quasi_jacobi_span:.16g}",
            "torus_closure_error": f"{scene.torus_closure_error:.16g}",
            "rotation_angle_rad": f"{scene.rotation_angle_rad:.16g}",
            "target_vertical_amplitude_nd": f"{scene.target_vertical_amplitude:.16g}",
        }

        def write_state(kind, time_idx, curve_idx, time_value, phase, state):
            row = {
                "kind": kind,
                "time_index": time_idx,
                "curve_index": curve_idx,
                "time_nd": f"{time_value:.16g}",
                "time_days": f"{time_value * (system.time_unit_days or 1.0):.16g}",
                "phase_rad": "" if phase is None else f"{phase:.16g}",
                "x": f"{state[0]:.16g}",
                "y": f"{state[1]:.16g}",
                "z": f"{state[2]:.16g}",
                "xdot": f"{state[3]:.16g}",
                "ydot": f"{state[4]:.16g}",
                "zdot": f"{state[5]:.16g}",
                "jacobi": f"{jacobi_constant(state, system.mu):.16g}",
            }
            row.update(common)
            writer.writerow(row)

        for time_idx, (time_value, state) in enumerate(zip(scene.periodic_times, scene.periodic_states)):
            write_state("periodic_dro", time_idx, 0, time_value, None, state)
        for time_idx, (time_value, state) in enumerate(zip(scene.quasi_times, scene.quasi_states)):
            write_state("quasi_dro_10_return", time_idx, 0, time_value, None, state)
        for time_idx, time_value in enumerate(scene.torus_times):
            for curve_idx, state in enumerate(scene.torus_states[time_idx]):
                write_state(
                    "corrected_local_torus",
                    time_idx,
                    curve_idx,
                    time_value,
                    scene.torus_phases[curve_idx],
                    state,
                )

    print(
        "Chapter 5 corrected resonant DRO/quasi-DRO: "
        f"period={scene.period_days:.6f} days, duration={scene.duration_days:.3f} days, "
        f"rp={scene.periselene_radius_km:.1f} km, "
        f"periodicity={scene.periodicity_error:.3e}, "
        f"quasi Jacobi span={scene.quasi_jacobi_span:.3e}"
    )
    print(f"Wrote {output}")


def assert_chapter5_de421_quasi_dro_scenes() -> None:
    system = SYSTEMS["earth_moon"]
    family_path = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv"
    kernel_path = PROJECT_ROOT / "data" / "raw" / "ephemeris" / "de421.bsp"
    member = load_corrected_dro_family_csv(family_path)[-1]
    phases_deg = (0.0, 24.0, 80.0, 120.0)
    epochs = (
        "2020-06-01T00:00:00Z",
        "2020-06-04T00:00:00Z",
        "2020-06-10T00:00:00Z",
        "2020-06-15T00:00:00Z",
    )
    phase_scenes = de421_quasi_dro_phase_scenes(
        member,
        system,
        kernel_path,
        epoch_utc="2020-06-15T00:00:00Z",
        phases_deg=phases_deg,
        samples=360,
    )
    epoch_scenes = de421_quasi_dro_epoch_scenes(
        member,
        system,
        kernel_path,
        epochs_utc=epochs,
        phase_deg=0.0,
        samples=360,
    )
    scenes = phase_scenes + epoch_scenes

    assert len(phase_scenes) == len(epoch_scenes) == 4
    assert np.allclose([scene.phase_deg for scene in phase_scenes], phases_deg, atol=1.0e-10)
    assert [scene.epoch_utc[:10] for scene in epoch_scenes] == [epoch[:10] for epoch in epochs]
    assert all(scene.points_km.shape == (360, 3) for scene in scenes)
    assert all(scene.shadow_surface_km.shape == (36, 28, 3) for scene in scenes)
    assert all(np.isfinite(scene.points_km).all() for scene in scenes)
    assert max(scene.frame_orthogonality_error for scene in scenes) < 1.0e-12
    assert max(scene.cr3bp_jacobi_span for scene in scenes) < 1.0e-10
    assert all(147.4 < scene.times_days[-1] < 147.6 for scene in scenes)
    assert all(np.ptp(scene.points_km[:, 0]) > 1.5e5 for scene in scenes)
    assert all(np.ptp(scene.points_km[:, 1]) > 1.5e5 for scene in scenes)
    assert all(np.ptp(scene.points_km[:, 2]) > 2.0e4 for scene in scenes)
    assert min(scene.earth_moon_distances_km.min() for scene in scenes) > 3.4e5
    assert max(scene.earth_moon_distances_km.max() for scene in scenes) < 4.2e5
    assert min(scene.sun_moon_distances_km.min() for scene in scenes) > 1.4e8
    phase_markers = np.asarray([scene.marker_km for scene in phase_scenes])
    epoch_markers = np.asarray([scene.marker_km for scene in epoch_scenes])
    phase_track_rms = np.asarray(
        [np.sqrt(np.mean((scene.points_km - phase_scenes[0].points_km) ** 2)) for scene in phase_scenes]
    )
    assert np.max(np.linalg.norm(phase_markers - phase_markers[0], axis=1)) > 3.0e3
    assert phase_track_rms.max() > 1.0e3
    assert np.max(np.linalg.norm(epoch_markers - epoch_markers[0], axis=1)) > 1.0e4
    assert min(scene.minimum_shadow_clearance_km for scene in phase_scenes) > 0.0

    output = PROJECT_ROOT / "data" / "computed" / "chapter5_de421_quasi_dro_scenes.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "mode",
        "panel",
        "sample",
        "epoch_utc",
        "phase_deg",
        "time_days",
        "x_sun_moon_km",
        "y_sun_moon_km",
        "z_sun_moon_km",
        "earth_moon_distance_km",
        "sun_moon_distance_km",
        "lunar_eclipse",
        "earth_occultation",
        "cr3bp_jacobi_span",
        "frame_orthogonality_error",
        "eclipse_duration_hours",
        "earth_occultation_hours",
        "minimum_shadow_clearance_km",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()

        def write_scenes(mode, mode_scenes):
            for panel, scene in enumerate(mode_scenes):
                common = {
                    "mode": mode,
                    "panel": panel,
                    "epoch_utc": scene.epoch_utc,
                    "phase_deg": f"{scene.phase_deg:.16g}",
                    "cr3bp_jacobi_span": f"{scene.cr3bp_jacobi_span:.16g}",
                    "frame_orthogonality_error": f"{scene.frame_orthogonality_error:.16g}",
                    "eclipse_duration_hours": f"{scene.eclipse_duration_hours:.16g}",
                    "earth_occultation_hours": f"{scene.earth_occultation_hours:.16g}",
                    "minimum_shadow_clearance_km": f"{scene.minimum_shadow_clearance_km:.16g}",
                }
                for sample, point in enumerate(scene.points_km):
                    writer.writerow(
                        {
                            **common,
                            "sample": sample,
                            "time_days": f"{scene.times_days[sample]:.16g}",
                            "x_sun_moon_km": f"{point[0]:.16g}",
                            "y_sun_moon_km": f"{point[1]:.16g}",
                            "z_sun_moon_km": f"{point[2]:.16g}",
                            "earth_moon_distance_km": f"{scene.earth_moon_distances_km[sample]:.16g}",
                            "sun_moon_distance_km": f"{scene.sun_moon_distances_km[sample]:.16g}",
                            "lunar_eclipse": int(scene.eclipse_mask[sample]),
                            "earth_occultation": int(scene.earth_occultation_mask[sample]),
                        }
                    )

        write_scenes("phase", phase_scenes)
        write_scenes("epoch", epoch_scenes)

    print(
        "Chapter 5 DE421-oriented corrected quasi-DRO scenes: "
        f"8 panels, max frame error={max(scene.frame_orthogonality_error for scene in scenes):.3e}, "
        f"max Jacobi span={max(scene.cr3bp_jacobi_span for scene in scenes):.3e}, "
        f"eclipse={min(scene.eclipse_duration_hours for scene in scenes):.2f}.."
        f"{max(scene.eclipse_duration_hours for scene in scenes):.2f} h"
    )
    print(f"Wrote {output}")


def assert_chapter5_application_proxies() -> None:
    l1_scene = sun_earth_l1_long_propagation(5, n_major=48, n_minor=10)
    cr3bp_l1_scene = sun_earth_l1_cr3bp_long_propagation(
        5,
        n_major=48,
        n_minor=10,
        samples=220,
    )
    dro_scene = quasi_dro_return_scene()
    dro_curve, dro_marker = dro_ephemeris_trajectory(phase=0.4, epoch_shift=1.0, samples=220)
    transfer_scene = halo_to_lyapunov_scene()
    nrho_scene = converged_transfer_pair(1)
    arrival_hours, delta_v = rendezvous_delta_v_curve(samples=80)
    theta0, theta1, radius = periapsis_radius_map(samples=80)
    leo_scene = leo_to_l1_transfer(samples=220)

    assert l1_scene.surface[:, :, 0].min() > 0.987
    assert np.ptp(l1_scene.surface[:, :, 2]) > 0.010
    assert len(l1_scene.curves) == 5
    assert len(cr3bp_l1_scene.curves) == 5
    assert cr3bp_l1_scene.duration_days > 70.0
    assert np.max(cr3bp_l1_scene.jacobi_spans) < 1.0e-10
    cr3bp_l1_points = np.concatenate(cr3bp_l1_scene.curves, axis=0)
    assert 0.986 < cr3bp_l1_points[:, 0].min() < cr3bp_l1_points[:, 0].max() < 1.001
    assert np.ptp(cr3bp_l1_points[:, 1]) > 0.002
    assert np.ptp(cr3bp_l1_points[:, 2]) > 0.005
    assert dro_scene.surface[:, :, 0].max() > 1.10
    assert np.ptp(dro_scene.curves[0][:, 1]) > 0.45
    assert np.ptp(dro_curve[:, 0]) > 1.3e5
    assert abs(dro_marker[2]) < 7.0e4
    assert len(transfer_scene.transfer_arcs) >= 6
    assert len(nrho_scene.transfer_arcs) == 3
    assert delta_v[0] > 150.0
    assert delta_v.min() < 5.0
    assert radius.min() < 1.0e4
    assert radius.max() > 2.0e5
    assert theta0.size == theta1.size == 80
    assert np.ptp(leo_scene.curves[0][:, 0]) > 1.0e6
    assert np.ptp(leo_scene.surface[:, :, 2]) > 1.0e6

    output = PROJECT_ROOT / "data" / "computed" / "chapter5_application_proxy.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["kind", "x", "y"])
        writer.writeheader()
        for x, y in zip(arrival_hours, delta_v):
            writer.writerow({"kind": "rendezvous_delta_v", "x": f"{x:.16g}", "y": f"{y:.16g}"})
        sample_idx = np.linspace(0, dro_curve.shape[0] - 1, 24, dtype=int)
        for idx in sample_idx:
            writer.writerow(
                {
                    "kind": "dro_ephemeris_xy_km",
                    "x": f"{dro_curve[idx, 0]:.16g}",
                    "y": f"{dro_curve[idx, 1]:.16g}",
                }
            )
        min_idx = np.unravel_index(np.argmin(radius), radius.shape)
        writer.writerow({"kind": "min_periapsis_theta0_deg", "x": f"{theta0[min_idx[1]]:.16g}", "y": ""})
        writer.writerow({"kind": "min_periapsis_theta1_deg", "x": f"{theta1[min_idx[0]]:.16g}", "y": ""})
        writer.writerow({"kind": "min_periapsis_radius_km", "x": f"{radius[min_idx]:.16g}", "y": ""})

    l1_output = PROJECT_ROOT / "data" / "computed" / "chapter5_sun_earth_l1_cr3bp_long_propagation.csv"
    l1_output.parent.mkdir(parents=True, exist_ok=True)
    with l1_output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "curve",
                "sample",
                "time_nd",
                "time_days",
                "x",
                "y",
                "z",
                "jacobi",
                "curve_jacobi_span",
            ],
        )
        writer.writeheader()
        for curve_idx, states in enumerate(cr3bp_l1_scene.states):
            sample_idx = np.linspace(0, states.shape[0] - 1, 24, dtype=int)
            jacobi_values = jacobi_constant(states, SYSTEMS["sun_earth"].mu)
            for sample in sample_idx:
                writer.writerow(
                    {
                        "curve": curve_idx,
                        "sample": int(sample),
                        "time_nd": f"{cr3bp_l1_scene.times[sample]:.16g}",
                        "time_days": f"{cr3bp_l1_scene.times[sample] * SYSTEMS['sun_earth'].time_unit_days:.16g}",
                        "x": f"{states[sample, 0]:.16g}",
                        "y": f"{states[sample, 1]:.16g}",
                        "z": f"{states[sample, 2]:.16g}",
                        "jacobi": f"{jacobi_values[sample]:.16g}",
                        "curve_jacobi_span": f"{cr3bp_l1_scene.jacobi_spans[curve_idx]:.16g}",
                    }
                )

    print("Chapter 5 application proxy checks: ok")
    print(f"Wrote {output}")
    print(
        "Chapter 5 Sun-Earth L1 CR3BP long propagation: "
        f"{len(cr3bp_l1_scene.curves)} curves, "
        f"duration={cr3bp_l1_scene.duration_days:.1f} days, "
        f"max Jacobi span={np.max(cr3bp_l1_scene.jacobi_spans):.3e}"
    )
    print(f"Wrote {l1_output}")


def assert_chapter5_sun_earth_stable_manifold_baseline() -> None:
    system = SYSTEMS["sun_earth"]
    baseline = sun_earth_l1_stable_manifold_baseline(
        target_periapsis_radius_km=6563.0,
        scan_samples=36,
        trajectory_samples=360,
    )
    earth = np.array([1.0 - system.mu, 0.0, 0.0])
    earth_distance = np.linalg.norm(
        baseline.selected_states[:, :3] - earth,
        axis=1,
    ) * system.length_unit_km
    radial_inner_product = float(
        np.dot(
            baseline.selected_states[0, :3] - earth,
            baseline.selected_states[0, 3:],
        )
    )

    assert abs(baseline.selected_periapsis_radius_km - 6563.0) < 0.1
    assert abs(earth_distance[0] - 6563.0) < 0.1
    assert abs(radial_inner_product) < 1.0e-8
    assert baseline.transfer_time_days > 350.0
    assert baseline.jacobi_span < 1.0e-9
    assert baseline.periodicity_error < 1.0e-8
    assert baseline.stable_eigenvalue_magnitude < 1.0
    assert baseline.scan_periapsis_radius_km.min() < 100.0
    assert baseline.scan_periapsis_radius_km.max() > 4.0e5
    assert np.all(np.diff(baseline.selected_times_days) > 0.0)

    output = PROJECT_ROOT / "data" / "computed" / "chapter5_sun_earth_stable_manifold_baseline.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "kind",
        "sample",
        "phase_deg",
        "periapsis_radius_km",
        "time_days",
        "x_nd",
        "y_nd",
        "z_nd",
        "xdot_nd",
        "ydot_nd",
        "zdot_nd",
        "earth_distance_km",
        "jacobi",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for sample, (phase, radius) in enumerate(
            zip(baseline.scan_phase_deg, baseline.scan_periapsis_radius_km)
        ):
            writer.writerow(
                {
                    "kind": "phase_scan",
                    "sample": sample,
                    "phase_deg": f"{phase:.16g}",
                    "periapsis_radius_km": f"{radius:.16g}",
                }
            )
        jacobi_values = jacobi_constant(baseline.selected_states, system.mu)
        for sample, (time_days, state, distance, jacobi) in enumerate(
            zip(
                baseline.selected_times_days,
                baseline.selected_states,
                earth_distance,
                jacobi_values,
            )
        ):
            writer.writerow(
                {
                    "kind": "targeted_trajectory",
                    "sample": sample,
                    "phase_deg": f"{baseline.selected_phase_deg:.16g}",
                    "periapsis_radius_km": f"{baseline.selected_periapsis_radius_km:.16g}",
                    "time_days": f"{time_days:.16g}",
                    "x_nd": f"{state[0]:.16g}",
                    "y_nd": f"{state[1]:.16g}",
                    "z_nd": f"{state[2]:.16g}",
                    "xdot_nd": f"{state[3]:.16g}",
                    "ydot_nd": f"{state[4]:.16g}",
                    "zdot_nd": f"{state[5]:.16g}",
                    "earth_distance_km": f"{distance:.16g}",
                    "jacobi": f"{jacobi:.16g}",
                }
            )

    print(
        "Chapter 5 Sun-Earth stable-manifold baseline: "
        f"phase={baseline.selected_phase_deg:.6f} deg, "
        f"rp={baseline.selected_periapsis_radius_km:.6f} km, "
        f"TOF={baseline.transfer_time_days:.3f} d, "
        f"Jacobi span={baseline.jacobi_span:.3e}"
    )
    print(f"Wrote {output}")


def assert_chapter5_earth_moon_nrho_transfer_baseline() -> None:
    baseline = earth_moon_nrho_transfer_baseline(
        orbit_samples=360,
        transfer_samples=360,
        rendezvous_samples=49,
    )
    forward = baseline.forward_transfers
    reverse = baseline.reverse_transfers

    assert abs(baseline.departure_perilune_radius_km - 4_800.0) < 0.05
    assert abs(baseline.destination_perilune_radius_km - 12_610.0) < 0.05
    assert abs(baseline.departure_stability_index - 1.5425) < 0.01
    assert abs(baseline.destination_stability_index - 1.1762) < 0.01
    assert baseline.departure_periodicity_error < 1.0e-8
    assert baseline.destination_periodicity_error < 1.0e-8
    assert np.linalg.norm(
        baseline.departure_states[-1] - baseline.departure_states[0]
    ) < 1.0e-8
    assert np.linalg.norm(
        baseline.destination_states[-1] - baseline.destination_states[0]
    ) < 1.0e-8
    assert np.allclose([item.time_of_flight_days for item in forward], [23.0, 12.4])
    assert forward[0].total_delta_v_m_s < 100.0
    assert abs(forward[1].total_delta_v_m_s - 86.6) < 1.0
    for direct, symmetric in zip(forward, reverse):
        assert direct.endpoint_position_error_km < 1.0e-3
        assert direct.minimum_moon_radius_km > 2_000.0
        assert direct.jacobi_span < 1.0e-8
        assert np.isclose(direct.total_delta_v_m_s, symmetric.total_delta_v_m_s)
        assert np.isclose(direct.time_of_flight_days, symmetric.time_of_flight_days)
        assert np.allclose(direct.transfer_states[-1, :3], direct.arrival_state[:3], atol=1.0e-8)
        assert np.allclose(symmetric.transfer_states[-1, :3], symmetric.arrival_state[:3], atol=1.0e-8)
    assert baseline.rendezvous_offsets_hours[0] == -24.0
    assert baseline.rendezvous_offsets_hours[-1] >= 10.0
    assert baseline.rendezvous_offsets_hours.size >= 35
    minimum_index = int(np.argmin(baseline.rendezvous_delta_v_difference_m_s))
    assert 4.0 <= baseline.rendezvous_offsets_hours[minimum_index] <= 8.0
    assert baseline.rendezvous_delta_v_difference_m_s[minimum_index] < 0.0

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter5_earth_moon_nrho_transfer_baseline.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "kind",
        "case",
        "sample",
        "phase",
        "time_days",
        "x_nd",
        "y_nd",
        "z_nd",
        "xdot_nd",
        "ydot_nd",
        "zdot_nd",
        "perilune_radius_km",
        "stability_index",
        "periodicity_error",
        "time_of_flight_days",
        "departure_delta_v_m_s",
        "arrival_delta_v_m_s",
        "total_delta_v_m_s",
        "endpoint_position_error_km",
        "minimum_moon_radius_km",
        "jacobi_span",
        "arrival_offset_hours",
        "delta_v_difference_m_s",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for case, orbit, radius, stability, periodicity in (
            (
                "departure_4800_km",
                baseline.departure_orbit,
                baseline.departure_perilune_radius_km,
                baseline.departure_stability_index,
                baseline.departure_periodicity_error,
            ),
            (
                "destination_12610_km",
                baseline.destination_orbit,
                baseline.destination_perilune_radius_km,
                baseline.destination_stability_index,
                baseline.destination_periodicity_error,
            ),
        ):
            writer.writerow(
                {
                    "kind": "orbit_summary",
                    "case": case,
                    "x_nd": f"{orbit.initial_state[0]:.16g}",
                    "y_nd": f"{orbit.initial_state[1]:.16g}",
                    "z_nd": f"{orbit.initial_state[2]:.16g}",
                    "xdot_nd": f"{orbit.initial_state[3]:.16g}",
                    "ydot_nd": f"{orbit.initial_state[4]:.16g}",
                    "zdot_nd": f"{orbit.initial_state[5]:.16g}",
                    "perilune_radius_km": f"{radius:.16g}",
                    "stability_index": f"{stability:.16g}",
                    "periodicity_error": f"{periodicity:.16g}",
                }
            )
        for direction, transfers in (("forward", forward), ("reverse", reverse)):
            for case_index, transfer in enumerate(transfers, start=1):
                for sample, (time_days, state) in enumerate(
                    zip(transfer.transfer_times_days, transfer.transfer_states)
                ):
                    writer.writerow(
                        {
                            "kind": f"{direction}_transfer",
                            "case": case_index,
                            "sample": sample,
                            "phase": f"{transfer.departure_phase:.16g}",
                            "time_days": f"{time_days:.16g}",
                            "x_nd": f"{state[0]:.16g}",
                            "y_nd": f"{state[1]:.16g}",
                            "z_nd": f"{state[2]:.16g}",
                            "xdot_nd": f"{state[3]:.16g}",
                            "ydot_nd": f"{state[4]:.16g}",
                            "zdot_nd": f"{state[5]:.16g}",
                            "time_of_flight_days": f"{transfer.time_of_flight_days:.16g}",
                            "departure_delta_v_m_s": f"{transfer.departure_delta_v_m_s:.16g}",
                            "arrival_delta_v_m_s": f"{transfer.arrival_delta_v_m_s:.16g}",
                            "total_delta_v_m_s": f"{transfer.total_delta_v_m_s:.16g}",
                            "endpoint_position_error_km": f"{transfer.endpoint_position_error_km:.16g}",
                            "minimum_moon_radius_km": f"{transfer.minimum_moon_radius_km:.16g}",
                            "jacobi_span": f"{transfer.jacobi_span:.16g}",
                        }
                    )
        for sample, (offset, delta_v) in enumerate(
            zip(
                baseline.rendezvous_offsets_hours,
                baseline.rendezvous_delta_v_difference_m_s,
            )
        ):
            writer.writerow(
                {
                    "kind": "rendezvous_scan",
                    "sample": sample,
                    "arrival_offset_hours": f"{offset:.16g}",
                    "delta_v_difference_m_s": f"{delta_v:.16g}",
                }
            )

    print(
        "Chapter 5 Earth-Moon NRHO baseline: "
        f"nu={baseline.departure_stability_index:.6f}/"
        f"{baseline.destination_stability_index:.6f}, "
        f"delta-v={forward[0].total_delta_v_m_s:.3f}/"
        f"{forward[1].total_delta_v_m_s:.3f} m/s"
    )
    print(f"Wrote {output}")


def assert_chapter5_halo_lyapunov_transfer_baseline() -> None:
    system = SYSTEMS["earth_moon"]
    baseline = earth_moon_halo_to_lyapunov_transfer_baseline(
        orbit_samples=180,
        trajectory_samples=320,
    )
    assert abs(baseline.time_of_flight_days - 186.9) < 1.0e-12
    assert baseline.boundary_jacobi_difference < 1.0e-10
    assert baseline.endpoint_position_error_km < 1.0e-4
    assert baseline.maximum_continuity_error < 1.0e-9
    assert baseline.jacobi_span < 1.0e-8
    assert baseline.halo_periodicity_error < 1.0e-8
    assert baseline.lyapunov_periodicity_error < 1.0e-8
    assert baseline.halo_stability_index > 100.0
    assert 250.0 < baseline.total_delta_v_m_s < 350.0
    assert baseline.minimum_moon_radius_km > 2_000.0
    assert np.all(np.diff(baseline.transfer_times_days) > 0.0)
    assert np.isclose(baseline.transfer_times_days[-1], 186.9)

    output = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter5_earth_moon_halo_lyapunov_transfer_baseline.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "kind",
        "sample",
        "phase",
        "time_days",
        "x_nd",
        "y_nd",
        "z_nd",
        "xdot_nd",
        "ydot_nd",
        "zdot_nd",
        "jacobi",
        "departure_phase",
        "arrival_phase",
        "time_of_flight_days",
        "departure_delta_v_m_s",
        "arrival_delta_v_m_s",
        "total_delta_v_m_s",
        "endpoint_position_error_km",
        "maximum_continuity_error",
        "minimum_moon_radius_km",
        "jacobi_span",
        "boundary_jacobi_difference",
        "halo_stability_index",
        "halo_periodicity_error",
        "lyapunov_periodicity_error",
    ]
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "kind": "summary",
                "departure_phase": f"{baseline.departure_phase:.16g}",
                "arrival_phase": f"{baseline.arrival_phase:.16g}",
                "time_of_flight_days": f"{baseline.time_of_flight_days:.16g}",
                "departure_delta_v_m_s": f"{baseline.departure_delta_v_m_s:.16g}",
                "arrival_delta_v_m_s": f"{baseline.arrival_delta_v_m_s:.16g}",
                "total_delta_v_m_s": f"{baseline.total_delta_v_m_s:.16g}",
                "endpoint_position_error_km": f"{baseline.endpoint_position_error_km:.16g}",
                "maximum_continuity_error": f"{baseline.maximum_continuity_error:.16g}",
                "minimum_moon_radius_km": f"{baseline.minimum_moon_radius_km:.16g}",
                "jacobi_span": f"{baseline.jacobi_span:.16g}",
                "boundary_jacobi_difference": f"{baseline.boundary_jacobi_difference:.16g}",
                "halo_stability_index": f"{baseline.halo_stability_index:.16g}",
                "halo_periodicity_error": f"{baseline.halo_periodicity_error:.16g}",
                "lyapunov_periodicity_error": f"{baseline.lyapunov_periodicity_error:.16g}",
            }
        )
        for kind, states in (
            ("halo_orbit", baseline.halo_states),
            ("lyapunov_orbit", baseline.lyapunov_states),
        ):
            jacobi_values = jacobi_constant(states, system.mu)
            for sample, (state, jacobi) in enumerate(zip(states, jacobi_values)):
                writer.writerow(
                    {
                        "kind": kind,
                        "sample": sample,
                        "phase": f"{sample / (states.shape[0] - 1):.16g}",
                        "x_nd": f"{state[0]:.16g}",
                        "y_nd": f"{state[1]:.16g}",
                        "z_nd": f"{state[2]:.16g}",
                        "xdot_nd": f"{state[3]:.16g}",
                        "ydot_nd": f"{state[4]:.16g}",
                        "zdot_nd": f"{state[5]:.16g}",
                        "jacobi": f"{jacobi:.16g}",
                    }
                )
        transfer_jacobi = jacobi_constant(baseline.transfer_states, system.mu)
        for sample, (time_days, state, jacobi) in enumerate(
            zip(
                baseline.transfer_times_days,
                baseline.transfer_states,
                transfer_jacobi,
            )
        ):
            writer.writerow(
                {
                    "kind": "transfer",
                    "sample": sample,
                    "time_days": f"{time_days:.16g}",
                    "x_nd": f"{state[0]:.16g}",
                    "y_nd": f"{state[1]:.16g}",
                    "z_nd": f"{state[2]:.16g}",
                    "xdot_nd": f"{state[3]:.16g}",
                    "ydot_nd": f"{state[4]:.16g}",
                    "zdot_nd": f"{state[5]:.16g}",
                    "jacobi": f"{jacobi:.16g}",
                }
            )
    print(
        "Chapter 5 halo-to-Lyapunov baseline: "
        f"TOF={baseline.time_of_flight_days:.1f} d, "
        f"delta-v={baseline.departure_delta_v_m_s:.3f}+"
        f"{baseline.arrival_delta_v_m_s:.3f}="
        f"{baseline.total_delta_v_m_s:.3f} m/s, "
        f"endpoint={baseline.endpoint_position_error_km:.3e} km"
    )
    print(f"Wrote {output}")


def assert_l1_center_modes() -> None:
    modes = center_modes(SYSTEMS["earth_moon"].mu, point="L1")
    assert 2.2 < modes.planar_frequency < 2.5, modes.planar_frequency
    assert 2.1 < modes.vertical_frequency < 2.4, modes.vertical_frequency
    print(
        "L1 center-mode frequencies: "
        f"planar={modes.planar_frequency:.6f}, vertical={modes.vertical_frequency:.6f}"
    )


def main() -> None:
    assert_earth_moon_points()
    assert_jacobi_conservation()
    assert_l1_center_modes()
    assert_planar_lyapunov_correction()
    assert_l1_manifold_foundation()
    assert_jupiter_europa_lyapunov_family()
    assert_jupiter_europa_halo_like_family()
    assert_jupiter_europa_vertical_seed_family()
    assert_earth_moon_stability_curve()
    assert_earth_moon_halo_stability_curve()
    assert_linear_quasi_halo_family()
    assert_linear_quasi_vertical_family()
    write_frequency_ratio_curves()
    assert_constant_energy_periodic_boundaries()
    assert_corrected_l1_constant_energy_families()
    assert_corrected_l1_constant_energy_halo_pseudo_arclength_family()
    assert_corrected_l1_constant_energy_halo_high_order_family()
    assert_corrected_l1_constant_energy_vertical_staged_family()
    assert_period_q_halo_examples()
    assert_l2_constant_frequency_families()
    assert_corrected_l2_constant_frequency_families()
    assert_chapter3_central_periodic_scene()
    assert_stroboscopic_invariant_curve_seed()
    assert_corrected_stroboscopic_torus()
    assert_corrected_stroboscopic_torus_family()
    assert_corrected_vertical_stroboscopic_torus_family()
    assert_corrected_dro_fixed_mapping_family()
    assert_quasi_dro_family()
    assert_chapter4_proxy_foundation()
    assert_chapter4_corrected_curve_dg()
    assert_chapter4_corrected_vertical_curve_dg()
    assert_chapter4_corrected_curve_stability_family()
    assert_chapter4_corrected_l1_constant_energy_halo_dg_family()
    assert_chapter4_corrected_l1_constant_energy_halo_pseudo_arclength_dg()
    assert_chapter4_corrected_l1_constant_energy_halo_high_order_dg()
    assert_chapter4_corrected_l1_constant_energy_halo_manifolds()
    assert_chapter4_corrected_curve_unstable_manifold()
    assert_chapter4_corrected_curve_stable_manifold()
    assert_chapter4_corrected_vertical_curve_unstable_manifolds()
    assert_chapter4_corrected_vertical_global_unstable_manifold()
    assert_chapter4_periodic_halo_manifold()
    assert_chapter5_corrected_dro_scene()
    assert_chapter5_de421_quasi_dro_scenes()
    assert_chapter5_halo_lyapunov_transfer_baseline()
    assert_chapter5_earth_moon_nrho_transfer_baseline()
    assert_chapter5_sun_earth_stable_manifold_baseline()
    assert_chapter5_application_proxies()
    write_libration_points()
    print("CR3BP foundation validation: ok")


if __name__ == "__main__":
    main()
