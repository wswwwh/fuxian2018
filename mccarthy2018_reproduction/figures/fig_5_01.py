"""Figure 5.1: one active-geometry L1 torus trajectory at three durations."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _chapter5_plotting import plot_surface, style_sun_earth_l1_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.1"
SOURCE_PAGE = 96
REPRO_LEVEL = "numerical invariant-torus long-time shadowing reproduction"
SYSTEM = "Sun-Earth CR3BP"
NOTES = (
    "Accepted active-geometry torus and one common-initial-phase trajectory truncated at "
    "325, 1068, and 2182 days; segmentwise invariant-torus shadowing, not unconstrained IVP."
)


def _load_scene() -> tuple[np.ndarray, np.ndarray, tuple[tuple[float, np.ndarray], ...]]:
    path = (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "chapter5_sun_earth_l1_active_geometry_long_trajectory.npz"
    )
    with np.load(path) as data:
        surface = data["torus_surface_nd"].copy()
        invariant_curve = data["invariant_curve_nd"].copy()
        durations = tuple(float(value) for value in data["durations_days"])
        trajectories = tuple(
            (
                duration,
                data[f"trajectory_{int(round(duration)):04d}_days_states"][:, :3].copy(),
            )
            for duration in durations
        )
    if durations != (325.0, 1068.0, 2182.0):
        raise RuntimeError(f"Unexpected Figure 5.1 durations: {durations}")
    return surface, invariant_curve, trajectories


def main() -> None:
    apply_style()
    surface, invariant_curve, trajectories = _load_scene()
    fig = plt.figure(figsize=(8.4, 9.2), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=(1.0, 1.08), hspace=0.12)
    labels = ["(a)", "(b)", "(c)"]
    positions = [grid[0, 0], grid[0, 1], grid[1, :]]
    for position, (duration, trajectory), label in zip(positions, trajectories, labels):
        ax = fig.add_subplot(position, projection="3d")
        plot_surface(ax, surface, alpha=0.34)
        ax.plot(
            invariant_curve[:, 0],
            invariant_curve[:, 1],
            invariant_curve[:, 2],
            color="#6a8f35",
            linewidth=0.70,
            alpha=0.80,
        )
        ax.plot(
            trajectory[:, 0],
            trajectory[:, 1],
            trajectory[:, 2],
            color="#0877bd",
            linewidth=0.78,
            alpha=0.94,
        )
        ax.scatter(*trajectory[0], color="#c9253d", s=8, depthshade=False)
        ax.text2D(0.03, 0.94, f"{duration:.0f} days", transform=ax.transAxes, fontsize=9)
        style_sun_earth_l1_axis(ax, label=label)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
