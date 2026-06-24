"""Figure 3.3: discretized invariant-curve mapping."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import stroboscopic_curve_newton_correction, stroboscopic_invariant_curve_seed


FIGURE_ID = "3.3"
SOURCE_PAGE = 49
REPRO_LEVEL = "shape-match"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Uses a corrected L1 Lyapunov monodromy seed and a fixed-rotation global curve Newton correction."


def draw_base_panel(ax, *, mapped: bool, seed, correction=None) -> None:
    ax.set_aspect("equal")
    ax.set_facecolor("#d4d1d1")
    ax.set_xlim(-1.95, 1.95)
    ax.set_ylim(-1.18, 1.18)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#6d7f9d")
        spine.set_linewidth(1.0)

    curve = seed.curve_points
    initial = seed.initial_points
    ax.plot(curve[:, 0], curve[:, 1], color="#314d78", linewidth=1.4)
    ax.scatter(initial[:, 0], initial[:, 1], s=36, facecolor="#f1cf4a", edgecolor="black", linewidth=1.1, zorder=6)
    ax.scatter([0.0], [0.0], color="#234f88", s=18, zorder=5)
    ax.plot([0.0, 1.42], [0.0, 0.0], color="black", linestyle=(0, (6, 3)), linewidth=1.4)
    ax.annotate("Fixed Point", xy=(0.0, 0.0), xytext=(-0.34, -0.45), fontsize=9)
    ax.annotate("", xy=(0.0, 0.0), xytext=(-0.05, -0.36), arrowprops={"arrowstyle": "-|>", "lw": 1.4})
    ax.text(-1.85, 0.92, r"$\theta_0$", fontsize=13)
    ax.text(0.98, 0.50, r"$\theta_1$", fontsize=13)

    arc = Arc((0.0, 0.0), 1.62, 1.62, theta1=355, theta2=45, color="black", linewidth=1.5)
    ax.add_patch(arc)
    ax.add_patch(FancyArrowPatch((0.62, 0.50), (0.48, 0.70), arrowstyle="-|>", mutation_scale=12, color="black"))

    if not mapped:
        ax.text(-1.88, -1.06, "Integration Time = 0", fontsize=8)
        return

    predicted = correction.corrected_target_points if correction is not None else seed.predicted_points
    mapped_points = seed.mapped_points
    ax.plot(predicted[:, 0], predicted[:, 1], color="#888888", linestyle=":", linewidth=1.2, alpha=0.9)
    ax.scatter(predicted[:, 0], predicted[:, 1], s=18, color="#1f77b4", zorder=4)
    ax.scatter(mapped_points[:, 0], mapped_points[:, 1], s=14, color="#b2182b", zorder=5)
    if correction is not None:
        corrected = correction.corrected_mapped_points
        ax.scatter(
            corrected[:, 0],
            corrected[:, 1],
            s=34,
            facecolors="none",
            edgecolors="#2ca25f",
            linewidths=1.1,
            zorder=8,
        )
    for start, stop in zip(initial, mapped_points):
        arrow = FancyArrowPatch(
            start,
            stop,
            arrowstyle="-|>",
            mutation_scale=10,
            color="red",
            linewidth=1.2,
            connectionstyle="arc3,rad=0.23",
            zorder=7,
        )
        ax.add_patch(arrow)
    ax.text(-1.88, -1.06, rf"Integration Time = $T_0$, $\rho={seed.rotation_angle_rad:.2f}$", fontsize=8)
    ax.text(0.80, -0.94, rf"$\max\|r_i\|={seed.residual_norms.max():.1e}$", fontsize=8)
    if correction is not None:
        ax.text(0.78, -1.08, rf"$\max\|R_i^+\|={correction.final_residual_norms.max():.1e}$", fontsize=8)


def main() -> None:
    apply_style()
    seed = stroboscopic_invariant_curve_seed(SYSTEMS["earth_moon"].mu, samples=7, curve_samples=260)
    correction = stroboscopic_curve_newton_correction(seed)
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.45), constrained_layout=True)
    draw_base_panel(axes[0], mapped=False, seed=seed)
    draw_base_panel(axes[1], mapped=True, seed=seed, correction=correction)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
