"""Scan the N=25 L2 constant-energy quasi-halo branch for Figure 4.1."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    corrected_constant_energy_pseudo_arclength_family,
    corrected_constant_energy_curve_family,
    stroboscopic_spatial_jacobi_seed,
)
from qp_orbits.torus_stability import corrected_curve_dg


ROOT = Path(__file__).resolve().parents[1]
TARGET_JACOBI = 3.044
TARGET_NU = 1.3837
AMPLITUDES = (
    1e-8, 2e-8, 5e-8, 1e-7, 2e-7, 5e-7, 1e-6, 2e-6, 5e-6,
)


def main() -> None:
    system = SYSTEMS["earth_moon"]
    seed = stroboscopic_spatial_jacobi_seed(
        system.mu,
        target_jacobi=TARGET_JACOBI,
        family_label="halo",
        point="L2",
        mode_component=1,
        mode_amplitude=AMPLITUDES[0],
        samples=25,
        curve_samples=120,
    )
    natural = corrected_constant_energy_curve_family(
        seed,
        target_jacobi=TARGET_JACOBI,
        mode_amplitudes=AMPLITUDES,
        max_iterations=24,
    )
    family = corrected_constant_energy_pseudo_arclength_family(
        natural[-2:],
        members=24,
        minimum_step_size=1e-7,
        max_iterations=32,
    )

    rows: list[dict[str, object]] = []
    for member_index, correction in enumerate(family):
        displacement = correction.corrected_states[:, seed.mode_component] - seed.orbit_state[seed.mode_component]
        amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
        dg = corrected_curve_dg(correction)
        magnitudes = np.sort(np.abs(dg.eigenvalues))[::-1]
        unstable_ring = magnitudes[:25]
        radius = float(np.median(unstable_ring))
        nu = 0.5 * (radius + 1.0 / radius)
        jacobi = jacobi_constant(correction.corrected_states, system.mu)
        rows.append(
            {
                "member_index": member_index,
                "continuation_method": "natural_anchor" if member_index < 2 else "pseudo_arclength",
                "mode_amplitude_nd": amplitude,
                "spectral_samples": 25,
                "dg_dimension": dg.map_jacobian.shape[0],
                "base_z0_nd": seed.base_orbit_amplitude,
                "base_orbit_jacobi": seed.orbit_jacobi,
                "mapping_time_nd": dg.mapping_time,
                "mapping_time_days": dg.mapping_time * (system.time_unit_days or 1.0),
                "rotation_angle_rad": dg.rotation_angle_rad,
                "frequency_ratio": 2.0 * np.pi / dg.rotation_angle_rad,
                "mean_jacobi": float(np.mean(jacobi)),
                "curve_jacobi_span": float(np.ptp(jacobi)),
                "curve_residual_norm": float(correction.final_residual_norms.max()),
                "determinant": dg.determinant,
                "determinant_error": abs(dg.determinant - 1.0),
                "unstable_ring_radius_median": radius,
                "unstable_ring_radius_min": float(np.min(unstable_ring)),
                "unstable_ring_radius_max": float(np.max(unstable_ring)),
                "unstable_ring_relative_span": float(np.ptp(unstable_ring) / radius),
                "stability_index": nu,
                "paper_stability_index": TARGET_NU,
                "stability_index_error": nu - TARGET_NU,
                "acceptance": (
                    "pass"
                    if abs(nu - TARGET_NU) <= 5e-4
                    and correction.final_residual_norms.max() <= 1e-8
                    and np.ptp(jacobi) <= 1e-8
                    and np.ptp(unstable_ring) / radius <= 5e-3
                    else "fail"
                ),
            }
        )
        print(
            f"amp={amplitude:.1e} residual={correction.final_residual_norms.max():.3e} "
            f"Jspan={np.ptp(jacobi):.3e} Ru={radius:.9f} nu={nu:.9f}"
        )

    csv_path = ROOT / "data" / "computed" / "chapter4_fig41_l2_constant_energy_scan.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    best = min(rows, key=lambda row: abs(float(row["stability_index_error"])))
    doc_path = ROOT / "docs" / "chapter4_fig41_l2_constant_energy_scan.md"
    doc_path.write_text(
        f"""# Chapter 4 Figure 4.1 L2 constant-energy scan

- Target: `JC={TARGET_JACOBI}`, `N=25`, `nu={TARGET_NU}`
- Periodic boundary: `z0={seed.base_orbit_amplitude:.16g}`, `JC={seed.orbit_jacobi:.16g}`
- Members: `{len(rows)}`
- Best mode amplitude: `{best['mode_amplitude_nd']}`
- Best unstable-ring radius: `{best['unstable_ring_radius_median']}`
- Best stability index: `{best['stability_index']}`
- Best stability-index error: `{best['stability_index_error']}`
- Acceptance: `{best['acceptance']}`

The unstable radius is the median magnitude of the outermost `N=25` DG
eigenvalues, matching the reducible-ring interpretation in McCarthy and Howell.
The relative span of that ring is retained as a separate reducibility/numerical
quality gate; a visually plausible radius is not sufficient for acceptance.
""",
        encoding="utf-8",
    )
    print(csv_path)
    print(doc_path)


if __name__ == "__main__":
    main()
