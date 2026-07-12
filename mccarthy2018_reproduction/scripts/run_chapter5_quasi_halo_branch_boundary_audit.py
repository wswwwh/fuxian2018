"""Audit the finite-amplitude boundary of the Sun-Earth L1 quasi-halo branch."""

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
    stroboscopic_curve_free_rotation_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)


OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_branch_boundary_audit.csv"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_quasi_halo_branch_boundary_audit.md"

# Accepted natural-parameter continuation path found by step-halving. Keeping
# the path explicit makes the fold/boundary audit deterministic and reviewable.
AMPLITUDES = (
    1.0e-5, 2.0e-5, 4.0e-5, 8.0e-5, 9.6e-5, 1.152e-4,
    1.3824e-4, 1.65888e-4, 1.990656e-4, 2.1897216e-4,
    2.44153958e-4, 2.76443319e-4, 2.97465106e-4, 3.23478523e-4,
    3.39744294e-4, 3.59390524e-4, 3.83290172e-4, 3.97946340e-4,
    4.15445415e-4, 4.36454270e-4, 4.61836221e-4, 4.77279591e-4,
    4.95633341e-4, 5.17551814e-4, 5.30712286e-4, 5.46231675e-4,
    5.64600872e-4, 5.86435847e-4, 5.99476505e-4, 6.14806747e-4,
    6.32887366e-4, 6.54291563e-4, 6.79738861e-4, 6.94940146e-4,
    7.03876357e-4, 7.14285148e-4, 7.26432268e-4, 7.40639017e-4,
    7.48967655e-4, 7.58653295e-4, 7.69935823e-4, 7.83103691e-4,
    7.90804707e-4, 7.99747967e-4, 8.10149027e-4, 8.22265807e-4,
    8.29337158e-4, 8.37539145e-4, 8.47064714e-4, 8.52604210e-4,
    8.59016291e-4,
)
VERIFIED_FRONTIER_AMPLITUDE = 8.66445640e-4


def correct(seed, amplitude: float, previous, previous_amplitude, rotation):
    initial = None
    if previous is not None:
        initial = previous.copy()
        scale = amplitude / previous_amplitude
        for component in (2, 5):
            initial[:, component] = seed.orbit_state[component] + scale * (
                initial[:, component] - seed.orbit_state[component]
            )
    correction = stroboscopic_curve_free_rotation_correction(
        seed,
        target_amplitude=amplitude,
        amplitude_component=2,
        initial_states=initial,
        initial_rotation_angle_rad=rotation,
        phase_reference_states=initial,
        max_iterations=80,
        max_step=0.01,
        max_state_step=2.0e-4 if previous is not None else 5.0e-4,
        max_rotation_step=0.02,
    )
    metric = max(
        float(np.max(correction.final_residual_norms)),
        abs(float(correction.amplitude_residual_history[-1])),
        abs(float(correction.phase_residual_history[-1])),
    )
    return correction, metric


def main() -> None:
    system = SYSTEMS["sun_earth"]
    seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=0.002125,
        vertical_amplitude=AMPLITUDES[0],
        samples=11,
        curve_samples=120,
    )
    rows: list[dict[str, object]] = []
    previous = None
    previous_amplitude = None
    rotation = None
    final_correction = None
    for amplitude in (*AMPLITUDES, VERIFIED_FRONTIER_AMPLITUDE):
        correction, metric = correct(seed, amplitude, previous, previous_amplitude, rotation)
        accepted = metric <= 1.0e-8
        rows.append(
            {
                "vertical_rms_amplitude_nd": amplitude,
                "accepted": str(accepted).lower(),
                "combined_newton_metric": metric,
                "curve_residual_norm": float(np.max(correction.final_residual_norms)),
                "amplitude_residual": float(correction.amplitude_residual_history[-1]),
                "phase_residual": float(correction.phase_residual_history[-1]),
                "rotation_angle_rad": correction.rotation_angle_rad,
                "strobe_max_abs_y_km": float(np.max(np.abs(correction.corrected_states[:, 1])) * system.length_unit_km),
                "strobe_max_abs_z_km": float(np.max(np.abs(correction.corrected_states[:, 2])) * system.length_unit_km),
            }
        )
        print(f"amplitude={amplitude:.9g} accepted={accepted} metric={metric:.3e}", flush=True)
        if not accepted:
            raise RuntimeError(f"Deterministic continuation path failed at {amplitude:.9g}")
        previous = correction.corrected_states.copy()
        previous_amplitude = amplitude
        rotation = correction.rotation_angle_rad
        final_correction = correction

    if final_correction is None:
        raise RuntimeError("Continuation did not produce an accepted member")
    torus = sweep_corrected_curve_correction(final_correction, time_samples=48, max_step=0.01)
    surface, _ = resample_corrected_torus_surface(torus, phase_samples=96)
    max_y = float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km)
    max_z = float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km)
    jacobi_span = float(np.ptp(torus.jacobi_values))

    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    REPORT.write_text(
        f"""# Chapter 5 Sun-Earth L1 quasi-halo continuation-frontier audit

- Planar Lyapunov base amplitude: `0.002125`
- Accepted continuation members: `{sum(row['accepted'] == 'true' for row in rows)}`
- Last accepted vertical RMS amplitude: `{VERIFIED_FRONTIER_AMPLITUDE:.9g}`
- Last accepted full-torus max |y|: `{max_y:.3f}` km
- Last accepted full-torus max |z|: `{max_z:.3f}` km
- Full-torus Jacobi span: `{jacobi_span:.3e}`
- Paper target pair: `|y| ~ 660000 km`, `|z| ~ 940000 km`
- Target pair accepted: `false`

Natural-parameter free-rotation continuation has been verified through
vertical RMS amplitude `{VERIFIED_FRONTIER_AMPLITUDE:.3e}`. An earlier adaptive
run stalled here, but deterministic warm-start replay converged, so this point
is a verified frontier rather than a demonstrated branch boundary. The full
torus remains far below the paper's out-of-plane scale and its sampled Jacobi
span is above the strict `1e-8` gate. This quasi-halo route therefore does not
replace the currently accepted quasi-vertical source. Further continuation,
resolution lifting, and tighter propagation are required before acceptance.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(REPORT)


if __name__ == "__main__":
    main()
