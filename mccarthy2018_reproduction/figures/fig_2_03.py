"""Figure 2.3: CR3BP libration-point geometry."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.3"
SOURCE_PAGE = 14
REPRO_LEVEL = "shape-match schematic"
SYSTEM = "Generic CR3BP geometry"


def main() -> None:
    apply_style()
    p1 = (0.0, 0.0)
    p2 = (1.52, 0.0)
    l1 = (1.14, 0.0)
    l2 = (1.88, 0.0)
    l3 = (-1.70, 0.0)
    l4 = (0.76, 1.36)
    l5 = (0.76, -1.36)

    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    ax.annotate("", xy=(2.15, 0.0), xytext=(-1.88, 0.0), arrowprops={"arrowstyle": "->", "lw": 1.8})
    ax.annotate("", xy=(0.0, 1.70), xytext=(0.0, -1.52), arrowprops={"arrowstyle": "->", "lw": 1.8})

    ax.plot([p1[0], l4[0], p2[0], l5[0], p1[0]], [p1[1], l4[1], p2[1], l5[1], p1[1]],
            color="0.20", linestyle=":", linewidth=1.25)
    ax.add_patch(Circle(p1, 0.18, facecolor="#4a78c7", edgecolor="#4a78c7", zorder=4))
    ax.add_patch(Circle(p2, 0.075, facecolor="#4a78c7", edgecolor="#4a78c7", zorder=4))

    for point in (l1, l2, l3, l4, l5):
        ax.plot(*point, "ko", markersize=4.4, zorder=5)

    ax.text(p1[0] - 0.35, p1[1] + 0.20, r"$P_1$", fontsize=16)
    ax.text(p2[0] + 0.03, p2[1] + 0.16, r"$P_2$", fontsize=16)
    ax.text(l1[0] - 0.04, l1[1] - 0.23, r"$L_1$", fontsize=16)
    ax.text(l2[0] - 0.02, l2[1] - 0.23, r"$L_2$", fontsize=16)
    ax.text(l3[0] - 0.02, l3[1] - 0.23, r"$L_3$", fontsize=16)
    ax.text(l4[0] + 0.08, l4[1] + 0.02, r"$L_4$", fontsize=16)
    ax.text(l5[0] + 0.08, l5[1] - 0.15, r"$L_5$", fontsize=16)
    ax.text(2.15, -0.12, r"$\hat{x}$", fontsize=17)
    ax.text(-0.15, 1.67, r"$\hat{y}$", fontsize=17)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.90, 2.24)
    ax.set_ylim(-1.55, 1.78)
    ax.axis("off")
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
