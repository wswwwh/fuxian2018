"""Figure 4.2: quasi-halo stability index versus mapping time."""

from __future__ import annotations

import csv
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "4.2"
SOURCE_PAGE = 87
REPRO_LEVEL = "numerical DG overlap pass with fold-tail boundary"
SYSTEM = "Earth-Moon CR3BP"
NOTES = (
    "Accepted corrected DG samples are compared directly with the digitized native-PDF "
    "curve. The final 0.04945-day paper tail is shown as uncovered and is not extrapolated."
)


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
    digitized_path = PROJECT_ROOT / "data" / "digitized" / "fig_4_2_digitized_points.csv"
    with digitized_path.open(newline="", encoding="utf-8") as stream:
        digitized_rows = [
            row for row in csv.DictReader(stream) if row["series"] == "blue_stability_curve"
        ]
    reference_times = [float(row["mapping_time_days"]) for row in digitized_rows]
    reference_values = [float(row["stability_index"]) for row in digitized_rows]

    fig, ax = plt.subplots(figsize=(7.0, 3.2), constrained_layout=True)
    ax.plot(
        reference_times,
        reference_values,
        color="#777777",
        linestyle="--",
        linewidth=1.05,
        alpha=0.75,
        label="digitized paper curve",
    )
    ax.plot(
        times,
        values,
        color="#1f77b4",
        marker="o",
        markersize=3.6,
        linewidth=1.6,
        label="accepted corrected DG branch",
    )
    ax.scatter(
        [float(periodic["mapping_time_days"])],
        [float(periodic["stability_index"])],
        color="#d95319",
        s=28,
        zorder=4,
        label="periodic anchor",
    )
    computed_end = max(times)
    paper_end = max(reference_times)
    ax.axvspan(computed_end, paper_end, color="#d97706", alpha=0.12, linewidth=0)
    ax.text(
        0.985,
        0.08,
        f"uncovered tail\n{paper_end - computed_end:.5f} day\n(no extrapolation)",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        color="#8a4b08",
    )
    ax.set_xlabel("Mapping Time [days]")
    ax.set_ylabel(r"Stability Index, $\nu$")
    ax.set_xlim(12.0, 12.49)
    ax.set_ylim(600.0, 810.0)
    ax.legend(loc="upper left", fontsize=7, frameon=False)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
