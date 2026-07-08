"""Route H Chapter 4 source-layer DG/manifold figure for high-amplitude quasi-DROs."""

from __future__ import annotations

import csv
import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import _member_from_correction
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    _corrected_curve_manifold_from_dg,
    corrected_curve_dg,
    real_hyperbolic_eigen_index,
)


FIGURE_ID = "4.route_h"
SOURCE_PAGE = None
REPRO_LEVEL = "Route H source-layer numerical audit"
SYSTEM = "Earth-Moon CR3BP"
NOTES = (
    "Accepted high-amplitude quasi-DRO corrections converted to Chapter 4 "
    "discrete-curve DG spectra and short local unstable manifold probes."
)

ROUTE_H_CACHE = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "cache"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
DG_PATH = PROJECT_ROOT / "data" / "computed" / "chapter4_route_h_quasi_dro_dg.csv"
MANIFOLD_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter4_route_h_quasi_dro_manifold_probe.csv"
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _load_cache(path: Path):
    with path.open("rb") as stream:
        return pickle.load(stream)


def _float(row: dict[str, str], field: str) -> float:
    return float(row[field])


def _route_h_manifold_sheet(correction, *, max_step: float = 0.02):
    system = SYSTEMS["earth_moon"]
    dg = corrected_curve_dg(correction, max_step=max_step)
    eigen_index = real_hyperbolic_eigen_index(dg, branch="unstable")
    return _corrected_curve_manifold_from_dg(
        system.mu,
        dg=dg,
        branch="unstable",
        eigen_index=eigen_index,
        duration_periods=0.1,
        perturbation_scale=1.0e-7,
        perturbation_sign=1.0,
        time_samples=12,
        max_step=max_step,
    )


def _style_3d_axis(ax) -> None:
    ax.set_xlabel("X [nd]", labelpad=-6)
    ax.set_ylabel("Y [nd]", labelpad=-5)
    ax.set_zlabel("Z [nd]", labelpad=-6)
    ax.set_xlim(0.78, 0.86)
    ax.set_ylim(-0.13, 0.16)
    ax.set_zlim(-0.05, 0.05)
    ax.view_init(elev=23, azim=-132)
    ax.set_box_aspect((0.95, 1.55, 0.65))
    ax.tick_params(labelsize=7, pad=-2)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis._axinfo["grid"]["color"] = (0.88, 0.88, 0.88, 0.40)
        axis._axinfo["grid"]["linewidth"] = 0.35


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    dg_rows = _read_rows(DG_PATH)
    manifold_rows = _read_rows(MANIFOLD_PATH)
    cache = _load_cache(ROUTE_H_CACHE)
    selected = [int(row["member_index"]) for row in dg_rows]
    colors = ["#0f766e", "#b45309", "#7c3aed"]

    z_values = np.asarray([_float(row, "max_abs_z_km") for row in dg_rows], dtype=float)
    stability = np.asarray([_float(row, "stability_index") for row in dg_rows], dtype=float)
    multipliers = np.asarray([_float(row, "max_multiplier") for row in dg_rows], dtype=float)
    det_errors = np.asarray([_float(row, "determinant_error_from_one") for row in dg_rows])
    reciprocity = np.asarray([_float(row, "real_pair_reciprocity_error") for row in dg_rows])
    jacobi = np.asarray([_float(row, "jacobi_drift_max") for row in manifold_rows])

    fig = plt.figure(figsize=(9.4, 5.3), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, width_ratios=(0.88, 1.28))
    ax_stability = fig.add_subplot(grid[0, 0])
    ax_quality = fig.add_subplot(grid[1, 0])
    ax_sheet = fig.add_subplot(grid[:, 1], projection="3d")

    ax_stability.plot(z_values, stability, color="#0f766e", marker="o", label=r"$\nu$")
    ax_stability_b = ax_stability.twinx()
    ax_stability_b.plot(
        z_values,
        multipliers,
        color="#b45309",
        marker="s",
        markersize=4,
        linewidth=1.2,
        label=r"$|\lambda|_{max}$",
    )
    ax_stability.set_xlabel(r"$|z|_{max}$ [km]")
    ax_stability.set_ylabel(r"Stability index, $\nu$")
    ax_stability_b.set_ylabel(r"$|\lambda|_{max}$")
    ax_stability.tick_params(labelsize=7)
    ax_stability_b.tick_params(labelsize=7)

    ax_quality.semilogy(z_values, det_errors, color="#0f766e", marker="o", label=r"$|\det DG-1|$")
    ax_quality.semilogy(z_values, reciprocity, color="#7c3aed", marker="^", label="reciprocity")
    ax_quality.semilogy(z_values, jacobi, color="#b45309", marker="s", label=r"manifold $\Delta C$")
    ax_quality.set_xlabel(r"$|z|_{max}$ [km]")
    ax_quality.set_ylabel("audit residual")
    ax_quality.legend(fontsize=6, loc="upper right")
    ax_quality.tick_params(labelsize=7)

    for member_index, color in zip(selected, colors):
        correction = cache[member_index]
        member = _member_from_correction(member_index, correction, system)
        sheet = _route_h_manifold_sheet(correction)
        base_curve = np.vstack([member.points, member.points[0]])
        ax_sheet.plot(
            base_curve[:, 0],
            base_curve[:, 1],
            base_curve[:, 2],
            color=color,
            linewidth=1.1,
            alpha=0.75,
        )
        surface = sheet.surface
        ax_sheet.plot_wireframe(
            surface[:, :, 0],
            surface[:, :, 1],
            surface[:, :, 2],
            rstride=2,
            cstride=5,
            color=color,
            linewidth=0.28,
            alpha=0.55,
        )
        ax_sheet.text(
            float(surface[-1, 0, 0]),
            float(surface[-1, 0, 1]),
            float(surface[-1, 0, 2]),
            f"{member.max_abs_z_km:.0f} km",
            color=color,
            fontsize=7,
        )

    _style_3d_axis(ax_sheet)
    ax_sheet.set_title("Route H local unstable manifold probes", fontsize=10, pad=2)
    fig.suptitle(
        "Chapter 4 Route H source layer: accepted quasi-DRO DG spectra and local manifold probes",
        fontsize=10,
    )
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
