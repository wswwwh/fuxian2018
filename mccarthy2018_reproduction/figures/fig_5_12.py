"""Figure 5.12: rendezvous maneuver versus arrival time."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import (
    earth_moon_nrho_transfer_baseline,
    rendezvous_delta_v_curve,
)
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.12"
SOURCE_PAGE = 109
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP fixed-TOF arrival scan"
NOTES = "Blue branch is converged direct shooting; grey dashed curve preserves the thesis-scale proxy beyond its fold."


def main() -> None:
    apply_style()
    proxy_x, proxy_y = rendezvous_delta_v_curve()
    baseline = earth_moon_nrho_transfer_baseline(rendezvous_samples=49)
    x = baseline.rendezvous_offsets_hours
    y = baseline.rendezvous_delta_v_difference_m_s
    fig, ax = plt.subplots(figsize=(6.3, 3.2), constrained_layout=True)
    ax.plot(proxy_x, proxy_y, color="#a6a6a6", linewidth=1.0, linestyle="--")
    ax.plot(x, y, color="#1f8fd4", linewidth=1.7)
    minimum = int(y.argmin())
    ax.scatter([x[minimum]], [y[minimum]], color="#1f8fd4", s=18, zorder=3)
    ax.text(0.03, 0.90, "Local direct-shooting branch", transform=ax.transAxes, fontsize=7)
    ax.set_xlim(-24, 24)
    ax.set_ylim(-50, 250)
    ax.set_xlabel("Arrival Time Relative to Baseline [hrs]")
    ax.set_ylabel(r"$\Delta V_{tot}-\Delta V_{tot,baseline}$ [m/s]")
    ax.set_xticks([-20, -15, -10, -5, 0, 5, 10, 15, 20])
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
