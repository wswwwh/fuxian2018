"""Figure 5.7: quasi-DRO ephemeris trajectories by insertion epoch."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import plot_de421_dro_scene, style_moon_km_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import load_or_compute_corrected_dro_family
from qp_orbits.ephemeris import de421_quasi_dro_epoch_scenes
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.7"
SOURCE_PAGE = 104
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP + JPL DE421 geometry"
NOTES = "Corrected theta1=0 quasi-DRO embedded at four DE421 epochs; full ephemeris shooting remains pending."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    member = load_or_compute_corrected_dro_family(
        PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv",
        system,
    )[-1]
    epochs = (
        "2020-06-01T00:00:00Z",
        "2020-06-04T00:00:00Z",
        "2020-06-10T00:00:00Z",
        "2020-06-15T00:00:00Z",
    )
    scenes = de421_quasi_dro_epoch_scenes(
        member,
        system,
        PROJECT_ROOT / "data" / "raw" / "ephemeris" / "de421.bsp",
        epochs_utc=epochs,
        phase_deg=0.0,
    )
    fig = plt.figure(figsize=(8.4, 7.0), constrained_layout=True)
    labels = ["(a)", "(b)", "(c)", "(d)"]
    for idx, (label, epoch, scene) in enumerate(zip(labels, epochs, scenes), start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        plot_de421_dro_scene(ax, scene)
        style_moon_km_axis(ax, label=label)
        ax.text2D(0.02, 0.96, epoch[:10], transform=ax.transAxes, fontsize=8)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
