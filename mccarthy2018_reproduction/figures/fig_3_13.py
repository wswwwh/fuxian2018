"""Figure 3.13: constant-frequency quasi-halo amplitudes and Jacobi constant."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import (
    corrected_l2_constant_frequency_halo_energy_corrections,
    sweep_corrected_curve_correction,
)


FIGURE_ID = "3.13"
SOURCE_PAGE = 77
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected fixed-ratio quasi-halo amplitudes and Jacobi trend."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    corrections = corrected_l2_constant_frequency_halo_energy_corrections(system.mu)
    family = [
        sweep_corrected_curve_correction(correction, time_samples=20)
        for correction in corrections
    ]
    mapping_time = np.asarray(
        [correction.mapping_time * system.time_unit_days for correction in corrections]
    )
    y_amplitude = np.asarray(
        [
            0.5 * np.ptp(member.surface[:, :, 1]) * system.length_unit_km
            for member in family
        ]
    )
    z_amplitude = np.asarray(
        [
            0.5 * np.ptp(member.surface[:, :, 2]) * system.length_unit_km
            for member in family
        ]
    )
    jacobi = np.asarray([correction.target_jacobi for correction in corrections])

    fig, axes = plt.subplots(1, 2, figsize=(8.1, 3.1), constrained_layout=True)
    axes[0].plot(mapping_time, y_amplitude, color="#1f77b4", label="Y-Amplitude")
    axes[0].plot(mapping_time, z_amplitude, color="#d95319", label="Z-Amplitude")
    axes[0].set_xlabel("Mapping Time [days]")
    axes[0].set_ylabel("Amplitude [km]")
    axes[0].set_xlim(14.4, 17.8)
    axes[0].set_ylim(2.0e4, 1.22e5)
    axes[0].legend(loc="upper left", fontsize=8)
    fmt = ScalarFormatter(useMathText=True)
    fmt.set_powerlimits((4, 4))
    axes[0].yaxis.set_major_formatter(fmt)

    axes[1].plot(mapping_time, jacobi, color="#1f77b4")
    axes[1].set_xlabel("Mapping Time [days]")
    axes[1].set_ylabel("Jacobi Constant")
    axes[1].set_xlim(14.4, 17.8)
    axes[1].set_ylim(3.00, 3.14)
    axes[1].grid(True, alpha=0.24)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
