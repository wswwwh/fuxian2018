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
REPRO_LEVEL = "numerical reproduction"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "N=25 corrected L2 quasi-halo at paper-reported JC precision with raw DG spectrum."


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
    ax3d.plot_surface(surface[:, :, 0], surface[:, :, 1], surface[:, :, 2], color="#168bd2",
                      edgecolor="none", linewidth=0, alpha=0.72, shade=True)
    curve = surface[0]
    ax3d.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#168bd2", linewidth=1.4)
    ax3d.plot(surface[:, 0, 0], surface[:, 0, 1], surface[:, 0, 2], color="#168bd2", linewidth=1.6)
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
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
