"""Figure 4.7: quasi-halo and periodic-halo manifold comparison."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import add_earth_moon_labels, plot_sheet_wire, plot_torus_wire, style_long_axis
from qp_orbits.constants import SYSTEMS
from qp_orbits.manifolds import periodic_halo_manifold_sample
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    base_torus,
    corrected_l1_constant_energy_halo_unstable_manifolds,
    corrected_manifold_validation_row,
    manifold_sheet,
    update_chapter4_manifold_validation,
)


FIGURE_ID = "4.7"
SOURCE_PAGE = 93
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = (
    "Main red sheet is propagated from the corrected quasi-halo DG unstable "
    "eigenvector; grey sheet is retained only as a thesis-scale proxy reference."
)


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    torus = base_torus(system, "halo", n_major=84, n_minor=18)
    proxy_sheet = manifold_sheet(
        system,
        family="halo",
        direction="minus",
        stage_fraction=1.18,
        n_curve=96,
        n_steps=48,
    )
    _, corrected_sheet = corrected_l1_constant_energy_halo_unstable_manifolds(
        system.mu,
        time_unit_days=system.time_unit_days,
    )
    update_chapter4_manifold_validation(
        PROJECT_ROOT,
        [
            corrected_manifold_validation_row(
                corrected_sheet,
                system,
                figure_id=FIGURE_ID,
                family="quasi-halo",
                branch="earthward_minus_x_unstable",
                source_curve="JC=3.1389 quasi-halo pseudo-arclength endpoint",
                uses_proxy_background=True,
                validation_status="main corrected DG sheet audited with periodic-halo comparison; proxy reference retained",
                next_action="Extend the corrected quasi-halo sheet across a thesis-scale continued torus family",
            )
        ],
    )
    periodic_manifold = periodic_halo_manifold_sample(
        system.mu,
        point="L1",
        include_stable=False,
        samples_on_orbit=8,
        duration=4.0,
        trajectory_samples=180,
    )
    earthward_unstable = [
        curve
        for curve in periodic_manifold.unstable
        if curve[:, 0].min() < 0.55 and curve[-1, 1] > 0.02
    ]

    fig = plt.figure(figsize=(8.1, 4.2), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    plot_sheet_wire(
        ax,
        proxy_sheet,
        color="#bdbdbd",
        alpha=0.20,
        linewidth=0.22,
        curve_stride=4,
        time_stride=6,
    )
    plot_sheet_wire(
        ax,
        corrected_sheet,
        color="#b2182b",
        alpha=0.82,
        linewidth=0.34,
        curve_stride=1,
        time_stride=10,
    )
    plot_torus_wire(ax, torus, color="black", alpha=0.42, linewidth=0.30)
    ax.plot(
        periodic_manifold.orbit_curve[:, 0],
        periodic_manifold.orbit_curve[:, 1],
        periodic_manifold.orbit_curve[:, 2],
        color="#1f2937",
        linewidth=1.0,
        alpha=0.88,
    )
    for curve in earthward_unstable:
        ax.plot(
            curve[:, 0],
            curve[:, 1],
            curve[:, 2],
            color="#b2182b",
            linewidth=0.62,
            alpha=0.72,
        )
    add_earth_moon_labels(ax, include_l1=False)
    style_long_axis(ax, vertical=False)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
