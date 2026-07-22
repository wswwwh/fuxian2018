"""Figure 5.14: LEO to quasi-periodic Sun-Earth L1 Lissajous transfer."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import csv

from _chapter5_plotting import add_axis_arrow, plot_surface
from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.14"
SOURCE_PAGE = 112
REPRO_LEVEL = "numerical Lissajous stable-manifold transfer reproduction"
SYSTEM = "Sun-Earth CR3BP stable-manifold baseline"
NOTES = "Accepted active-geometry torus and stable-manifold transfer to a 185-km LEO boundary; no legacy torus or transfer."


def _load_numerical_scene(system):
    surface_path = PROJECT_ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_long_trajectory.npz"
    with np.load(surface_path) as data:
        surface = data["torus_surface_nd"].copy() * system.length_unit_km
        invariant_curve = data["invariant_curve_nd"].copy() * system.length_unit_km
    trajectory_path = PROJECT_ROOT / "data" / "computed" / "chapter5_active_geometry_leo_transfer.csv"
    with trajectory_path.open(newline="", encoding="utf-8") as stream:
        trajectory_rows = list(csv.DictReader(stream))
    transfer = np.array([[float(row[key]) for key in ("x_nd", "y_nd", "z_nd")] for row in trajectory_rows])
    transfer *= system.length_unit_km
    return surface, invariant_curve, transfer


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
    system = SYSTEMS["sun_earth"]
    surface, lissajous, transfer = _load_numerical_scene(system)
    earth = ((1.0 - system.mu) * system.length_unit_km, 0.0, 0.0)
    arrival = transfer[-1]
    fig = plt.figure(figsize=(6.5, 8.2), constrained_layout=True)
    ax = fig.add_subplot(211, projection="3d")
    plot_surface(ax, surface, alpha=0.46)
    ax.plot(transfer[:, 0], transfer[:, 1], transfer[:, 2], color="#1f8fd4", linewidth=1.2)
    ax.plot(lissajous[:, 0], lissajous[:, 1], lissajous[:, 2], color="#91ad58", linewidth=0.7, alpha=0.70)
    ax.scatter([earth[0]], [earth[1]], [earth[2]], color="black", s=16)
    ax.scatter(*arrival, color="#c9253d", s=18)
    ax.text2D(0.63, 0.52, "Earth", transform=ax.transAxes, fontsize=10)
    ax.text2D(0.27, 0.56, "Arrival\nLocation", transform=ax.transAxes, fontsize=10)
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
    for col in range(0, surface.shape[1], 3):
        ax2.plot(surface[:, col, 0], surface[:, col, 1], color="0.45", linewidth=0.35, alpha=0.22)
    ax2.plot(transfer[:, 0], transfer[:, 1], color="#1f8fd4", linewidth=1.1)
    ax2.plot(lissajous[:, 0], lissajous[:, 1], color="#91ad58", linewidth=0.7, alpha=0.70)
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
