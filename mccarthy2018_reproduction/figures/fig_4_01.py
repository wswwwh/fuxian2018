"""Figure 4.1: quasi-halo orbit and DG eigenvalue structure."""

from __future__ import annotations

import csv
import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import add_earth_moon_labels
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
FIGURE_ID = "4.1"
SOURCE_PAGE = 86
REPRO_LEVEL = "quantitative DG reproduction with torus-geometry boundary"
SYSTEM = "Earth-Moon CR3BP"
NOTES = (
    "The raw N=25 DG spectrum reproduces the reported stability target. The accepted "
    "state family is phase-degenerate and is therefore shown as a collapsed orbit, not a torus."
)


def _read_rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    apply_style()
    _ = SYSTEMS["earth_moon"]
    state_rows = _read_rows(
        PROJECT_ROOT / "data" / "computed" / "chapter4_fig41_reported_precision_states.csv"
    )
    spectrum_rows = _read_rows(
        PROJECT_ROOT / "data" / "computed" / "chapter4_fig41_reported_precision_spectrum.csv"
    )
    time_count = 1 + max(int(row["time_index"]) for row in state_rows)
    curve_count = 1 + max(int(row["curve_index"]) for row in state_rows)
    surface = np.array(
        [[float(row[name]) for name in ("x", "y", "z")] for row in state_rows]
    ).reshape(time_count, curve_count, 3)

    fig = plt.figure(figsize=(8.2, 3.65), constrained_layout=True)
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    phase_width_nd = max(
        float(np.max(np.linalg.norm(slice_[:, None, :] - slice_[None, :, :], axis=2)))
        for slice_ in surface
    )
    phase_width_m = phase_width_nd * SYSTEMS["earth_moon"].length_unit_km * 1000.0
    for curve_index in range(0, curve_count, max(1, curve_count // 8)):
        curve = surface[:, curve_index]
        ax3d.plot(
            curve[:, 0],
            curve[:, 1],
            curve[:, 2],
            color="#7fb8da",
            linewidth=0.65,
            alpha=0.55,
        )
    representative = surface[:, 0]
    ax3d.plot(
        representative[:, 0],
        representative[:, 1],
        representative[:, 2],
        color="#168bd2",
        linewidth=1.7,
    )
    add_earth_moon_labels(ax3d, include_l1=False, include_l2=False)
    ax3d.set_xlim(0.982, 1.030)
    ax3d.set_ylim(-0.052, 0.052)
    ax3d.set_zlim(-0.195, 0.018)
    ax3d.set_xlabel("X [nd]", labelpad=-6)
    ax3d.set_ylabel("Y [nd]", labelpad=-6)
    ax3d.set_zlabel("Z [nd]", labelpad=-6)
    ax3d.view_init(elev=25, azim=-132)
    ax3d.set_box_aspect((1.0, 1.0, 1.55))
    ax3d.tick_params(labelsize=8, pad=-2)
    ax3d.text2D(
        0.02,
        0.97,
        "Finite-torus geometry: FAIL\n"
        f"max phase width = {phase_width_m:.2f} m",
        transform=ax3d.transAxes,
        fontsize=7,
        va="top",
        color="#8a4b08",
        bbox={"facecolor": "white", "alpha": 0.84, "edgecolor": "none", "pad": 2},
    )

    ax = fig.add_subplot(1, 2, 2)
    colors = {"unstable": "#b2182b", "unit": "0.25", "stable": "#168bd2"}
    for name in ("unstable", "unit", "stable"):
        values = np.array(
            [complex(float(row["real"]), float(row["imag"])) for row in spectrum_rows if row["classification"] == name]
        )
        if name != "unit":
            ordered = values[np.argsort(np.angle(values))]
            closed = np.append(ordered, ordered[0])
            ax.plot(np.real(closed), np.imag(closed), color=colors[name], linewidth=1.0, alpha=0.8)
        ax.scatter(np.real(values), np.imag(values), color=colors[name], s=14)
    ax.axhline(0.0, color="0.82", linewidth=0.8)
    ax.axvline(0.0, color="0.82", linewidth=0.8)
    ax.set_xlabel(r"$\mathrm{Re}(\lambda)$")
    ax.set_ylabel(r"$\mathrm{Imag}(\lambda)$")
    ax.set_xlim(-2.55, 2.55)
    ax.set_ylim(-2.45, 2.45)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(r"Raw DG spectrum: $\nu=1.3837$ target passed", fontsize=8, color="#075b4d")
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
