"""Figure 5.14: LEO to quasi-periodic Sun-Earth L1 Lissajous transfer."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _chapter5_plotting import add_axis_arrow, plot_surface
from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import leo_to_l1_transfer
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.14"
SOURCE_PAGE = 112
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Sun-Earth CR3BP stable-manifold baseline"
NOTES = "Proxy Lissajous context arranged to match the thesis transfer-scene layout."


def _add_planar_arrow(ax, curve: np.ndarray, index: int) -> None:
    start = curve[index]
    stop = curve[min(index + 18, len(curve) - 1)]
    ax.annotate(
        "",
        xy=(stop[0], stop[1]),
        xytext=(start[0], start[1]),
        arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "#1f8fd4"},
    )


def main() -> None:
    apply_style()
    scene = leo_to_l1_transfer()
    transfer, lissajous = scene.curves
    system = SYSTEMS["sun_earth"]
    earth = ((1.0 - system.mu) * system.length_unit_km, 0.0, 0.0)
    arrival = transfer[-1]
    theta = np.linspace(0.0, 2.0 * np.pi, 160)
    parking_orbit = np.column_stack(
        [
            earth[0] + 1.25e5 * np.cos(theta),
            1.25e5 * np.sin(theta),
            np.zeros_like(theta),
        ]
    )

    fig = plt.figure(figsize=(6.5, 8.2), constrained_layout=True)
    ax = fig.add_subplot(211, projection="3d")
    plot_surface(ax, scene.surface, alpha=0.46)
    ax.plot(transfer[:, 0], transfer[:, 1], transfer[:, 2], color="#1f8fd4", linewidth=1.2)
    ax.plot(lissajous[:, 0], lissajous[:, 1], lissajous[:, 2], color="#91ad58", linewidth=0.7, alpha=0.70)
    ax.plot(parking_orbit[:, 0], parking_orbit[:, 1], parking_orbit[:, 2], color="#c9253d", linewidth=0.75)
    ax.scatter([earth[0]], [earth[1]], [earth[2]], color="black", s=16)
    ax.scatter(*arrival, color="#c9253d", s=18)
    ax.text(earth[0] - 2.0e5, earth[1] + 1.0e5, earth[2], "Earth", fontsize=10)
    ax.text(arrival[0] - 2.5e5, arrival[1] - 0.8e5, arrival[2] + 1.2e5, "Arrival\nLocation", fontsize=10)
    ax.set_xlabel("X [km]", labelpad=-7)
    ax.set_ylabel("Y [km]", labelpad=-6)
    ax.set_zlabel("Z [km]", labelpad=-6)
    ax.tick_params(labelsize=8, pad=-3)
    ax.view_init(elev=22, azim=-58)
    ax.set_box_aspect((1.35, 1.0, 0.95))
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis._axinfo["grid"]["color"] = (0.88, 0.88, 0.88, 0.45)
        axis._axinfo["grid"]["linewidth"] = 0.38
    add_axis_arrow(ax, "To Sun", xy=(0.67, 0.10), xytext=(0.80, 0.18), rotation=16)
    ax.text2D(0.48, -0.12, "(a)", transform=ax.transAxes, fontsize=12)

    ax2 = fig.add_subplot(212)
    for col in range(0, scene.surface.shape[1], 3):
        ax2.plot(scene.surface[:, col, 0], scene.surface[:, col, 1], color="0.45", linewidth=0.35, alpha=0.22)
    ax2.plot(transfer[:, 0], transfer[:, 1], color="#1f8fd4", linewidth=1.1)
    ax2.plot(lissajous[:, 0], lissajous[:, 1], color="#91ad58", linewidth=0.7, alpha=0.70)
    ax2.plot(parking_orbit[:, 0], parking_orbit[:, 1], color="#c9253d", linewidth=0.8)
    ax2.scatter([earth[0]], [earth[1]], color="black", s=18)
    ax2.scatter([arrival[0]], [arrival[1]], color="#c9253d", s=18)
    ax2.text(earth[0] - 3.0e5, earth[1] - 1.3e5, "Earth", fontsize=11)
    ax2.text(arrival[0] - 2.7e5, arrival[1] - 2.0e5, "Arrival\nLocation", fontsize=10)
    _add_planar_arrow(ax2, transfer, 135)
    _add_planar_arrow(ax2, transfer, 390)
    _add_planar_arrow(ax2, transfer, 610)
    ax2.annotate("To Sun", xy=(0.05, 0.86), xytext=(0.17, 0.92), xycoords="axes fraction",
                 arrowprops={"arrowstyle": "-|>", "lw": 1.4, "color": "black"}, fontsize=10)
    ax2.set_xlabel("X [km]")
    ax2.set_ylabel("Y [km]")
    ax2.set_aspect("equal", adjustable="box")
    ax2.set_xlim(1.479e8, 1.508e8)
    ax2.set_ylim(-1.12e6, 0.88e6)
    ax2.text(0.50, -0.22, "(b)", transform=ax2.transAxes, fontsize=12)

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
