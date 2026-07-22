"""Figure 3.16: audited constant-mapping-time quasi-DRO tori."""

from __future__ import annotations

import csv

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    CorrectedDROFamilyMember,
    load_best_chapter3_corrected_dro_family,
    sweep_corrected_dro_member,
    write_chapter3_quasi_dro_validation,
)
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "3.16"
SOURCE_PAGE = 82
REPRO_LEVEL = "audited Route H source layer with thesis-range boundary"
SYSTEM = "Earth-Moon CR3BP"
NOTES = (
    "The four fixed-time Jacobi anchors are drawn from the hybrid cold-start target-state "
    "audit and rendered as smooth surfaces. The blue central orbit is the audited periodic DRO."
)
FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv"
EXTENDED_FAMILY_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family_extended.csv"
)
VALIDATION_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_extended_validation.csv"
CONTINUATION_LOG_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_continuation_log.csv"
PALC_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
PALC_VALIDATION_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_validation.csv"
ROUTE_H_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_family.csv"
ROUTE_H_VALIDATION_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_validation.csv"
)
TARGET_STATE_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_h_fixed_time_target_states.csv"
)
PERIODIC_DRO_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter5_corrected_dro_quasi_dro_return.csv"
)


def load_target_members(path) -> tuple[CorrectedDROFamilyMember, ...]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    grouped: dict[float, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(float(row["target_jacobi"]), []).append(row)
    members = []
    for member_id, target in enumerate(sorted(grouped, reverse=True)):
        member_rows = sorted(grouped[target], key=lambda row: int(row["phase_index"]))
        states = np.asarray(
            [
                [float(row[field]) for field in ("x", "y", "z", "xdot", "ydot", "zdot")]
                for row in member_rows
            ]
        )
        jacobi = np.asarray([float(row["point_jacobi"]) for row in member_rows])
        phases = np.asarray([float(row["phase_rad"]) for row in member_rows])
        amplitude = float(np.sqrt(2.0 * np.mean(states[:, 2] ** 2)))
        members.append(
            CorrectedDROFamilyMember(
                member=member_id,
                curve_indices=np.arange(len(member_rows)),
                phases_rad=phases,
                states=states,
                jacobi_values=jacobi,
                target_vertical_amplitude_nd=amplitude,
                target_vertical_amplitude_km=amplitude * SYSTEMS["earth_moon"].length_unit_km,
                max_abs_z_km=float(
                    np.max(np.abs(states[:, 2])) * SYSTEMS["earth_moon"].length_unit_km
                ),
                rotation_angle_rad=float(member_rows[0]["rotation_angle_rad"]),
                mapping_time_days=float(member_rows[0]["mapping_time_days"]),
                map_residual_norm=float(member_rows[0]["max_map_residual"]),
                amplitude_residual=0.0,
                phase_residual=0.0,
                curve_jacobi_span=float(member_rows[0]["curve_jacobi_span"]),
            )
        )
    return tuple(members)


def load_periodic_dro(path) -> np.ndarray:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = [row for row in csv.DictReader(stream) if row["kind"] == "periodic_dro"]
    rows.sort(key=lambda row: int(row["time_index"]))
    return np.asarray([[float(row[name]) for name in ("x", "y", "z")] for row in rows])


def plot_corrected_torus(
    ax,
    member,
    periodic_dro: np.ndarray,
    *,
    time_samples: int = 48,
) -> None:
    system = SYSTEMS["earth_moon"]
    sweep = sweep_corrected_dro_member(member, system, time_samples=time_samples)
    points = np.concatenate([sweep.points, sweep.points[:, :1]], axis=1)
    ax.plot_surface(
        points[:, :, 0],
        points[:, :, 1],
        points[:, :, 2],
        color="#b8b8b8",
        edgecolor="none",
        linewidth=0.0,
        antialiased=True,
        shade=False,
        alpha=0.74,
        rcount=points.shape[0],
        ccount=points.shape[1],
    )
    curve = np.vstack([member.points, member.points[0]])
    ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#555555", linewidth=0.65, alpha=0.8)
    ax.plot(
        periodic_dro[:, 0],
        periodic_dro[:, 1],
        periodic_dro[:, 2],
        color="#1f77b4",
        linewidth=1.35,
        zorder=10,
    )
    ax.text2D(
        0.02,
        0.96,
        rf"$JC={member.mean_jacobi:.4f}$, $|z|_{{max}}={member.max_abs_z_km:.0f}$ km"
        "\n"
        rf"$\rho={member.rotation_angle_rad:.3f}$, $N={member.states.shape[0]}$",
        transform=ax.transAxes,
        fontsize=7,
        color="#075b4d",
        va="top",
    )


def representative_members(family, count: int = 4):
    if len(family) < count:
        raise ValueError(f"need at least {count} corrected quasi-DRO members")
    indices = np.linspace(0, len(family) - 1, count, dtype=int)
    return tuple(family[int(index)] for index in indices)


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
    if TARGET_STATE_PATH.exists():
        corrected_family = load_target_members(TARGET_STATE_PATH)
    else:
        corrected_family = load_best_chapter3_corrected_dro_family(
            FAMILY_PATH,
            EXTENDED_FAMILY_PATH,
            PALC_FAMILY_PATH,
            CONTINUATION_LOG_PATH,
            system,
            ROUTE_H_FAMILY_PATH,
        )
    periodic_dro = load_periodic_dro(PERIODIC_DRO_PATH)
    fig = plt.figure(figsize=(7.6, 7.0), constrained_layout=True)
    panels = zip(representative_members(corrected_family), ["(a)", "(b)", "(c)", "(d)"])
    for idx, (member, label) in enumerate(panels, start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        plot_corrected_torus(ax, member, periodic_dro)
        style_axis(ax, label)
    fig.suptitle(
        "Audited Route H source layer; full thesis branch/range equivalence remains open",
        fontsize=9,
        color="#8a4b08",
    )
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
