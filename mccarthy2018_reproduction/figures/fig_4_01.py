"""Figure 4.1: quasi-halo orbit and DG eigenvalue structure."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from _chapter4_plotting import add_earth_moon_labels
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.torus_stability import (
    chapter4_quasi_halo_orbit,
    corrected_stroboscopic_curve_dg,
    dg_eigenvalue_loops,
    display_scaled_corrected_dg_spectrum,
)


FIGURE_ID = "4.1"
SOURCE_PAGE = 86
REPRO_LEVEL = "shape-match"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Proxy thesis-scale torus with display-scaled corrected local DG eigenvalue markers."


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    member = chapter4_quasi_halo_orbit(system)
    loops = dg_eigenvalue_loops(samples=28)
    corrected_spectrum = display_scaled_corrected_dg_spectrum(
        corrected_stroboscopic_curve_dg(system.mu, samples=15)
    )

    fig = plt.figure(figsize=(8.2, 3.65), constrained_layout=True)
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    surface = member.surface
    ax3d.plot_surface(surface[:, :, 0], surface[:, :, 1], surface[:, :, 2], color="#168bd2",
                      edgecolor="none", linewidth=0, alpha=0.72, shade=True)
    curve = member.invariant_curve
    ax3d.plot(curve[:, 0], curve[:, 1], curve[:, 2], color="#168bd2", linewidth=1.4)
    add_earth_moon_labels(ax3d, include_l1=False, include_l2=False)
    ax3d.set_xlim(0.94, 1.04)
    ax3d.set_ylim(-0.06, 0.06)
    ax3d.set_zlim(0.0, 0.18)
    ax3d.set_xlabel("X [nd]", labelpad=-6)
    ax3d.set_ylabel("Y [nd]", labelpad=-6)
    ax3d.set_zlabel("Z [nd]", labelpad=-6)
    ax3d.view_init(elev=25, azim=-132)
    ax3d.set_box_aspect((1.0, 1.0, 1.55))
    ax3d.tick_params(labelsize=8, pad=-2)

    ax = fig.add_subplot(1, 2, 2)
    for name, color, size in [("outer", "#b2182b", 18), ("middle", "black", 16), ("inner", "#168bd2", 16)]:
        values = loops[name]
        closed = np.append(values, values[0])
        ax.plot(np.real(closed), np.imag(closed), color=color, linewidth=1.4)
        ax.scatter(np.real(values), np.imag(values), color=color, s=size)
    for name, color in [("unstable", "#ef8a62"), ("unit", "0.35"), ("stable", "#56b4e9")]:
        values = corrected_spectrum[name]
        ax.scatter(
            np.real(values),
            np.imag(values),
            marker="x",
            color=color,
            s=14,
            linewidths=0.7,
            alpha=0.85,
            zorder=4,
        )
    ax.axhline(0.0, color="0.82", linewidth=0.8)
    ax.axvline(0.0, color="0.82", linewidth=0.8)
    ax.set_xlabel(r"$\mathrm{Re}(\lambda)$")
    ax.set_ylabel(r"$\mathrm{Imag}(\lambda)$")
    ax.set_xlim(-2.55, 2.55)
    ax.set_ylim(-2.45, 2.45)
    ax.set_aspect("equal", adjustable="box")
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
