"""Figure 2.15: corrected stability index curve for an Earth-Moon L2 halo-like family."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from scipy.interpolate import PchipInterpolator

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.manifolds import spatial_symmetric_folded_family_stability
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.15"
SOURCE_PAGE = 45
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected natural-parameter and pseudo-arclength L2 halo/NRHO branch down to the lunar surface."


def _load_or_compute_rows(path: Path) -> list[dict[str, float | str]]:
    if path.exists():
        with path.open(newline="", encoding="utf-8") as stream:
            raw = list(csv.DictReader(stream))
        if raw and "branch_method" in raw[0] and min(
            float(row["perilune_radius_km"]) for row in raw
        ) < 1_800.0:
            return raw
    system = SYSTEMS["earth_moon"]
    return spatial_symmetric_folded_family_stability(
        system.mu,
        system.length_unit_km or 1.0,
        point="L2",
        seed_x_amplitude=-0.002,
    )


def main() -> None:
    apply_style()
    rows = _load_or_compute_rows(
        PROJECT_ROOT / "data" / "computed" / "earth_moon_l2_halo_stability.csv"
    )
    rows = sorted(rows, key=lambda row: float(row["perilune_radius_km"]))

    x = np.array([float(row["perilune_radius_km"]) for row in rows])
    y = np.array([float(row["stability_index"]) for row in rows])
    unique_x, unique_indices = np.unique(x, return_index=True)
    unique_y = y[unique_indices]
    display_x = np.linspace(unique_x[0], unique_x[-1], 500)
    display_y = PchipInterpolator(unique_x, unique_y)(display_x)

    fig, ax = plt.subplots(figsize=(6.8, 4.9))
    ax.plot(display_x, display_y, color="#168bd2", linewidth=2.0)

    ax.set_xlabel("Perilune Radius [km]")
    ax.set_ylabel(r"Stability Index, $\nu$")
    ax.set_xlim(0.0, 6.0e4)
    ax.set_ylim(0.0, 700.0)
    ax.grid(alpha=0.24)

    formatter = ScalarFormatter(useMathText=True)
    formatter.set_powerlimits((4, 4))
    ax.xaxis.set_major_formatter(formatter)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
