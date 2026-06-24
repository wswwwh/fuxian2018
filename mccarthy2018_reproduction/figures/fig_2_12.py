"""Figure 2.12: natural and pseudo-arclength continuation schemes."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.12"
SOURCE_PAGE = 39
REPRO_LEVEL = "shape-match"


def branch(x: np.ndarray) -> np.ndarray:
    return 1.1 + 0.16 * (x - 1.0) ** 3 - 0.58 * np.exp(-((x - 1.25) / 0.82) ** 2) + 1.15 / (1 + np.exp(-11 * (x - 2.55)))


def draw_panel(ax, pseudo: bool) -> None:
    ax.grid(False)
    ax.spines["left"].set_position(("data", 0.0))
    ax.spines["bottom"].set_position(("data", 0.0))
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0.0, 3.55)
    ax.set_ylim(0.0, 2.7)
    ax.annotate("", xy=(3.45, 0.0), xytext=(0.0, 0.0), arrowprops={"arrowstyle": "-|>", "color": "black", "linewidth": 1.3})
    ax.annotate("", xy=(0.0, 2.55), xytext=(0.0, 0.0), arrowprops={"arrowstyle": "-|>", "color": "black", "linewidth": 1.3})
    ax.text(3.25, -0.18, r"$p$", fontsize=17)
    ax.text(-0.25, 2.45, r"$X^*$", fontsize=17)

    x = np.linspace(0.05, 3.1, 500)
    y = branch(x)
    ax.plot(x, y, color="black", linewidth=1.8)

    p0 = 1.04
    p1 = 1.52 if not pseudo else 1.38
    y0 = branch(np.array([p0]))[0]
    y1 = branch(np.array([p1]))[0]
    ax.plot([p0, p0], [0.0, y0], "--", color="0.45", linewidth=1.0)
    ax.plot([p1, p1], [0.0, y1], "--", color="0.45", linewidth=1.0)
    ax.scatter([p0], [y0], color="#2b6cb0", s=18)
    ax.scatter([p1], [y1], color="tab:red", s=18)
    ax.annotate("", xy=(p1, y1), xytext=(p0, y0), arrowprops={"arrowstyle": "->", "color": "#2b6cb0", "linewidth": 1.2})

    label = r"$\delta S$" if pseudo else r"$\delta p$"
    ax.text((p0 + p1) / 2.0 - 0.05, max(y0, y1) + 0.17, label, fontsize=12)
    ax.text(p1 + 0.08, y1 + 0.2, "Initial\nguess", fontsize=8)
    ax.text(p1 + 0.12, y1 - 0.35, "Converged\nsolution", fontsize=8)


def main() -> None:
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.9), constrained_layout=True)
    draw_panel(axes[0], pseudo=False)
    draw_panel(axes[1], pseudo=True)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
