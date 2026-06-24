"""Figure 2.9: single-shooting differential correction targeting."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.9"
SOURCE_PAGE = 29
REPRO_LEVEL = "shape-match"


def bezier(p0, p1, p2, p3, n=120):
    t = np.linspace(0.0, 1.0, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3


def main() -> None:
    apply_style()
    fig, ax = plt.subplots(figsize=(6.5, 2.3))
    ax.grid(False)
    ax.axis("off")
    ax.set_aspect("equal")

    start = np.array([0.0, 0.0])
    target = np.array([5.15, 0.72])
    final = np.array([4.45, 2.35])
    arc_guess = bezier(start, np.array([1.6, 0.45]), np.array([3.3, 0.55]), target)
    arc_current = bezier(start, np.array([1.1, 1.0]), np.array([2.55, 1.7]), final)

    ax.plot(arc_current[:, 0], arc_current[:, 1], color="#365a98", linewidth=2.2)
    ax.plot(arc_guess[:, 0], arc_guess[:, 1], color="#d95f02", linewidth=1.8)
    ax.scatter([start[0], target[0], final[0]], [start[1], target[1], final[1]], color="#3b6fb6", s=[40, 36, 36], zorder=5)
    ax.scatter([target[0]], [target[1]], color="black", s=22, zorder=6)

    ax.text(start[0] - 0.08, start[1] - 0.33, r"$\vec{x}(t_0), \vec{x}^*(t_0)$", fontsize=13)
    ax.text(final[0] + 0.05, final[1] + 0.1, r"$\vec{x}(t_0+\tau)$", fontsize=13)
    ax.text(target[0] + 0.1, target[1] - 0.18, r"$\vec{r}^{\,*}$" + "\n" + r"$\vec{x}^{\,*}(t_0+\tau^*)$", fontsize=12)
    ax.text(1.75, 1.45, r"$\tau$", fontsize=15)
    ax.text(2.55, 0.48, r"$\tau^*$", fontsize=15)

    ax.set_xlim(-0.45, 5.9)
    ax.set_ylim(-0.55, 2.75)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
