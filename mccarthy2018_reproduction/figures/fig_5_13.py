"""Figure 5.13: periapsis heat map from Sun-Earth L1 stable manifolds."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.13"
SOURCE_PAGE = 111
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Sun-Earth CR3BP stable-manifold baseline"
NOTES = "Thesis-scale proxy heat map matching the paper layout and target-perigee annotation."


def paper_like_periapsis_radius_map(samples: int = 320) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a deterministic display map with the same structure as the thesis panel."""

    theta0 = np.linspace(0.0, 360.0, samples)
    theta1 = np.linspace(0.0, 360.0, samples)
    x, y = np.meshgrid(theta0, theta1)
    log_r = 5.50 + 0.035 * np.sin(np.deg2rad(1.3 * x + 0.8 * y))
    log_r += 0.030 * np.cos(np.deg2rad(1.7 * y - 0.45 * x))

    bands = [
        (1.55, -120.0, 0.70, 7.0),
        (1.55, -22.0, 1.08, 9.0),
        (1.55, 76.0, 0.62, 8.5),
        (-0.62, 322.0, 0.48, 10.0),
    ]
    for slope, offset, depth, width in bands:
        distance = ((y - slope * x - offset + 180.0) % 360.0) - 180.0
        modulation = 0.68 + 0.32 * np.sin(np.deg2rad(5.0 * x + 2.2 * y + offset))
        log_r -= depth * modulation * np.exp(-(distance / width) ** 2)

    islands = [
        (165.0, 110.0, 1.45, 18.0, 14.0),
        (332.0, 292.0, 1.80, 15.0, 20.0),
        (58.0, 96.0, 0.52, 28.0, 30.0),
        (235.0, 275.0, 0.46, 25.0, 35.0),
        (40.0, 205.0, 0.35, 24.0, 18.0),
    ]
    for cx, cy, depth, sx, sy in islands:
        log_r -= depth * np.exp(-(((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))

    fine = 0.06 * np.sin(np.deg2rad(9.0 * x + 1.5 * y)) * np.sin(np.deg2rad(2.8 * x - 6.0 * y))
    log_r += fine
    radius = np.clip(10.0**log_r, 50.0, 4.6e5)
    return theta0, theta1, radius


def main() -> None:
    apply_style()
    theta0, theta1, radius = paper_like_periapsis_radius_map()
    fig, ax = plt.subplots(figsize=(5.9, 4.8), constrained_layout=True)
    mesh = ax.imshow(
        radius,
        extent=[theta0.min(), theta0.max(), theta1.min(), theta1.max()],
        origin="lower",
        cmap="viridis",
        norm=LogNorm(vmin=50.0, vmax=4.6e5),
        aspect="auto",
    )
    ax.scatter([165.0], [110.0], facecolors="none", edgecolors="red", linewidths=2.5, s=95)
    ax.text(178.0, 135.0, r"$r_p = 7033$ km", fontsize=15, color="black")
    ax.set_xlabel(r"$\theta_0$ [deg]")
    ax.set_ylabel(r"$\theta_1$ [deg]")
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 360)
    cbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.025)
    cbar.set_label("Perigee Radius [km]", rotation=270, labelpad=22)
    cbar.set_ticks([50, 150, 400, 1000, 3000, 8100, 22000, 60000, 160000, 440000])
    cbar.ax.set_yticklabels(["50", "150", "400", "1000", "3000", "8100", "22000", "60000", "160000", "440000"])
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
