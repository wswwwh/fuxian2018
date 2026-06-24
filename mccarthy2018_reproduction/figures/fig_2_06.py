"""Figure 2.6: ZVC comparison for three CR3BP systems."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import zero_velocity_grid
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.6"
SOURCE_PAGE = 18
REPRO_LEVEL = "physical-consistency"


SYSTEM_ORDER = ["earth_moon", "saturn_titan", "sun_earth"]


def draw_system(ax, key: str) -> None:
    system = SYSTEMS[key]
    points = compute_libration_points(system.mu)
    jc = 0.5 * (points["L1"].jacobi + points["L2"].jacobi)

    x_grid, y_grid, c_grid = zero_velocity_grid(system.mu, (0.72, 1.2), (-0.24, 0.24), n=620)
    forbidden = c_grid < jc
    ax.contourf(x_grid, y_grid, forbidden, levels=[0.5, 1.5], colors=["0.7"], alpha=0.95)
    ax.contour(x_grid, y_grid, c_grid, levels=[jc], colors="black", linewidths=1.0)
    ax.scatter([1.0 - system.mu], [0.0], s=30, color="0.2", zorder=5)
    ax.scatter([points["L1"].x, points["L2"].x], [0.0, 0.0], s=18, color="tab:red", zorder=5)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(0.72, 1.2)
    ax.set_ylim(-0.24, 0.24)
    ax.set_xlabel(r"$\hat{x}$")
    ax.set_ylabel(r"$\hat{y}$")
    ax.set_title(f"{system.name}\nmu={system.mu:.4g}, JC={jc:.6f}")
    ax.grid(False)


def main() -> None:
    apply_style()
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.0), constrained_layout=True)
    for ax, key in zip(axes, SYSTEM_ORDER):
        draw_system(ax, key)
    fig.suptitle("Zero-velocity curve comparison near the secondary")
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
