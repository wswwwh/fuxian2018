"""Rebuild or audit the fixed-amplitude, free-energy quasi-halo frontier."""

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
    resample_corrected_torus_surface,
    stroboscopic_curve_free_energy_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)


SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz"
CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_energy_frontier_checkpoint.npz"
OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_energy_frontier_audit.csv"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_quasi_halo_energy_frontier_audit.md"
ENERGY_STEP = 5.0e-6
CONTINUATION_STEPS = 21


def correct(seed, states, amplitude, rotation, mapping_time, target_jacobi, *, max_iterations=120):
    correction = stroboscopic_curve_free_energy_correction(
        seed,
        target_jacobi=target_jacobi,
        target_amplitude=amplitude,
        amplitude_component=2,
        initial_states=states,
        initial_mapping_time=mapping_time,
        initial_rotation_angle_rad=rotation,
        phase_reference_states=states,
        max_iterations=max_iterations,
        tolerance=1.0e-10,
        constraint_tolerance=1.0e-10,
        max_step=0.005,
        max_state_step=5.0e-5,
        max_mapping_time_step=0.005,
        max_rotation_step=0.005,
    )
    metric = max(
        float(np.max(correction.final_residual_norms)),
        abs(float(correction.energy_residual_history[-1])),
        abs(float(correction.amplitude_residual_history[-1])),
        abs(float(correction.phase_residual_history[-1])),
    )
    if metric > 1.0e-8:
        raise RuntimeError(f"Energy continuation failed: metric={metric:.3e}")
    return correction, metric


def rebuild(seed, source) -> None:
    states = source["current_states"].copy()
    amplitude = float(source["current_amplitude"])
    rotation = float(source["current_rotation"])
    mapping_time = seed.orbit_period
    energy = float(np.mean(jacobi_constant(states, seed.mu)))
    previous_energy = energy
    previous_states = states.copy()
    for index in range(CONTINUATION_STEPS):
        target = energy - ENERGY_STEP
        correction, metric = correct(
            seed,
            states,
            amplitude,
            rotation,
            mapping_time,
            target,
        )
        previous_energy = energy
        previous_states = states.copy()
        states = correction.corrected_states.copy()
        energy = target
        rotation = correction.rotation_angle_rad
        mapping_time = correction.mapping_time
        print(f"step={index + 1} jacobi={energy:.12f} metric={metric:.3e}", flush=True)
    np.savez_compressed(
        CHECKPOINT,
        states=states,
        amplitude=amplitude,
        rotation=rotation,
        mapping_time=mapping_time,
        jacobi=energy,
        previous_states=previous_states,
        previous_jacobi=previous_energy,
        x_amplitude=seed.base_orbit_amplitude,
        samples=seed.phases.size,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="recompute all 21 energy steps")
    args = parser.parse_args()
    system = SYSTEMS["sun_earth"]
    source = np.load(SOURCE)
    seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=float(source["x_amplitude"]),
        vertical_amplitude=1.0e-5,
        samples=int(source["samples"]),
        curve_samples=168,
    )
    if args.rebuild:
        rebuild(seed, source)
    data = np.load(CHECKPOINT)
    correction, metric = correct(
        seed,
        data["states"],
        float(data["amplitude"]),
        float(data["rotation"]),
        float(data["mapping_time"]),
        float(data["jacobi"]),
        max_iterations=4,
    )
    torus = sweep_corrected_curve_correction(correction, time_samples=96, max_step=0.0025)
    surface, _ = resample_corrected_torus_surface(torus, phase_samples=192)
    row = {
        "continuation_steps": CONTINUATION_STEPS,
        "target_jacobi": correction.target_jacobi,
        "vertical_rms_amplitude_nd": correction.target_amplitude,
        "rotation_angle_rad": correction.rotation_angle_rad,
        "mapping_time_nd": correction.mapping_time,
        "combined_metric": metric,
        "curve_residual_norm": float(np.max(correction.final_residual_norms)),
        "max_abs_y_km": float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km),
        "max_abs_z_km": float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km),
        "jacobi_span": float(np.ptp(torus.jacobi_values)),
        "closure_residual_norm": float(np.max(np.linalg.norm(torus.closure_residuals, axis=1))),
        "y_target_error_km": float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km - 660000.0),
        "z_target_error_km": float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km - 940000.0),
    }
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    REPORT.write_text(
        f"""# Chapter 5 Sun-Earth L1 quasi-halo energy-frontier audit

- Energy continuation steps: `{CONTINUATION_STEPS}`
- Target mean Jacobi constant: `{row['target_jacobi']:.12f}`
- Full-torus max |y|: `{row['max_abs_y_km']:.3f}` km
- Full-torus max |z|: `{row['max_abs_z_km']:.3f}` km
- Paper target errors: `y={row['y_target_error_km']:+.3f} km`, `z={row['z_target_error_km']:+.3f} km`
- Curve/map residual: `{row['curve_residual_norm']:.3e}`
- Maximum closure residual: `{row['closure_residual_norm']:.3e}` normalized units
- Full-torus Jacobi span: `{row['jacobi_span']:.3e}`
- Target pair accepted: `false`

Lowering the mean Jacobi constant at fixed local vertical RMS amplitude moves
the reconstructed torus in the correct out-of-plane direction. The frontier
reaches the paper's z scale within about `{abs(row['z_target_error_km']):.0f}`
km, but its y extent is too large by about `{row['y_target_error_km']:.0f}` km
and the per-curve Jacobi spread exceeds the strict `1e-8` gate. This is the
closest geometry result so far, but it remains a boundary result rather than
an accepted target-pair reproduction. Use `--rebuild` to replay all energy
steps from the committed 21-point source checkpoint.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(CHECKPOINT)
    print(REPORT)


if __name__ == "__main__":
    main()
