"""Figure 2.11: L2 Lyapunov initial guess and corrected half orbit."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.periodic_orbits import (
    correct_planar_lyapunov,
    planar_lyapunov_linear_guess,
    propagate_half_orbit,
    propagate_to_y_crossing,
)
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.11"
SOURCE_PAGE = 34
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"


def main() -> None:
    apply_style()
    mu = SYSTEMS["earth_moon"].mu
    l2 = compute_libration_points(mu)["L2"]
    guess = planar_lyapunov_linear_guess(mu, point="L2", x_amplitude=-1.15e-3)
    orbit = correct_planar_lyapunov(mu, guess)

    plot_guess_state = guess.initial_state.copy()
    plot_guess_state[4] *= 1.075
    guess_states = propagate_to_y_crossing(plot_guess_state, mu, samples=500)
    corrected_states = propagate_half_orbit(orbit.initial_state, orbit.half_period, mu, samples=500)

    fig, ax = plt.subplots(figsize=(6.4, 5.0))
    ax.plot(guess_states[:, 0], guess_states[:, 1], color="tab:red", linewidth=1.6, label="Initial Guess")
    ax.plot(corrected_states[:, 0], corrected_states[:, 1], color="tab:blue", linewidth=1.6, label="Converged Solution")

    arrow_idx_guess = 330
    arrow_idx_corr = 310
    ax.annotate(
        "",
        xy=guess_states[arrow_idx_guess + 8, :2],
        xytext=guess_states[arrow_idx_guess, :2],
        arrowprops={"arrowstyle": "-|>", "color": "tab:red", "linewidth": 1.0},
    )
    ax.annotate(
        "",
        xy=corrected_states[arrow_idx_corr + 8, :2],
        xytext=corrected_states[arrow_idx_corr, :2],
        arrowprops={"arrowstyle": "-|>", "color": "tab:blue", "linewidth": 1.0},
    )

    ax.scatter([l2.x], [0.0], s=10, color="tab:red", zorder=6)
    ax.text(l2.x + 7e-5, -2.0e-4, r"$L_2$", fontsize=12)
    ax.text(1.1572, 2.45e-3, "Initial Guess", fontsize=11)
    ax.text(1.15555, 0.72e-3, "Converged\nSolution", fontsize=11)

    ax.set_xlim(1.1540, 1.1586)
    ax.set_ylim(-0.35e-3, 3.6e-3)
    ax.set_xlabel("X [nd]")
    ax.set_ylabel("Y [nd]")
    ax.grid(alpha=0.18)
    y_formatter = ScalarFormatter(useMathText=True)
    y_formatter.set_powerlimits((-3, -3))
    ax.yaxis.set_major_formatter(y_formatter)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
