"""Figure 3.17: quasi-DRO amplitude and Jacobi constant versus rotation angle."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import load_or_compute_corrected_dro_family
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import dro_parameter_curve


FIGURE_ID = "3.17"
SOURCE_PAGE = 83
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Thesis-scale proxy trends with the corrected fixed-mapping-time CR3BP quasi-DRO family."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    rows = dro_parameter_curve(system, samples=64)
    rho = [row["rotation_angle_rad"] for row in rows]
    z_amp = [row["z_amplitude_km"] for row in rows]
    jacobi = [row["jacobi"] for row in rows]
    corrected = load_or_compute_corrected_dro_family(
        PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv",
        system,
    )
    corrected_rho = [member.rotation_angle_rad for member in corrected]
    corrected_z_amp = [member.max_abs_z_km for member in corrected]
    corrected_jacobi = [member.mean_jacobi for member in corrected]

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.1), constrained_layout=True)
    axes[0].plot(rho, z_amp, color="#d95319", label="thesis-scale proxy")
    axes[0].plot(
        corrected_rho,
        corrected_z_amp,
        color="#16856b",
        marker="o",
        markersize=4,
        linewidth=1.2,
        label="corrected CR3BP",
    )
    axes[0].set_xlabel(r"Rotation Angle, $\rho$ [rad]")
    axes[0].set_ylabel("Z-Amplitude [km]")
    axes[0].set_xlim(1.42, 1.52)
    axes[0].set_ylim(0.4e4, 3.65e4)
    fmt = ScalarFormatter(useMathText=True)
    fmt.set_powerlimits((4, 4))
    axes[0].yaxis.set_major_formatter(fmt)
    axes[0].legend(loc="upper left", fontsize=7, frameon=False)

    inset = axes[0].inset_axes([0.54, 0.08, 0.42, 0.40])
    inset.plot(corrected_rho, corrected_z_amp, color="#16856b", marker="o", markersize=3)
    inset.set_xlim(1.4295, 1.4402)
    inset.set_ylim(0.0, 8200.0)
    inset.set_xticks([1.431, 1.438])
    inset.set_yticks([0.0, 4000.0, 8000.0])
    inset.tick_params(labelsize=6, pad=1)
    inset.set_title("corrected local branch", fontsize=6, pad=2)

    axes[1].plot(rho, jacobi, color="#1f77b4", label="thesis-scale proxy")
    axes[1].plot(
        corrected_rho,
        corrected_jacobi,
        color="#16856b",
        marker="o",
        markersize=4,
        linewidth=1.2,
        label="corrected CR3BP",
    )
    axes[1].set_xlabel(r"Rotation Angle, $\rho$ [rad]")
    axes[1].set_ylabel("Jacobi Constant")
    axes[1].set_xlim(1.42, 1.52)
    axes[1].set_ylim(2.921, 2.9225)
    axes[1].legend(loc="lower left", fontsize=7, frameon=False)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
