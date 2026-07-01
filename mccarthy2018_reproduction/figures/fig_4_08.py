"""Figure 4.8: quasi-vertical and periodic-halo manifold comparison."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import add_earth_moon_labels, plot_sheet_wire, plot_torus_wire, style_long_axis
from qp_orbits.constants import SYSTEMS
from qp_orbits.manifolds import periodic_halo_manifold_sample
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    base_torus,
    corrected_manifold_validation_row,
    corrected_vertical_global_unstable_manifold,
    manifold_sheet,
    update_chapter4_manifold_validation,
)


FIGURE_ID = "4.8"
SOURCE_PAGE = 93
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = (
    "Main red sheet is propagated from the corrected quasi-vertical DG unstable "
    "eigenvector; grey sheet is retained only as a thesis-scale proxy reference."
)


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    torus = base_torus(system, "vertical", n_major=84, n_minor=18)
    proxy_sheet = manifold_sheet(
        system,
        family="vertical",
        direction="minus",
        stage_fraction=1.22,
        n_curve=96,
        n_steps=48,
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
    corrected_vertical = corrected_vertical_global_unstable_manifold(system.mu)
    update_chapter4_manifold_validation(
        PROJECT_ROOT,
        [
            corrected_manifold_validation_row(
                corrected_vertical,
                system,
                figure_id=FIGURE_ID,
                family="quasi-vertical",
                branch="earthward_global_unstable",
                source_curve="corrected quasi-vertical stroboscopic curve",
                uses_proxy_background=True,
                validation_status="main corrected DG global sheet audited with periodic-halo comparison; proxy reference retained",
                next_action="Continue the source quasi-vertical torus family before global manifold propagation",
            )
        ],
    )

    fig = plt.figure(figsize=(8.1, 4.2), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    plot_sheet_wire(
        ax,
        proxy_sheet,
        color="#bdbdbd",
        alpha=0.18,
        linewidth=0.22,
        curve_stride=4,
        time_stride=6,
    )
    plot_torus_wire(ax, torus, color="black", alpha=0.42, linewidth=0.30)
    plot_sheet_wire(
        ax,
        corrected_vertical,
        color="#b2182b",
        alpha=0.76,
        linewidth=0.36,
        curve_stride=1,
        time_stride=18,
    )
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
            linewidth=0.56,
            alpha=0.60,
        )
    add_earth_moon_labels(ax, include_l1=False)
    style_long_axis(ax, vertical=True)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
