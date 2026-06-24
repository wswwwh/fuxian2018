"""Figure 2.8: linearized Lissajous motion near Earth-Moon L1."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.linear_modes import center_modes, linear_lissajous
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.8"
SOURCE_PAGE = 24
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    modes = center_modes(system.mu, point="L1")
    length_unit = system.length_unit_km or 1.0

    y_amp_nd = 1.35e4 / length_unit
    z_amp_nd = 1.35e4 / length_unit
    planar_period = 2.0 * np.pi / modes.planar_frequency
    times = np.linspace(0.0, 18.0 * planar_period, 4200)
    path = linear_lissajous(modes, y_amp_nd, z_amp_nd, times, vertical_phase=0.38 * np.pi)[:, :3] * length_unit

    fig = plt.figure(figsize=(12.3, 4.3), constrained_layout=True)
    gs = GridSpec(1, 3, figure=fig, width_ratios=[1.15, 0.72, 1.15])

    ax3d = fig.add_subplot(gs[0, 0], projection="3d")
    ax_xy = fig.add_subplot(gs[0, 1])
    ax_yz = fig.add_subplot(gs[0, 2])

    ax3d.plot(path[:, 0], path[:, 1], path[:, 2], color="tab:blue", linewidth=0.8)
    ax3d.scatter([0.0], [0.0], [0.0], color="black", s=10)
    ax3d.text(400.0, 0.0, -1000.0, r"$L_1$", fontsize=12)
    ax3d.set_xlabel("X [km]", labelpad=-5)
    ax3d.set_ylabel("Y [km]", labelpad=-2)
    ax3d.set_zlabel("Z [km]", labelpad=-7)
    ax3d.set_xlim(-4200, 4200)
    ax3d.set_ylim(-1.45e4, 1.45e4)
    ax3d.set_zlim(-1.45e4, 1.45e4)
    ax3d.set_xticks([-3000, 0, 3000])
    ax3d.set_yticks([-10000, 0, 10000])
    ax3d.set_zticks([-10000, 0, 10000])
    ax3d.tick_params(labelsize=8, pad=0)
    ax3d.view_init(elev=18, azim=-55)
    ax3d.set_box_aspect((0.8, 1.5, 1.7))

    ax_xy.plot(path[:, 0], path[:, 1], color="tab:blue", linewidth=1.0)
    ax_xy.scatter([0.0], [0.0], color="black", s=10)
    ax_xy.text(350.0, -1500.0, r"$L_1$", fontsize=12)
    ax_xy.annotate(
        "",
        xy=(path[320, 0], path[320, 1]),
        xytext=(path[260, 0], path[260, 1]),
        arrowprops={"arrowstyle": "->", "color": "black", "linewidth": 1.0},
    )
    ax_xy.set_xlabel("X [km]")
    ax_xy.set_ylabel("Y [km]")
    ax_xy.set_xlim(-4200, 4200)
    ax_xy.set_ylim(-1.45e4, 1.45e4)
    ax_xy.set_aspect("equal", adjustable="box")

    ax_yz.plot(path[:, 1], path[:, 2], color="tab:blue", linewidth=0.8)
    ax_yz.scatter([0.0], [0.0], color="black", s=10)
    ax_yz.text(550.0, -1300.0, r"$L_1$", fontsize=12)
    ax_yz.set_xlabel("Y [km]")
    ax_yz.set_ylabel("Z [km]")
    ax_yz.set_xlim(-1.45e4, 1.45e4)
    ax_yz.set_ylim(-1.45e4, 1.45e4)
    ax_yz.set_aspect("equal", adjustable="box")

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
