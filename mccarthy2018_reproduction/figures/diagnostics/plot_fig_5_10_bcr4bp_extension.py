"""Plot the dedicated Fig. 5.10 DE421-initialized BCR4BP audit.

This is a diagnostic extension of the CR3BP Fig. 5.10 reproduction.  It is
deliberately saved outside the canonical figure directories because the
project-selected DE421 epoch and the BCR4BP boundary states are not a thesis
pointwise reproduction.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.plot_style import apply_style, finalize_figure  # noqa: E402


AUDIT_PATH = PROJECT_ROOT / "data" / "computed" / "chapter5_fig510_bcr4bp_transfer_audit.csv"
TRAJECTORY_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter5_fig510_bcr4bp_transfer_trajectories.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "diagnostics"
PNG_PATH = OUTPUT_DIR / "fig_5_10_bcr4bp_extension.png"
PDF_PATH = OUTPUT_DIR / "fig_5_10_bcr4bp_extension.pdf"
PDF_METADATA = {
    "Title": "Fig. 5.10 DE421-initialized planar BCR4BP diagnostic",
    "Creator": "mccarthy2018_reproduction",
    "CreationDate": None,
    "ModDate": None,
}

CR3BP_COLOR = "#2563b8"
BCR4BP_COLOR = "#d97706"
PAPER_COLOR = "#6b7280"
CORRECTED_COLOR = "#0f766e"
MOON_COLOR = "#111827"


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"required audit artifact is missing: {path}")
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _float(row: dict[str, str], field: str) -> float:
    value = float(row[field])
    if not np.isfinite(value):
        raise ValueError(f"non-finite {field!r} in case {row.get('case_id', '?')}")
    return value


def _truth(row: dict[str, str], field: str) -> bool:
    value = row[field].strip().lower()
    if value not in {"true", "false"}:
        raise ValueError(f"invalid boolean {field!r}: {row[field]!r}")
    return value == "true"


def _audit_by_case() -> dict[int, dict[str, str]]:
    rows = _read_rows(AUDIT_PATH)
    result = {int(row["case_id"]): row for row in rows}
    if set(result) != {1, 2} or len(rows) != 2:
        raise RuntimeError("Fig. 5.10 BCR4BP audit must contain exactly cases 1 and 2")
    return result


def _trajectories_by_case() -> dict[int, dict[str, np.ndarray]]:
    rows = _read_rows(TRAJECTORY_PATH)
    grouped: dict[int, dict[str, list[dict[str, str]]]] = {}
    for row in rows:
        case_id = int(row["case_id"])
        grouped.setdefault(case_id, {}).setdefault(row["model"], []).append(row)

    result: dict[int, dict[str, np.ndarray]] = {}
    for case_id in (1, 2):
        if set(grouped.get(case_id, {})) != {"cr3bp_seed", "bcr4bp_strict"}:
            raise RuntimeError(
                f"case {case_id} must contain cr3bp_seed and bcr4bp_strict trajectories"
            )
        result[case_id] = {}
        for model, model_rows in grouped[case_id].items():
            ordered = sorted(model_rows, key=lambda row: int(row["sample"]))
            states = np.asarray(
                [[_float(row, field) for field in ("x_nd", "y_nd", "z_nd")] for row in ordered],
                dtype=float,
            )
            if states.shape[0] < 2:
                raise RuntimeError(f"case {case_id} {model} trajectory has fewer than two samples")
            result[case_id][model] = states
    return result


def _set_limits(ax, states: list[np.ndarray]) -> None:
    combined = np.vstack(states)
    lower = np.min(combined, axis=0)
    upper = np.max(combined, axis=0)
    span = np.maximum(upper - lower, 1.0e-4)
    padding = 0.08 * span
    ax.set_xlim(lower[0] - padding[0], upper[0] + padding[0])
    ax.set_ylim(lower[1] - padding[1], upper[1] + padding[1])
    ax.set_zlim(lower[2] - padding[2], upper[2] + padding[2])
    ax.set_box_aspect(tuple((span / np.max(span)).tolist()))


def _plot_transfer_panel(
    ax,
    *,
    case_id: int,
    audit: dict[str, str],
    trajectories: dict[str, np.ndarray],
) -> None:
    seed = trajectories["cr3bp_seed"]
    corrected = trajectories["bcr4bp_strict"]
    moon = np.array([1.0 - SYSTEMS["earth_moon"].mu, 0.0, 0.0])

    ax.plot(
        seed[:, 0],
        seed[:, 1],
        seed[:, 2],
        color=CR3BP_COLOR,
        linestyle="--",
        linewidth=1.45,
        label="CR3BP seed",
    )
    ax.plot(
        corrected[:, 0],
        corrected[:, 1],
        corrected[:, 2],
        color=BCR4BP_COLOR,
        linewidth=1.75,
        label="BCR4BP corrected",
    )
    ax.scatter(*corrected[0], color=MOON_COLOR, s=18, depthshade=False, label="departure")
    ax.scatter(*seed[-1], color=CR3BP_COLOR, marker="x", s=28, depthshade=False)
    ax.scatter(
        *corrected[-1],
        facecolor="white",
        edgecolor=BCR4BP_COLOR,
        linewidth=1.1,
        s=30,
        depthshade=False,
        label="corrected arrival",
    )
    ax.scatter(*moon, color=MOON_COLOR, marker="o", s=12, depthshade=False)
    ax.text(moon[0], moon[1], moon[2], "  Moon", fontsize=6.5)

    _set_limits(ax, [seed, corrected, moon.reshape(1, 3)])
    ax.set_xlabel("X [nd]")
    ax.set_ylabel("Y [nd]")
    ax.set_zlabel("Z [nd]")
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.label.set_fontsize(9)
    ax.view_init(elev=22, azim=-58)
    ax.set_title(
        f"({chr(96 + case_id)}) Case {case_id}: {_float(audit, 'time_of_flight_days'):.1f} d"
        f"  |  numerical PASS",
        fontsize=9,
    )
    ax.legend(fontsize=6.2, loc="upper left", borderaxespad=0.1)


def _annotate_bars(ax, containers, *, scientific: bool = False) -> None:
    for container in containers:
        for bar in container:
            value = bar.get_height()
            label = f"{value:.1e}" if scientific else f"{value:.1f}"
            ax.annotate(
                label,
                xy=(bar.get_x() + bar.get_width() / 2.0, value),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=6.5,
            )


def _plot_delta_v_panel(ax, audit: dict[int, dict[str, str]]) -> None:
    cases = (1, 2)
    x = np.arange(len(cases), dtype=float)
    width = 0.24
    paper = [_float(audit[case], "paper_total_delta_v_m_s") for case in cases]
    seed = [_float(audit[case], "cr3bp_seed_total_delta_v_m_s") for case in cases]
    bcr4bp = [_float(audit[case], "total_delta_v_m_s") for case in cases]

    bars = [
        ax.bar(x - width, paper, width, color=PAPER_COLOR, label="thesis target"),
        ax.bar(x, seed, width, color=CR3BP_COLOR, label="CR3BP seed"),
        ax.bar(x + width, bcr4bp, width, color=BCR4BP_COLOR, label="BCR4BP corrected"),
    ]
    _annotate_bars(ax, bars)
    ax.set_xticks(x, [f"Case {case}" for case in cases])
    ax.set_ylabel(r"Total $\Delta v$ [m/s]")
    ax.set_ylim(0.0, 110.0)
    ax.set_title("(c) Two-impulse total $\Delta v$ comparison", fontsize=9)
    ax.legend(fontsize=7, loc="upper left", ncols=3)


def _plot_endpoint_panel(ax, audit: dict[int, dict[str, str]]) -> None:
    cases = (1, 2)
    x = np.arange(len(cases), dtype=float)
    width = 0.31
    uncorrected = [_float(audit[case], "uncorrected_endpoint_error_km") for case in cases]
    independent = [_float(audit[case], "independent_endpoint_error_km") for case in cases]

    bars = [
        ax.bar(x - width / 2.0, uncorrected, width, color=PAPER_COLOR, label="uncorrected"),
        ax.bar(
            x + width / 2.0,
            independent,
            width,
            color=CORRECTED_COLOR,
            label="independent corrected",
        ),
    ]
    _annotate_bars(ax, bars, scientific=True)
    ax.axhline(1.0e-3, color="#b91c1c", linestyle="--", linewidth=1.0, label="1e-3 km gate")
    ax.set_yscale("log")
    ax.set_ylim(1.0e-6, 3.0e5)
    ax.set_xticks(x, [f"Case {case}" for case in cases])
    ax.set_ylabel("Endpoint position error [km]")
    ax.set_title("(d) Independent terminal propagation audit", fontsize=9)
    ax.legend(fontsize=7, loc="upper right")


def main() -> None:
    apply_style()
    audit = _audit_by_case()
    trajectories = _trajectories_by_case()

    if not all(_truth(audit[case], "numerical_acceptance") for case in (1, 2)):
        raise RuntimeError("the dedicated numerical audit is not accepted for both cases")
    if any(_truth(audit[case], "paper_equivalence") for case in (1, 2)):
        raise RuntimeError("the diagnostic boundary expects paper_equivalence=false for both cases")

    fig = plt.figure(figsize=(11.2, 8.6), constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=0.05, h_pad=0.10, wspace=0.06, hspace=0.16)
    grid = fig.add_gridspec(2, 2, height_ratios=(1.15, 0.90))
    for case_id in (1, 2):
        ax = fig.add_subplot(grid[0, case_id - 1], projection="3d")
        _plot_transfer_panel(
            ax,
            case_id=case_id,
            audit=audit[case_id],
            trajectories=trajectories[case_id],
        )

    _plot_delta_v_panel(fig.add_subplot(grid[1, 0]), audit)
    _plot_endpoint_panel(fig.add_subplot(grid[1, 1]), audit)
    fig.suptitle(
        "Fig. 5.10 diagnostic: DE421-initialized planar BCR4BP extension\n"
        "Numerical acceptance 2/2; paper equivalence 0/2 (not a canonical thesis-figure replacement)",
        fontsize=11,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    finalize_figure(fig)
    fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight", pad_inches=0.20)
    fig.savefig(
        PDF_PATH,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.20,
        metadata=PDF_METADATA,
    )
    plt.close(fig)
    print(PNG_PATH)
    print(PDF_PATH)


if __name__ == "__main__":
    main()
