"""Route H / BCR4BP optimized-transfer source-layer figure."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.bcr4bp import (
    correct_bcr4bp_velocity_to_position_target,
    earth_moon_bcr4bp_parameters,
    integrate_bcr4bp,
)
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import load_corrected_dro_family_csv
from qp_orbits.cr3bp import integrate_cr3bp
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.bcr4bp_optimized_transfer"
SOURCE_PAGE = None
REPRO_LEVEL = "Route H / BCR4BP source-layer optimization audit"
SYSTEM = "Earth-Moon BCR4BP"
NOTES = (
    "Accepted Route H quasi-DRO short-transfer candidates ranked by BCR4BP "
    "velocity-correction delta-v; not a full thesis optimized-transfer replacement."
)

AUDIT_PATH = PROJECT_ROOT / "data" / "computed" / "chapter5_optimized_transfer_audit.csv"
ROUTE_H_FAMILY = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_family.csv"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _float(row: dict[str, str], field: str) -> float:
    return float(row[field])


def _best_row(rows: list[dict[str, str]]) -> dict[str, str]:
    accepted = [row for row in rows if row["optimization_acceptance"].lower() == "true"]
    if not accepted:
        raise RuntimeError("no accepted optimized transfer row is available")
    return min(accepted, key=lambda row: _float(row, "objective"))


def _trajectory(initial_state: np.ndarray, tof: float, *, corrected: bool) -> np.ndarray:
    system = SYSTEMS["earth_moon"]
    params = earth_moon_bcr4bp_parameters(system)
    t_eval = np.linspace(0.0, tof, 160)
    if corrected:
        target = integrate_cr3bp(
            initial_state,
            (0.0, tof),
            system.mu,
            t_eval=np.array([tof]),
            rtol=1.0e-11,
            atol=1.0e-13,
            max_step=0.005,
        ).y[:3, -1]
        correction = correct_bcr4bp_velocity_to_position_target(
            initial_state,
            target,
            tof,
            params,
            rtol=1.0e-11,
            atol=1.0e-13,
            max_step=0.005,
            max_nfev=25,
        )
        state = correction.corrected_initial_state
    else:
        state = initial_state
    solution = integrate_bcr4bp(
        state,
        (0.0, tof),
        params,
        t_eval=t_eval,
        rtol=1.0e-11,
        atol=1.0e-13,
        max_step=0.005,
    )
    if not solution.success:
        raise RuntimeError("failed to integrate BCR4BP transfer trajectory")
    return solution.y.T


def _cr3bp_reference(initial_state: np.ndarray, tof: float) -> np.ndarray:
    system = SYSTEMS["earth_moon"]
    t_eval = np.linspace(0.0, tof, 160)
    solution = integrate_cr3bp(
        initial_state,
        (0.0, tof),
        system.mu,
        t_eval=t_eval,
        rtol=1.0e-11,
        atol=1.0e-13,
        max_step=0.005,
    )
    if not solution.success:
        raise RuntimeError("failed to integrate CR3BP reference trajectory")
    return solution.y.T


def _style_3d(ax) -> None:
    ax.set_xlabel("X [nd]", labelpad=-6)
    ax.set_ylabel("Y [nd]", labelpad=-6)
    ax.set_zlabel("Z [nd]", labelpad=-7)
    ax.tick_params(labelsize=7, pad=-2)
    ax.view_init(elev=24, azim=-126)
    ax.set_box_aspect((1.2, 1.0, 0.7))
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis._axinfo["grid"]["color"] = (0.86, 0.86, 0.86, 0.42)
        axis._axinfo["grid"]["linewidth"] = 0.35


def main() -> None:
    apply_style()
    rows = _read_rows(AUDIT_PATH)
    best = _best_row(rows)
    family = load_corrected_dro_family_csv(ROUTE_H_FAMILY, require_contiguous_members=False)
    member = family[-1]
    phase_index = int(best["phase_index"])
    tof = _float(best, "time_of_flight")
    initial_state = member.states[phase_index]

    cr3bp = _cr3bp_reference(initial_state, tof)
    uncorrected = _trajectory(initial_state, tof, corrected=False)
    corrected = _trajectory(initial_state, tof, corrected=True)

    fig = plt.figure(figsize=(9.0, 4.7), constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=(1.25, 1.0))
    ax3d = fig.add_subplot(grid[0, 0], projection="3d")
    ax_obj = fig.add_subplot(grid[0, 1])

    ax3d.plot(cr3bp[:, 0], cr3bp[:, 1], cr3bp[:, 2], color="#374151", linestyle="--", label="CR3BP target arc")
    ax3d.plot(
        uncorrected[:, 0],
        uncorrected[:, 1],
        uncorrected[:, 2],
        color="#b45309",
        alpha=0.55,
        label="BCR4BP uncorrected",
    )
    ax3d.plot(corrected[:, 0], corrected[:, 1], corrected[:, 2], color="#0f766e", label="BCR4BP optimized")
    ax3d.scatter(corrected[0, 0], corrected[0, 1], corrected[0, 2], color="#111827", s=18)
    ax3d.scatter(corrected[-1, 0], corrected[-1, 1], corrected[-1, 2], color="#7c3aed", s=18)
    _style_3d(ax3d)
    ax3d.legend(fontsize=6, loc="upper left")
    ax3d.set_title("Best accepted Route H / BCR4BP short transfer", fontsize=9)

    accepted = [row for row in rows if row["optimization_acceptance"].lower() == "true"]
    phase_values = sorted({int(row["phase_index"]) for row in accepted})
    colors = ["#0f766e", "#b45309", "#7c3aed", "#2563eb", "#be123c"]
    for phase, color in zip(phase_values, colors):
        phase_rows = sorted(
            [row for row in accepted if int(row["phase_index"]) == phase],
            key=lambda row: _float(row, "time_of_flight"),
        )
        ax_obj.plot(
            [_float(row, "time_of_flight_days") for row in phase_rows],
            [_float(row, "delta_v_m_s") for row in phase_rows],
            marker="o",
            markersize=3,
            color=color,
            label=f"phase {phase}",
        )
    ax_obj.scatter(
        [_float(best, "time_of_flight_days")],
        [_float(best, "delta_v_m_s")],
        color="#111827",
        s=32,
        zorder=5,
        label="best",
    )
    ax_obj.set_xlabel("Time of flight [days]")
    ax_obj.set_ylabel(r"Corrective $\Delta v$ [m/s]")
    ax_obj.set_title("Discrete transfer objective", fontsize=9)
    ax_obj.legend(fontsize=6, loc="upper left", ncols=2)
    ax_obj.tick_params(labelsize=7)
    ax_obj.text(
        0.03,
        0.05,
        f"best defect = {_float(best, 'corrected_position_defect'):.2e}\n"
        f"best dv = {_float(best, 'delta_v_m_s'):.3f} m/s",
        transform=ax_obj.transAxes,
        fontsize=7,
    )

    fig.suptitle(
        "Chapter 5 Route H / BCR4BP source-layer transfer optimization",
        fontsize=10,
    )
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
