"""Figure 3.16: constant-mapping-time quasi-DRO tori."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    load_or_compute_extended_corrected_dro_family,
    sweep_corrected_dro_member,
    write_chapter3_quasi_dro_validation,
)
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import quasi_dro_family


FIGURE_ID = "3.16"
SOURCE_PAGE = 82
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Proxy surfaces retained as references with expanded corrected fixed-mapping-time CR3BP quasi-DRO wireframes."
FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv"
EXTENDED_FAMILY_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family_extended.csv"
)
VALIDATION_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_extended_validation.csv"
CONTINUATION_LOG_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_continuation_log.csv"


def plot_corrected_torus(ax, member) -> None:
    system = SYSTEMS["earth_moon"]
    sweep = sweep_corrected_dro_member(member, system, time_samples=23)
    points = np.concatenate([sweep.points, sweep.points[:, :1]], axis=1)
    ax.plot_wireframe(
        points[:, :, 0],
        points[:, :, 1],
        points[:, :, 2],
        rstride=3,
        cstride=3,
        color="#16856b",
        linewidth=0.72,
        alpha=0.92,
    )
    curve = np.vstack([member.points, member.points[0]])
    ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#075b4d", linewidth=1.55)
    ax.text2D(
        0.02,
        0.96,
        rf"corrected: $|z|_{{max}}={member.max_abs_z_km:.0f}$ km, $\rho={member.rotation_angle_rad:.3f}$",
        transform=ax.transAxes,
        fontsize=7,
        color="#075b4d",
        va="top",
    )


def style_axis(ax, label: str) -> None:
    system = SYSTEMS["earth_moon"]
    points = compute_libration_points(system.mu)
    moon_x = 1.0 - system.mu
    ax.scatter([points["L2"].x, points["L1"].x], [0.0, 0.0], [0.0, 0.0], color="#cc4c25", s=8)
    ax.scatter([moon_x], [0.0], [0.0], color="black", s=9)
    ax.text(points["L2"].x - 0.025, 0.010, 0.025, r"$L_2$", fontsize=8)
    ax.text(points["L1"].x + 0.010, -0.005, -0.035, r"$L_1$", fontsize=8)
    ax.text(moon_x - 0.020, -0.012, 0.010, "Moon", fontsize=8)
    ax.set_xlim(0.75, 1.22)
    ax.set_ylim(-0.30, 0.30)
    ax.set_zlim(-0.11, 0.11)
    ax.set_xlabel("X [nd]", labelpad=-6)
    ax.set_ylabel("Y [nd]", labelpad=-5)
    ax.set_zlabel("Z [nd]", labelpad=-6)
    ax.tick_params(labelsize=8, pad=-2)
    ax.view_init(elev=22, azim=-132)
    ax.set_box_aspect((1.5, 1.7, 0.75))
    ax.text2D(0.47, -0.10, label, transform=ax.transAxes, fontsize=12)


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    family = quasi_dro_family(system, samples=4, n_major=128, n_minor=28)
    corrected_family = load_or_compute_extended_corrected_dro_family(
        FAMILY_PATH,
        EXTENDED_FAMILY_PATH,
        CONTINUATION_LOG_PATH,
        system,
    )
    write_chapter3_quasi_dro_validation(VALIDATION_PATH, corrected_family, system)
    selected_indices = np.linspace(0, len(corrected_family) - 1, 4, dtype=int)
    selected_corrected = [corrected_family[index] for index in selected_indices]
    fig = plt.figure(figsize=(8.3, 7.4), constrained_layout=True)
    panels = zip(family, selected_corrected, ["(a)", "(b)", "(c)", "(d)"])
    for idx, (member, corrected_member, label) in enumerate(panels, start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        surface = member.surface
        ax.plot_surface(surface[:, :, 0], surface[:, :, 1], surface[:, :, 2], color="#b8b8b8",
                        edgecolor="none", linewidth=0, antialiased=True, shade=True, alpha=0.30)
        curve = member.invariant_curve
        ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#7f8c8d", linewidth=0.9, linestyle="--")
        plot_corrected_torus(ax, corrected_member)
        style_axis(ax, label)
    rho_values = [member.rotation_angle_rad for member in corrected_family]
    z_values = [member.max_abs_z_km for member in corrected_family]
    fig.suptitle(
        (
            "Expanded corrected branch: "
            f"rho={min(rho_values):.4f}-{max(rho_values):.4f} rad, "
            f"|z|max={min(z_values):.0f}-{max(z_values):.0f} km; "
            "grey surfaces are thesis-scale proxy references"
        ),
        fontsize=9,
        color="#263238",
    )
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
