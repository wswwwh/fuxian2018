"""Figure 3.11: Poincare map and central periodic orbits."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import central_periodic_orbit_scene


FIGURE_ID = "3.11"
SOURCE_PAGE = 73
REPRO_LEVEL = "shape-match"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected CR3BP central periodic orbits with section-anchored Poincare island contours."


def style_map_axis(ax) -> None:
    ax.set_xlim(0.800, 0.900)
    ax.set_ylim(-0.115, 0.120)
    ax.set_xlabel("X [nd]")
    ax.set_ylabel("Y [nd]")
    ax.set_aspect("equal", adjustable="box")
    ax.tick_params(labelsize=8)
    ax.annotate(
        "Lyapunov\nOrbit",
        xy=(0.823, 0.070),
        xytext=(0.803, 0.107),
        arrowprops={"arrowstyle": "->", "lw": 1.0},
        fontsize=8,
    )
    ax.annotate(
        "Central Halo\nOrbit",
        xy=(0.858, 0.081),
        xytext=(0.906, 0.036),
        arrowprops={"arrowstyle": "->", "lw": 1.0},
        fontsize=8,
    )
    ax.annotate(
        "Central\nVertical Orbit",
        xy=(0.837, 0.0),
        xytext=(0.876, -0.045),
        arrowprops={"arrowstyle": "->", "lw": 1.0},
        fontsize=8,
    )
    ax.annotate("", xy=(0.805, -0.103), xytext=(0.835, -0.103), arrowprops={"arrowstyle": "-|>", "lw": 1.1})
    ax.annotate("", xy=(0.895, -0.103), xytext=(0.865, -0.103), arrowprops={"arrowstyle": "-|>", "lw": 1.1})
    ax.text(0.812, -0.095, "To\nEarth", ha="center", va="top", fontsize=8)
    ax.text(0.888, -0.095, "To\nMoon", ha="center", va="top", fontsize=8)


def style_3d_axis(ax) -> None:
    points = compute_libration_points(SYSTEMS["earth_moon"].mu)
    ax.scatter([points["L1"].x], [0.0], [0.0], color="#cc4c25", s=10)
    ax.set_xlim(0.80, 0.92)
    ax.set_ylim(-0.12, 0.12)
    ax.set_zlim(-0.12, 0.12)
    ax.set_xlabel("X [nd]", labelpad=-5)
    ax.set_ylabel("Y [nd]", labelpad=-5)
    ax.set_zlabel("Z [nd]", labelpad=-5)
    ax.tick_params(labelsize=8, pad=-2)
    ax.view_init(elev=22, azim=-122)
    ax.set_box_aspect((1.0, 1.5, 1.35))
    ax.annotate(
        "To Earth",
        xy=(0.12, 0.10),
        xytext=(0.28, 0.17),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "lw": 1.2},
        fontsize=8,
    )


def main() -> None:
    apply_style()
    scene = central_periodic_orbit_scene(SYSTEMS["earth_moon"].mu)

    fig = plt.figure(figsize=(8.7, 4.5), constrained_layout=True)
    gs = GridSpec(1, 2, width_ratios=[0.82, 1.18], figure=fig)
    ax_map = fig.add_subplot(gs[0, 0])
    ax_3d = fig.add_subplot(gs[0, 1], projection="3d")

    for curve in scene.map_halo_upper:
        ax_map.plot(curve[:, 0], curve[:, 1], color="#b2182b", linewidth=0.8)
    for curve in scene.map_halo_lower:
        ax_map.plot(curve[:, 0], curve[:, 1], color="#b2182b", linewidth=0.8)
    for curve in scene.map_lyapunov:
        ax_map.plot(curve[:, 0], curve[:, 1], color="#168bd2", linewidth=0.75)
    ax_map.scatter(
        [scene.vertical_section_center[0]],
        [scene.vertical_section_center[1]],
        color="#168bd2",
        s=12,
        zorder=3,
    )
    style_map_axis(ax_map)

    for orbit in scene.lyapunov_orbits:
        ax_3d.plot(orbit[:, 0], orbit[:, 1], orbit[:, 2], color="#168bd2", linewidth=0.55, alpha=0.78)
    for curve in scene.map_halo_upper:
        ax_3d.plot(curve[:, 0], curve[:, 1], curve[:, 0] * 0.0, color="#b2182b", linewidth=0.55, alpha=0.82)
    for curve in scene.map_halo_lower:
        ax_3d.plot(curve[:, 0], curve[:, 1], curve[:, 0] * 0.0, color="#b2182b", linewidth=0.55, alpha=0.82)
    ax_3d.plot(
        scene.halo_orbit[:, 0],
        scene.halo_orbit[:, 1],
        scene.halo_orbit[:, 2],
        color="#b2182b",
        linewidth=1.2,
    )
    ax_3d.plot(
        scene.vertical_orbit[:, 0],
        scene.vertical_orbit[:, 1],
        scene.vertical_orbit[:, 2],
        color="#168bd2",
        linewidth=1.2,
    )
    style_3d_axis(ax_3d)

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
