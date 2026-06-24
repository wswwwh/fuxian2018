"""Figure 3.1: two-dimensional torus phase coordinates."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _torus_schematic import add_curve_arrow, clean_torus_axes, plot_torus, section_circle, torus_curve
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "3.1"
SOURCE_PAGE = 48
REPRO_LEVEL = "shape-match"


def main() -> None:
    apply_style()
    fig = plt.figure(figsize=(6.4, 4.3))
    ax = fig.add_subplot(111, projection="3d")
    clean_torus_axes(ax)
    plot_torus(ax)

    u = np.linspace(0.0, 2.0 * np.pi, 360)
    v = -0.18 * np.ones_like(u)
    x, y, z = torus_curve(u, v)
    ax.plot(x, y, z, color="#1f77b4", linewidth=2.1)

    sx, sy, sz = section_circle(-0.34)
    ax.plot(sx, sy, sz, color="#9b1b3d", linewidth=2.0)

    add_curve_arrow(ax, x, y, z, 286, "black", length=0.36, linewidth=1.7)
    add_curve_arrow(ax, sx, sy, sz, 32, "black", length=0.26, linewidth=1.6)

    ax.annotate(
        r"$\theta_0$",
        xy=(0.80, 0.22),
        xytext=(0.89, 0.07),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": "black", "connectionstyle": "arc3,rad=-0.25"},
        fontsize=20,
    )
    ax.annotate(
        r"$\theta_1$",
        xy=(0.72, 0.42),
        xytext=(0.78, 0.27),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": "black", "connectionstyle": "arc3,rad=0.25"},
        fontsize=20,
    )

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
