"""Figure 5.3: Earth-Moon-spacecraft line-of-sight geometry."""

from __future__ import annotations

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.3"
SOURCE_PAGE = 100
REPRO_LEVEL = "shape-match"
SYSTEM = "Earth-Moon-spacecraft geometry"


def main() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(8.6, 2.7), constrained_layout=True)
    ax.set_aspect("equal")
    ax.axis("off")

    earth = patches.Circle((0.0, 0.0), 0.55, facecolor="#4774c4", edgecolor="none")
    moon = patches.Circle((4.0, 0.0), 0.22, facecolor="#8a8a8a", edgecolor="black", linewidth=0.8)
    ax.add_patch(earth)
    ax.add_patch(moon)
    ax.add_patch(patches.Polygon([(4.20, 0.20), (8.9, 0.52), (8.9, -0.52), (4.20, -0.20)],
                                 facecolor="#d70000", edgecolor="black", alpha=0.92))
    ax.plot([0.0, 8.9], [0.0, 0.0], color="black", linewidth=0.9)
    ax.plot([0.0, 4.0, 5.55], [0.0, 0.22, -0.42], color="black", linewidth=0.9)
    ax.plot([0.0, 4.0], [0.0, -0.22], color="black", linewidth=0.9)
    ax.scatter([5.55], [-0.42], color="black", s=13)

    ax.text(-0.15, 0.65, "Earth", fontsize=12)
    ax.text(3.74, 0.38, "Moon", fontsize=12)
    ax.text(5.42, -0.60, "S/C", fontsize=11)
    ax.text(3.86, 0.17, r"$R_M$", fontsize=10)

    ax.plot([0.0, 0.0], [-0.55, -1.02], color="black", linestyle="--", linewidth=1.0)
    ax.plot([4.0, 4.0], [-0.22, -1.02], color="black", linestyle="--", linewidth=1.0)
    ax.annotate("", xy=(0.0, -1.10), xytext=(4.0, -1.10), arrowprops={"arrowstyle": "-[", "lw": 1.6})
    ax.text(1.90, -1.33, r"$L$", fontsize=12)
    ax.annotate(r"$\eta$", xy=(1.55, 0.08), xytext=(1.90, -0.42),
                arrowprops={"arrowstyle": "->", "lw": 1.0}, fontsize=12)
    ax.annotate(r"$\beta$", xy=(2.35, 0.12), xytext=(2.85, -0.38),
                arrowprops={"arrowstyle": "->", "lw": 1.0}, fontsize=12)

    ax.set_xlim(-0.65, 8.9)
    ax.set_ylim(-1.42, 0.90)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
