"""Continue and audit the Sun-Earth L1 quasi-halo branch with PALC."""

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
    stroboscopic_curve_fixed_mapping_pseudo_arclength_correction,
    stroboscopic_curve_free_rotation_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)


SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_frontier_checkpoint.npz"
OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_palc_frontier_audit.csv"
CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_palc_frontier_checkpoint.npz"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_quasi_halo_palc_frontier_audit.md"

# First step uses the natural secant length. Subsequent values are accepted
# step-halving results from the predictor-distance guarded PALC solver.
PALC_STEPS = (None, 1.2992e-4, 1.4292e-4, 3.9302e-5)


def rebuild(seed, data, prefix: str):
    states = data[f"{prefix}_states"]
    return stroboscopic_curve_free_rotation_correction(
        seed,
        target_amplitude=float(data[f"{prefix}_amplitude"]),
        amplitude_component=2,
        initial_states=states,
        initial_rotation_angle_rad=float(data[f"{prefix}_rotation"]),
        phase_reference_states=states,
        max_iterations=4,
        max_step=0.01,
        max_state_step=2.0e-4,
        max_rotation_step=0.02,
    )


def main() -> None:
    system = SYSTEMS["sun_earth"]
    data = np.load(SOURCE)
    seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=float(data["x_amplitude"]),
        vertical_amplitude=1.0e-5,
        samples=int(data["samples"]),
        curve_samples=120,
    )
    previous = rebuild(seed, data, "previous")
    current = rebuild(seed, data, "current")
    rows: list[dict[str, object]] = []
    members = [previous, current]
    for index, step in enumerate(PALC_STEPS, start=1):
        correction = stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
            previous,
            current,
            step_size=step,
            max_iterations=60,
            tolerance=1.0e-8,
            constraint_tolerance=1.0e-10,
            max_step=0.01,
            max_state_step=2.0e-4,
            max_rotation_step=0.02,
        )
        rows.append(
            {
                "palc_member": index,
                "step_size": correction.step_size,
                "vertical_rms_amplitude_nd": correction.target_amplitude,
                "rotation_angle_rad": correction.rotation_angle_rad,
                "curve_residual_norm": float(np.max(correction.final_residual_norms)),
                "phase_residual": float(correction.phase_residual_history[-1]),
                "arclength_residual": float(correction.arclength_residual_history[-1]),
                "iterations": correction.residual_history.shape[0],
                "strobe_max_abs_y_km": float(np.max(np.abs(correction.corrected_states[:, 1])) * system.length_unit_km),
                "strobe_max_abs_z_km": float(np.max(np.abs(correction.corrected_states[:, 2])) * system.length_unit_km),
            }
        )
        print(
            f"PALC {index}: amplitude={correction.target_amplitude:.9g} "
            f"residual={np.max(correction.final_residual_norms):.3e}",
            flush=True,
        )
        previous, current = current, correction
        members.append(correction)

    torus = sweep_corrected_curve_correction(current, time_samples=72, max_step=0.005)
    surface, _ = resample_corrected_torus_surface(torus, phase_samples=128)
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
        previous_states=members[-2].corrected_states,
        previous_rotation=members[-2].rotation_angle_rad,
        current_states=members[-1].corrected_states,
        current_rotation=members[-1].rotation_angle_rad,
        x_amplitude=seed.base_orbit_amplitude,
        samples=seed.phases.size,
    )
    REPORT.write_text(
        f"""# Chapter 5 Sun-Earth L1 quasi-halo PALC frontier audit

- Accepted PALC members: `{len(rows)}`
- Source vertical RMS amplitude: `{float(data['current_amplitude']):.9g}`
- Verified PALC frontier amplitude: `{current.target_amplitude:.9g}`
- Frontier full-torus max |y|: `{max_y:.3f}` km
- Frontier full-torus max |z|: `{max_z:.3f}` km
- Full-torus Jacobi span: `{jacobi_span:.3e}`
- Maximum closure residual: `{closure:.3e}` normalized units
- Paper target pair: `|y| ~ 660000 km`, `|z| ~ 940000 km`
- Target pair accepted: `false`

Fixed-mapping-time pseudo-arclength continuation advances beyond the verified
natural-parameter frontier and supplies four accepted members. The final
member still falls short of the paper's out-of-plane amplitude. Continuation
after this member is numerically ill-conditioned under the current 11-point
curve discretization: predictor-distance guards reject remote solutions even
after repeated step reduction. The saved terminal secant permits resolution
lifting or free-mapping-time continuation without replaying the full branch.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(CHECKPOINT)
    print(REPORT)


if __name__ == "__main__":
    main()
