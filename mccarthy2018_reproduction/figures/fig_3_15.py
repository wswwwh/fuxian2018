"""Figure 3.15: quasi-vertical Jacobi constant and mapping time."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import (
    corrected_l2_constant_frequency_vertical_pseudo_arclength_corrections,
)


FIGURE_ID = "3.15"
SOURCE_PAGE = 79
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected fixed-ratio quasi-vertical branch through its periodic-orbit endpoint."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    corrections = corrected_l2_constant_frequency_vertical_pseudo_arclength_corrections(
        system.mu
    )
    orbit_index = np.linspace(0.0, 800.0, len(corrections))
    jacobi = np.asarray(
        [
            float(np.mean(jacobi_constant(correction.corrected_states, system.mu)))
            for correction in corrections
        ]
    )
    mapping_time = np.asarray(
        [correction.mapping_time * system.time_unit_days for correction in corrections]
    )

    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.1), constrained_layout=True)
    axes[0].plot(orbit_index, jacobi, color="#1f77b4", linewidth=1.8)
    axes[0].scatter([orbit_index[-1]], [jacobi[-1]], color="#16856b", s=28, zorder=4)
    axes[0].set_xlabel("Orbit Index")
    axes[0].set_ylabel("Jacobi Constant")
    axes[0].set_xlim(0, 800)
    axes[0].set_ylim(3.0275, 3.0450)
    axes[0].grid(True, alpha=0.24)

    axes[1].plot(orbit_index, mapping_time, color="#1f77b4", linewidth=1.8)
    axes[1].scatter(
        [orbit_index[-1]], [mapping_time[-1]], color="#16856b", s=28, zorder=4
    )
    axes[1].set_xlabel("Orbit Index")
    axes[1].set_ylabel("Mapping Time [days]")
    axes[1].set_xlim(0, 800)
    axes[1].set_ylim(16.85, 17.28)
    axes[1].grid(True, alpha=0.24)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
