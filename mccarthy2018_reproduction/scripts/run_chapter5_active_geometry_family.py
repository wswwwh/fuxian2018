"""Audit or extend the adaptive active-event geometry family."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _propagated_active_geometry_constraints,
    resample_corrected_torus_surface,
    stroboscopic_curve_dual_geometry_correction,
    stroboscopic_invariant_curve_seed,
    sweep_corrected_curve_correction,
)


SEED_SOURCE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz"
CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_family_checkpoint.npz"
OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_family_audit.csv"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_active_geometry_family_audit.md"


def metric(correction) -> float:
    return max(
        float(np.max(correction.final_residual_norms)),
        abs(float(correction.energy_residual_history[-1])),
        float(np.max(np.abs(correction.geometry_residual_history[-1]))),
        abs(float(correction.phase_residual_history[-1])),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--additional-members", type=int, default=0)
    args = parser.parse_args()
    if args.additional_members < 0:
        raise ValueError("additional-members must be non-negative")
    system = SYSTEMS["sun_earth"]
    seed_data = np.load(SEED_SOURCE)
    data = np.load(CHECKPOINT)
    seed = stroboscopic_invariant_curve_seed(
        system.mu,
        point="L1",
        x_amplitude=float(seed_data["x_amplitude"]),
        vertical_amplitude=1.0e-5,
        samples=int(seed_data["samples"]),
        curve_samples=168,
    )
    states = data["states"].copy()
    mapping_time = float(data["mapping_time"])
    rotation = float(data["rotation"])
    target_jacobi = float(data["jacobi"])
    accepted = int(data["accepted"])
    step = min(1.5e-4, float(data["step"]) * 1.05)
    fractions = np.linspace(0.0, 1.0, 17)
    last = None
    for _ in range(args.additional_members):
        correction = None
        for _retry in range(5):
            residuals, _, _, _, _ = _propagated_active_geometry_constraints(
                states,
                source_phases=seed.phases,
                mapping_time=mapping_time,
                rotation_angle_rad=rotation,
                mu=system.mu,
                time_fractions=fractions,
                phase_samples=64,
                target_y_support=1.0,
                target_z_support=1.0,
                max_step=0.005,
            )
            y_support, z_support = 1.0 + residuals
            candidate = stroboscopic_curve_dual_geometry_correction(
                seed,
                target_jacobi=target_jacobi,
                target_y_support=(1.0 - step) * y_support,
                target_z_support=z_support,
                initial_states=states,
                initial_mapping_time=mapping_time,
                initial_rotation_angle_rad=rotation,
                phase_reference_states=states,
                geometry_time_fractions=fractions,
                active_geometry_phase_samples=64,
                regularization=1.0e-8,
                geometry_residual_scale=10.0,
                max_iterations=60,
                tolerance=1.0e-8,
                constraint_tolerance=1.0e-8,
                max_step=0.005,
                max_state_step=5.0e-6,
                max_mapping_time_step=5.0e-4,
                max_rotation_step=5.0e-4,
            )
            if metric(candidate) < 1.0e-8:
                correction = candidate
                break
            step *= 0.5
        if correction is None:
            raise RuntimeError("Active-event continuation exhausted step retries")
        states = correction.corrected_states.copy()
        mapping_time = correction.mapping_time
        rotation = correction.rotation_angle_rad
        accepted += 1
        last = correction
        step = min(1.5e-4, step * 1.05)
        np.savez_compressed(
            CHECKPOINT,
            states=states,
            mapping_time=mapping_time,
            rotation=rotation,
            jacobi=target_jacobi,
            accepted=accepted,
            step=step / 1.05,
        )
        print(f"accepted={accepted} metric={metric(correction):.3e}", flush=True)

    if last is None:
        residuals, _, _, _, _ = _propagated_active_geometry_constraints(
            states,
            source_phases=seed.phases,
            mapping_time=mapping_time,
            rotation_angle_rad=rotation,
            mu=system.mu,
            time_fractions=fractions,
            phase_samples=64,
            target_y_support=1.0,
            target_z_support=1.0,
            max_step=0.005,
        )
        last = stroboscopic_curve_dual_geometry_correction(
            seed,
            target_jacobi=target_jacobi,
            target_y_support=1.0 + residuals[0],
            target_z_support=1.0 + residuals[1],
            initial_states=states,
            initial_mapping_time=mapping_time,
            initial_rotation_angle_rad=rotation,
            geometry_time_fractions=fractions,
            active_geometry_phase_samples=64,
            max_iterations=2,
            tolerance=1.0e-8,
            constraint_tolerance=1.0e-8,
            max_step=0.005,
        )
    torus = sweep_corrected_curve_correction(last, time_samples=128, max_step=0.0025)
    surface, _ = resample_corrected_torus_surface(torus, phase_samples=256)
    row = {
        "accepted_members": accepted,
        "last_step": float(np.load(CHECKPOINT)["step"]),
        "combined_metric": metric(last),
        "max_abs_y_km": float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km),
        "max_abs_z_km": float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km),
        "jacobi_span": float(np.ptp(torus.jacobi_values)),
        "closure_residual": float(np.max(np.linalg.norm(torus.closure_residuals, axis=1))),
    }
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    REPORT.write_text(
        f"""# Chapter 5 active-event geometry family audit

- Accepted family members: `{accepted}`
- Last relative y-event step: `{row['last_step']:.3e}`
- Combined metric: `{row['combined_metric']:.3e}`
- Full-torus max |y|: `{row['max_abs_y_km']:.3f}` km
- Full-torus max |z|: `{row['max_abs_z_km']:.3f}` km
- Jacobi span: `{row['jacobi_span']:.3e}`
- Closure residual: `{row['closure_residual']:.3e}`
- Target pair accepted: `false`

The family uses active-event relocation after every accepted member and an
adaptive trust step capped at `1.5e-4`. Run this script with
`--additional-members N` to continue from the committed checkpoint without
replaying the accepted prefix.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(CHECKPOINT)
    print(REPORT)


if __name__ == "__main__":
    main()
