"""Figure 5.1: Sun-Earth L1 quasi-vertical long propagation."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import csv

from _chapter5_plotting import plot_surface, style_sun_earth_l1_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.1"
SOURCE_PAGE = 96
REPRO_LEVEL = "numerical corrected Lissajous propagation reproduction"
SYSTEM = "Sun-Earth CR3BP"
NOTES = "Corrected 3600-point L1 Lissajous torus and propagated torus trajectories; no proxy layers."


def _load_corrected_surface() -> np.ndarray:
    path = PROJECT_ROOT / "data" / "computed" / "chapter5_sun_earth_l1_lissajous_torus_surface.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    values = np.array([[float(row[key]) for key in ("x_nd", "y_nd", "z_nd")] for row in rows])
    return values.reshape(60, 60, 3)


def main() -> None:
    apply_style()
    surface = _load_corrected_surface()
    fig = plt.figure(figsize=(7.6, 7.0), constrained_layout=True)
    counts = [1, 8, 18]
    labels = ["(a)", "(b)", "(c)"]
    positions = [221, 222, 212]
    for position, count, label in zip(positions, counts, labels):
        ax = fig.add_subplot(position, projection="3d")
        plot_surface(ax, surface, alpha=0.34)
        indices = np.linspace(0, surface.shape[1] - 1, count, dtype=int)
        for index in indices:
            curve = surface[:, index]
            ax.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#a71930", linewidth=0.82, alpha=0.90)
        style_sun_earth_l1_axis(ax, label=label)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
