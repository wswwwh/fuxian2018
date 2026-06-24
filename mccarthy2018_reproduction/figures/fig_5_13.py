"""Figure 5.13: periapsis heat map from Sun-Earth L1 stable manifolds."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import periapsis_radius_map, sun_earth_l1_stable_manifold_baseline
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.13"
SOURCE_PAGE = 111
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Sun-Earth CR3BP stable-manifold baseline"
NOTES = "Thesis-scale proxy heat map with a corrected periodic-L1 stable-manifold phase scan inset."


def main() -> None:
    apply_style()
    theta0, theta1, radius = periapsis_radius_map()
    baseline = sun_earth_l1_stable_manifold_baseline(
        target_periapsis_radius_km=7033.0,
        scan_samples=72,
        trajectory_samples=240,
    )
    fig, ax = plt.subplots(figsize=(6.6, 4.8), constrained_layout=True)
    mesh = ax.imshow(
        radius,
        extent=[theta0.min(), theta0.max(), theta1.min(), theta1.max()],
        origin="lower",
        cmap="viridis",
        norm=LogNorm(vmin=50.0, vmax=4.6e5),
        aspect="auto",
    )
    ax.scatter([165.0], [110.0], facecolors="none", edgecolors="red", linewidths=2.5, s=95)
    ax.text(172.0, 132.0, r"$r_p = 7033$ km", fontsize=15, color="black")
    ax.set_xlabel(r"$\theta_0$ [deg]")
    ax.set_ylabel(r"$\theta_1$ [deg]")
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 360)
    cbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.025)
    cbar.set_label("Perigee Radius [km]", rotation=270, labelpad=22)
    cbar.set_ticks([50, 150, 400, 1000, 3000, 8100, 22000, 60000, 160000, 440000])
    cbar.ax.set_yticklabels(["50", "150", "400", "1000", "3000", "8100", "22000", "60000", "160000", "440000"])
    inset = ax.inset_axes([0.055, 0.62, 0.40, 0.30])
    inset.semilogy(
        baseline.scan_phase_deg,
        np.clip(baseline.scan_periapsis_radius_km, 50.0, 4.6e5),
        color="#1b9e77",
        marker="o",
        markersize=1.8,
        linewidth=0.8,
    )
    inset.axhline(7033.0, color="#c9253d", linewidth=0.6, alpha=0.75)
    inset.scatter(
        [baseline.selected_phase_deg],
        [baseline.selected_periapsis_radius_km],
        facecolors="none",
        edgecolors="#c9253d",
        s=24,
        linewidths=1.0,
        zorder=4,
    )
    inset.set_xlim(0.0, 360.0)
    inset.set_ylim(50.0, 6.0e5)
    inset.set_xlabel(r"periodic phase [deg]", fontsize=5.5, labelpad=0)
    inset.set_ylabel(r"$r_p$ [km]", fontsize=5.5, labelpad=0)
    inset.tick_params(labelsize=5.5, pad=1)
    inset.grid(True, alpha=0.18)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
