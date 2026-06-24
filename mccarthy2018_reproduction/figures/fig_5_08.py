"""Figure 5.8: halo-to-Lyapunov transfer initial guess and converged transfer."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import plot_nrho_scene, plot_surface, style_nrho_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import (
    NRHOTransferScene,
    earth_moon_halo_to_lyapunov_transfer_baseline,
)
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.8"
SOURCE_PAGE = 106
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP equal-Jacobi halo-to-Lyapunov transfer"
NOTES = "Corrected equal-energy boundaries and 186.9-day multiple-shooting baseline; grey corridor remains geometric."


def _style_axis(ax) -> None:
    style_nrho_axis(ax, wide=True)
    ax.set_xlim(0.94, 1.22)
    ax.set_ylim(-0.21, 0.21)
    ax.set_zlim(-0.15, 0.18)
    ax.set_box_aspect((1.15, 1.45, 1.15))


def main() -> None:
    apply_style()
    baseline = earth_moon_halo_to_lyapunov_transfer_baseline()
    halo = baseline.halo_states[:, :3]
    lyapunov = baseline.lyapunov_states[:, :3]
    fig = plt.figure(figsize=(8.7, 4.2), constrained_layout=True)

    ax = fig.add_subplot(121, projection="3d")
    plot_surface(ax, baseline.corridor_surface, alpha=0.48)
    ax.plot(halo[:, 0], halo[:, 1], halo[:, 2], color="#1f8fd4", linewidth=1.2)
    ax.plot(lyapunov[:, 0], lyapunov[:, 1], lyapunov[:, 2], color="#a71930", linewidth=1.1)
    _style_axis(ax)
    ax.text2D(0.06, 0.84, "Northern $L_2$\nUnstable Halo", transform=ax.transAxes, fontsize=8)
    ax.text2D(0.64, 0.80, "Planar $L_2$\nLyapunov Orbit", transform=ax.transAxes, fontsize=8)

    ax = fig.add_subplot(122, projection="3d")
    scene = NRHOTransferScene(
        departure=halo,
        destination=lyapunov,
        transfer_arcs=(baseline.transfer_states[:, :3],),
        departure_location=baseline.departure_state[:3],
        arrival_location=baseline.arrival_state[:3],
    )
    plot_nrho_scene(ax, scene, show_surface=False, annotate=False)
    _style_axis(ax)
    ax.text2D(0.57, 0.78, "Departure\nLocation", transform=ax.transAxes, fontsize=8)
    ax.text2D(0.76, 0.55, "Arrival\nLocation", transform=ax.transAxes, fontsize=8)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
