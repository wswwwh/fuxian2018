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
REPRO_LEVEL = "truncated numerical CR3BP branch with explicit coverage boundary"
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
    computed_end = float(x.max())
    ax.axvspan(computed_end, 24.0, color="#d97706", alpha=0.13, linewidth=0)
    ax.axvline(computed_end, color="#8a4b08", linestyle=":", linewidth=0.9)
    ax.text(
        18.0,
        220.0,
        "+12 to +24 h\nnot computed\n(no extrapolation)",
        fontsize=7,
        color="#8a4b08",
        ha="center",
        va="top",
    )
    ax.set_xlim(-24, 24)
    ax.set_ylim(-50, 250)
    ax.set_xlabel("Arrival Time Relative to Baseline [hrs]")
    ax.set_ylabel(r"$\Delta V_{tot}-\Delta V_{tot,baseline}$ [m/s]")
    ax.set_xticks([-24, -16, -8, 0, 8, 16, 24])
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
