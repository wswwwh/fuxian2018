"""Figure 4.2: quasi-halo stability index versus mapping time."""

from __future__ import annotations

import csv
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "4.2"
SOURCE_PAGE = 87
REPRO_LEVEL = "numerical DG reproduction"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Accepted corrected DG samples from the N=9, N=15, and N=21 branches; no analytic proxy."


def main() -> None:
    apply_style()
    path = PROJECT_ROOT / "data" / "computed" / "chapter4_fig42_stability_family_audit.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    quasi = sorted(
        [row for row in rows if row["kind"] == "quasi_halo" and row["acceptance"] == "pass"],
        key=lambda row: float(row["mapping_time_days"]),
    )
    periodic = next(row for row in rows if row["kind"] == "periodic_halo_anchor")
    times = [float(row["mapping_time_days"]) for row in quasi]
    values = [float(row["stability_index"]) for row in quasi]

    fig, ax = plt.subplots(figsize=(7.0, 3.2), constrained_layout=True)
    ax.plot(times, values, color="#1f77b4", marker="o", markersize=3.6, linewidth=1.6)
    ax.scatter(
        [float(periodic["mapping_time_days"])],
        [float(periodic["stability_index"])],
        color="#d95319",
        s=28,
        zorder=4,
    )
    ax.set_xlabel("Mapping Time [days]")
    ax.set_ylabel(r"Stability Index, $\nu$")
    ax.set_xlim(12.0, 12.45)
    ax.set_ylim(600.0, 790.0)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
