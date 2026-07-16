"""Generate publication-ready invariant-bundle research figures."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import sys
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "research" / "invariant_bundles" / "results"
CSV_DIR = RESULTS / "csv"
NPZ_DIR = RESULTS / "npz"
OUTPUT = ROOT / "research" / "invariant_bundles" / "figures"
REGISTRY = ROOT / "research" / "invariant_bundles" / "benchmarks" / "benchmark_registry.csv"
METHOD_CSV = CSV_DIR / "method_comparison.csv"
RESOLUTION_CSV = CSV_DIR / "resolution_convergence.csv"
PHASE_CSV = CSV_DIR / "phase_continuity.csv"
MANIFOLD_CSV = CSV_DIR / "manifold_convergence.csv"
MANIFOLD_NPZ = NPZ_DIR / "manifold_convergence.npz"
MANIFEST = OUTPUT / "research_figure_manifest.csv"

METHODS = (
    "traditional_pointwise_eigendecomposition",
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
)
METHOD_LABEL = {
    METHODS[0]: "Pointwise eig",
    METHODS[1]: "Partial real Schur",
    METHODS[2]: "QR/SVD cocycle",
}
METHOD_COLOR = {
    METHODS[0]: "#D55E00",
    METHODS[1]: "#0072B2",
    METHODS[2]: "#009E73",
}
METHOD_MARKER = {METHODS[0]: "o", METHODS[1]: "s", METHODS[2]: "^"}
FAMILY_MARKER = {
    "earth_moon_l1_quasi_halo": "o",
    "earth_moon_l1_quasi_vertical": "s",
    "earth_moon_route_h_quasi_dro": "D",
    "sun_earth_l1_two_frequency_torus": "^",
}
FAMILY_LABEL = {
    "earth_moon_l1_quasi_halo": "Halo",
    "earth_moon_l1_quasi_vertical": "Vertical",
    "earth_moon_route_h_quasi_dro": "Route H",
    "sun_earth_l1_two_frequency_torus": "Sun–Earth",
}
METHOD_LINESTYLE = {METHODS[0]: "-", METHODS[1]: "--", METHODS[2]: "-"}
CASE_LABEL = {
    "em_halo_12p40_n21": "Halo 12.40 N21",
    "em_halo_12p40_n33": "Halo 12.40 N33",
    "em_halo_12p40_n45": "Halo 12.40 N45",
    "em_halo_12p09_n15_small": "Halo small N15",
    "em_halo_12p097_n9_lowres_negative": "Halo old N9",
    "em_vertical_12p66_n33": "Vertical N33",
    "em_vertical_12p66_n45": "Vertical N45",
    "em_vertical_12p66_n57": "Vertical N57",
    "route_h_member_68": "Route H 68 physical",
    "route_h_member_17": "Route H 17",
    "route_h_member_32": "Route H 32",
    "route_h_member_54": "Route H 54 max-z",
    "route_h_member_68_legacy_dg_positive": "Route H 68 legacy",
    "se_active_geometry_member_468": "Sun–Earth 468",
    "se_quasi_halo_small_n21": "Sun–Earth small",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.0,
        "axes.labelsize": 8.0,
        "xtick.labelsize": 7.0,
        "ytick.labelsize": 7.0,
        "legend.fontsize": 7.0,
        "axes.linewidth": 0.7,
        "lines.linewidth": 1.4,
        "lines.markersize": 4.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.dpi": 320,
    }
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def panel_label(axis: plt.Axes, label: str) -> None:
    axis.text(
        -0.12,
        1.04,
        label,
        transform=axis.transAxes,
        fontweight="bold",
        fontsize=9,
        va="bottom",
    )


def style_axis(axis: plt.Axes, *, grid: bool = True) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    if grid:
        axis.grid(True, which="major", color="#D9D9D9", linewidth=0.55, alpha=0.8)
        axis.set_axisbelow(True)


def save_figure(figure: plt.Figure, stem: str) -> tuple[Path, Path]:
    png = OUTPUT / f"{stem}.png"
    pdf = OUTPUT / f"{stem}.pdf"
    figure.savefig(png, dpi=320, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return png, pdf


def method_summary(methods: pd.DataFrame) -> tuple[Path, Path]:
    cases = list(dict.fromkeys(methods["case_id"]))
    positions = np.arange(len(cases), dtype=float)
    offsets = {-1: -0.23, 0: 0.0, 1: 0.23}
    figure, axes = plt.subplots(2, 2, figsize=(7.25, 5.6), constrained_layout=True)
    axis = axes[0, 0]
    for method_index, method in enumerate(METHODS):
        selected = methods.set_index(["case_id", "method"]).loc[
            [(case, method) for case in cases]
        ]
        values = selected["max_invariance_residual"].to_numpy(float)
        valid = np.isfinite(values)
        axis.scatter(
            positions[valid] + offsets[method_index - 1],
            values[valid],
            color=METHOD_COLOR[method],
            marker=METHOD_MARKER[method],
            label=METHOD_LABEL[method],
            edgecolor="white",
            linewidth=0.35,
            zorder=3,
        )
    axis.axhline(1.0e-6, color="#333333", linestyle="--", linewidth=0.9, label="research pass")
    axis.set_yscale("log")
    axis.set_ylabel("Max bundle invariance residual")
    axis.set_xticks(positions, [CASE_LABEL[case] for case in cases], rotation=58, ha="right")
    style_axis(axis)
    panel_label(axis, "a")

    axis = axes[0, 1]
    counts = (
        methods.groupby(["method", "research_status"])
        .size()
        .unstack(fill_value=0)
        .reindex(METHODS)
    )
    bottom = np.zeros(len(METHODS))
    status_colors = {"accepted": "#009E73", "boundary": "#E69F00", "fail": "#777777"}
    for status in ("accepted", "boundary", "fail"):
        values = counts.get(status, pd.Series(0, index=METHODS)).to_numpy()
        axis.bar(
            np.arange(len(METHODS)),
            values,
            bottom=bottom,
            color=status_colors[status],
            width=0.66,
            label=status,
        )
        bottom += values
    axis.set_xticks(np.arange(len(METHODS)), [METHOD_LABEL[method] for method in METHODS], rotation=20, ha="right")
    axis.set_ylabel("Benchmark cases")
    axis.set_ylim(0, 16)
    axis.legend(frameon=False, ncol=3, loc="upper center")
    style_axis(axis)
    panel_label(axis, "b")

    axis = axes[1, 0]
    for method in METHODS:
        selected = methods[methods["method"] == method]
        for family, group in selected.groupby("family"):
            valid = np.isfinite(group["max_invariance_residual"])
            axis.scatter(
                group.loc[valid, "runtime_seconds"],
                group.loc[valid, "max_invariance_residual"],
                color=METHOD_COLOR[method],
                marker=FAMILY_MARKER[family],
                alpha=0.85,
                edgecolor="white",
                linewidth=0.35,
            )
    axis.axhline(1.0e-6, color="#333333", linestyle="--", linewidth=0.9)
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Runtime per case (s)")
    axis.set_ylabel("Max invariance residual")
    style_axis(axis)
    panel_label(axis, "c")
    method_handles = [
        Line2D([0], [0], color=METHOD_COLOR[m], marker="o", linestyle="", label=METHOD_LABEL[m])
        for m in METHODS
    ]
    family_handles = [
        Line2D([0], [0], color="#555555", marker=marker, linestyle="", label=FAMILY_LABEL[family])
        for family, marker in FAMILY_MARKER.items()
    ]
    method_legend = axis.legend(handles=method_handles, frameon=False, loc="lower left")
    axis.add_artist(method_legend)
    axis.legend(handles=family_handles, frameon=False, loc="upper right", ncol=2)

    axis = axes[1, 1]
    high_cases = [
        "em_halo_12p40_n45",
        "em_vertical_12p66_n57",
        "se_active_geometry_member_468",
    ]
    nominal = methods[methods["case_id"].isin(high_cases)]
    width = 0.24
    for method_index, method in enumerate(METHODS):
        selected = nominal[nominal["method"] == method].set_index("case_id").loc[high_cases]
        axis.bar(
            np.arange(len(high_cases)) + (method_index - 1) * width,
            selected["phase_principal_angle_max_deg"],
            width=width,
            color=METHOD_COLOR[method],
            label=METHOD_LABEL[method],
        )
    axis.set_yscale("log")
    axis.set_ylabel("Max adjacent-phase angle (deg)")
    axis.set_xticks(np.arange(len(high_cases)), [CASE_LABEL[c] for c in high_cases], rotation=20, ha="right")
    style_axis(axis)
    panel_label(axis, "d")
    return save_figure(figure, "fig_bundle_method_summary")


def resolution_figure(methods: pd.DataFrame, resolution: pd.DataFrame, manifold: pd.DataFrame) -> tuple[Path, Path]:
    figure, axes = plt.subplots(2, 2, figsize=(7.0, 5.2), constrained_layout=True)
    groups = {
        "halo_12p40": ["em_halo_12p40_n21", "em_halo_12p40_n33", "em_halo_12p40_n45"],
        "vertical_12p66": ["em_vertical_12p66_n33", "em_vertical_12p66_n45", "em_vertical_12p66_n57"],
    }
    for axis, (group_name, cases), label in zip(axes[0], groups.items(), ("a", "b")):
        for method in METHODS:
            values = methods[(methods["case_id"].isin(cases)) & (methods["method"] == method)].set_index("case_id").loc[cases]
            axis.plot(
                values["spectral_samples"],
                values["max_invariance_residual"],
                color=METHOD_COLOR[method],
                marker=METHOD_MARKER[method],
                label=METHOD_LABEL[method],
            )
        axis.axhline(1.0e-6, color="#333333", linestyle="--", linewidth=0.9)
        axis.set_yscale("log")
        axis.set_xlabel("Spectral samples N")
        axis.set_ylabel("Max invariance residual")
        axis.set_xticks([int(methods[methods["case_id"] == case]["spectral_samples"].iloc[0]) for case in cases])
        style_axis(axis)
        panel_label(axis, label)
    axes[0, 0].legend(frameon=False, loc="best")

    nominal = manifold[
        np.isclose(manifold["perturbation_norm"], 1.0e-7)
        & (manifold["perturbation_sign"] == 1)
    ]
    axis = axes[1, 0]
    for group_name, cases in groups.items():
        for method in METHODS[1:]:
            comparison_cases = cases[:-1]
            values = nominal[(nominal["case_id"].isin(comparison_cases)) & (nominal["method"] == method)].set_index("case_id").loc[comparison_cases]
            linestyle = "-" if group_name == "halo_12p40" else "--"
            axis.plot(
                values["spectral_samples"],
                values["cross_resolution_normalized_3d_distance"],
                color=METHOD_COLOR[method],
                marker="o" if group_name == "halo_12p40" else "s",
                linestyle=linestyle,
                label=f"{METHOD_LABEL[method]} / {'Halo' if group_name == 'halo_12p40' else 'Vertical'}",
            )
    axis.axhline(0.01, color="#333333", linestyle="--", linewidth=0.9, label="0.01 boundary")
    axis.set_yscale("log")
    axis.set_ylim(8.0e-3, 3.0e-2)
    axis.set_xlabel("Spectral samples N")
    axis.set_ylabel("Cross-N full-sheet distance")
    style_axis(axis)
    panel_label(axis, "c")
    axis.legend(frameon=False, ncol=2, loc="best")

    axis = axes[1, 1]
    for group_name in groups:
        selected = resolution[resolution["resolution_group"] == group_name]
        for method in METHODS:
            values = selected[selected["method"] == method].sort_values("spectral_samples")
            axis.plot(
                values["spectral_samples"],
                values["principal_angle_max_deg"],
                color=METHOD_COLOR[method],
                marker="o" if group_name == "halo_12p40" else "s",
                linestyle="-" if group_name == "halo_12p40" else "--",
                alpha=0.9,
            )
    axis.set_yscale("log")
    axis.set_xlabel("Spectral samples N")
    axis.set_ylabel("Cross-N principal angle (deg)")
    style_axis(axis)
    panel_label(axis, "d")
    return save_figure(figure, "fig_resolution_convergence")


def route_h_control(methods: pd.DataFrame) -> tuple[Path, Path]:
    physical = "route_h_member_68"
    legacy = "route_h_member_68_legacy_dg_positive"
    cases = [physical, legacy]
    selected = methods[methods["case_id"].isin(cases)]
    figure, axes = plt.subplots(1, 3, figsize=(7.25, 2.65), constrained_layout=True)
    axis = axes[0]
    values = selected.groupby("case_id")["source_map_residual_recomputed"].first().reindex(cases)
    axis.bar([0, 1], values, color=["#0072B2", "#E69F00"], width=0.62)
    axis.set_yscale("log")
    axis.set_ylabel("Curve map residual")
    axis.set_xticks([0, 1], ["corrected ρ", "legacy seed ρ"], rotation=18, ha="right")
    style_axis(axis)
    panel_label(axis, "a")

    axis = axes[1]
    schur = selected[selected["method"] == METHODS[1]].set_index("case_id").loc[cases]
    axis.bar([0, 1], schur["relative_imaginary_part"], color=["#0072B2", "#E69F00"], width=0.62)
    axis.axhline(1.0e-10, color="#333333", linestyle="--", linewidth=0.9)
    axis.set_yscale("symlog", linthresh=1.0e-12)
    axis.set_ylabel("Selected relative imaginary part")
    axis.set_xticks(
        [0, 1],
        [
            f"corrected ρ\n(dim {int(schur.loc[physical, 'bundle_dimension'])})",
            f"legacy seed ρ\n(dim {int(schur.loc[legacy, 'bundle_dimension'])})",
        ],
    )
    axis.text(0, float(schur.loc[physical, "relative_imaginary_part"]) * 1.08, f"{schur.loc[physical, 'relative_imaginary_part']:.3f}", ha="center", va="bottom", fontsize=7)
    axis.text(1, 2.0e-12, "0", ha="center", va="bottom", fontsize=7)
    style_axis(axis)
    panel_label(axis, "b")

    axis = axes[2]
    width = 0.34
    for method_index, method in enumerate(METHODS[1:]):
        values = selected[selected["method"] == method].set_index("case_id").loc[cases]
        axis.bar(
            np.arange(2) + (method_index - 0.5) * width,
            values["max_invariance_residual"],
            width=width,
            color=METHOD_COLOR[method],
            label=METHOD_LABEL[method],
        )
    axis.axhline(1.0e-6, color="#333333", linestyle="--", linewidth=0.9)
    axis.set_yscale("log")
    axis.set_ylabel("Max invariance residual")
    axis.set_xticks([0, 1], ["corrected ρ", "legacy seed ρ"], rotation=18, ha="right")
    axis.legend(frameon=False, loc="best")
    style_axis(axis)
    panel_label(axis, "c")
    return save_figure(figure, "fig_route_h_rho_control")


def manifold_metrics(manifold: pd.DataFrame) -> tuple[Path, Path]:
    nominal = manifold[
        np.isclose(manifold["perturbation_norm"], 1.0e-7)
        & (manifold["perturbation_sign"] == 1)
    ]
    high_cases = [
        "em_halo_12p40_n45",
        "em_vertical_12p66_n57",
        "se_active_geometry_member_468",
    ]
    figure, axes = plt.subplots(2, 2, figsize=(7.0, 5.1), constrained_layout=True)
    width = 0.24
    axis = axes[0, 0]
    for method_index, method in enumerate(METHODS):
        values = nominal[(nominal["case_id"].isin(high_cases)) & (nominal["method"] == method)].set_index("case_id").loc[high_cases]
        axis.bar(
            np.arange(len(high_cases)) + (method_index - 1) * width,
            values["direction_principal_angle_max_deg_to_qr"].clip(lower=1.0e-7),
            width=width,
            color=METHOD_COLOR[method],
            label=METHOD_LABEL[method],
        )
    axis.set_yscale("log")
    axis.set_ylabel("Direction angle to QR (deg)")
    axis.set_xticks(np.arange(len(high_cases)), [CASE_LABEL[c] for c in high_cases], rotation=20, ha="right")
    style_axis(axis)
    panel_label(axis, "a")

    axis = axes[0, 1]
    for method_index, method in enumerate(METHODS):
        values = nominal[(nominal["case_id"].isin(high_cases)) & (nominal["method"] == method)].set_index("case_id").loc[high_cases]
        axis.bar(
            np.arange(len(high_cases)) + (method_index - 1) * width,
            values["normalized_displacement_distance_to_qr"].clip(lower=1.0e-12),
            width=width,
            color=METHOD_COLOR[method],
        )
    axis.set_yscale("log")
    axis.set_ylabel("Normalized displacement distance to QR")
    axis.set_xticks(np.arange(len(high_cases)), [CASE_LABEL[c] for c in high_cases], rotation=20, ha="right")
    style_axis(axis)
    panel_label(axis, "b")

    axis = axes[1, 0]
    selected = manifold[manifold["case_id"].isin(high_cases)]
    for method in METHODS:
        values = (
            selected[selected["method"] == method]
            .groupby("perturbation_norm")["normalized_displacement_perturbation_sensitivity"]
            .max()
        )
        axis.plot(
            values.index,
            values.values.clip(min=1.0e-12),
            color=METHOD_COLOR[method],
            marker=METHOD_MARKER[method],
            label=METHOD_LABEL[method],
        )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Perturbation norm")
    axis.set_ylabel("Normalized displacement sensitivity")
    style_axis(axis)
    panel_label(axis, "c")
    axis.legend(frameon=False, loc="best")

    axis = axes[1, 1]
    for method in METHODS:
        values = nominal[nominal["method"] == method]
        axis.scatter(
            values["bundle_invariance_residual_max"],
            values["normalized_displacement_distance_to_qr"].clip(lower=1.0e-12),
            color=METHOD_COLOR[method],
            marker=METHOD_MARKER[method],
            label=METHOD_LABEL[method],
            alpha=0.85,
            edgecolor="white",
            linewidth=0.35,
        )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlabel("Bundle invariance residual")
    axis.set_ylabel("Displacement distance to QR")
    style_axis(axis)
    panel_label(axis, "d")
    return save_figure(figure, "fig_manifold_method_metrics")


def phase_profiles(phase: pd.DataFrame) -> tuple[Path, Path]:
    cases = [
        "em_halo_12p40_n45",
        "em_vertical_12p66_n57",
        "se_active_geometry_member_468",
    ]
    figure, axes = plt.subplots(2, 3, figsize=(7.25, 4.5), constrained_layout=True, sharex="col")
    for column, case_id in enumerate(cases):
        selected = phase[phase["case_id"] == case_id]
        for method in METHODS:
            values = selected[selected["method"] == method].sort_values("phase_rad")
            axes[0, column].plot(
                values["phase_rad"] / (2.0 * np.pi),
                values["invariance_residual"].clip(lower=1.0e-15),
                color=METHOD_COLOR[method],
                linestyle=METHOD_LINESTYLE[method],
                label=METHOD_LABEL[method],
            )
            axes[1, column].plot(
                values["phase_rad"] / (2.0 * np.pi),
                values["principal_angle_to_next_deg"].clip(lower=1.0e-8),
                color=METHOD_COLOR[method],
                linestyle=METHOD_LINESTYLE[method],
            )
        axes[0, column].set_yscale("log")
        axes[1, column].set_yscale("log")
        axes[1, column].set_xlabel("Phase / 2π")
        axes[0, column].text(0.03, 0.94, CASE_LABEL[case_id], transform=axes[0, column].transAxes, va="top", fontsize=8)
        style_axis(axes[0, column])
        style_axis(axes[1, column])
        panel_label(axes[0, column], chr(ord("a") + column))
        panel_label(axes[1, column], chr(ord("d") + column))
    axes[0, 0].set_ylabel("Local invariance residual")
    axes[1, 0].set_ylabel("Adjacent-phase angle (deg)")
    axes[0, 2].legend(frameon=False, loc="best")
    return save_figure(figure, "fig_phase_continuity_profiles")


def manifold_sheet() -> tuple[Path, Path]:
    case_id = "em_halo_12p40_n45"
    epsilon_key = "eps_1em07__sign_p1"
    figure = plt.figure(figsize=(7.25, 2.65), constrained_layout=True)
    axes = [figure.add_subplot(1, 3, index + 1, projection="3d") for index in range(3)]
    values_by_method: dict[str, np.ndarray] = {}
    with np.load(MANIFOLD_NPZ, allow_pickle=False) as archive:
        base = np.asarray(archive[f"{case_id}__base_states"])
        for method in METHODS:
            key = f"{case_id}__{method}__{epsilon_key}__manifold_states"
            history = np.asarray(archive[key])
            values_by_method[method] = (history[:, :, :3] - base[:, :, :3]) / 1.0e-7
    stacked = np.concatenate([values.reshape(-1, 3) for values in values_by_method.values()])
    limits = np.max(np.abs(stacked), axis=0)
    for axis, method, label in zip(axes, METHODS, ("a", "b", "c")):
        values = values_by_method[method]
        for phase_index in range(0, values.shape[1], 3):
            axis.plot(
                values[:, phase_index, 0],
                values[:, phase_index, 1],
                values[:, phase_index, 2],
                color=METHOD_COLOR[method],
                alpha=0.52,
                linewidth=0.75,
            )
        for time_index in (0, 10, 20, 30, 40):
            loop = np.vstack((values[time_index], values[time_index, 0]))
            axis.plot(loop[:, 0], loop[:, 1], loop[:, 2], color="#333333", alpha=0.35, linewidth=0.55)
        axis.set_xlim(-limits[0], limits[0])
        axis.set_ylim(-limits[1], limits[1])
        axis.set_zlim(-limits[2], limits[2])
        axis.set_xlabel("δx / ε", labelpad=-1)
        axis.set_ylabel("δy / ε", labelpad=-1)
        axis.set_zlabel("δz / ε", labelpad=-1)
        axis.tick_params(pad=0, labelsize=6)
        axis.view_init(elev=22, azim=-58)
        axis.text2D(0.02, 0.96, f"{label}  {METHOD_LABEL[method]}", transform=axis.transAxes, fontweight="bold", fontsize=8)
    return save_figure(figure, "fig_halo_manifold_displacement_sheets")


def write_manifest(outputs: list[tuple[str, tuple[Path, Path], str]], run_id: str) -> None:
    with MANIFEST.open("w", newline="", encoding="utf-8") as stream:
        fields = (
            "figure_id",
            "format",
            "artifact",
            "sha256",
            "source_run_id",
            "source_method_csv_sha256",
            "source_manifold_csv_sha256",
            "description",
        )
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for figure_id, paths, description in outputs:
            for path in paths:
                writer.writerow(
                    {
                        "figure_id": figure_id,
                        "format": path.suffix.lstrip("."),
                        "artifact": os.path.relpath(path, ROOT).replace("\\", "/"),
                        "sha256": sha256(path),
                        "source_run_id": run_id,
                        "source_method_csv_sha256": sha256(METHOD_CSV),
                        "source_manifold_csv_sha256": sha256(MANIFOLD_CSV),
                        "description": description,
                    }
                )


def generate() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    methods = pd.read_csv(METHOD_CSV)
    resolution = pd.read_csv(RESOLUTION_CSV)
    phase = pd.read_csv(PHASE_CSV)
    manifold = pd.read_csv(MANIFOLD_CSV)
    run_ids = set(methods["run_id"])
    if len(run_ids) != 1:
        raise RuntimeError("method comparison contains mixed run IDs")
    outputs = [
        ("F1", method_summary(methods), "Bundle residual, status, runtime, and phase-continuity summary."),
        ("F2", resolution_figure(methods, resolution, manifold), "Bundle and manifold convergence with spectral resolution."),
        ("F3", route_h_control(methods), "Route-H member-68 corrected-rho versus frozen legacy-DG control."),
        ("F4", manifold_metrics(manifold), "Direction, displacement, perturbation, and residual manifold metrics."),
        ("F5", phase_profiles(phase), "Phase-resolved residual and adjacent-angle profiles."),
        ("F6", manifold_sheet(), "Normalized Halo N45 displacement sheets for the three methods."),
    ]
    write_manifest(outputs, next(iter(run_ids)))
    print(f"research figures WRITE PASS figures={len(outputs)} artifacts={2 * len(outputs)}")


def check() -> None:
    if not MANIFEST.is_file():
        raise RuntimeError("research figure manifest is missing")
    with MANIFEST.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 12 or len({row["figure_id"] for row in rows}) != 6:
        raise RuntimeError("research figure manifest coverage drifted")
    for row in rows:
        path = ROOT / row["artifact"]
        if not path.is_file() or sha256(path) != row["sha256"]:
            raise RuntimeError(f"research figure hash drifted: {row['artifact']}")
        if path.suffix == ".png" and path.stat().st_size < 20_000:
            raise RuntimeError(f"research PNG appears empty: {row['artifact']}")
    if any(row["source_method_csv_sha256"] != sha256(METHOD_CSV) for row in rows):
        raise RuntimeError("research figure method source hash drifted")
    if any(row["source_manifold_csv_sha256"] != sha256(MANIFOLD_CSV) for row in rows):
        raise RuntimeError("research figure manifold source hash drifted")
    print("research figures CHECK PASS figures=6 artifacts=12")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    else:
        generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
