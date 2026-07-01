"""Figure 3.17: quasi-DRO amplitude and Jacobi constant versus rotation angle."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    load_best_chapter3_corrected_dro_family,
    write_chapter3_quasi_dro_validation,
)
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import dro_parameter_curve


FIGURE_ID = "3.17"
SOURCE_PAGE = 83
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Proxy trends retained as reference with an expanded corrected fixed-mapping-time CR3BP quasi-DRO family."
FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv"
EXTENDED_FAMILY_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family_extended.csv"
)
VALIDATION_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_extended_validation.csv"
CONTINUATION_LOG_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_continuation_log.csv"
PALC_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
PALC_VALIDATION_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_validation.csv"


def max_audit_metric(rows, field: str) -> float | None:
    values = [float(row[field]) for row in rows if row[field] != "N/A"]
    return max(values) if values else None


def metric_text(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2e}"


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    rows = dro_parameter_curve(system, samples=64)
    rho = [row["rotation_angle_rad"] for row in rows]
    z_amp = [row["z_amplitude_km"] for row in rows]
    jacobi = [row["jacobi"] for row in rows]
    corrected = load_best_chapter3_corrected_dro_family(
        FAMILY_PATH,
        EXTENDED_FAMILY_PATH,
        PALC_FAMILY_PATH,
        CONTINUATION_LOG_PATH,
        system,
    )
    validation_path = (
        PALC_VALIDATION_PATH
        if corrected[-1].max_abs_z_km > 11000.0
        else VALIDATION_PATH
    )
    audit_rows = write_chapter3_quasi_dro_validation(validation_path, corrected, system)
    corrected_rho = [member.rotation_angle_rad for member in corrected]
    corrected_z_amp = [member.max_abs_z_km for member in corrected]
    corrected_jacobi = [member.mean_jacobi for member in corrected]
    max_map_residual = max_audit_metric(audit_rows, "map_residual_norm")
    max_jacobi_drift = max_audit_metric(audit_rows, "one_map_sweep_jacobi_drift")

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.1), constrained_layout=True)
    axes[0].plot(
        rho,
        z_amp,
        color="#a9a9a9",
        linestyle="--",
        linewidth=1.1,
        label="proxy reference",
    )
    axes[0].plot(
        corrected_rho,
        corrected_z_amp,
        color="#16856b",
        marker="o",
        markersize=4,
        linewidth=1.7,
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
    inset.set_xlim(min(corrected_rho) - 0.001, max(corrected_rho) + 0.001)
    inset.set_ylim(0.0, max(corrected_z_amp) * 1.08)
    inset.set_xticks([round(min(corrected_rho), 3), round(max(corrected_rho), 3)])
    inset.set_yticks([0.0, 5000.0, 10000.0])
    inset.tick_params(labelsize=6, pad=1)
    inset.set_title("extended corrected branch", fontsize=6, pad=2)

    axes[1].plot(
        rho,
        jacobi,
        color="#a9a9a9",
        linestyle="--",
        linewidth=1.1,
        label="proxy reference",
    )
    axes[1].plot(
        corrected_rho,
        corrected_jacobi,
        color="#16856b",
        marker="o",
        markersize=4,
        linewidth=1.7,
        label="corrected CR3BP",
    )
    axes[1].set_xlabel(r"Rotation Angle, $\rho$ [rad]")
    axes[1].set_ylabel("Jacobi Constant")
    axes[1].set_xlim(1.42, 1.52)
    axes[1].set_ylim(2.921, 2.9225)
    axes[1].legend(loc="lower left", fontsize=7, frameon=False)
    axes[1].text(
        0.98,
        0.96,
        (
            f"expanded corrected branch: rho={min(corrected_rho):.4f}-{max(corrected_rho):.4f}"
            "\n"
            rf"max residual {metric_text(max_map_residual)}, "
            rf"one-map $\Delta C$ {metric_text(max_jacobi_drift)}"
        ),
        transform=axes[1].transAxes,
        ha="right",
        va="top",
        fontsize=7,
        color="#263238",
    )
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
