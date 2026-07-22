"""Figure 5.13: periapsis heat map from Sun-Earth L1 stable manifolds."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
import csv

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.13"
SOURCE_PAGE = 111
REPRO_LEVEL = "numerical two-angle stable-manifold reproduction"
SYSTEM = "Sun-Earth CR3BP stable-manifold baseline"
NOTES = "Full accepted active-geometry two-angle scan with the 7033-km tight-scan candidate overlaid; no legacy stripe map."


def numerical_periapsis_radius_map() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    path = PROJECT_ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_stable_manifold_scan.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    theta0 = np.array(sorted({float(row["theta0_deg"]) for row in rows}))
    theta1 = np.array(sorted({float(row["theta1_deg"]) for row in rows}))
    lookup = {
        (float(row["theta0_deg"]), float(row["theta1_deg"])): float(row["periapsis_radius_km"])
        for row in rows
    }
    radius = np.array([[lookup[(x, y)] for x in theta0] for y in theta1])
    return theta0, theta1, radius


def accepted_7033_candidate() -> tuple[float, float, float]:
    path = PROJECT_ROOT / "data" / "computed" / "chapter5_active_geometry_stable_manifold_tight_target_scan.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    selected = min(rows, key=lambda row: abs(float(row["periapsis_radius_km"]) - 7_033.0))
    return (
        float(selected["theta0_deg"]),
        float(selected["theta1_deg"]),
        float(selected["periapsis_radius_km"]),
    )


def main() -> None:
    apply_style()
    theta0, theta1, radius = numerical_periapsis_radius_map()
    best_theta0, best_theta1, best_radius = accepted_7033_candidate()
    fig, ax = plt.subplots(figsize=(5.9, 4.8), constrained_layout=True)
    mesh = ax.pcolormesh(
        theta0,
        theta1,
        radius,
        cmap="viridis",
        norm=LogNorm(vmin=max(50.0, float(radius.min())), vmax=float(radius.max())),
        shading="auto",
    )
    ax.scatter([best_theta0], [best_theta1], facecolors="none", edgecolors="red", linewidths=2.0, s=80)
    ax.annotate(
        rf"$r_p = {best_radius:.1f}$ km",
        xy=(best_theta0, best_theta1),
        xytext=(best_theta0 + 24.0, best_theta1 + 28.0),
        arrowprops={"arrowstyle": "-", "lw": 0.7, "color": "red"},
        fontsize=10,
    )
    ax.set_xlabel(r"$\theta_0$ [deg]")
    ax.set_ylabel(r"$\theta_1$ [deg]")
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 360)
    cbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.025)
    cbar.set_label("Perigee Radius [km]", rotation=270, labelpad=22)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
