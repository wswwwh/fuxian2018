"""Figure 4.3: quasi-halo unstable manifold in the +x direction."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import (
    add_earth_moon_labels,
    plot_fixed_time_base_torus,
    plot_fixed_time_manifold_snapshot,
    style_manifold_axis,
)
from qp_orbits.constants import SYSTEMS
from qp_orbits.chapter4_reproduction_lock import load_chapter4_reproduction_lock
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    corrected_l1_constant_energy_halo_unstable_manifold_snapshots,
    corrected_torus_snapshot_validation_row,
    update_chapter4_manifold_validation,
)


FIGURE_ID = "4.3"
SOURCE_PAGE = 89
REPRO_LEVEL = "numerical state-space manifold; paper-projection holdout failed"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Fixed-time full-torus numerical snapshots; frozen paper-projection holdout is 0/4."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    reproduction_lock = load_chapter4_reproduction_lock(PROJECT_ROOT)
    snapshot_days = [7.79, 9.75, 11.39, 13.02]
    plus_x, _ = corrected_l1_constant_energy_halo_unstable_manifold_snapshots(
        system.mu,
        time_unit_days=system.time_unit_days,
        perturbation_scale=reproduction_lock.epsilon_by_family["halo"],
    )
    update_chapter4_manifold_validation(
        PROJECT_ROOT,
        [
            corrected_torus_snapshot_validation_row(
                plus_x,
                system,
                figure_id=FIGURE_ID,
                family="quasi-halo",
                branch="plus_x_unstable",
                source_curve="JC=3.1389 quasi-halo pseudo-arclength endpoint",
                uses_proxy_background=False,
                validation_status="fixed-time full-torus snapshots generated; dedicated audit owns acceptance",
                next_action="Run the frozen 12.40-day N21 halo source-member and N-convergence falsification; keep panel (d) post-hoc only",
            )
        ],
    )
    fig = plt.figure(figsize=(8.60, 7.48), constrained_layout=True)
    for idx, elapsed_days in enumerate(snapshot_days, start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        plot_fixed_time_base_torus(ax, plus_x)
        plot_fixed_time_manifold_snapshot(ax, plus_x, elapsed_days=elapsed_days)
        add_earth_moon_labels(ax)
        style_manifold_axis(
            ax,
            direction="plus",
            compact=True,
            figure_id=FIGURE_ID,
        )
        ax.text2D(0.47, -0.10, f"({chr(96 + idx)})", transform=ax.transAxes, fontsize=12)
    fig.suptitle(
        "Numerical state-space snapshots; paper_projection=FAIL (frozen holdout 0/4)",
        fontsize=9,
        color="#8a4b08",
    )
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
