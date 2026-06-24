"""Figure 2.14: stable and unstable manifolds from an L1 Lyapunov orbit."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import zero_velocity_grid
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.manifolds import manifold_trajectories
from qp_orbits.periodic_orbits import correct_planar_lyapunov, planar_lyapunov_linear_guess, propagate_half_orbit
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.14"
SOURCE_PAGE = 43
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"


def main() -> None:
    apply_style()
    mu = SYSTEMS["earth_moon"].mu
    points = compute_libration_points(mu)

    guess = planar_lyapunov_linear_guess(mu, point="L1", x_amplitude=0.0111)
    orbit = correct_planar_lyapunov(mu, guess, max_iterations=20)
    stable, unstable, _data = manifold_trajectories(
        orbit,
        samples_on_orbit=16,
        epsilon=1e-5,
        duration=5.0,
        trajectory_samples=260,
    )

    half = propagate_half_orbit(orbit.initial_state, orbit.half_period, mu, samples=300)
    full_x = np.concatenate([half[:, 0], half[::-1, 0]])
    full_y = np.concatenate([half[:, 1], -half[::-1, 1]])

    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    x_grid, y_grid, c_grid = zero_velocity_grid(mu, (0.62, 1.07), (-0.15, 0.15), n=700)
    ax.contour(x_grid, y_grid, c_grid, levels=[orbit.jacobi], colors="black", linewidths=1.2)

    for traj in stable:
        ax.plot(traj[:, 0], traj[:, 1], color="#2389d7", linewidth=0.8, alpha=0.9)
    for traj in unstable:
        ax.plot(traj[:, 0], traj[:, 1], color="#c9253d", linewidth=0.8, alpha=0.9)

    ax.plot(full_x, full_y, color="black", linewidth=1.3)
    ax.scatter([1.0 - mu], [0.0], color="black", s=42, zorder=6)
    ax.scatter([points["L1"].x], [0.0], color="black", s=18, zorder=6)
    ax.text(points["L1"].x + 0.02, -0.085, r"$L_1$", fontsize=14)
    ax.text(0.96, -0.01, "Moon", fontsize=11, ha="right")
    ax.annotate("To Earth", xy=(0.625, 0.0), xytext=(0.69, 0.0), ha="center", va="center", fontsize=11)
    ax.annotate("", xy=(0.635, 0.0), xytext=(0.705, 0.0), arrowprops={"arrowstyle": "-|>", "linewidth": 1.4, "color": "black"})

    ax.annotate("", xy=(0.73, 0.085), xytext=(0.77, 0.065), arrowprops={"arrowstyle": "->", "linewidth": 1.8, "color": "#c9253d"})
    ax.annotate("", xy=(1.02, 0.092), xytext=(1.00, 0.055), arrowprops={"arrowstyle": "->", "linewidth": 1.8, "color": "#c9253d"})
    ax.annotate("", xy=(0.78, -0.083), xytext=(0.745, -0.105), arrowprops={"arrowstyle": "->", "linewidth": 1.8, "color": "#2389d7"})
    ax.annotate("", xy=(1.03, -0.035), xytext=(1.01, -0.07), arrowprops={"arrowstyle": "->", "linewidth": 1.8, "color": "#2389d7"})

    ax.set_xlim(0.62, 1.07)
    ax.set_ylim(-0.15, 0.15)
    ax.set_xlabel("X [nd]")
    ax.set_ylabel("Y [nd]")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.22)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
