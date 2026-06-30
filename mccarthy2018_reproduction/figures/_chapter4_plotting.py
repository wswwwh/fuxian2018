"""Plotting helpers for Chapter 4 stability/manifold figures."""

from __future__ import annotations

import numpy as np

from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.torus_stability import (
    corrected_curve_unstable_manifold,
    corrected_vertical_curve_unstable_manifold,
)


def plot_torus_wire(ax, member, color: str = "black", alpha: float = 0.55, linewidth: float = 0.45) -> None:
    surface = member.surface
    ax.plot_wireframe(
        surface[:, :, 0],
        surface[:, :, 1],
        surface[:, :, 2],
        rstride=4,
        cstride=2,
        color=color,
        linewidth=linewidth,
        alpha=alpha,
    )
    curve = member.invariant_curve
    ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], color=color, linewidth=1.0, alpha=0.8)


def plot_sheet(ax, sheet, color: str = "#c9253d", alpha: float = 0.42) -> None:
    surface = sheet.surface
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


def plot_sheet_wire(
    ax,
    sheet,
    *,
    color: str = "#b2182b",
    alpha: float = 0.82,
    linewidth: float = 0.34,
    curve_stride: int = 2,
    time_stride: int = 4,
) -> None:
    surface = sheet.surface
    ax.plot_wireframe(
        surface[:, :, 0],
        surface[:, :, 1],
        surface[:, :, 2],
        rstride=max(1, time_stride),
        cstride=max(1, curve_stride),
        color=color,
        linewidth=linewidth,
        alpha=0.45,
    )
    for curve_idx in range(0, surface.shape[1], max(1, curve_stride)):
        ax.plot(
            surface[:, curve_idx, 0],
            surface[:, curve_idx, 1],
            surface[:, curve_idx, 2],
            color=color,
            linewidth=linewidth,
            alpha=alpha,
        )
    for time_idx in range(0, surface.shape[0], max(1, time_stride)):
        ax.plot(
            surface[time_idx, :, 0],
            surface[time_idx, :, 1],
            surface[time_idx, :, 2],
            color=color,
            linewidth=0.24,
            alpha=0.52,
        )


def plot_corrected_manifold_stage(
    ax,
    sheet,
    *,
    elapsed_days: float,
    color: str = "#16834f",
) -> None:
    """Overlay a finite-amplitude corrected DG manifold through one snapshot."""

    system = SYSTEMS["earth_moon"]
    elapsed_time = elapsed_days / (system.time_unit_days or 1.0)
    stop = int(np.searchsorted(sheet.times, elapsed_time, side="right"))
    surface = sheet.surface[: max(stop, 2)]
    ax.plot_surface(
        surface[:, :, 0],
        surface[:, :, 1],
        surface[:, :, 2],
        color=color,
        edgecolor="none",
        linewidth=0,
        shade=False,
        alpha=0.22,
    )
    for curve_idx in range(surface.shape[1]):
        ax.plot(
            surface[:, curve_idx, 0],
            surface[:, curve_idx, 1],
            surface[:, curve_idx, 2],
            color=color,
            linewidth=0.75,
            alpha=0.88,
        )
    ax.plot_wireframe(
        surface[:, :, 0],
        surface[:, :, 1],
        surface[:, :, 2],
        rstride=3,
        cstride=5,
        color="black",
        linewidth=0.22,
        alpha=0.42,
    )


def _plot_corrected_local_growth_inset(ax, sheet, bounds=(0.56, 0.60, 0.36, 0.28)) -> None:
    system = SYSTEMS["earth_moon"]
    time_ratio = sheet.times / sheet.dg.correction.seed.orbit_period
    mean_separation_km = np.mean(sheet.position_separation_norms, axis=1) * (system.length_unit_km or 1.0)

    inset = ax.inset_axes(bounds)
    inset.plot(time_ratio, mean_separation_km, color="#2ca25f", linewidth=1.0)
    inset.set_yscale("log")
    inset.set_xlabel(r"$t/T$", fontsize=5.5, labelpad=0)
    inset.set_ylabel(r"$\Delta r$ [km]", fontsize=5.5, labelpad=0)
    inset.tick_params(labelsize=5.5, pad=1)
    inset.grid(True, alpha=0.20)


def add_corrected_local_growth_inset(ax, *, perturbation_sign: float = 1.0) -> None:
    """Add a compact diagnostic for the corrected local quasi-halo manifold."""

    system = SYSTEMS["earth_moon"]
    sheet = corrected_curve_unstable_manifold(
        system.mu,
        samples=9,
        time_samples=18,
        perturbation_sign=perturbation_sign,
    )
    _plot_corrected_local_growth_inset(ax, sheet)


def add_corrected_vertical_local_growth_inset(
    ax,
    *,
    perturbation_sign: float = 1.0,
    bounds=(0.56, 0.60, 0.36, 0.28),
) -> None:
    """Add a compact diagnostic for the corrected local quasi-vertical manifold."""

    system = SYSTEMS["earth_moon"]
    sheet = corrected_vertical_curve_unstable_manifold(
        system.mu,
        samples=9,
        time_samples=18,
        perturbation_sign=perturbation_sign,
    )
    _plot_corrected_local_growth_inset(ax, sheet, bounds=bounds)


def add_earth_moon_labels(ax, *, include_l1: bool = True, include_l2: bool = True, text_scale: float = 1.0) -> None:
    system = SYSTEMS["earth_moon"]
    points = compute_libration_points(system.mu)
    moon_x = 1.0 - system.mu
    ax.scatter([moon_x], [0.0], [0.0], color="black", s=12)
    ax.text(moon_x - 0.014, -0.012, 0.0, "Moon", fontsize=9 * text_scale)
    if include_l1:
        ax.scatter([points["L1"].x], [0.0], [0.0], color="#cc4c25", s=10)
        ax.text(points["L1"].x + 0.006, 0.004, 0.0, r"$L_1$", fontsize=9 * text_scale)
    if include_l2:
        ax.scatter([points["L2"].x], [0.0], [0.0], color="#d9a300", s=10)
        ax.text(points["L2"].x - 0.020, 0.006, 0.0, r"$L_2$", fontsize=8 * text_scale)


def add_to_earth_arrow(ax, xy=(0.16, 0.14), xytext=(0.34, 0.23), rotation=-25) -> None:
    ax.annotate(
        "To Earth",
        xy=xy,
        xytext=xytext,
        xycoords="axes fraction",
        fontsize=10,
        rotation=rotation,
        arrowprops={"arrowstyle": "-|>", "lw": 1.4, "color": "black"},
    )


def style_manifold_axis(ax, *, direction: str = "plus", compact: bool = False) -> None:
    if direction == "plus":
        ax.set_xlim(0.78, 1.17)
        ax.set_ylim(-0.15, 0.15)
        ax.set_zlim(-0.12, 0.12)
        ax.view_init(elev=24, azim=-132)
        ax.set_box_aspect((1.15, 1.20, 0.9))
        add_to_earth_arrow(ax, xy=(0.14, 0.11), xytext=(0.34, 0.20), rotation=-28)
    else:
        ax.set_xlim(0.18, 1.04)
        ax.set_ylim(-0.04, 0.40)
        ax.set_zlim(-0.14, 0.14)
        ax.view_init(elev=20, azim=-52)
        ax.set_box_aspect((1.7, 1.05, 0.75))
        add_to_earth_arrow(ax, xy=(0.27, 0.71), xytext=(0.41, 0.79), rotation=-24)

    if compact:
        ax.tick_params(labelsize=7, pad=-2)
    else:
        ax.tick_params(labelsize=8, pad=-2)
    ax.set_xlabel("X [nd]", labelpad=0)
    ax.set_ylabel("Y [nd]", labelpad=-5)
    ax.set_zlabel("Z [nd]", labelpad=-6)


def style_long_axis(ax, *, vertical: bool = False) -> None:
    ax.set_xlim(0.16, 1.16)
    ax.set_ylim(-0.03, 0.33)
    ax.set_zlim(-0.13, 0.13)
    ax.view_init(elev=17, azim=-62 if not vertical else -70)
    ax.set_box_aspect((2.2, 0.95, 0.55))
    ax.set_xlabel("X [nd]", labelpad=-6)
    ax.set_ylabel("Y [nd]", labelpad=-5)
    ax.set_zlabel("Z [nd]", labelpad=-6)
    ax.tick_params(labelsize=8, pad=-2)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis._axinfo["grid"]["color"] = (0.88, 0.88, 0.88, 0.42)
        axis._axinfo["grid"]["linewidth"] = 0.35
    ax.annotate(
        "",
        xy=(0.26, 0.28),
        xytext=(0.40, 0.38),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "lw": 1.4, "color": "black"},
    )
    ax.text2D(0.24, 0.25, "To Earth", transform=ax.transAxes, fontsize=9, rotation=-24)
