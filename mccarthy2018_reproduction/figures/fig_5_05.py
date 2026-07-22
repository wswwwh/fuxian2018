"""Figure 5.5: quasi-DRO and associated planar periodic DRO."""

from __future__ import annotations

import matplotlib.pyplot as plt
import csv
import numpy as np

from _chapter5_plotting import plot_surface, style_earth_moon_dro_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.5"
SOURCE_PAGE = 102
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Audited corrected CR3BP 2:1 resonant DRO, ten-return quasi-DRO, and corrected torus; no proxy surface."


def _load_corrected_scene() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    path = PROJECT_ROOT / "data" / "computed" / "chapter5_corrected_dro_quasi_dro_return.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    def curve(kind: str) -> np.ndarray:
        selected = sorted(
            (row for row in rows if row["kind"] == kind),
            key=lambda row: int(row["time_index"]),
        )
        return np.array([[float(row[key]) for key in ("x", "y", "z")] for row in selected])

    torus_rows = [row for row in rows if row["kind"] == "corrected_local_torus"]
    time_count = len({int(row["time_index"]) for row in torus_rows})
    phase_count = len({int(row["curve_index"]) for row in torus_rows})
    torus_rows.sort(key=lambda row: (int(row["time_index"]), int(row["curve_index"])))
    surface = np.array([[float(row[key]) for key in ("x", "y", "z")] for row in torus_rows])
    surface = surface.reshape(time_count, phase_count, 3)
    periodic = curve("periodic_dro")
    quasi = curve("quasi_dro_10_return")
    invariant_curve = surface[0]
    return surface, periodic, quasi, invariant_curve


def main() -> None:
    apply_style()
    surface, periodic, quasi, invariant_curve = _load_corrected_scene()
    fig = plt.figure(figsize=(6.3, 4.8), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    plot_surface(ax, surface, alpha=0.34)
    ax.plot(
        periodic[:, 0],
        periodic[:, 1],
        periodic[:, 2],
        color="#78a641",
        linewidth=1.2,
    )
    ax.plot(
        quasi[:, 0],
        quasi[:, 1],
        quasi[:, 2],
        color="#0877bd",
        linewidth=0.82,
        alpha=0.94,
    )
    ax.plot(
        invariant_curve[:, 0],
        invariant_curve[:, 1],
        invariant_curve[:, 2],
        color="black",
        linewidth=0.65,
    )
    marker = quasi[0]
    ax.plot([marker[0], marker[0]], [marker[1], marker[1]], [-0.070, marker[2]], color="black", linewidth=0.9)
    ax.scatter(*marker, color="#c9253d", s=18)
    style_earth_moon_dro_axis(ax)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
