"""Figure 3.2: invariant curve and stroboscopic mapping."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _torus_schematic import add_curve_arrow, clean_torus_axes, plot_torus, section_circle, torus_curve
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "3.2"
SOURCE_PAGE = 49
REPRO_LEVEL = "shape-match"


def main() -> None:
    apply_style()
    fig = plt.figure(figsize=(6.3, 4.35))
    ax = fig.add_subplot(111, projection="3d")
    clean_torus_axes(ax)
    plot_torus(ax)

    u = np.linspace(0.18, 2.0 * np.pi + 0.18, 420)
    v = 0.52 + 0.10 * np.sin(2.0 * u)
    x, y, z = torus_curve(u, v)
    ax.plot(x, y, z, color="#dca80a", linewidth=2.0)
    for idx in (62, 205, 340):
        add_curve_arrow(ax, x, y, z, idx, "#dca80a", length=0.28, linewidth=1.5)

    sx, sy, sz = section_circle(-0.30, scale=1.00)
    ax.plot(sx, sy, sz, color="#1f77b4", linewidth=2.0)
    add_curve_arrow(ax, sx, sy, sz, 22, "black", length=0.23, linewidth=1.5)

    ax.annotate(
        "Stroboscopic\nmap integration\ntime, $T_0$",
        xy=(0.76, 0.45),
        xytext=(0.86, 0.22),
        xycoords="axes fraction",
        ha="left",
        fontsize=12,
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": "black", "connectionstyle": "arc3,rad=-0.25"},
    )
    ax.annotate(
        "Invariant\nCurve",
        xy=(0.66, 0.28),
        xytext=(0.73, 0.02),
        xycoords="axes fraction",
        ha="center",
        fontsize=12,
        arrowprops={"arrowstyle": "-|>", "lw": 1.8, "color": "black"},
    )
    ax.text2D(0.70, 0.31, r"$\rho$", transform=ax.transAxes, fontsize=18)

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
