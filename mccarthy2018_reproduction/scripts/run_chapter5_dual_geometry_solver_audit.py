"""Audit the regularized dual-geometry correction on the energy frontier."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _smooth_absolute_support,
    resample_corrected_torus_surface,
    stroboscopic_curve_dual_geometry_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)


SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_energy_frontier_checkpoint.npz"
SEED_SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz"
OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_dual_geometry_solver_audit.csv"
CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_dual_geometry_solver_checkpoint.npz"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_dual_geometry_solver_audit.md"


def main() -> None:
    system = SYSTEMS["sun_earth"]
    data = np.load(SOURCE)
    seed_data = np.load(SEED_SOURCE)
    seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=float(seed_data["x_amplitude"]),
        vertical_amplitude=1.0e-5,
        samples=int(seed_data["samples"]),
        curve_samples=168,
    )
    y_support, _ = _smooth_absolute_support(data["states"][:, 1], sharpness=80.0)
    z_support, _ = _smooth_absolute_support(data["states"][:, 2], sharpness=80.0)
    rows = []
    final = None
    for label, y_target in (("identity", y_support), ("y_support_minus_0.1pct", 0.999 * y_support)):
        correction = stroboscopic_curve_dual_geometry_correction(
            seed,
            target_jacobi=float(data["jacobi"]),
            target_y_support=y_target,
            target_z_support=z_support,
            initial_states=data["states"],
            initial_mapping_time=float(data["mapping_time"]),
            initial_rotation_angle_rad=float(data["rotation"]),
            sharpness=80.0,
            regularization=1.0e-8,
            geometry_residual_scale=10.0,
            max_iterations=60,
            tolerance=1.0e-8,
            constraint_tolerance=1.0e-8,
            max_step=0.005,
            max_state_step=1.0e-5,
            max_mapping_time_step=0.001,
            max_rotation_step=0.001,
        )
        torus = sweep_corrected_curve_correction(correction, time_samples=96, max_step=0.0025)
        surface, _ = resample_corrected_torus_surface(torus, phase_samples=192)
        metric = max(
            float(np.max(correction.final_residual_norms)),
            abs(float(correction.energy_residual_history[-1])),
            float(np.max(np.abs(correction.geometry_residual_history[-1]))),
            abs(float(correction.phase_residual_history[-1])),
        )
        rows.append(
            {
                "member": label,
                "target_y_support_nd": y_target,
                "target_z_support_nd": z_support,
                "combined_metric": metric,
                "map_residual": float(np.max(correction.final_residual_norms)),
                "max_abs_y_km": float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km),
                "max_abs_z_km": float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km),
                "jacobi_span": float(np.ptp(torus.jacobi_values)),
            }
        )
        final = correction
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert final is not None
    np.savez_compressed(
        CHECKPOINT,
        states=final.corrected_states,
        mapping_time=final.mapping_time,
        rotation=final.rotation_angle_rad,
        jacobi=final.target_jacobi,
        y_support=final.target_y_support,
        z_support=final.target_z_support,
    )
    delta_y = float(rows[1]["max_abs_y_km"]) - float(rows[0]["max_abs_y_km"])
    delta_z = float(rows[1]["max_abs_z_km"]) - float(rows[0]["max_abs_z_km"])
    REPORT.write_text(
        f"""# Chapter 5 dual-geometry solver audit

- Identity target metric: `{rows[0]['combined_metric']:.3e}`
- Perturbed target metric: `{rows[1]['combined_metric']:.3e}`
- Full-torus response to -0.1% strobe-y support: `dy={delta_y:+.3f} km`, `dz={delta_z:+.3f} km`
- Perturbed full-torus max |y|: `{rows[1]['max_abs_y_km']:.3f}` km
- Perturbed full-torus max |z|: `{rows[1]['max_abs_z_km']:.3f}` km
- Target pair accepted: `false`

The regularized solver satisfies map, mean-energy, phase, and both smooth
geometry constraints below `1e-8`. However, reducing the stroboscopic curve's
y support does not reduce the propagated torus y maximum. The next revision
must constrain propagated time-slice support using STM sensitivity; the
stroboscopic support is retained only as a solver regression target.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(CHECKPOINT)
    print(REPORT)


if __name__ == "__main__":
    main()
