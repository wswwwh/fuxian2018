"""Figure 5.1: Sun-Earth L1 quasi-vertical long propagation."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import plot_surface, style_sun_earth_l1_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import sun_earth_l1_cr3bp_long_propagation, sun_earth_l1_long_propagation
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.1"
SOURCE_PAGE = 96
REPRO_LEVEL = "shape-match"
SYSTEM = "Sun-Earth CR3BP"
NOTES = "Proxy long-propagation scene with local CR3BP-propagated Sun-Earth L1 arc overlays."


def main() -> None:
    apply_style()
    fig = plt.figure(figsize=(7.6, 7.0), constrained_layout=True)
    counts = [1, 8, 18]
    labels = ["(a)", "(b)", "(c)"]
    positions = [221, 222, 212]
    for position, count, label in zip(positions, counts, labels):
        ax = fig.add_subplot(position, projection="3d")
        scene = sun_earth_l1_long_propagation(count)
        cr3bp_scene = sun_earth_l1_cr3bp_long_propagation(count, samples=260)
        plot_surface(ax, scene.surface, alpha=0.46)
        for curve in scene.curves:
            ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#a71930", linewidth=0.78, alpha=0.82)
        for curve in cr3bp_scene.curves:
            ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#2ca25f", linewidth=0.72, alpha=0.88)
        style_sun_earth_l1_axis(ax, label=label)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
