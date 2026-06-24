"""Figure 2.7: decoupled L1 planar and out-of-plane linear variations."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.linear_modes import center_modes, scaled_planar_mode
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.7"
SOURCE_PAGE = 24
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    modes = center_modes(system.mu, point="L1")
    length_unit = system.length_unit_km or 1.0

    y_amp_km = 1.25e4
    z_amp_km = 1.35e4
    y_amp_nd = y_amp_km / length_unit
    period = 2.0 * np.pi / modes.planar_frequency
    times = np.linspace(0.0, period, 500)
    planar = scaled_planar_mode(modes, y_amp_nd, times)[:, :3] * length_unit

    fig = plt.figure(figsize=(6.1, 5.1))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot(planar[:, 0], planar[:, 1], planar[:, 2], color="#d9531e", linewidth=1.8)
    ax.plot([0.0, 0.0], [0.0, 0.0], [-z_amp_km, z_amp_km], color="tab:blue", linewidth=1.8)
    ax.scatter([0.0], [0.0], [0.0], color="black", s=12)
    ax.text(450.0, 0.0, -1100.0, r"$L_1$", fontsize=12)

    idx = 70
    delta = planar[idx + 8] - planar[idx]
    ax.quiver(
        planar[idx, 0],
        planar[idx, 1],
        planar[idx, 2],
        delta[0],
        delta[1],
        delta[2],
        color="black",
        arrow_length_ratio=0.45,
        linewidth=1.0,
    )

    ax.set_xlabel("X [km]", labelpad=-6)
    ax.set_ylabel("Y [km]", labelpad=-2)
    ax.set_zlabel("Z [km]", labelpad=-8)
    ax.set_xlim(-4500, 4500)
    ax.set_ylim(-1.35e4, 1.35e4)
    ax.set_zlim(-1.45e4, 1.45e4)
    ax.set_xticks([-4000, 0, 4000])
    ax.set_yticks([-10000, 0, 10000])
    ax.set_zticks([-10000, 0, 10000])
    ax.tick_params(labelsize=8, pad=0)
    ax.view_init(elev=24, azim=-42)
    ax.set_box_aspect((0.9, 1.6, 1.6))
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
