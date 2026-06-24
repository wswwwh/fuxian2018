"""Figure 4.7: quasi-halo and periodic-halo manifold comparison."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import add_earth_moon_labels, plot_sheet, plot_torus_wire, style_long_axis
from qp_orbits.constants import SYSTEMS
from qp_orbits.manifolds import periodic_halo_manifold_sample
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import base_torus, manifold_sheet


FIGURE_ID = "4.7"
SOURCE_PAGE = 93
REPRO_LEVEL = "shape-match"
SYSTEM = "Earth-Moon CR3BP"


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    torus = base_torus(system, "halo", n_major=84, n_minor=18)
    sheet = manifold_sheet(system, family="halo", direction="minus", stage_fraction=1.18, n_curve=96, n_steps=48)
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
    plot_sheet(ax, sheet, alpha=0.34)
    plot_torus_wire(ax, torus, color="black", alpha=0.45, linewidth=0.38)
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
            color="#165a9f",
            linewidth=1.05,
            alpha=0.82,
        )
    add_earth_moon_labels(ax, include_l1=False)
    style_long_axis(ax, vertical=False)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
