"""Figure 2.5: conceptual Earth-Moon rotating-frame zero-velocity surface."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.5"
SOURCE_PAGE = 17
REPRO_LEVEL = "shape-match"
SYSTEM = "Earth-Moon CR3BP"


def main() -> None:
    apply_style()
    mu = SYSTEMS["earth_moon"].mu
    points = compute_libration_points(mu)

    theta = np.linspace(0.0, 2.0 * np.pi, 96)
    z = np.linspace(-0.95, 0.95, 70)
    th_grid, z_grid = np.meshgrid(theta, z)

    radius_outer = 1.05 - 0.36 * np.exp(-(z_grid / 0.24) ** 2)
    x_outer = radius_outer * np.cos(th_grid) - 0.05
    y_outer = radius_outer * np.sin(th_grid)
    radius_inner = 0.48 + 0.06 * np.cos(np.pi * z_grid / 0.95)
    x_inner = radius_inner * np.cos(th_grid) - 0.12
    y_inner = radius_inner * np.sin(th_grid)

    fig = plt.figure(figsize=(7.1, 5.2))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(x_outer, y_outer, z_grid, color="#d95f5f", alpha=0.33, linewidth=0, shade=True)
    ax.plot_surface(x_inner, y_inner, z_grid * 0.72, color="#9c1f1f", alpha=0.55, linewidth=0, shade=True)

    earth = (-mu, 0.0, 0.0)
    moon = (1.0 - mu, 0.0, 0.0)
    ax.scatter([earth[0]], [earth[1]], [earth[2]], color="black", s=18)
    ax.scatter([moon[0]], [moon[1]], [moon[2]], color="tab:blue", s=28)
    ax.scatter(
        [points["L1"].x, points["L2"].x, points["L3"].x],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        color="tab:red",
        s=14,
    )
    ax.text(points["L1"].x + 0.05, 0.02, -0.13, r"$L_1$", fontsize=11)
    ax.text(points["L2"].x - 0.02, 0.02, 0.12, r"$L_2$", fontsize=11)
    ax.text(points["L3"].x - 0.03, 0.02, 0.08, r"$L_3$", fontsize=11)

    ax.text(-0.45, -0.08, 0.48, "Interior\nRegion", fontsize=10, ha="center")
    ax.text(1.1, 0.7, -0.18, "Exterior\nRegion", fontsize=10)
    ax.text(-0.78, -0.72, 0.38, "Earth", fontsize=9)
    ax.text(1.08, 0.2, 0.2, "Moon", fontsize=9)
    ax.plot([-0.5, earth[0]], [-0.65, earth[1]], [0.33, earth[2]], color="black", linewidth=1.0)
    ax.plot([1.08, moon[0]], [0.14, moon[1]], [0.07, moon[2]], color="black", linewidth=1.0)

    ax.set_xlabel("X [nd]", labelpad=-2)
    ax.set_ylabel("Y [nd]", labelpad=-2)
    ax.set_zlabel("Z [nd]", labelpad=-6)
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.15, 1.15)
    ax.set_zlim(-1.0, 1.0)
    ax.set_xticks([-1, 0, 1])
    ax.set_yticks([-1, 0, 1])
    ax.set_zticks([-0.5, 0, 0.5])
    ax.view_init(elev=24, azim=-42)
    ax.set_box_aspect((1.2, 1.2, 0.8))
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
