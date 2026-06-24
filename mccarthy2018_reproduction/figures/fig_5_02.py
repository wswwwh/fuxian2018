"""Figure 5.2: Sun-Moon eclipsing geometry."""

from __future__ import annotations

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.2"
SOURCE_PAGE = 98
REPRO_LEVEL = "shape-match"
SYSTEM = "Sun-Moon-spacecraft geometry"


def main() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(8.6, 3.0), constrained_layout=True)
    ax.set_aspect("equal")
    ax.axis("off")

    sun = patches.Circle((0.0, 0.0), 0.78, facecolor="#ffc20a", edgecolor="none")
    moon = patches.Circle((5.6, 0.0), 0.28, facecolor="#7f7f7f", edgecolor="black", linewidth=0.8)
    ax.add_patch(sun)
    ax.add_patch(moon)

    ax.add_patch(patches.Polygon([(5.88, 0.23), (8.35, 0.48), (8.35, -0.48), (5.88, -0.23)],
                                 closed=True, facecolor="#244f9f", alpha=0.90, edgecolor="black", linewidth=0.6))
    ax.add_patch(patches.Polygon([(5.78, 0.18), (7.35, 0.0), (5.78, -0.18)],
                                 closed=True, facecolor="#c94c19", alpha=0.90, edgecolor="black", linewidth=0.6))
    ax.add_patch(patches.Polygon([(7.35, 0.0), (8.35, 0.22), (8.35, -0.22)],
                                 closed=True, facecolor="#4e7c2f", alpha=0.90, edgecolor="black", linewidth=0.6))

    for sign in (-1, 1):
        ax.plot([0.0, 5.6, 8.35], [sign * 0.78, sign * 0.28, sign * 0.48], color="black", linewidth=0.8)
        ax.plot([0.0, 5.6, 8.35], [0.0, sign * 0.28, sign * 0.22], color="black", linewidth=0.8)
    ax.plot([0.0, 8.35], [0.0, 0.0], color="black", linewidth=0.7)

    ax.scatter([6.95], [-0.20], color="black", s=12)
    ax.text(6.82, -0.05, "S/C", fontsize=10)
    ax.text(-0.18, 0.95, "Sun", fontsize=12)
    ax.text(5.36, 0.42, "Moon", fontsize=12)
    ax.annotate(r"$R$", xy=(-0.34, 0.38), xytext=(-0.05, 0.05), arrowprops={"arrowstyle": "-|>", "lw": 1.0})
    ax.annotate(r"$r$", xy=(5.72, 0.14), xytext=(5.45, -0.05), arrowprops={"arrowstyle": "-|>", "lw": 1.0})

    ax.plot([0.0, 0.0], [-0.78, -1.04], color="black", linestyle="--", linewidth=1.1)
    ax.plot([5.6, 5.6], [-0.28, -1.04], color="black", linestyle="--", linewidth=1.1)
    ax.plot([7.35, 7.35], [-0.22, -1.04], color="black", linestyle="--", linewidth=1.1)
    ax.annotate("", xy=(0.0, -1.15), xytext=(5.6, -1.15), arrowprops={"arrowstyle": "-[", "lw": 1.6})
    ax.text(2.65, -1.38, r"$d$", fontsize=12)
    ax.annotate("", xy=(5.6, -1.15), xytext=(7.35, -1.15), arrowprops={"arrowstyle": "-[", "lw": 1.6})
    ax.text(6.40, -1.38, r"$l$", fontsize=12)
    ax.annotate("", xy=(4.95, -0.84), xytext=(5.60, -0.84), arrowprops={"arrowstyle": "-[", "lw": 1.3})
    ax.text(5.20, -1.05, r"$x$", fontsize=12)
    ax.text(5.16, 0.45, r"$\alpha$", fontsize=12)
    ax.text(6.30, 0.62, r"$\theta$", fontsize=12)
    ax.text(6.78, -0.48, r"$\zeta$", fontsize=12)

    ax.set_xlim(-0.65, 8.35)
    ax.set_ylim(-1.55, 1.20)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
