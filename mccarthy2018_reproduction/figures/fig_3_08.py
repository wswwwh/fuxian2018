"""Figure 3.8: quasi-vertical amplitude trends."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import (
    corrected_l1_constant_energy_vertical_staged_corrections,
    resample_corrected_torus_surface,
    sweep_corrected_curve_correction,
)


FIGURE_ID = "3.8"
SOURCE_PAGE = 71
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Amplitude trends from the propagated staged N=9 through N=33 corrected family."


def sci_y(ax) -> None:
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((4, 4))
    ax.yaxis.set_major_formatter(formatter)


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    corrections = corrected_l1_constant_energy_vertical_staged_corrections(system.mu)
    family = [
        sweep_corrected_curve_correction(correction, time_samples=20)
        for correction in corrections
    ]
    mapping_time: list[float] = []
    y_amp: list[float] = []
    z_amp: list[float] = []
    for member in family:
        surface, _ = resample_corrected_torus_surface(member, phase_samples=96)
        points = surface.reshape(-1, 3)
        mapping_time.append(member.correction.mapping_time * system.time_unit_days)
        y_amp.append(0.5 * np.ptp(points[:, 1]) * system.length_unit_km)
        z_amp.append(0.5 * np.ptp(points[:, 2]) * system.length_unit_km)
    mapping_time.reverse()
    y_amp.reverse()
    z_amp.reverse()

    fig, axes = plt.subplots(1, 2, figsize=(8.1, 3.1), constrained_layout=True)
    axes[0].plot(mapping_time, y_amp, color="#1f77b4", label="Y-Amplitude")
    axes[0].plot(mapping_time, z_amp, color="#d95319", label="Z-Amplitude")
    axes[0].set_xlabel("Mapping Time [days]")
    axes[0].set_ylabel("Amplitude [km]")
    axes[0].set_xlim(12.6, 12.9)
    axes[0].set_ylim(0.0, 4.55e4)
    axes[0].legend(loc="lower left", fontsize=8)
    axes[0].grid(True, alpha=0.24)
    sci_y(axes[0])

    axes[1].plot(y_amp, z_amp, color="#1f77b4")
    axes[1].set_xlabel("Y-Amplitude [km]")
    axes[1].set_ylabel("Z-Amplitude [km]")
    axes[1].set_xlim(0.0, 4.35e4)
    axes[1].set_ylim(2.4e4, 5.05e4)
    axes[1].grid(True, alpha=0.24)
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((4, 4))
    axes[1].xaxis.set_major_formatter(formatter)
    axes[1].yaxis.set_major_formatter(formatter)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
