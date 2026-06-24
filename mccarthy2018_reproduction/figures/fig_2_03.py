"""Figure 2.3: Earth-Moon libration point locations."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure


FIGURE_ID = "2.3"
SOURCE_PAGE = 14
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    points = compute_libration_points(system.mu)

    fig, ax = plt.subplots(figsize=(6.7, 5.8))
    ax.scatter([-system.mu], [0.0], s=110, color="tab:blue", label=system.primary, zorder=4)
    ax.scatter([1.0 - system.mu], [0.0], s=42, color="0.25", label=system.secondary, zorder=4)

    for label, point in points.items():
        ax.scatter(point.x, point.y, s=35, color="tab:red", zorder=5)
        dx = 0.025 if label in {"L1", "L2", "L4"} else -0.075
        dy = 0.035 if label != "L5" else -0.055
        ax.text(point.x + dx, point.y + dy, label)

    ax.axhline(0.0, color="0.45", linewidth=0.8)
    ax.axvline(0.0, color="0.8", linewidth=0.7)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-1.25, 1.25)
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel(r"$\hat{x}$")
    ax.set_ylabel(r"$\hat{y}$")
    ax.set_title("Earth-Moon libration points in the rotating frame")
    ax.legend(loc="upper right")
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
