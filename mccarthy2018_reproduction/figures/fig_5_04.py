"""Figure 5.4: Sun-Earth-Moon synodic geometry."""

from __future__ import annotations

import numpy as np
import matplotlib.patches as patches
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.4"
SOURCE_PAGE = 101
REPRO_LEVEL = "shape-match"
SYSTEM = "Sun-Earth-Moon synodic geometry"


def main() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(6.4, 5.3), constrained_layout=True)
    ax.set_aspect("equal")
    ax.axis("off")

    sun = np.array([0.0, 0.0])
    earths = [np.array([2.75, 0.0]), np.array([2.20, 1.15]), np.array([1.35, 2.10])]
    moon_offsets = [np.array([0.62, 0.0]), np.array([0.42, 0.48]), np.array([-0.10, 0.63])]

    ax.add_patch(patches.Circle(sun, 0.23, facecolor="#ff8c00", edgecolor="none"))
    ax.add_patch(patches.Circle(sun, 2.80, fill=False, edgecolor="#6c86b4", linewidth=1.0))
    for idx, (earth, moon_offset) in enumerate(zip(earths, moon_offsets)):
        moon = earth + moon_offset
        ax.plot([sun[0], earth[0] + moon_offset[0]], [sun[1], earth[1] + moon_offset[1]],
                color="black", linestyle="--", linewidth=1.6 if idx == 0 else 1.2)
        ax.add_patch(patches.Circle(earth, 0.24, facecolor="#4f86c6", edgecolor="white", linewidth=0.8))
        ax.add_patch(patches.Circle(earth, 0.62, fill=False, edgecolor="black", linewidth=0.9))
        ax.add_patch(patches.Circle(moon, 0.12, facecolor="#9c9c9c", edgecolor="black", linewidth=0.7))
        ax.annotate("", xy=earth + np.array([0.50, 0.28]), xytext=earth + np.array([0.06, 0.58]),
                    arrowprops={"arrowstyle": "->", "lw": 1.0})
    ax.annotate("", xy=(3.34, 0.08), xytext=(3.04, 1.23), arrowprops={"arrowstyle": "->", "lw": 2.0})
    ax.text(3.10, 0.66, r"$T_{syn}\approx 29.5$ days", rotation=84, fontsize=11)
    ax.annotate("", xy=(2.64, 1.68), xytext=(2.04, 2.28), arrowprops={"arrowstyle": "->", "lw": 2.0})
    ax.text(2.52, 2.08, r"$T_{syn}\approx 29.5$ days", rotation=-10, fontsize=11)

    ax.set_xlim(-0.55, 3.75)
    ax.set_ylim(-0.70, 3.10)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
