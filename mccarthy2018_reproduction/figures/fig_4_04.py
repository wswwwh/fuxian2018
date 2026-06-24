"""Figure 4.4: quasi-halo unstable manifold in the -x direction."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import (
    add_earth_moon_labels,
    plot_corrected_manifold_stage,
    plot_sheet,
    plot_torus_wire,
    style_manifold_axis,
)
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    base_torus,
    corrected_l1_constant_energy_halo_unstable_manifolds,
    manifold_sheet,
)


FIGURE_ID = "4.4"
SOURCE_PAGE = 90
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Proxy thesis-scale sheet with finite-amplitude JC=3.1389 corrected DG-manifold overlay."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    torus = base_torus(system, "halo")
    stages = [0.16, 0.34, 0.64, 1.0]
    snapshot_days = [7.79, 9.75, 11.39, 13.02]
    _, minus_x = corrected_l1_constant_energy_halo_unstable_manifolds(
        system.mu,
        time_unit_days=system.time_unit_days,
    )
    fig = plt.figure(figsize=(8.4, 7.4), constrained_layout=True)
    for idx, stage in enumerate(stages, start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        plot_torus_wire(ax, torus)
        plot_sheet(ax, manifold_sheet(system, family="halo", direction="minus", stage_fraction=stage))
        plot_corrected_manifold_stage(ax, minus_x, elapsed_days=snapshot_days[idx - 1])
        add_earth_moon_labels(ax, include_l2=False)
        style_manifold_axis(ax, direction="minus", compact=True)
        ax.text2D(0.47, -0.10, f"({chr(96 + idx)})", transform=ax.transAxes, fontsize=12)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
