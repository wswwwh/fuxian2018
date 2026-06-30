"""Figure 3.10: period-2, period-3, and period-8 halo examples."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.periodic_orbits import period_q_halo_examples
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "3.10"
SOURCE_PAGE = 72
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Floquet-seeded period-q branches corrected by STM multiple shooting."


def style_axis(ax, label: str) -> None:
    points = compute_libration_points(SYSTEMS["earth_moon"].mu)
    moon_x = 1.0 - SYSTEMS["earth_moon"].mu
    ax.scatter([points["L1"].x], [0.0], [0.0], color="#cc4c25", s=10)
    ax.scatter([moon_x], [0.0], [0.0], color="black", s=10)
    ax.text(points["L1"].x + 0.008, 0.003, 0.0, r"$L_1$", fontsize=8)
    ax.text(moon_x - 0.018, -0.012, -0.018, "Moon", fontsize=8)
    ax.set_xlim(0.70, 1.18)
    ax.set_ylim(-0.16, 0.16)
    ax.set_zlim(-0.20, 0.20)
    ax.set_xlabel("X [nd]", labelpad=-8)
    ax.set_ylabel("Y [nd]", labelpad=-7)
    ax.set_zlabel("Z [nd]", labelpad=-7)
    ax.tick_params(labelsize=7, pad=-3)
    ax.view_init(elev=18, azim=-60)
    ax.set_box_aspect((1.25, 0.92, 1.10))
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis._axinfo["grid"]["color"] = (0.86, 0.86, 0.86, 0.55)
        axis._axinfo["grid"]["linewidth"] = 0.35
    ax.text2D(0.48, -0.10, label, transform=ax.transAxes, fontsize=11)


def main() -> None:
    apply_style()
    examples = {
        example.resonance: example
        for example in period_q_halo_examples(SYSTEMS["earth_moon"].mu)
    }
    fig = plt.figure(figsize=(7.4, 6.2))
    axes = [
        fig.add_axes([0.05, 0.54, 0.40, 0.40], projection="3d"),
        fig.add_axes([0.54, 0.54, 0.40, 0.40], projection="3d"),
        fig.add_axes([0.18, 0.08, 0.43, 0.40], projection="3d"),
    ]
    for ax, resonance, label in zip(axes, [2, 3, 8], ["(a)", "(b)", "(c)"]):
        path = examples[resonance].trajectory
        ax.plot(path[:, 0], path[:, 1], path[:, 2], color="#168bd2", linewidth=1.05)
        style_axis(ax, label)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
