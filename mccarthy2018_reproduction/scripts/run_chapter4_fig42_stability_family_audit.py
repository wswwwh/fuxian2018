"""Build an all-numerical Figure 4.2 stability-family audit."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from qp_orbits.constants import SYSTEMS
from qp_orbits.manifolds import monodromy
from qp_orbits.periodic_orbits import target_spatial_orbit_jacobi
from qp_orbits.quasi_torus import stroboscopic_spatial_jacobi_seed
from qp_orbits.torus_stability import (
    corrected_l1_constant_energy_halo_high_order_dg_family,
    corrected_l1_constant_energy_halo_pseudo_arclength_dg_family,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"


def main() -> None:
    system = SYSTEMS["earth_moon"]
    rows: list[dict[str, object]] = []

    def append_family(values, source: str) -> None:
        for dg in values:
            correction = dg.correction
            sample_count = correction.corrected_states.shape[0]
            component = correction.seed.mode_component
            displacement = correction.corrected_states[:, component] - correction.seed.orbit_state[component]
            amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
            magnitudes = np.sort(np.abs(dg.eigenvalues))[::-1]
            unstable_ring = magnitudes[:sample_count]
            radius = float(np.median(unstable_ring))
            stability = 0.5 * (radius + 1.0 / radius)
            ring_span = float(np.ptp(unstable_ring) / radius)
            rows.append(
                {
                    "kind": "quasi_halo",
                    "source_branch": source,
                    "curve_samples": sample_count,
                    "mapping_time_days": float(dg.mapping_time) * system.time_unit_days,
                    "mode_amplitude_nd": amplitude,
                    "unstable_ring_radius": radius,
                    "unstable_ring_relative_span": ring_span,
                    "stability_index": stability,
                    "curve_residual_norm": float(correction.final_residual_norms.max()),
                    "determinant_error": abs(float(dg.determinant) - 1.0),
                    "max_multiplier": dg.max_multiplier,
                    "min_multiplier": dg.min_multiplier,
                    "acceptance": (
                        "pass"
                        if float(correction.final_residual_norms.max()) <= 1e-9
                        and abs(float(dg.determinant) - 1.0) <= 5e-9
                        and ring_span <= 6e-2
                        else "fail"
                    ),
                }
            )

    append_family(
        corrected_l1_constant_energy_halo_pseudo_arclength_dg_family(system.mu),
        "N9_pseudo_arclength",
    )
    append_family(
        corrected_l1_constant_energy_halo_high_order_dg_family(
            system.mu,
            samples=15,
            members=27,
            member_indices=(8, 16, 26),
            tolerance=5e-10,
        ),
        "N15_spectral_lift",
    )
    append_family(
        corrected_l1_constant_energy_halo_high_order_dg_family(
            system.mu,
            samples=21,
            members=25,
            member_indices=(0, 4, 8, 12, 16, 20, 24),
            tolerance=3e-10,
            max_iterations=64,
        ),
        "N21_fold_tail",
    )

    seed = stroboscopic_spatial_jacobi_seed(
        system.mu,
        target_jacobi=3.1389,
        family_label="halo",
        mode_component=2,
        mode_amplitude=2.5e-4,
        samples=9,
        curve_samples=120,
    )
    targeted = target_spatial_orbit_jacobi(
        system.mu,
        target_jacobi=3.1389,
        z_amplitudes=np.arange(0.005, 0.0601, 0.005),
        point="L1",
        family_label="halo",
        seed_x_amplitude=0.002,
    )
    periodic = monodromy(targeted.orbit)
    periodic_magnitudes = np.abs(periodic.eigenvalues)
    rows.append(
        {
            "kind": "periodic_halo_anchor",
            "source_branch": "targeted_periodic_boundary",
            "curve_samples": 1,
            "mapping_time_days": seed.orbit_period * system.time_unit_days,
            "mode_amplitude_nd": 0.0,
            "unstable_ring_radius": float(np.max(periodic_magnitudes)),
            "unstable_ring_relative_span": 0.0,
            "stability_index": periodic.stability_index,
            "curve_residual_norm": periodic.periodicity_error,
            "determinant_error": abs(float(np.linalg.det(periodic.matrix)) - 1.0),
            "max_multiplier": float(np.max(periodic_magnitudes)),
            "min_multiplier": float(np.min(periodic_magnitudes)),
            "acceptance": "pass" if periodic.periodicity_error <= 1e-8 else "fail",
        }
    )
    rows.sort(key=lambda row: (float(row["mapping_time_days"]), str(row["kind"])))

    csv_path = DATA / "chapter4_fig42_stability_family_audit.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    quasi = [row for row in rows if row["kind"] == "quasi_halo"]
    passed = [row for row in quasi if row["acceptance"] == "pass"]
    max_time = max(float(row["mapping_time_days"]) for row in passed)
    max_nu = max(float(row["stability_index"]) for row in passed)
    coverage = len(passed) >= len(quasi) - 1 and max_time >= 12.424 and max_nu >= 770.0
    doc_path = DOCS / "chapter4_fig42_stability_family_audit.md"
    doc_path.write_text(
        f"""# Chapter 4 Figure 4.2 stability-family audit

- Corrected quasi-halo rows: `{len(quasi)}`
- Accepted quasi-halo rows: `{len(passed)}`
- Rejected spectral-transition rows: `{len(quasi) - len(passed)}`
- Mapping-time coverage: `{min(float(row['mapping_time_days']) for row in passed):.12f}` to `{max_time:.12f}` days
- Stability-index coverage: `{min(float(row['stability_index']) for row in passed):.12f}` to `{max_nu:.12f}`
- Highest resolution: `N={max(int(row['curve_samples']) for row in passed)}`
- Periodic-halo anchor stability index: `{periodic.stability_index:.12f}`
- Coverage acceptance: `{'pass' if coverage else 'fail'}`

The plotted family is assembled only from accepted corrected DG rows at N=9,
15, and 21. One N=21 spectral-lift transition row is rejected by the unstable-ring
dispersion gate. The former analytic/proxy curve is excluded. The N=21 branch approaches a
mapping-time fold near 12.4246 days; this audit does not extrapolate beyond the
accepted continuation. The separate native-PDF audit in
`data/computed/chapter4_fig42_digitized_comparison_audit.csv` supplies the
pointwise paper comparison over the shared interval. It remains
lower-authority image evidence and does not substitute for dynamics. Full
curve coverage stays false until the accepted corrected branch covers the
digitized fold tail.
""",
        encoding="utf-8",
    )
    print(csv_path)
    print(doc_path)
    print(f"coverage={'pass' if coverage else 'fail'} rows={len(passed)} Tmax={max_time:.9f} nu_max={max_nu:.9f}")


if __name__ == "__main__":
    main()
