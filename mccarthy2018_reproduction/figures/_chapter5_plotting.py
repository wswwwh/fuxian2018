"""Plotting helpers for Chapter 5 application figures."""

from __future__ import annotations

import numpy as np
from matplotlib.ticker import MaxNLocator, ScalarFormatter

from _figure_paths import PROJECT_ROOT  # noqa: F401  # ensures src is importable for direct helper imports
from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points


def plot_surface(ax, surface: np.ndarray, *, color: str = "#9d9d9d", alpha: float = 0.50) -> None:
    ax.plot_surface(
        surface[:, :, 0],
        surface[:, :, 1],
        surface[:, :, 2],
        color=color,
        edgecolor="none",
        linewidth=0,
        antialiased=True,
        shade=True,
        alpha=alpha,
    )
    ax.plot_wireframe(
        surface[:, :, 0],
        surface[:, :, 1],
        surface[:, :, 2],
        rstride=8,
        cstride=6,
        color="black",
        linewidth=0.20,
        alpha=0.22,
    )


def add_axis_arrow(ax, text: str, *, xy: tuple[float, float], xytext: tuple[float, float], rotation: float = 0.0) -> None:
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        xycoords="axes fraction",
        fontsize=10,
        rotation=rotation,
        arrowprops={"arrowstyle": "-|>", "lw": 1.4, "color": "black"},
    )


def style_sun_earth_l1_axis(ax, *, label: str) -> None:
    system = SYSTEMS["sun_earth"]
    points = compute_libration_points(system.mu)
    earth_x = 1.0 - system.mu
    ax.scatter([points["L1"].x], [0.0], [0.0], color="#7a4635", s=10)
    ax.scatter([earth_x], [0.0], [0.0], color="black", s=8)
    ax.text(points["L1"].x - 0.0006, 0.0005, 0.0, r"$L_1$", fontsize=8)
    ax.text(earth_x - 0.0008, 0.0010, -0.0010, "Earth", fontsize=8)
    ax.text(points["L2"].x + 0.0002, 0.0045, -0.0045, r"$L_2$", fontsize=7)
    ax.set_xlim(0.9860, 1.0004)
    ax.set_ylim(-0.0065, 0.0065)
    ax.set_zlim(-0.0068, 0.0068)
    ax.set_xlabel("X [nd]", labelpad=-7)
    ax.set_ylabel("Y [nd]", labelpad=-6)
    ax.set_zlabel("Z [nd]", labelpad=-6)
    ax.tick_params(labelsize=7, pad=-3)
    ax.view_init(elev=25, azim=-128)
    ax.set_box_aspect((1.0, 1.15, 0.95))
    ax.text2D(0.48, -0.10, label, transform=ax.transAxes, fontsize=12)
    add_axis_arrow(ax, "To Sun", xy=(0.13, 0.13), xytext=(0.30, 0.22), rotation=-26)


def style_moon_km_axis(ax, *, label: str | None = None) -> None:
    ax.scatter([0.0], [0.0], [0.0], color="black", s=8)
    ax.text(-1.6e4, 0.5e4, 0.6e4, "Moon", fontsize=8)
    ax.set_xlim(-1.0e5, 1.0e5)
    ax.set_ylim(-1.0e5, 1.0e5)
    ax.set_zlim(-0.65e5, 0.65e5)
    ax.set_xlabel("X [km]", labelpad=-7)
    ax.set_ylabel("Y [km]", labelpad=-6)
    ax.set_zlabel("Z [km]", labelpad=-6)
    for axis, power in ((ax.xaxis, 5), (ax.yaxis, 5), (ax.zaxis, 4)):
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((power, power))
        axis.set_major_formatter(formatter)
        axis.set_major_locator(MaxNLocator(5))
    ax.tick_params(labelsize=7, pad=-3)
    ax.view_init(elev=23, azim=-48)
    ax.set_box_aspect((1.20, 1.20, 0.80))
    add_axis_arrow(ax, "To Sun", xy=(0.09, 0.13), xytext=(0.25, 0.20), rotation=-27)
    if label is not None:
        ax.text2D(0.48, -0.10, label, transform=ax.transAxes, fontsize=12)


def plot_de421_dro_scene(ax, scene) -> None:
    shadow = scene.shadow_surface_km
    ax.plot_surface(
        shadow[:, :, 0],
        shadow[:, :, 1],
        shadow[:, :, 2],
        color="#777777",
        edgecolor="none",
        linewidth=0.0,
        alpha=0.42,
        shade=True,
    )
    ax.plot(
        scene.points_km[:, 0],
        scene.points_km[:, 1],
        scene.points_km[:, 2],
        color="#1787d4",
        linewidth=0.95,
    )
    ax.scatter(*scene.marker_km, color="#e85d24", s=16, depthshade=False)


def style_earth_moon_dro_axis(ax) -> None:
    system = SYSTEMS["earth_moon"]
    points = compute_libration_points(system.mu)
    moon_x = 1.0 - system.mu
    ax.scatter([moon_x], [0.0], [0.0], color="black", s=12)
    ax.text(moon_x - 0.010, 0.012, 0.006, "Moon", fontsize=9)
    ax.scatter([points["L1"].x, points["L2"].x], [0.0, 0.0], [0.0, 0.0], color="#777777", s=8)
    ax.text(points["L1"].x + 0.006, 0.010, 0.0, r"$L_1$", fontsize=9)
    ax.text(points["L2"].x - 0.030, 0.010, 0.0, r"$L_2$", fontsize=9)
    ax.set_xlim(0.76, 1.22)
    ax.set_ylim(-0.32, 0.30)
    ax.set_zlim(-0.11, 0.11)
    ax.set_xlabel("X [nd]", labelpad=-8)
    ax.set_ylabel("Y [nd]", labelpad=-6)
    ax.set_zlabel("Z [nd]", labelpad=-7)
    ax.tick_params(labelsize=8, pad=-3)
    ax.view_init(elev=24, azim=-132)
    ax.set_box_aspect((1.35, 1.70, 0.85))
    add_axis_arrow(ax, "To Earth", xy=(0.18, 0.13), xytext=(0.36, 0.22), rotation=-28)


def style_nrho_axis(ax, *, label: str | None = None, wide: bool = False) -> None:
    system = SYSTEMS["earth_moon"]
    moon_x = 1.0 - system.mu
    ax.scatter([moon_x], [0.0], [-0.025], color="black", s=14)
    ax.text(moon_x - 0.010, -0.010, -0.018, "Moon", fontsize=9)
    ax.set_xlim(0.965, 1.105 if wide else 1.085)
    ax.set_ylim(-0.115, 0.105)
    ax.set_zlim(-0.055, 0.225)
    ax.set_xlabel("X [nd]", labelpad=-8)
    ax.set_ylabel("Y [nd]", labelpad=-6)
    ax.set_zlabel("Z [nd]", labelpad=-7)
    ax.tick_params(labelsize=8, pad=-3)
    ax.view_init(elev=20, azim=-58)
    ax.set_box_aspect((0.80, 1.0, 1.45))
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis._axinfo["grid"]["color"] = (0.88, 0.88, 0.88, 0.48)
        axis._axinfo["grid"]["linewidth"] = 0.38
    add_axis_arrow(ax, "To Earth", xy=(0.44, 0.12), xytext=(0.60, 0.19), rotation=-22)
    if label is not None:
        ax.text2D(0.48, -0.10, label, transform=ax.transAxes, fontsize=12)


def plot_nrho_scene(ax, scene, *, show_surface: bool = False, annotate: bool = True) -> None:
    if show_surface and scene.surface is not None:
        plot_surface(ax, scene.surface, alpha=0.45)
    ax.plot(scene.destination[:, 0], scene.destination[:, 1], scene.destination[:, 2], color="#c9253d", linewidth=1.2)
    ax.plot(scene.departure[:, 0], scene.departure[:, 1], scene.departure[:, 2], color="#1f77b4", linewidth=1.2)
    colors = ["#78a641", "#78a641", "#8fbf4f", "#a5c96a"]
    for idx, arc in enumerate(scene.transfer_arcs):
        ax.plot(arc[:, 0], arc[:, 1], arc[:, 2], color=colors[idx % len(colors)], linewidth=1.0)
    if scene.departure_location is not None:
        ax.scatter(*scene.departure_location, color="#1f77b4", s=16)
    if scene.arrival_location is not None:
        ax.scatter(*scene.arrival_location, color="#c9253d", s=16)
    if annotate and scene.departure_location is not None and scene.arrival_location is not None:
        ax.text(scene.departure_location[0] + 0.006, scene.departure_location[1], scene.departure_location[2] + 0.020,
                "Departure\nLocation", fontsize=8)
        ax.text(scene.arrival_location[0] - 0.018, scene.arrival_location[1], scene.arrival_location[2] + 0.010,
                "Arrival\nLocation", fontsize=8)
