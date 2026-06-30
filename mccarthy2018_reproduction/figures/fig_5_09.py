"""Figure 5.9: NRHOs and potential departure locations."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import plot_surface, style_nrho_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import earth_moon_nrho_transfer_baseline
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.9"
SOURCE_PAGE = 107
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP corrected NRHO boundaries"
NOTES = "Corrected 4,800/12,610 km NRHOs; grey corridor remains a quasi-NRHO surface proxy."


def main() -> None:
    apply_style()
    baseline = earth_moon_nrho_transfer_baseline()
    fig = plt.figure(figsize=(4.25, 5.35), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    plot_surface(ax, baseline.corridor_surface, alpha=0.50)
    departure = baseline.departure_states[:, :3]
    destination = baseline.destination_states[:, :3]
    ax.plot(departure[:, 0], departure[:, 1], departure[:, 2], color="#1f77b4", linewidth=1.25)
    ax.plot(destination[:, 0], destination[:, 1], destination[:, 2], color="#c9253d", linewidth=1.25)
    style_nrho_axis(ax, wide=True)
    ax.view_init(elev=21, azim=-50)
    ax.text2D(0.06, 0.87, "Departure\nNRHO", transform=ax.transAxes, fontsize=10)
    ax.text2D(0.58, 0.90, "Destination\nNRHO", transform=ax.transAxes, fontsize=10)
    ax.annotate("", xy=(0.33, 0.66), xytext=(0.18, 0.84), xycoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "lw": 1.2, "color": "black"})
    ax.annotate("", xy=(0.73, 0.75), xytext=(0.66, 0.88), xycoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "lw": 1.2, "color": "black"})
    for label, transfer in enumerate(baseline.forward_transfers, start=1):
        point = transfer.departure_state[:3]
        ax.scatter(*point, color="#55b8e8", s=19, depthshade=False)
        ax.text(point[0] + 0.006, point[1], point[2] + 0.006, str(label), fontsize=11)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
