"""Figure 3.4: patch curves on a torus for multiple shooting."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _torus_schematic import clean_torus_axes, plot_torus, section_circle, section_disk
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "3.4"
SOURCE_PAGE = 62
REPRO_LEVEL = "shape-match"


def add_patch_curve(ax, u0: float, color: str) -> None:
    dx, dy, dz = section_disk(u0)
    ax.plot_surface(dx, dy, dz, color="#d7d7d7", edgecolor="#444444", linewidth=0.25, alpha=0.42, shade=False)
    cx, cy, cz = section_circle(u0, scale=1.04)
    ax.plot(cx, cy, cz, color=color, linewidth=2.0)


def main() -> None:
    apply_style()
    fig = plt.figure(figsize=(6.6, 4.25))
    ax = fig.add_subplot(111, projection="3d")
    clean_torus_axes(ax)
    plot_torus(ax, alpha=0.43)

    add_patch_curve(ax, -0.35, "#1f77b4")
    add_patch_curve(ax, 0.92, "#9b1b3d")
    add_patch_curve(ax, 2.28, "#9b1b3d")
    add_patch_curve(ax, 4.05, "#9b1b3d")

    ax.annotate(
        "Patch Curve III",
        xy=(0.26, 0.74),
        xytext=(0.02, 0.88),
        xycoords="axes fraction",
        fontsize=13,
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": "black"},
    )
    ax.annotate(
        "Patch Curve II",
        xy=(0.72, 0.72),
        xytext=(0.76, 0.89),
        xycoords="axes fraction",
        fontsize=13,
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": "black"},
    )
    ax.annotate(
        "Patch Curve IV",
        xy=(0.24, 0.30),
        xytext=(0.02, 0.10),
        xycoords="axes fraction",
        fontsize=13,
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": "black"},
    )
    ax.annotate(
        "Initial Invariant Curve\n(Patch Curve I)",
        xy=(0.76, 0.31),
        xytext=(0.76, 0.02),
        xycoords="axes fraction",
        ha="center",
        fontsize=13,
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": "black"},
    )

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
