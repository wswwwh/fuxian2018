"""Figure 5.14: LEO to quasi-periodic Sun-Earth L1 Lissajous transfer."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import add_axis_arrow, plot_surface
from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import leo_to_l1_transfer, sun_earth_l1_stable_manifold_baseline
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.14"
SOURCE_PAGE = 112
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Sun-Earth CR3BP stable-manifold baseline"
NOTES = "Proxy Lissajous context with a corrected periodic-L1 stable manifold targeted to 6563 km."


def main() -> None:
    apply_style()
    scene = leo_to_l1_transfer()
    proxy_transfer, lissajous = scene.curves
    baseline = sun_earth_l1_stable_manifold_baseline(
        target_periapsis_radius_km=6563.0,
        scan_samples=36,
    )
    system = SYSTEMS["sun_earth"]
    transfer = baseline.selected_states[:, :3] * system.length_unit_km
    periodic_orbit = baseline.orbit_states[:, :3] * system.length_unit_km
    earth = ((1.0 - system.mu) * system.length_unit_km, 0.0, 0.0)

    fig = plt.figure(figsize=(6.5, 8.2), constrained_layout=True)
    ax = fig.add_subplot(211, projection="3d")
    plot_surface(ax, scene.surface, alpha=0.46)
    ax.plot(proxy_transfer[:, 0], proxy_transfer[:, 1], proxy_transfer[:, 2], color="#9b9b9b", linewidth=0.7,
            linestyle="--", alpha=0.65)
    ax.plot(transfer[:, 0], transfer[:, 1], transfer[:, 2], color="#1f8fd4", linewidth=1.2)
    ax.plot(lissajous[:, 0], lissajous[:, 1], lissajous[:, 2], color="#91ad58", linewidth=0.7, alpha=0.70)
    ax.plot(periodic_orbit[:, 0], periodic_orbit[:, 1], periodic_orbit[:, 2], color="#287a3f", linewidth=1.0)
    ax.scatter([earth[0]], [earth[1]], [earth[2]], color="black", s=16)
    ax.scatter(*transfer[0], color="#c9253d", s=18)
    ax.text(earth[0] - 2.0e5, earth[1] + 1.0e5, earth[2], "Earth", fontsize=10)
    ax.text(transfer[-1, 0] - 2.5e5, transfer[-1, 1], transfer[-1, 2] + 1.2e5,
            "Arrival\nLocation", fontsize=10)
    ax.set_xlabel("X [km]", labelpad=-7)
    ax.set_ylabel("Y [km]", labelpad=-6)
    ax.set_zlabel("Z [km]", labelpad=-6)
    ax.tick_params(labelsize=8, pad=-3)
    ax.view_init(elev=22, azim=-62)
    ax.set_box_aspect((1.35, 1.0, 0.95))
    add_axis_arrow(ax, "To Sun", xy=(0.67, 0.10), xytext=(0.80, 0.18), rotation=16)
    ax.text2D(0.48, -0.12, "(a)", transform=ax.transAxes, fontsize=12)

    ax2 = fig.add_subplot(212)
    ax2.plot(proxy_transfer[:, 0], proxy_transfer[:, 1], color="#9b9b9b", linewidth=0.7,
             linestyle="--", alpha=0.65)
    ax2.plot(transfer[:, 0], transfer[:, 1], color="#1f8fd4", linewidth=1.1)
    ax2.plot(lissajous[:, 0], lissajous[:, 1], color="#91ad58", linewidth=0.7, alpha=0.70)
    ax2.plot(periodic_orbit[:, 0], periodic_orbit[:, 1], color="#287a3f", linewidth=1.0)
    ax2.plot(baseline.parking_orbit_km[:, 0], baseline.parking_orbit_km[:, 1], color="#c9253d", linewidth=0.8)
    ax2.scatter([earth[0]], [earth[1]], color="black", s=18)
    ax2.scatter([transfer[0, 0]], [transfer[0, 1]], color="#c9253d", s=18)
    ax2.text(earth[0] - 3.0e5, earth[1] - 1.3e5, "Earth", fontsize=11)
    ax2.text(transfer[-1, 0] - 2.6e5, transfer[-1, 1] - 2.0e5, "Arrival\nLocation", fontsize=10)
    ax2.annotate("To Sun", xy=(0.05, 0.86), xytext=(0.17, 0.92), xycoords="axes fraction",
                 arrowprops={"arrowstyle": "-|>", "lw": 1.4, "color": "black"}, fontsize=10)
    ax2.set_xlabel("X [km]")
    ax2.set_ylabel("Y [km]")
    ax2.set_aspect("equal", adjustable="box")
    ax2.text(0.50, -0.22, "(b)", transform=ax2.transAxes, fontsize=12)

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
