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
    corrected_vertical_global_unstable_manifold,
    manifold_sheet,
)


FIGURE_ID = "4.8"
SOURCE_PAGE = 93
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Proxy global sheet with corrected quasi-vertical and periodic-halo CR3BP manifold overlays."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    torus = base_torus(system, "vertical", n_major=84, n_minor=18)
    sheet = manifold_sheet(system, family="vertical", direction="minus", stage_fraction=1.22, n_curve=96, n_steps=48)
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

    fig = plt.figure(figsize=(8.1, 4.2), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    plot_sheet_wire(ax, sheet, alpha=0.84, linewidth=0.32, curve_stride=2, time_stride=3)
    plot_torus_wire(ax, torus, color="black", alpha=0.42, linewidth=0.30)
    surface = corrected_vertical.surface
    for curve_idx in range(0, surface.shape[1], 1):
        ax.plot(
            surface[:, curve_idx, 0],
            surface[:, curve_idx, 1],
            surface[:, curve_idx, 2],
            color="#b2182b",
            linewidth=0.42,
            alpha=0.48,
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
