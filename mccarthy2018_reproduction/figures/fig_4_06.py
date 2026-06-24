"""Figure 4.6: quasi-vertical unstable manifold in the -x direction."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import (
    add_corrected_vertical_local_growth_inset,
    add_earth_moon_labels,
    plot_sheet,
    plot_torus_wire,
    style_manifold_axis,
)
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import base_torus, manifold_sheet


FIGURE_ID = "4.6"
SOURCE_PAGE = 92
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Proxy global sheet with corrected local quasi-vertical DG-manifold growth inset."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    torus = base_torus(system, "vertical")
    stages = [0.14, 0.32, 0.62, 1.0]
    fig = plt.figure(figsize=(8.4, 7.4), constrained_layout=True)
    for idx, stage in enumerate(stages, start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        plot_torus_wire(ax, torus)
        plot_sheet(ax, manifold_sheet(system, family="vertical", direction="minus", stage_fraction=stage))
        add_earth_moon_labels(ax, include_l2=False)
        style_manifold_axis(ax, direction="minus", compact=True)
        if idx == len(stages):
            add_corrected_vertical_local_growth_inset(
                ax,
                perturbation_sign=-1.0,
                bounds=(0.70, 0.58, 0.24, 0.22),
            )
        ax.text2D(0.47, -0.10, f"({chr(96 + idx)})", transform=ax.transAxes, fontsize=12)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
