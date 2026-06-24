"""Figure 5.10: converged transfer trajectories for two departure locations."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import plot_nrho_scene, style_nrho_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import NRHOTransferScene, earth_moon_nrho_transfer_baseline
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.10"
SOURCE_PAGE = 108
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP corrected NRHO direct shooting"
NOTES = "Position-matched single-arc baselines at thesis flight times; not the thesis optimized quasi-NRHO arcs."


def main() -> None:
    apply_style()
    baseline = earth_moon_nrho_transfer_baseline()
    fig = plt.figure(figsize=(7.8, 4.1), constrained_layout=True)
    for idx, label in enumerate(["(a)", "(b)"], start=1):
        ax = fig.add_subplot(1, 2, idx, projection="3d")
        transfer = baseline.forward_transfers[idx - 1]
        scene = NRHOTransferScene(
            departure=baseline.departure_states[:, :3],
            destination=baseline.destination_states[:, :3],
            transfer_arcs=(transfer.transfer_states[:, :3],),
            departure_location=transfer.departure_state[:3],
            arrival_location=transfer.arrival_state[:3],
        )
        plot_nrho_scene(ax, scene, annotate=False)
        style_nrho_axis(ax, label=label)
        ax.text2D(0.08, 0.76, "Arrival\nLocation", transform=ax.transAxes, fontsize=8)
        ax.text2D(0.58, 0.76, "Departure\nLocation", transform=ax.transAxes, fontsize=8)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
