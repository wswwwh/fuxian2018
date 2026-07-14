"""Run fast, read-only integrity checks for the reproduction workspace."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


EXPECTED_FIGURE_COUNT = 54
EXPECTED_V0_COUNT = 13
EXPECTED_V2_COUNT = 41
ALLOWED_SOURCE_TYPES = {"explicit", "derived", "digitized", "assumption"}
REQUIRED_TARGET_COLUMNS = {
    "figure_id",
    "source_page",
    "pdf_page",
    "figure_type",
    "title",
    "script",
    "acceptance_tier",
    "target_status",
    "paper_targets",
    "source_type",
    "current_repro_level",
    "uses_proxy",
    "validation_artifact",
    "next_action",
}


class SmokeFailure(RuntimeError):
    """Raised when a read-only reproduction integrity check fails."""


def read_csv(path: Path, project_root: Path) -> list[dict[str, str]]:
    if not path.is_file():
        relative = path.relative_to(project_root).as_posix()
        raise SmokeFailure(f"missing required file: {relative}")
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def require_unique_ids(rows: list[dict[str, str]], label: str) -> list[str]:
    figure_ids = [row.get("figure_id", "").strip() for row in rows]
    if any(not figure_id for figure_id in figure_ids):
        raise SmokeFailure(f"empty figure_id in {label}")
    duplicate_ids = sorted(
        figure_id
        for figure_id, count in Counter(figure_ids).items()
        if count > 1
    )
    if duplicate_ids:
        raise SmokeFailure(
            f"duplicate figure_id in {label}: {duplicate_ids[0]}"
        )
    return figure_ids


def expected_figure_filename(figure_id: str, suffix: str) -> str:
    chapter, number = figure_id.split(".", maxsplit=1)
    return f"fig_{int(chapter)}_{int(number)}.{suffix}"


def require_nonempty_outputs(
    project_root: Path, figure_ids: list[str], suffix: str
) -> int:
    directory = project_root / "outputs" / f"figures_{suffix}"
    missing = [
        expected_figure_filename(figure_id, suffix)
        for figure_id in figure_ids
        if not (directory / expected_figure_filename(figure_id, suffix)).is_file()
        or (directory / expected_figure_filename(figure_id, suffix)).stat().st_size == 0
    ]
    if missing:
        raise SmokeFailure(
            f"missing or empty {suffix.upper()} figure: {missing[0]}"
        )
    return len(figure_ids)


def validate(project_root: Path) -> dict[str, float | int | str]:
    target_path = project_root / "data" / "reproduction_targets.csv"
    target_rows = read_csv(target_path, project_root)
    target_ids = require_unique_ids(target_rows, "target registry")
    if len(target_rows) != EXPECTED_FIGURE_COUNT:
        raise SmokeFailure(
            f"target registry must contain {EXPECTED_FIGURE_COUNT} rows; "
            f"found {len(target_rows)}"
        )
    target_columns = set(target_rows[0]) if target_rows else set()
    missing_columns = sorted(REQUIRED_TARGET_COLUMNS - target_columns)
    if missing_columns:
        raise SmokeFailure(
            f"target registry missing column: {missing_columns[0]}"
        )
    tier_counts = Counter(row["acceptance_tier"] for row in target_rows)
    if tier_counts != Counter({"V0": EXPECTED_V0_COUNT, "V2": EXPECTED_V2_COUNT}):
        raise SmokeFailure(
            "target tier counts must be V0=13 and V2=41; "
            f"found {dict(tier_counts)}"
        )
    unknown_source_types = sorted(
        {row["source_type"] for row in target_rows} - ALLOWED_SOURCE_TYPES
    )
    if unknown_source_types:
        raise SmokeFailure(
            f"unknown target source_type: {unknown_source_types[0]}"
        )
    incomplete_targets = [
        row["figure_id"]
        for row in target_rows
        if "needs_parameter_extraction" in row["target_status"]
    ]
    if incomplete_targets:
        raise SmokeFailure(
            f"incomplete target extraction for figure: {incomplete_targets[0]}"
        )

    index_rows = read_csv(project_root / "data" / "figure_index.csv", project_root)
    validation_rows = read_csv(
        project_root / "data" / "computed" / "figure_validation_table.csv",
        project_root,
    )
    index_ids = require_unique_ids(index_rows, "figure index")
    validation_ids = require_unique_ids(validation_rows, "validation table")
    if set(target_ids) != set(index_ids) or set(target_ids) != set(validation_ids):
        raise SmokeFailure(
            "figure_id sets differ across target registry, figure index, and validation table"
        )

    route_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "chapter3_fixed_mapping_cache_accepted_validation.csv",
        project_root,
    )
    if len(route_rows) < 30:
        raise SmokeFailure(f"Route H validation requires at least 30 rows; found {len(route_rows)}")
    if any("validated" not in row["validation_status"] for row in route_rows):
        raise SmokeFailure("Route H validation contains a non-validated row")
    max_z = max(float(row["max_abs_z_km"]) for row in route_rows)
    max_residual = max(float(row["map_residual_norm"]) for row in route_rows)
    max_jacobi_span = max(float(row["curve_jacobi_span"]) for row in route_rows)
    max_phase_error = max(
        float(row["one_map_phase_return_error"]) for row in route_rows
    )
    if sum(float(row["max_abs_z_km"]) >= 10500.0 for row in route_rows) < 30:
        raise SmokeFailure("Route H has fewer than 30 rows at or above 10,500 km")
    if sum(float(row["max_abs_z_km"]) >= 11000.0 for row in route_rows) < 29:
        raise SmokeFailure("Route H has fewer than 29 rows at or above 11,000 km")
    if max_z < 14500.0:
        raise SmokeFailure(f"Route H maximum amplitude regressed below 14,500 km: {max_z}")
    if max_residual > 1e-9:
        raise SmokeFailure(f"Route H map residual exceeds 1e-9: {max_residual}")
    if max_jacobi_span > 1e-9:
        raise SmokeFailure(f"Route H Jacobi span exceeds 1e-9: {max_jacobi_span}")
    if max_phase_error > 1e-9:
        raise SmokeFailure(f"Route H phase return error exceeds 1e-9: {max_phase_error}")

    cold_start_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "chapter3_fixed_mapping_cold_start_full_audit.csv",
        project_root,
    )
    if len(cold_start_rows) != 1 or not cold_start_rows[0].get("status"):
        raise SmokeFailure("Route H full cold-start audit is incomplete")
    hybrid_cold_start_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "chapter3_route_h_hybrid_cold_start_audit.csv",
        project_root,
    )
    if (
        len(hybrid_cold_start_rows) != 1
        or hybrid_cold_start_rows[0].get("status") != "pass"
    ):
        raise SmokeFailure("Route H hybrid cold-start reconstruction is not pass")

    gate_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "mccarthy2018_staged_goal_gate_status.csv",
        project_root,
    )
    gate_by_id = {row["gate_id"]: row for row in gate_rows}
    goal_gate = gate_by_id.get("STAGED-GOAL-STATUS")
    if not goal_gate or not goal_gate["status"]:
        raise SmokeFailure("staged goal status is missing")
    route_gate = gate_by_id.get("C3-ROUTE-H")
    if not route_gate or route_gate["status"] != "pass":
        raise SmokeFailure("C3-ROUTE-H gate is not pass")

    fig42_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "chapter4_fig42_digitized_comparison_audit.csv",
        project_root,
    )
    if len(fig42_rows) != 1:
        raise SmokeFailure("Fig. 4.2 digitized comparison audit must contain one row")
    fig42 = fig42_rows[0]
    if fig42.get("pointwise_overlap_acceptance") != "true":
        raise SmokeFailure("Fig. 4.2 pointwise overlap is not accepted")
    if fig42.get("full_curve_coverage") != "false":
        raise SmokeFailure("Fig. 4.2 fold-tail boundary is not recorded explicitly")
    fig42_coverage = float(fig42["reference_time_coverage_fraction"])
    fig42_rmse = float(fig42["pointwise_rmse_nu"])
    fig42_tail = float(fig42["computed_tail_time_gap_days"])
    if fig42_coverage < 0.85:
        raise SmokeFailure(f"Fig. 4.2 digitized coverage is below 85%: {fig42_coverage}")
    if fig42_rmse > float(fig42["estimated_y_uncertainty_nu"]):
        raise SmokeFailure(f"Fig. 4.2 pointwise RMSE exceeds uncertainty: {fig42_rmse}")
    if fig42_tail <= 0.0:
        raise SmokeFailure("Fig. 4.2 uncovered fold tail is missing")

    png_count = require_nonempty_outputs(project_root, target_ids, "png")
    pdf_count = require_nonempty_outputs(project_root, target_ids, "pdf")
    level_counts = Counter(row["current_repro_level"] for row in validation_rows)
    return {
        "figures": len(target_ids),
        "targets_v0": tier_counts["V0"],
        "targets_v2": tier_counts["V2"],
        "current_numerical": level_counts["numerical reproduction"],
        "current_open": len(target_ids)
        - EXPECTED_V0_COUNT
        - level_counts["numerical reproduction"],
        "route_h_rows": len(route_rows),
        "route_h_max_z_km": max_z,
        "route_h_max_residual": max_residual,
        "route_h_cold_start_status": cold_start_rows[0]["status"],
        "route_h_hybrid_cold_start_status": hybrid_cold_start_rows[0]["status"],
        "staged_goal_status": goal_gate["status"],
        "fig42_digitized_status": fig42["overall_status"],
        "fig42_digitized_coverage": fig42_coverage,
        "fig42_digitized_rmse": fig42_rmse,
        "fig42_tail_days": fig42_tail,
        "png": png_count,
        "pdf": pdf_count,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root to validate (defaults to this repository).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    try:
        summary = validate(project_root)
    except (SmokeFailure, KeyError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print("SMOKE PASS")
    print(
        f"figures={summary['figures']} "
        f"targets_v0={summary['targets_v0']} targets_v2={summary['targets_v2']}"
    )
    print(
        f"current_numerical={summary['current_numerical']} "
        f"current_open={summary['current_open']}"
    )
    print(
        f"route_h_rows={summary['route_h_rows']} "
        f"max_z_km={summary['route_h_max_z_km']:.12g} "
        f"max_residual={summary['route_h_max_residual']:.3e}"
    )
    print(f"route_h_cold_start_status={summary['route_h_cold_start_status']}")
    print(
        "route_h_hybrid_cold_start_status="
        f"{summary['route_h_hybrid_cold_start_status']}"
    )
    print(f"staged_goal_status={summary['staged_goal_status']}")
    print(
        f"fig42_digitized_status={summary['fig42_digitized_status']} "
        f"coverage={summary['fig42_digitized_coverage']:.6f} "
        f"rmse={summary['fig42_digitized_rmse']:.6f} "
        f"tail_days={summary['fig42_tail_days']:.6f}"
    )
    print(f"png={summary['png']} pdf={summary['pdf']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
