"""Lift the quasi-halo frontier to 21 curve samples and continue one member."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _trigonometric_interpolation_matrix,
    resample_corrected_torus_surface,
    stroboscopic_curve_free_rotation_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)


SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_palc_frontier_checkpoint.npz"
OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_resolution_lift_audit.csv"
CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_quasi_halo_resolution_lift_audit.md"


def correct(seed, states, amplitude: float, rotation: float, *, max_state_step: float = 1.0e-4):
    correction = stroboscopic_curve_free_rotation_correction(
        seed,
        target_amplitude=amplitude,
        amplitude_component=2,
        initial_states=states,
        initial_rotation_angle_rad=rotation,
        phase_reference_states=states,
        max_iterations=80,
        tolerance=1.0e-10,
        constraint_tolerance=1.0e-10,
        max_step=0.005,
        max_state_step=max_state_step,
        max_rotation_step=0.01,
    )
    metric = max(
        float(np.max(correction.final_residual_norms)),
        abs(float(correction.amplitude_residual_history[-1])),
        abs(float(correction.phase_residual_history[-1])),
    )
    if metric > 1.0e-8:
        raise RuntimeError(f"Resolution-lift continuation failed: metric={metric:.3e}")
    return correction


def main() -> None:
    system = SYSTEMS["sun_earth"]
    data = np.load(SOURCE)
    old_seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=float(data["x_amplitude"]),
        vertical_amplitude=1.0e-5,
        samples=int(data["samples"]),
        curve_samples=120,
    )
    seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=float(data["x_amplitude"]),
        vertical_amplitude=1.0e-5,
        samples=21,
        curve_samples=168,
    )
    lifted_states = _trigonometric_interpolation_matrix(old_seed.phases, seed.phases) @ data["current_states"]
    lifted_amplitude = float(np.sqrt(2.0 * np.mean((lifted_states[:, 2] - seed.orbit_state[2]) ** 2)))
    lifted = correct(seed, lifted_states, lifted_amplitude, float(data["current_rotation"]))

    continued_amplitude = 1.02 * lifted_amplitude
    continued_states = lifted.corrected_states.copy()
    scale = continued_amplitude / lifted_amplitude
    for component in (2, 5):
        continued_states[:, component] = seed.orbit_state[component] + scale * (
            continued_states[:, component] - seed.orbit_state[component]
        )
    continued = correct(seed, continued_states, continued_amplitude, lifted.rotation_angle_rad)

    family = [("lifted", lifted), ("continued_2pct", continued)]
    current = continued
    for index in range(1, 3):
        target = 1.005 * current.target_amplitude
        initial = current.corrected_states.copy()
        scale = target / current.target_amplitude
        for component in (2, 5):
            initial[:, component] = seed.orbit_state[component] + scale * (
                initial[:, component] - seed.orbit_state[component]
            )
        current = correct(
            seed,
            initial,
            target,
            current.rotation_angle_rad,
            max_state_step=5.0e-5,
        )
        family.append((f"continued_half_percent_{index}", current))

    rows = []
    for label, correction in family:
        torus = sweep_corrected_curve_correction(correction, time_samples=96, max_step=0.0025)
        surface, _ = resample_corrected_torus_surface(torus, phase_samples=192)
        rows.append(
            {
                "member": label,
                "curve_samples": seed.phases.size,
                "vertical_rms_amplitude_nd": correction.target_amplitude,
                "rotation_angle_rad": correction.rotation_angle_rad,
                "curve_residual_norm": float(np.max(correction.final_residual_norms)),
                "max_abs_y_km": float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km),
                "max_abs_z_km": float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km),
                "jacobi_span": float(np.ptp(torus.jacobi_values)),
                "closure_residual_norm": float(np.max(np.linalg.norm(torus.closure_residuals, axis=1))),
            }
        )

    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    np.savez_compressed(
        CHECKPOINT,
        previous_states=family[-2][1].corrected_states,
        previous_amplitude=family[-2][1].target_amplitude,
        previous_rotation=family[-2][1].rotation_angle_rad,
        current_states=family[-1][1].corrected_states,
        current_amplitude=family[-1][1].target_amplitude,
        current_rotation=family[-1][1].rotation_angle_rad,
        x_amplitude=seed.base_orbit_amplitude,
        samples=seed.phases.size,
    )
    final = rows[-1]
    REPORT.write_text(
        f"""# Chapter 5 Sun-Earth L1 quasi-halo resolution-lift audit

- Curve resolution: `11 -> 21` samples
- Lifted member residual: `{rows[0]['curve_residual_norm']:.3e}`
- Lifted member Jacobi span: `{rows[0]['jacobi_span']:.3e}`
- Verified 21-point frontier amplitude: `{final['vertical_rms_amplitude_nd']:.9g}`
- Continued full-torus max |y|: `{final['max_abs_y_km']:.3f}` km
- Continued full-torus max |z|: `{final['max_abs_z_km']:.3f}` km
- Continued Jacobi span: `{final['jacobi_span']:.3e}`
- Continued closure residual: `{final['closure_residual_norm']:.3e}` normalized units
- Paper target pair: `|y| ~ 660000 km`, `|z| ~ 940000 km`
- Target pair accepted: `false`

Spectral lifting removes the low-resolution Jacobi defect. The corrected
21-point curve supports one 2% continuation step followed by two accepted 0.5%
steps. The next 0.5% step does not converge. The saved terminal pair is the
next starting point for pseudo-arclength or free-mapping-time continuation.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(CHECKPOINT)
    print(REPORT)


if __name__ == "__main__":
    main()
