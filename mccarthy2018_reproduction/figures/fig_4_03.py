"""Figure 4.3: quasi-halo unstable manifold in the +x direction."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import (
    add_earth_moon_labels,
    plot_corrected_base_torus,
    plot_corrected_manifold_stage,
    style_manifold_axis,
)
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    corrected_l1_constant_energy_halo_unstable_manifolds,
    corrected_manifold_validation_row,
    update_chapter4_manifold_validation,
)


FIGURE_ID = "4.3"
SOURCE_PAGE = 89
REPRO_LEVEL = "numerical manifold reproduction"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected JC=3.1389 DG unstable manifold at the four paper snapshot times; no proxy layers."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    snapshot_days = [7.79, 9.75, 11.39, 13.02]
    plus_x, _ = corrected_l1_constant_energy_halo_unstable_manifolds(
        system.mu,
        time_unit_days=system.time_unit_days,
    )
    update_chapter4_manifold_validation(
        PROJECT_ROOT,
        [
            corrected_manifold_validation_row(
                plus_x,
                system,
                figure_id=FIGURE_ID,
                family="quasi-halo",
                branch="plus_x_unstable",
                source_curve="JC=3.1389 quasi-halo pseudo-arclength endpoint",
                uses_proxy_background=False,
                validation_status="corrected DG global branch audited at all four paper snapshot times",
                next_action="Increase source-curve resolution and digitize the paper panels for pointwise geometry comparison",
            )
        ],
    )
    fig = plt.figure(figsize=(8.2, 7.6), constrained_layout=True)
    for idx, elapsed_days in enumerate(snapshot_days, start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        plot_corrected_base_torus(ax, plus_x)
        plot_corrected_manifold_stage(ax, plus_x, elapsed_days=elapsed_days)
        add_earth_moon_labels(ax)
        style_manifold_axis(ax, direction="plus", compact=True)
        ax.set_xlim(0.78, 1.02)
        ax.set_ylim(-0.11, 0.11)
        ax.set_zlim(-0.095, 0.085)
        ax.text2D(0.47, -0.10, f"({chr(96 + idx)})", transform=ax.transAxes, fontsize=12)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
