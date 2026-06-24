"""Figure 2.13: Jupiter-Europa L2 Lyapunov, halo, and vertical families."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.periodic_orbits import (
    planar_lyapunov_family,
    propagate_periodic_orbit,
    spatial_symmetric_family,
    vertical_symmetric_family,
)
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.13"
SOURCE_PAGE = 40
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Jupiter-Europa CR3BP"
NOTES = "Lyapunov, halo-like, and z0=0.0005..0.05 vertical families are corrected CR3BP periodic orbits."


def main() -> None:
    apply_style()
    system = SYSTEMS["jupiter_europa"]
    mu = system.mu
    points = compute_libration_points(mu)
    l2_x = points["L2"].x
    europa_x = 1.0 - mu

    amplitudes = [0.0008, 0.0013, 0.0018, 0.0024, 0.0030, 0.0038, 0.0048, 0.0060, 0.0080, 0.0100, 0.0150, 0.0200]
    lyapunov_orbits = planar_lyapunov_family(mu, amplitudes, point="L2")
    halo_orbits = spatial_symmetric_family(
        mu,
        [0.001, 0.002, 0.003, 0.004, 0.005, 0.006],
        point="L2",
        seed_x_amplitude=-0.001,
        family_label="halo",
    )
    vertical_amplitudes = np.r_[
        np.arange(0.0005, 0.0061, 0.0005),
        np.arange(0.010, 0.0501, 0.004),
    ]
    vertical_orbits = vertical_symmetric_family(
        mu,
        vertical_amplitudes,
        point="L2",
        max_iterations=32,
        secant_predictor=True,
    )

    fig = plt.figure(figsize=(6.2, 5.4))
    ax = fig.add_subplot(111, projection="3d")

    for orbit in lyapunov_orbits:
        states = propagate_periodic_orbit(orbit, samples=360)
        ax.plot(states[:, 0], states[:, 1], states[:, 2], color="#168bd2", linewidth=1.0, alpha=0.95)

    for orbit in halo_orbits:
        states = propagate_periodic_orbit(orbit, samples=360)
        ax.plot(states[:, 0], states[:, 1], states[:, 2], color="#5aa832", linewidth=1.0, alpha=0.92)

    for orbit in vertical_orbits:
        states = propagate_periodic_orbit(orbit, samples=360)
        ax.plot(states[:, 0], states[:, 1], states[:, 2], color="#f0aa00", linewidth=0.95, alpha=0.78)

    ax.scatter([europa_x], [0.0], [0.0], color="black", s=40, zorder=5)
    ax.scatter([points["L1"].x, l2_x], [0.0, 0.0], [0.0, 0.0], color="black", s=16, zorder=5)
    ax.text(points["L1"].x - 0.006, -0.004, -0.011, r"$L_1$", fontsize=9)
    ax.text(l2_x + 0.002, 0.002, -0.002, r"$L_2$", fontsize=9)
    ax.text(europa_x - 0.014, -0.009, -0.023, "Europa", fontsize=8)

    ax.text(1.035, 0.018, -0.035, "Lyapunov", color="#168bd2", fontsize=8, weight="bold")
    ax.text(1.024, 0.015, 0.013, "Halo", color="#5aa832", fontsize=8, weight="bold")
    ax.text(1.000, -0.005, 0.050, "Vertical", color="#f0aa00", fontsize=8, weight="bold")
    ax.annotate("To Jupiter", xy=(0.46, 0.09), xytext=(0.60, 0.16), xycoords="axes fraction", textcoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "color": "black", "linewidth": 1.0}, fontsize=10)

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_zlabel("")
    ax.text2D(0.18, 0.03, "X [nd]", transform=ax.transAxes, fontsize=9, rotation=-24)
    ax.text2D(0.69, 0.03, "Y [nd]", transform=ax.transAxes, fontsize=9, rotation=22)
    ax.text2D(0.92, 0.49, "Z [nd]", transform=ax.transAxes, fontsize=9, rotation=90)
    ax.set_xlim(0.975, 1.045)
    ax.set_ylim(-0.055, 0.055)
    ax.set_zlim(-0.06, 0.055)
    ax.set_xticks([0.98, 1.00, 1.02, 1.04])
    ax.set_yticks([-0.05, 0.0, 0.05])
    ax.set_zticks([-0.05, 0.0, 0.05])
    ax.tick_params(labelsize=8, pad=-2)
    ax.view_init(elev=23, azim=-38)
    ax.set_box_aspect((1.1, 1.0, 1.0))
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
