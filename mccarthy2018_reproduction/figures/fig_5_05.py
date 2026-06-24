"""Figure 5.5: quasi-DRO and associated planar periodic DRO."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _chapter5_plotting import plot_surface, style_earth_moon_dro_axis
from _figure_paths import PROJECT_ROOT
from qp_orbits.application_scenarios import quasi_dro_return_scene
from qp_orbits.application_scenarios import quasi_dro_cr3bp_return_scene
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "5.5"
SOURCE_PAGE = 102
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Proxy thesis-scale torus with corrected 2:1 resonant DRO and local quasi-DRO inset."


def add_corrected_dro_inset(ax, scene) -> None:
    inset = ax.inset_axes([0.69, 0.66, 0.25, 0.24], projection="3d")
    surface = scene.torus_surface
    inset.plot_surface(
        surface[:, :, 0],
        surface[:, :, 1],
        surface[:, :, 2],
        color="#9ccf9a",
        edgecolor="none",
        alpha=0.52,
        shade=True,
    )
    inset.plot(
        scene.periodic_states[:, 0],
        scene.periodic_states[:, 1],
        scene.periodic_states[:, 2],
        color="#4f8a36",
        linewidth=0.8,
    )
    inset.plot(
        scene.quasi_states[:, 0],
        scene.quasi_states[:, 1],
        scene.quasi_states[:, 2],
        color="#1f77b4",
        linewidth=0.7,
        alpha=0.82,
    )
    inset.plot(
        scene.invariant_curve[:, 0],
        scene.invariant_curve[:, 1],
        scene.invariant_curve[:, 2],
        color="black",
        linewidth=0.7,
    )
    inset.scatter(*scene.marker, color="#c9253d", s=7)
    points = surface.reshape(-1, 3)
    spans = points.max(axis=0) - points.min(axis=0)
    center = 0.5 * (points.max(axis=0) + points.min(axis=0))
    inset.set_xlim(center[0] - 0.55 * spans[0], center[0] + 0.55 * spans[0])
    inset.set_ylim(center[1] - 0.55 * spans[1], center[1] + 0.55 * spans[1])
    inset.set_zlim(center[2] - 0.60 * spans[2], center[2] + 0.60 * spans[2])
    inset.set_box_aspect((1.2, 1.6, 0.75))
    inset.view_init(elev=24, azim=-132)
    inset.patch.set_alpha(0.0)
    inset.xaxis.pane.set_alpha(0.0)
    inset.yaxis.pane.set_alpha(0.0)
    inset.zaxis.pane.set_alpha(0.0)
    inset.set_axis_off()


def main() -> None:
    apply_style()
    scene = quasi_dro_return_scene()
    corrected = quasi_dro_cr3bp_return_scene()
    fig = plt.figure(figsize=(6.3, 4.8), constrained_layout=True)
    ax = fig.add_subplot(111, projection="3d")
    plot_surface(ax, scene.surface, alpha=0.46)
    ax.plot(scene.curves[0][:, 0], scene.curves[0][:, 1], scene.curves[0][:, 2], color="#1f8fd4", linewidth=1.0)
    ax.plot(
        corrected.periodic_states[:, 0],
        corrected.periodic_states[:, 1],
        corrected.periodic_states[:, 2],
        color="#78a641",
        linewidth=1.2,
    )
    ax.plot(
        corrected.quasi_states[:, 0],
        corrected.quasi_states[:, 1],
        corrected.quasi_states[:, 2],
        color="#176f8f",
        linewidth=0.55,
        alpha=0.58,
    )
    if scene.marker is not None:
        ax.plot([scene.marker[0], scene.marker[0]], [scene.marker[1], scene.marker[1]], [-0.070, scene.marker[2]],
                color="black", linewidth=0.9)
        ax.scatter(*scene.marker, color="#c9253d", s=18)
    add_corrected_dro_inset(ax, corrected)
    style_earth_moon_dro_axis(ax)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
