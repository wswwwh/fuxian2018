"""Figure 2.6: ZVC comparison for three CR3BP systems."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import zero_velocity_grid
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.6"
SOURCE_PAGE = 18
REPRO_LEVEL = "shape-match + physical-consistency"


SYSTEM_ORDER = ["earth_moon", "saturn_titan", "sun_earth"]


def _plot_zvc(
    ax,
    key: str,
    *,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    n: int = 520,
    label_bodies: bool = True,
) -> None:
    system = SYSTEMS[key]
    points = compute_libration_points(system.mu)
    jc = 0.5 * (points["L1"].jacobi + points["L2"].jacobi)

    x_grid, y_grid, c_grid = zero_velocity_grid(system.mu, xlim, ylim, n=n)
    forbidden = c_grid < jc
    ax.contourf(x_grid, y_grid, forbidden, levels=[0.5, 1.5], colors=["0.72"], alpha=0.95)
    ax.contour(x_grid, y_grid, c_grid, levels=[jc], colors="black", linewidths=1.0)

    primary_x = -system.mu
    secondary_x = 1.0 - system.mu
    primary_size = 28 if key != "sun_earth" else 18
    secondary_size = 18 if key != "sun_earth" else 9
    ax.scatter([primary_x], [0.0], s=primary_size, color="0.35", zorder=5)
    ax.scatter([secondary_x], [0.0], s=secondary_size, color="0.15", zorder=6)
    ax.scatter([points["L1"].x, points["L2"].x], [0.0, 0.0], s=10, color="black", zorder=6)

    if label_bodies:
        ax.text(primary_x - 0.13, -0.02, system.primary, fontsize=8, ha="right", va="center")
        ax.text(secondary_x + 0.05, 0.08, system.secondary, fontsize=8, ha="left", va="center")
        ax.text(points["L1"].x - 0.09, 0.08, r"$L_1$", fontsize=8)
        ax.text(points["L2"].x + 0.03, -0.08, r"$L_2$", fontsize=8)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel("X [nd]")
    ax.set_ylabel("Y [nd]")
    ax.set_title(f"{system.name} System", fontsize=10, pad=6)
    ax.grid(False)


def main() -> None:
    apply_style()
    fig = plt.figure(figsize=(8.6, 7.1))
    ax_em = fig.add_axes([0.08, 0.57, 0.38, 0.35])
    ax_st = fig.add_axes([0.55, 0.57, 0.38, 0.35])
    ax_se = fig.add_axes([0.18, 0.09, 0.42, 0.36])

    _plot_zvc(ax_em, "earth_moon", xlim=(-1.55, 1.55), ylim=(-1.20, 1.20), n=620)
    _plot_zvc(ax_st, "saturn_titan", xlim=(-1.25, 1.25), ylim=(-1.05, 1.05), n=620)
    _plot_zvc(ax_se, "sun_earth", xlim=(-1.30, 1.30), ylim=(-1.05, 1.05), n=700)

    ax_em.text(0.50, -0.24, "(a)", transform=ax_em.transAxes, ha="center", va="top", fontsize=11)
    ax_st.text(0.50, -0.24, "(b)", transform=ax_st.transAxes, ha="center", va="top", fontsize=11)
    ax_se.text(0.50, -0.25, "(c)", transform=ax_se.transAxes, ha="center", va="top", fontsize=11)

    zoom = Rectangle((0.94, -0.055), 0.12, 0.11, fill=False, edgecolor="0.25", linewidth=0.8)
    ax_se.add_patch(zoom)
    inset = fig.add_axes([0.62, 0.21, 0.22, 0.18])
    _plot_zvc(inset, "sun_earth", xlim=(0.986, 1.014), ylim=(-0.020, 0.020), n=520, label_bodies=False)
    points = compute_libration_points(SYSTEMS["sun_earth"].mu)
    earth_x = 1.0 - SYSTEMS["sun_earth"].mu
    inset.text(earth_x, -0.0025, "Earth", fontsize=7, ha="center", va="top")
    inset.text(points["L1"].x - 0.0005, 0.003, r"$L_1$", fontsize=7, ha="right")
    inset.text(points["L2"].x + 0.0005, -0.003, r"$L_2$", fontsize=7, ha="left")
    inset.set_xlabel("")
    inset.set_ylabel("")
    inset.tick_params(labelsize=6, pad=1)

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
