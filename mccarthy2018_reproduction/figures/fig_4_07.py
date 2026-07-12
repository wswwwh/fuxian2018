"""Figure 4.7: quasi-halo and periodic-halo manifold comparison."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import add_earth_moon_labels, plot_corrected_base_torus, plot_sheet_wire, style_long_axis
from qp_orbits.constants import SYSTEMS
from qp_orbits.manifolds import periodic_halo_manifold_sample
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    corrected_l1_constant_energy_halo_unstable_manifolds,
    corrected_manifold_validation_row,
    update_chapter4_manifold_validation,
)


FIGURE_ID = "4.7"
SOURCE_PAGE = 93
REPRO_LEVEL = "numerical manifold comparison"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected JC=3.1389 quasi-halo DG sheet and numerical periodic-halo comparison; no proxy layers."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
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
                uses_proxy_background=False,
                validation_status="corrected DG sheet audited with numerical periodic-halo comparison",
                next_action="Digitize the paper panel for pointwise geometry comparison",
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
        corrected_sheet,
        color="#b2182b",
        alpha=0.82,
        linewidth=0.34,
        curve_stride=1,
        time_stride=10,
    )
    plot_corrected_base_torus(ax, corrected_sheet)
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
