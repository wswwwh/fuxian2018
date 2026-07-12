"""Audit secant-rotation, free-mapping-time continuation of the L1 torus."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    resample_corrected_torus_surface,
    stroboscopic_curve_free_mapping_time_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)


SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz"
OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_free_mapping_frontier_audit.csv"
CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_free_mapping_frontier_checkpoint.npz"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_quasi_halo_free_mapping_frontier_audit.md"


def correct(
    seed,
    states,
    amplitude,
    rotation,
    mapping_time,
    *,
    max_state_step=2.5e-5,
    max_mapping_time_step=0.005,
):
    correction = stroboscopic_curve_free_mapping_time_correction(
        seed,
        target_rotation_angle_rad=rotation,
        target_amplitude=amplitude,
        amplitude_component=2,
        initial_states=states,
        initial_mapping_time=mapping_time,
        phase_reference_states=states,
        max_iterations=120,
        tolerance=1.0e-10,
        constraint_tolerance=1.0e-10,
        max_step=0.005,
        max_state_step=max_state_step,
        max_mapping_time_step=max_mapping_time_step,
    )
    metric = max(
        float(np.max(correction.final_residual_norms)),
        abs(float(correction.amplitude_residual_history[-1])),
        abs(float(correction.phase_residual_history[-1])),
    )
    if metric > 1.0e-8:
        raise RuntimeError(f"Free-mapping-time continuation failed: metric={metric:.3e}")
    return correction, metric


def scaled_states(seed, states, old_amplitude, new_amplitude):
    result = states.copy()
    scale = new_amplitude / old_amplitude
    for component in (2, 5):
        result[:, component] = seed.orbit_state[component] + scale * (
            result[:, component] - seed.orbit_state[component]
        )
    return result


def main() -> None:
    system = SYSTEMS["sun_earth"]
    data = np.load(SOURCE)
    seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=float(data["x_amplitude"]),
        vertical_amplitude=1.0e-5,
        samples=int(data["samples"]),
        curve_samples=168,
    )
    previous_amplitude = float(data["current_amplitude"])
    previous_rotation = float(data["current_rotation"])
    amplitude = 1.005 * previous_amplitude
    rotation = 0.10087
    states = scaled_states(seed, data["current_states"], previous_amplitude, amplitude)
    correction, metric = correct(
        seed,
        states,
        amplitude,
        rotation,
        seed.orbit_period,
        max_state_step=5.0e-5,
        max_mapping_time_step=0.01,
    )
    rows = []

    for member in range(18):
        rows.append(
            {
                "member": member + 1,
                "vertical_rms_amplitude_nd": correction.target_amplitude,
                "rotation_angle_rad": correction.rotation_angle_rad,
                "mapping_time_nd": correction.mapping_time,
                "combined_metric": metric,
                "curve_residual_norm": float(np.max(correction.final_residual_norms)),
                "strobe_max_abs_y_km": float(np.max(np.abs(correction.corrected_states[:, 1])) * system.length_unit_km),
                "strobe_max_abs_z_km": float(np.max(np.abs(correction.corrected_states[:, 2])) * system.length_unit_km),
            }
        )
        if member == 17:
            break
        target_amplitude = 1.0025 * amplitude
        slope = (rotation - previous_rotation) / (amplitude - previous_amplitude)
        target_rotation = rotation + slope * (target_amplitude - amplitude)
        initial = scaled_states(seed, correction.corrected_states, amplitude, target_amplitude)
        next_correction, next_metric = correct(
            seed,
            initial,
            target_amplitude,
            target_rotation,
            correction.mapping_time,
        )
        previous_amplitude, previous_rotation = amplitude, rotation
        amplitude, rotation = target_amplitude, target_rotation
        correction, metric = next_correction, next_metric
        print(f"member={member + 2} amplitude={amplitude:.9g} metric={metric:.3e}", flush=True)

    torus = sweep_corrected_curve_correction(correction, time_samples=96, max_step=0.0025)
    surface, _ = resample_corrected_torus_surface(torus, phase_samples=192)
    max_y = float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km)
    max_z = float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km)
    jacobi_span = float(np.ptp(torus.jacobi_values))
    closure = float(np.max(np.linalg.norm(torus.closure_residuals, axis=1)))

    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    np.savez_compressed(
        CHECKPOINT,
        states=correction.corrected_states,
        amplitude=correction.target_amplitude,
        rotation=correction.rotation_angle_rad,
        mapping_time=correction.mapping_time,
        previous_amplitude=previous_amplitude,
        previous_rotation=previous_rotation,
        x_amplitude=seed.base_orbit_amplitude,
        samples=seed.phases.size,
    )
    REPORT.write_text(
        f"""# Chapter 5 Sun-Earth L1 quasi-halo free-mapping frontier audit

- Accepted free-mapping-time members: `{len(rows)}`
- Verified frontier amplitude: `{correction.target_amplitude:.9g}`
- Frontier rotation angle: `{correction.rotation_angle_rad:.9g}` rad
- Frontier mapping time: `{correction.mapping_time:.9g}` normalized units
- Frontier full-torus max |y|: `{max_y:.3f}` km
- Frontier full-torus max |z|: `{max_z:.3f}` km
- Full-torus Jacobi span: `{jacobi_span:.3e}`
- Maximum closure residual: `{closure:.3e}` normalized units
- Paper target pair: `|y| ~ 660000 km`, `|z| ~ 940000 km`
- Target pair accepted: `false`

Allowing mapping time to vary while extrapolating the rotation angle produces
18 additional, tightly converged members. However, the out-of-plane extent
decreases to about `{max_z:.0f}` km as amplitude grows. This is a valid nearby
frequency path but it moves away from the paper geometry, so it is retained as
negative evidence and must not replace the quasi-vertical source. The next
targeted method should constrain geometry or energy directly instead of
continuing this frequency trend.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(CHECKPOINT)
    print(REPORT)


if __name__ == "__main__":
    main()
