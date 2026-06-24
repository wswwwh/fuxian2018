"""Figure 5.11: converged transfer between two NRHOs."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import plot_nrho_scene, style_nrho_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import NRHOTransferScene, earth_moon_nrho_transfer_baseline
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.11"
SOURCE_PAGE = 109
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP symmetric reverse NRHO transfers"
NOTES = "Reverse transfers generated from the validated forward arcs by exact CR3BP symmetry."


def main() -> None:
    apply_style()
    baseline = earth_moon_nrho_transfer_baseline()
    fig = plt.figure(figsize=(7.8, 4.1), constrained_layout=True)
    for idx, label in enumerate(["(a)", "(b)"], start=1):
        ax = fig.add_subplot(1, 2, idx, projection="3d")
        transfer = baseline.reverse_transfers[idx - 1]
        scene = NRHOTransferScene(
            departure=baseline.destination_states[:, :3],
            destination=baseline.departure_states[:, :3],
            transfer_arcs=(transfer.transfer_states[:, :3],),
            departure_location=transfer.departure_state[:3],
            arrival_location=transfer.arrival_state[:3],
        )
        plot_nrho_scene(ax, scene, annotate=False)
        style_nrho_axis(ax, label=label, wide=True)
        ax.text2D(0.08, 0.76, "Arrival\nLocation", transform=ax.transAxes, fontsize=8)
        ax.text2D(0.58, 0.76, "Departure\nLocation", transform=ax.transAxes, fontsize=8)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
