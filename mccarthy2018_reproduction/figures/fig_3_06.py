"""Figure 3.6: quasi-halo amplitude trends."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import (
    corrected_l1_constant_energy_halo_high_order_corrections,
    corrected_l1_constant_energy_halo_pseudo_arclength_corrections,
    resample_corrected_torus_surface,
    sweep_corrected_curve_correction,
)


FIGURE_ID = "3.6"
SOURCE_PAGE = 69
REPRO_LEVEL = "numerical branch with paper-anchor boundary"
SYSTEM = "Earth-Moon CR3BP"
NOTES = (
    "Corrected fixed-JC N=9, N=15, and N=21 branches through the 12.40-day "
    "member; the paper's 12.03-day amplitude anchor is shown explicitly and is not passed."
)


def scientific_axis(ax) -> None:
    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((4, 4))
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    low_order = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
        system.mu,
        members=27,
    )
    n15 = corrected_l1_constant_energy_halo_high_order_corrections(
        system.mu,
        members=27,
        samples=15,
        max_iterations=48,
        tolerance=5.0e-10,
    )
    n21 = corrected_l1_constant_energy_halo_high_order_corrections(
        system.mu,
        members=15,
        samples=21,
        max_iterations=48,
        tolerance=2.0e-10,
    )
    corrections = list(low_order)
    for branch in (n15, n21):
        corrections.extend(
            correction
            for correction in branch
            if correction.mapping_time > corrections[-1].mapping_time + 1.0e-10
        )

    family = [
        sweep_corrected_curve_correction(correction, time_samples=24)
        for correction in corrections
    ]
    mapping_time = [member.correction.mapping_time * system.time_unit_days for member in family]
    y_amp: list[float] = []
    z_amp: list[float] = []
    for member in family:
        surface, _ = resample_corrected_torus_surface(member, phase_samples=96)
        points = surface.reshape(-1, 3)
        y_amp.append(0.5 * np.ptp(points[:, 1]) * system.length_unit_km)
        z_amp.append(0.5 * np.ptp(points[:, 2]) * system.length_unit_km)

    fig, axes = plt.subplots(1, 2, figsize=(8.1, 3.1), constrained_layout=True)

    axes[0].plot(mapping_time, y_amp, color="#1f77b4", label="Y-Amplitude")
    axes[0].plot(mapping_time, z_amp, color="#d95319", label="Z-Amplitude")
    paper_time = 12.03
    paper_y_amp = 34466.0
    paper_z_amp = 28547.0
    axes[0].scatter(
        [paper_time, paper_time],
        [paper_y_amp, paper_z_amp],
        marker="x",
        color="#111111",
        s=32,
        linewidth=1.2,
        zorder=5,
        label="paper 12.03-day anchors",
    )
    axes[0].set_xlabel("Mapping Time [days]")
    axes[0].set_ylabel("Amplitude [km]")
    axes[0].set_xlim(12.0, 12.5)
    axes[0].set_ylim(2.2e4, 4.25e4)
    axes[0].legend(loc="lower right", fontsize=8)
    axes[0].grid(True, alpha=0.24)
    y_formatter = ScalarFormatter(useMathText=True)
    y_formatter.set_powerlimits((4, 4))
    axes[0].yaxis.set_major_formatter(y_formatter)

    axes[1].plot(y_amp, z_amp, color="#1f77b4")
    axes[1].scatter(
        [paper_y_amp],
        [paper_z_amp],
        marker="x",
        color="#111111",
        s=34,
        linewidth=1.2,
        zorder=5,
        label="paper 12.03-day anchor",
    )
    axes[1].set_xlabel("Y-Amplitude [km]")
    axes[1].set_ylabel("Z-Amplitude [km]")
    axes[1].set_xlim(3.0e4, 4.4e4)
    axes[1].set_ylim(2.2e4, 3.72e4)
    axes[1].grid(True, alpha=0.24)
    axes[1].legend(loc="lower right", fontsize=7, frameon=False)
    scientific_axis(axes[1])

    fig.suptitle(
        "Solid curves: corrected branch; x markers: unmatched paper anchor",
        fontsize=9,
        color="#8a4b08",
    )

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
