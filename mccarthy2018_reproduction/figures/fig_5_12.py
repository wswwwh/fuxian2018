"""Figure 5.12: rendezvous maneuver versus arrival time."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import (
    earth_moon_nrho_transfer_baseline,
)
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.12"
SOURCE_PAGE = 109
REPRO_LEVEL = "numerical CR3BP rendezvous-branch reproduction"
SYSTEM = "Earth-Moon CR3BP fixed-TOF arrival scan"
NOTES = "Converged direct-shooting branch only; the +12 to +24 h fold boundary is left unplotted."


def main() -> None:
    apply_style()
    baseline = earth_moon_nrho_transfer_baseline(rendezvous_samples=49)
    x = baseline.rendezvous_offsets_hours
    y = baseline.rendezvous_delta_v_difference_m_s
    fig, ax = plt.subplots(figsize=(6.3, 3.2), constrained_layout=True)
    ax.plot(x, y, color="#1f8fd4", linewidth=1.7)
    minimum = int(y.argmin())
    ax.scatter([x[minimum]], [y[minimum]], color="#1f8fd4", s=18, zorder=3)
    ax.text(0.03, 0.90, "Converged direct-shooting branch", transform=ax.transAxes, fontsize=7)
    ax.text(0.62, 0.13, "branch fold at +11 h", transform=ax.transAxes, fontsize=7, color="#555555")
    ax.set_xlim(-24, 11)
    ax.set_ylim(-50, 250)
    ax.set_xlabel("Arrival Time Relative to Baseline [hrs]")
    ax.set_ylabel(r"$\Delta V_{tot}-\Delta V_{tot,baseline}$ [m/s]")
    ax.set_xticks([-20, -15, -10, -5, 0, 5, 10])
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
