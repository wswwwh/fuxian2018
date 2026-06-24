"""Figure 4.2: quasi-halo stability index versus mapping time."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    corrected_l1_constant_energy_halo_high_order_stability_family,
    corrected_l1_constant_energy_halo_pseudo_arclength_stability_family,
    quasi_halo_stability_curve,
)


FIGURE_ID = "4.2"
SOURCE_PAGE = 87
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Thesis-scale reference with DG samples from the staged N=9, N=15, and N=21 branches."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    rows = quasi_halo_stability_curve(samples=64)
    times = [row["mapping_time_days"] for row in rows]
    values = [row["stability_index"] for row in rows]
    local = corrected_l1_constant_energy_halo_pseudo_arclength_stability_family(system.mu)
    local.extend(
        corrected_l1_constant_energy_halo_high_order_stability_family(
            system.mu,
            samples=15,
            members=27,
            member_indices=(8, 16, 26),
            tolerance=5.0e-10,
        )
    )
    local.extend(
        corrected_l1_constant_energy_halo_high_order_stability_family(
            system.mu,
            samples=21,
            members=15,
            member_indices=(12,),
            tolerance=2.0e-10,
        )
    )
    local.sort(key=lambda row: row["mapping_time_nd"])
    local_amp = [row["mode_amplitude_nd"] * system.length_unit_km for row in local]
    local_time = [row["mapping_time_nd"] * system.time_unit_days for row in local]
    local_nu = [row["stability_index"] for row in local]
    local_delta_nu = [value - local_nu[0] for value in local_nu]

    fig, ax = plt.subplots(figsize=(7.0, 3.2), constrained_layout=True)
    ax.plot(times, values, color="#1f77b4", linewidth=1.8)
    ax.scatter([times[0]], [values[0]], color="#d95319", s=24, zorder=4)
    ax.plot(local_time, local_nu, color="#16834f", marker="o", markersize=3.2, linewidth=1.2, zorder=5)
    ax.set_xlabel("Mapping Time [days]")
    ax.set_ylabel(r"Stability Index, $\nu$")
    ax.set_xlim(12.0, 12.5)
    ax.set_ylim(600.0, 805.0)
    inset = ax.inset_axes([0.52, 0.15, 0.40, 0.40])
    inset.plot(local_amp, local_delta_nu, color="#2ca25f", marker="o", markersize=3, linewidth=1.0)
    inset.set_xlabel(r"$A_z$ seed [km]", fontsize=6, labelpad=1)
    inset.set_ylabel(r"$\Delta\nu$", fontsize=6, labelpad=1)
    inset.tick_params(labelsize=6, pad=1)
    inset.grid(True, alpha=0.20)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
