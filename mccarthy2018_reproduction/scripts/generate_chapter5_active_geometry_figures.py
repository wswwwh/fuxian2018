"""Create auditable PNG/PDF figures and NPZ bundles for active Chapter 5 outputs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "data" / "computed" / "chapter5_active_geometry_stable_manifold_tight_target_scan.csv"
LEO = ROOT / "data" / "computed" / "chapter5_active_geometry_leo_transfer.csv"
OUT = ROOT / "outputs" / "chapter5_active_geometry_figures"
OUT.mkdir(parents=True, exist_ok=True)


def _save_pair(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    with SCAN.open(newline="", encoding="utf-8") as stream:
        scan_rows = list(csv.DictReader(stream))
    theta0 = np.array([float(row["theta0_deg"]) for row in scan_rows])
    theta1 = np.array([float(row["theta1_deg"]) for row in scan_rows])
    radius = np.array([float(row["periapsis_radius_km"]) for row in scan_rows])
    drift = np.array([float(row["jacobi_drift"]) for row in scan_rows])
    theta0_values = np.unique(theta0)
    theta1_values = np.unique(theta1)
    radius_grid = radius.reshape(theta0_values.size, theta1_values.size)
    best = int(np.argmin(np.abs(radius - 7033.0)))
    np.savez_compressed(
        ROOT / "data" / "computed" / "chapter5_active_geometry_stable_manifold_tight_target.npz",
        theta0_deg=theta0_values,
        theta1_deg=theta1_values,
        periapsis_radius_km=radius_grid,
        jacobi_drift=drift.reshape(theta0_values.size, theta1_values.size),
        best_theta0_deg=theta0[best],
        best_theta1_deg=theta1[best],
        best_periapsis_radius_km=radius[best],
    )

    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    image = ax.imshow(
        radius_grid,
        origin="lower",
        aspect="auto",
        extent=(theta1_values.min(), theta1_values.max(), theta0_values.min(), theta0_values.max()),
        cmap="viridis",
    )
    contour = ax.contour(
        theta1_values,
        theta0_values,
        radius_grid,
        levels=[7033.0],
        colors="#D55E00",
        linewidths=1.5,
    )
    ax.clabel(contour, fmt={7033.0: "7033 km"}, inline=True, fontsize=8)
    ax.scatter([theta1[best]], [theta0[best]], marker="*", s=90, color="#E69F00", edgecolor="black", linewidth=0.5, zorder=3)
    ax.set_xlabel(r"Invariant-curve phase $\theta_1$ (deg)")
    ax.set_ylabel(r"Mapping phase $\theta_0$ (deg)")
    ax.set_title("Accepted active-geometry stable-manifold periapsis")
    colorbar = fig.colorbar(image, ax=ax, label="Periapsis radius (km)")
    colorbar.ax.tick_params(labelsize=8)
    _save_pair(fig, "chapter5_active_geometry_fig513_stable_manifold_heatmap")

    with LEO.open(newline="", encoding="utf-8") as stream:
        leo_rows = list(csv.DictReader(stream))
    days = np.array([float(row["elapsed_days"]) for row in leo_rows])
    radii = np.array([float(row["earth_radius_km"]) for row in leo_rows])
    jacobi = np.array([float(row["jacobi"]) for row in leo_rows])
    states = np.array(
        [
            [float(row[key]) for key in ("x_nd", "y_nd", "z_nd", "xdot_nd", "ydot_nd", "zdot_nd")]
            for row in leo_rows
        ]
    )
    np.savez_compressed(
        ROOT / "data" / "computed" / "chapter5_active_geometry_leo_transfer.npz",
        elapsed_days=days,
        earth_radius_km=radii,
        jacobi=jacobi,
        states=states,
    )
    fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    ax.plot(days, radii, color="#0072B2", linewidth=1.4, label="CR3BP transfer")
    ax.axhline(7033.0, color="#D55E00", linestyle="--", linewidth=1.2, label="7033 km target")
    ax.set_xlabel("Elapsed time from periapsis (days)")
    ax.set_ylabel("Earth-relative radius (km)")
    ax.set_title("Accepted active-geometry Lissajous-to-LEO transfer")
    ax.set_yscale("log")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    _save_pair(fig, "chapter5_active_geometry_fig514_leo_transfer")

    print(OUT)
    print(ROOT / "data" / "computed" / "chapter5_active_geometry_stable_manifold_tight_target.npz")
    print(ROOT / "data" / "computed" / "chapter5_active_geometry_leo_transfer.npz")


if __name__ == "__main__":
    main()
