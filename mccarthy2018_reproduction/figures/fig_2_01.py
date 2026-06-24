"""Figure 2.1: three-body geometry and reference frames."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.1"
SOURCE_PAGE = 8
REPRO_LEVEL = "shape-match"


def arrow(ax, start, end, **kwargs) -> None:
    kwargs.setdefault("linewidth", 1.6)
    patch = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=16, **kwargs)
    ax.add_patch(patch)


def main() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(6.1, 5.4))
    ax.grid(False)
    ax.set_aspect("equal")
    ax.axis("off")

    barycenter = np.array([0.0, 0.0])
    p1 = np.array([-0.9, 0.0])
    p2 = np.array([3.2, 0.0])
    p3 = np.array([1.7, 1.35])

    ax.scatter(*p1, s=580, color="#4b78c2", zorder=4)
    ax.scatter(*p2, s=95, color="#4b78c2", zorder=4)
    ax.scatter(*p3, s=28, color="black", zorder=5)
    ax.scatter(*barycenter, s=38, color="black", zorder=6)

    arrow(ax, barycenter, (3.75, 0.0), color="black", linewidth=2.0)
    arrow(ax, barycenter, (0.0, 3.2), color="black", linewidth=2.0)
    arrow(ax, barycenter, (2.0, 2.75), color="black", linewidth=2.0)
    arrow(ax, barycenter, (2.95, -1.9), color="black", linewidth=2.0)

    ax.plot([p1[0], p2[0]], [0.0, 0.0], color="black", linewidth=1.2)
    ax.plot([p2[0], p3[0]], [p2[1], p3[1]], color="black", linewidth=1.1)
    ax.plot([barycenter[0], p3[0]], [barycenter[1], p3[1]], color="black", linewidth=1.1)
    ax.plot([p1[0], p3[0]], [p1[1], p3[1]], color="black", linewidth=1.1)

    theta_arc = Arc((0, 0), 0.95, 0.95, angle=0, theta1=-42, theta2=0, color="#4b78c2", linewidth=1.5)
    ax.add_patch(theta_arc)
    arrow(ax, (0.42, -0.22), (0.47, -0.03), color="#4b78c2", linewidth=1.2)

    ax.text(3.78, -0.12, r"$\hat{x}$", fontsize=18)
    ax.text(0.05, 3.18, r"$\hat{y}$", fontsize=18)
    ax.text(2.02, 2.78, r"$\hat{Y}$", fontsize=17)
    ax.text(2.92, -2.1, r"$\hat{X}$", fontsize=17)
    ax.text(-1.3, -0.42, r"$P_1$", fontsize=15)
    ax.text(3.17, -0.32, r"$P_2$", fontsize=15)
    ax.text(1.62, 1.55, r"$P_3$", fontsize=15)
    ax.text(-0.23, 0.09, r"$B$", fontsize=15)
    ax.text(-0.55, -0.28, r"$D_1$", fontsize=15)
    ax.text(1.35, -0.25, r"$D_2$", fontsize=15)
    ax.text(0.52, 0.72, r"$\vec{D}$", fontsize=17)
    ax.text(1.0, 0.55, r"$\vec{P}$", fontsize=17)
    ax.text(2.45, 0.82, r"$\vec{R}$", fontsize=17)
    ax.text(0.56, -0.28, r"$\theta$", fontsize=17)

    ax.set_xlim(-1.45, 3.95)
    ax.set_ylim(-2.25, 3.45)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
