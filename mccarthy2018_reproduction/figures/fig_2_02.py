"""Figure 2.2: collinear libration point distance geometry."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.2"
SOURCE_PAGE = 14
REPRO_LEVEL = "shape-match"


def arrow(ax, start, end, **kwargs) -> None:
    kwargs.setdefault("linewidth", 1.8)
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=15, **kwargs))


def bracket(ax, x0: float, x1: float, y: float, label: str) -> None:
    ax.plot([x0, x1], [y, y], color="black", linewidth=1.2)
    ax.plot([x0, x0], [y - 0.07, y + 0.07], color="black", linewidth=1.2)
    ax.plot([x1, x1], [y - 0.07, y + 0.07], color="black", linewidth=1.2)
    ax.text((x0 + x1) / 2.0, y - 0.22, label, ha="center", va="top", fontsize=13)


def main() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(7.2, 2.2))
    ax.grid(False)
    ax.set_aspect("equal")
    ax.axis("off")

    p1_x = -0.55
    p2_x = 3.15
    arrow(ax, (-2.0, 0.0), (4.15, 0.0), color="black", linewidth=2.0)
    arrow(ax, (0.0, -0.05), (0.0, 0.85), color="black", linewidth=2.0)

    ax.scatter([p1_x], [0.0], s=560, color="#4b78c2", zorder=5)
    ax.scatter([p2_x], [0.0], s=55, color="#4b78c2", zorder=5)
    ax.text(p1_x - 0.22, 0.26, r"$P_1$", fontsize=14)
    ax.text(p2_x - 0.06, 0.18, r"$P_2$", fontsize=14)
    ax.text(4.2, -0.08, r"$\hat{x}$", fontsize=18)
    ax.text(-0.12, 0.92, r"$\hat{y}$", fontsize=18)

    bracket(ax, -1.95, p1_x, -0.28, r"$\gamma_3$")
    bracket(ax, 2.25, p2_x, -0.28, r"$\gamma_1$")
    bracket(ax, p2_x, 4.0, -0.28, r"$\gamma_2$")

    ax.set_xlim(-2.1, 4.3)
    ax.set_ylim(-0.65, 1.05)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
