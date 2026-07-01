"""Figure 4.5: quasi-vertical unstable manifold in the +x direction."""

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
from qp_orbits.torus_stability import (
    base_torus,
    corrected_manifold_validation_row,
    corrected_vertical_curve_unstable_manifold,
    manifold_sheet,
    update_chapter4_manifold_validation,
)


FIGURE_ID = "4.5"
SOURCE_PAGE = 91
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Proxy global sheet with corrected local quasi-vertical DG-manifold growth inset."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    torus = base_torus(system, "vertical")
    corrected_branch = corrected_vertical_curve_unstable_manifold(
        system.mu,
        samples=9,
        time_samples=24,
        perturbation_sign=1.0,
    )
    update_chapter4_manifold_validation(
        PROJECT_ROOT,
        [
            corrected_manifold_validation_row(
                corrected_branch,
                system,
                figure_id=FIGURE_ID,
                family="quasi-vertical",
                branch="plus_x_unstable_local",
                source_curve="corrected quasi-vertical stroboscopic curve",
                uses_proxy_background=True,
                validation_status="local corrected DG branch audited; global sheet remains proxy",
                next_action="Promote from local branch diagnostic to continued thesis-scale vertical manifold",
            )
        ],
    )
    stages = [0.16, 0.36, 0.66, 1.0]
    fig = plt.figure(figsize=(8.2, 7.5), constrained_layout=True)
    for idx, stage in enumerate(stages, start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        plot_torus_wire(ax, torus)
        plot_sheet(ax, manifold_sheet(system, family="vertical", direction="plus", stage_fraction=stage))
        add_earth_moon_labels(ax)
        style_manifold_axis(ax, direction="plus", compact=True)
        if idx == len(stages):
            add_corrected_vertical_local_growth_inset(
                ax,
                perturbation_sign=1.0,
                sheet=corrected_branch,
            )
        ax.text2D(0.47, -0.10, f"({chr(96 + idx)})", transform=ax.transAxes, fontsize=12)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
