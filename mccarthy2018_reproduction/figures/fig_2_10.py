"""Figure 2.10: multiple-shooting patch arcs."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.10"
SOURCE_PAGE = 31
REPRO_LEVEL = "shape-match"


def curve_between(p0, p1, wiggle=0.0, n=80):
    t = np.linspace(0.0, 1.0, n)
    line = (1 - t)[:, None] * p0 + t[:, None] * p1
    normal = np.array([-(p1 - p0)[1], (p1 - p0)[0]])
    norm = np.linalg.norm(normal)
    if norm > 0:
        normal /= norm
    return line + wiggle * np.sin(np.pi * t)[:, None] * normal


def main() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(9.0, 2.0))
    ax.grid(False)
    ax.axis("off")

    starts = [
        np.array([0.0, 0.0]),
        np.array([2.05, 0.32]),
        np.array([4.15, 0.38]),
        np.array([7.45, 0.58]),
    ]
    ends = [
        np.array([2.0, 0.75]),
        np.array([4.05, 1.05]),
        np.array([5.55, 0.72]),
        np.array([9.05, 0.48]),
    ]
    next_points = [
        np.array([2.25, 0.18]),
        np.array([4.35, 0.25]),
        np.array([5.95, 0.58]),
        np.array([9.45, 0.18]),
    ]
    wiggles = [0.24, 0.35, -0.18, 0.28]

    for idx, (start, end, next_point, wiggle) in enumerate(zip(starts, ends, next_points, wiggles), start=1):
        segment = curve_between(start, end, wiggle=wiggle)
        ax.plot(segment[:, 0], segment[:, 1], color="#365a98", linewidth=2.2)
        ax.scatter([start[0]], [start[1]], color="#3b6fb6", s=45, zorder=4)
        ax.scatter([next_point[0]], [next_point[1]], color="#3b6fb6", s=45, zorder=4)
        ax.text(start[0] - 0.12, start[1] - 0.34, rf"$\vec{{x}}_{idx}$", fontsize=13)
        ax.text(end[0] - 0.27, end[1] + 0.12, rf"$\vec{{x}}^t_{idx + 1}$", fontsize=13)
        ax.text(next_point[0] - 0.08, next_point[1] - 0.36, rf"$\vec{{x}}_{idx + 1}$", fontsize=13)
        ax.text((start[0] + end[0]) / 2.0 - 0.1, (start[1] + end[1]) / 2.0 + 0.22, rf"$\tau_{idx}$", fontsize=13)

    ax.text(6.25, 0.75, r"$\cdots$", fontsize=20)
    ax.text(8.55, 0.42, r"$\tau_{N-1}$", fontsize=13)
    ax.text(9.35, -0.2, r"$\vec{x}_{N}$", fontsize=13)
    ax.set_xlim(-0.25, 9.85)
    ax.set_ylim(-0.55, 1.35)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
