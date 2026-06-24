from __future__ import annotations

import pickle
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    stroboscopic_curve_fixed_mapping_pseudo_arclength_correction,
    stroboscopic_curve_fixed_rotation_correction,
)


cache = PROJECT_ROOT / "data" / "computed" / "cache" / "fixed_mapping_dro_v1_079947170b953a50.pkl"
with cache.open("rb") as stream:
    family = pickle.load(stream)
previous, current = family[-2:]
print(
    "anchor",
    current.rotation_angle_rad,
    float(np.mean(jacobi_constant(current.corrected_states, current.seed.mu))),
)
for step in (0.015, 0.01, 0.005, 0.002, 0.001, 0.0005):
    try:
        correction = stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
            previous,
            current,
            step_size=step,
            max_iterations=16,
        )
        jacobi = jacobi_constant(correction.corrected_states, correction.seed.mu)
        print(
            step,
            correction.predictor_variables[-1],
            float(np.linalg.norm(
                np.r_[correction.corrected_states.reshape(-1), correction.rotation_angle_rad]
                - correction.predictor_variables
            )),
            correction.rotation_angle_rad,
            float(np.mean(jacobi)),
            correction.target_amplitude,
            float(np.ptp(jacobi)),
            float(correction.final_residual_norms.max()),
        )
    except Exception as error:
        print(step, type(error).__name__, str(error))

delta_rho = current.rotation_angle_rad - previous.rotation_angle_rad
for factor in (0.25, 0.5, 1.0):
    target_rho = current.rotation_angle_rad + factor * delta_rho
    initial_states = current.corrected_states + factor * (
        current.corrected_states - previous.corrected_states
    )
    correction = stroboscopic_curve_fixed_rotation_correction(
        current.seed,
        target_rotation_angle_rad=target_rho,
        initial_states=initial_states,
        phase_reference_states=initial_states,
        max_iterations=16,
    )
    jacobi = jacobi_constant(correction.corrected_states, correction.seed.mu)
    print(
        "rho",
        factor,
        correction.rotation_angle_rad,
        float(np.mean(jacobi)),
        correction.target_amplitude,
        float(np.ptp(jacobi)),
        float(correction.final_residual_norms.max()),
        correction.phase_residual_history[-1],
    )
