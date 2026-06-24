"""Figure 2.4: Earth-Moon zero-velocity curves for two Jacobi constants."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import zero_velocity_grid
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.4"
SOURCE_PAGE = 16
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"


def draw_zvc(ax, jc: float) -> None:
    system = SYSTEMS["earth_moon"]
    points = compute_libration_points(system.mu)
    x_grid, y_grid, c_grid = zero_velocity_grid(system.mu, (-1.35, 1.35), (-1.15, 1.15), n=650)
    forbidden = c_grid < jc
    ax.contourf(x_grid, y_grid, forbidden, levels=[0.5, 1.5], colors=["0.68"], alpha=0.9)
    ax.contour(x_grid, y_grid, c_grid, levels=[jc], colors="black", linewidths=1.0)
    ax.scatter([-system.mu], [0.0], s=75, color="tab:blue", zorder=5)
    ax.scatter([1.0 - system.mu], [0.0], s=28, color="0.25", zorder=5)
    for label, point in points.items():
        ax.scatter([point.x], [point.y], s=8, color="tab:red", zorder=6)
        if label in {"L1", "L2"}:
            ax.annotate(
                label,
                xy=(point.x, point.y),
                xytext=(point.x + 0.12, point.y - 0.07),
                arrowprops={"arrowstyle": "-", "linewidth": 0.8, "color": "black"},
                fontsize=8,
            )
        elif label == "L3":
            ax.text(point.x - 0.1, point.y - 0.05, label, fontsize=8)
        else:
            ax.text(point.x + 0.03, point.y + (0.04 if label == "L4" else -0.08), label, fontsize=8)

    ax.text(-0.33, 0.72, "Forbidden\nRegion", ha="center", fontsize=8)
    ax.text(-0.2, 0.03, "Earth", ha="center", fontsize=8)
    ax.annotate(
        "Moon",
        xy=(1.0 - system.mu, 0.0),
        xytext=(1.18, 0.12),
        arrowprops={"arrowstyle": "-", "linewidth": 0.8, "color": "black"},
        fontsize=8,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.15, 1.15)
    ax.set_xlabel("X [nd]")
    ax.set_ylabel("Y [nd]")
    ax.set_title(f"JC = {jc:.2f}")
    ax.grid(False)


def main() -> None:
    apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), constrained_layout=True)
    draw_zvc(axes[0], 3.16)
    draw_zvc(axes[1], 3.18)
    fig.suptitle("Earth-Moon zero-velocity curves")
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
