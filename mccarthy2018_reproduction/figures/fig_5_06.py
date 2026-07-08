"""Figure 5.6: quasi-DRO ephemeris trajectories by phase."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import plot_de421_dro_scene, style_moon_km_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import load_best_chapter3_corrected_dro_family
from qp_orbits.ephemeris import de421_quasi_dro_phase_scenes
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.6"
SOURCE_PAGE = 103
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP + JPL DE421 geometry"
NOTES = "Route H accepted quasi-DRO phases embedded in the DE421 Sun-Moon frame; full ephemeris shooting remains pending."

BASE_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv"
EXTENDED_FAMILY_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family_extended.csv"
)
PALC_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
CONTINUATION_LOG_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_continuation_log.csv"
ROUTE_H_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_family.csv"


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    member = load_best_chapter3_corrected_dro_family(
        BASE_FAMILY_PATH,
        EXTENDED_FAMILY_PATH,
        PALC_FAMILY_PATH,
        CONTINUATION_LOG_PATH,
        system,
        ROUTE_H_FAMILY_PATH,
    )[-1]
    phases_deg = (0.0, 24.0, 80.0, 120.0)
    scenes = de421_quasi_dro_phase_scenes(
        member,
        system,
        PROJECT_ROOT / "data" / "raw" / "ephemeris" / "de421.bsp",
        epoch_utc="2020-06-15T00:00:00Z",
        phases_deg=phases_deg,
    )
    fig = plt.figure(figsize=(8.4, 7.0), constrained_layout=True)
    labels = ["(a)", "(b)", "(c)", "(d)"]
    for idx, (label, phase_deg, scene) in enumerate(zip(labels, phases_deg, scenes), start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        plot_de421_dro_scene(ax, scene)
        style_moon_km_axis(ax, label=label)
        ax.text2D(0.02, 0.96, rf"$\theta_1={phase_deg:.0f}^\circ$", transform=ax.transAxes, fontsize=8)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
