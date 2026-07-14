"""Run fast, read-only integrity checks for the reproduction workspace."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path


EXPECTED_FIGURE_COUNT = 54
EXPECTED_V0_COUNT = 13
EXPECTED_V2_COUNT = 41
EXPECTED_FIG510_EPOCH = "2020-06-15T00:00:00Z"
EXPECTED_DE421_SHA256 = (
    "A20A7139DA04CBC462454634918E9A9CA69127044E2CC9D4F9C16E238D2DEEDC"
)
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


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
    fig510_gate = gate_by_id.get("C5-FIG510-BCR4BP-TRANSFER-AUDIT")
    if not fig510_gate or fig510_gate["status"] != "pass":
        raise SmokeFailure("C5-FIG510-BCR4BP-TRANSFER-AUDIT gate is not pass")

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

    chapter4_fixed_time_rows: list[dict[str, str]] = []
    for audit_name, npz_name, generator_name, schema_version in (
        (
            "chapter4_fig43_fig44_global_manifold_audit.csv",
            "chapter4_fig43_fig44_global_manifold_audit.npz",
            "run_chapter4_fig43_fig44_global_manifold_audit.py",
            "chapter4_fig43_fig44_fixed_time_audit_v2",
        ),
        (
            "chapter4_fig45_fig48_vertical_manifold_audit.csv",
            "chapter4_fig45_fig48_vertical_manifold_audit.npz",
            "run_chapter4_fig45_fig48_vertical_manifold_audit.py",
            "fixed_time_vertical_manifold_audit_v2",
        ),
    ):
        rows = read_csv(
            project_root / "data" / "computed" / audit_name,
            project_root,
        )
        if len(rows) != 8:
            raise SmokeFailure(f"{audit_name} must contain eight panel rows")
        npz_path = project_root / "data" / "computed" / npz_name
        generator_path = project_root / "scripts" / generator_name
        core_path = project_root / "src" / "qp_orbits" / "torus_stability.py"
        for artifact in (npz_path, generator_path, core_path):
            if not artifact.is_file():
                raise SmokeFailure(
                    "missing Chapter 4 fixed-time fingerprint source: "
                    f"{artifact.relative_to(project_root).as_posix()}"
                )
        expected_fingerprint = {
            "artifact_fingerprint_version": "1",
            "npz_schema_version": schema_version,
            "npz_sha256": sha256(npz_path),
            "generator_sha256": sha256(generator_path),
            "core_torus_stability_sha256": sha256(core_path),
        }
        if any(
            any(row.get(field) != value for field, value in expected_fingerprint.items())
            for row in rows
        ):
            raise SmokeFailure(
                f"{audit_name} fingerprint is stale relative to NPZ/code"
            )
        chapter4_fixed_time_rows.extend(rows)
    if any(
        row.get("acceptance") != "pass"
        or row.get("numerical_acceptance") != "pass"
        or row.get("configuration_reach_acceptance") != "pass"
        or row.get("overall_acceptance") != "pass"
        or row.get("local_linearization_gate") != "pass"
        or row.get("linear_reference_method")
        != "base_trajectory_STM_first_order"
        or row.get("far_field_linearization_status") != "diagnostic_only"
        for row in chapter4_fixed_time_rows
    ):
        raise SmokeFailure(
            "Chapter 4 fixed-time numerical/configuration audit is not 16/16 pass"
        )
    if any(
        row.get("paper_projection_acceptance") != "not_run"
        or row.get("paper_3d_equivalence") != "false"
        or row.get("epsilon_selection_status")
        != "project_visualization_parameter_uncalibrated"
        for row in chapter4_fixed_time_rows
    ):
        raise SmokeFailure("Chapter 4 fixed-time paper boundary is not explicit")

    chapter4_source_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "chapter4_per_figure_source_layer_audit.csv",
        project_root,
    )
    fixed_time_source_rows = [
        row
        for row in chapter4_source_rows
        if row.get("figure_id") in {"4.3", "4.4", "4.5", "4.6"}
    ]
    if len(fixed_time_source_rows) != 4:
        raise SmokeFailure("Chapter 4 fixed-time per-figure mapping must contain four rows")
    if any(
        row.get("accepted_rows") != "4"
        or row.get("original_replacement_status")
            != "numerical_fixed_time_manifold_and_configuration_reach_pass_projection_pending_boundary"
        for row in fixed_time_source_rows
    ):
        raise SmokeFailure("Chapter 4 fixed-time per-figure status is inconsistent")

    projection_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "chapter4_fig43_fig46_projection_diagnostic.csv",
        project_root,
    )
    if len(projection_rows) != 16:
        raise SmokeFailure("Chapter 4 projection diagnostic must contain 16 panel rows")
    if any(
        row.get("status") != "diagnostic_only"
        or row.get("paper_projection_acceptance") != "not_run"
        or row.get("paper_3d_equivalence") != "false"
        for row in projection_rows
    ):
        raise SmokeFailure("Chapter 4 diagnostic-only projection boundary regressed")
    source_hashes: dict[Path, str] = {}
    for row in projection_rows:
        for source_field, hash_field in (
            ("paper_source", "paper_source_sha256"),
            ("reproduction_source", "reproduction_source_sha256"),
        ):
            source = (project_root / row[source_field]).resolve()
            try:
                source.relative_to(project_root)
            except ValueError as error:
                raise SmokeFailure(
                    f"Chapter 4 projection source escapes project root: {source}"
                ) from error
            if not source.is_file():
                raise SmokeFailure(
                    f"Chapter 4 projection source is missing: {row[source_field]}"
                )
            if source not in source_hashes:
                source_hashes[source] = sha256(source)
            current_hash = source_hashes[source]
            if current_hash != row.get(hash_field):
                raise SmokeFailure(
                    f"Chapter 4 projection source hash is stale: {row[source_field]}"
                )
    projection_alerts = sum(
        row.get("failure_items", "none") != "none" for row in projection_rows
    )

    fig510_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "chapter5_fig510_bcr4bp_transfer_audit.csv",
        project_root,
    )
    if len(fig510_rows) != 2 or {row["case_id"] for row in fig510_rows} != {"1", "2"}:
        raise SmokeFailure("Fig. 5.10 BCR4BP audit must contain cases 1 and 2")
    fig510_by_case = {row["case_id"]: row for row in fig510_rows}
    expected_tof = {"1": 23.0, "2": 12.4}
    for case_id, row in fig510_by_case.items():
        if row.get("epoch_utc") != EXPECTED_FIG510_EPOCH:
            raise SmokeFailure(f"Fig. 5.10 case {case_id} DE421 epoch changed")
        if row.get("kernel_sha256") != EXPECTED_DE421_SHA256:
            raise SmokeFailure(f"Fig. 5.10 case {case_id} DE421 kernel hash changed")
        if row.get("source_model") != "DE421-initialized planar Earth-Moon BCR4BP":
            raise SmokeFailure(f"Fig. 5.10 case {case_id} source model is not BCR4BP")
        if abs(float(row["time_of_flight_days"]) - expected_tof[case_id]) > 1.0e-12:
            raise SmokeFailure(f"Fig. 5.10 case {case_id} time of flight changed")
        if row.get("segment_time_origin") != "absolute":
            raise SmokeFailure(f"Fig. 5.10 case {case_id} segment time is not absolute")
        if row.get("numerical_acceptance") != "true":
            raise SmokeFailure(f"Fig. 5.10 case {case_id} numerical gate is not accepted")
        if row.get("paper_equivalence") != "false":
            raise SmokeFailure(f"Fig. 5.10 case {case_id} paper boundary is not explicit")
        if row.get("paper_model_geometry_match") != "false":
            raise SmokeFailure(f"Fig. 5.10 case {case_id} model boundary is not explicit")
        if float(row["independent_endpoint_error_km"]) > 1.0e-3:
            raise SmokeFailure(f"Fig. 5.10 case {case_id} endpoint error exceeds 1e-3 km")
        if float(row["segment_max_position_defect_km"]) > 1.0e-3:
            raise SmokeFailure(f"Fig. 5.10 case {case_id} segment defect exceeds 1e-3 km")
        if float(row["reset_time_negative_control_position_defect_km"]) <= 1.0:
            raise SmokeFailure(f"Fig. 5.10 case {case_id} reset-time negative control is weak")
        if row.get("minimum_moon_radius_method") != (
            "strict_DOP853_dense_output_all_sampled_local_minima"
        ):
            raise SmokeFailure(f"Fig. 5.10 case {case_id} lunar-clearance method changed")
        minimum_time = float(row["minimum_moon_radius_time_nd"])
        if not 0.0 <= minimum_time <= float(row["time_of_flight_nd"]):
            raise SmokeFailure(f"Fig. 5.10 case {case_id} lunar-clearance time is invalid")
        if float(row["minimum_moon_radius_km"]) <= 1737.4:
            raise SmokeFailure(f"Fig. 5.10 case {case_id} intersects the Moon")
        impulse_sum = float(row["departure_delta_v_m_s"]) + float(
            row["arrival_delta_v_m_s"]
        )
        if abs(impulse_sum - float(row["total_delta_v_m_s"])) > 1.0e-9:
            raise SmokeFailure(f"Fig. 5.10 case {case_id} delta-v sum is inconsistent")

    fig510_phase = max(float(row["sun_phase_rad"]) for row in fig510_rows)
    if max(abs(float(row["sun_phase_rad"]) - fig510_phase) for row in fig510_rows) > 1.0e-14:
        raise SmokeFailure("Fig. 5.10 cases do not share the audited initial Sun phase")
    if abs(fig510_phase - 1.2408947569934152) > 1.0e-12:
        raise SmokeFailure(f"Fig. 5.10 initial Sun phase changed: {fig510_phase}")

    chapter5_rows = read_csv(
        project_root
        / "data"
        / "computed"
        / "chapter5_per_figure_source_layer_audit.csv",
        project_root,
    )
    fig510_source = next(
        (row for row in chapter5_rows if row.get("figure_id") == "5.10"),
        None,
    )
    if not fig510_source:
        raise SmokeFailure("Fig. 5.10 per-figure source-layer row is missing")
    if fig510_source.get("accepted_rows") != "2":
        raise SmokeFailure("Fig. 5.10 per-figure source layer is not 2/2 accepted")
    if "chapter5_fig510_bcr4bp_transfer_audit.csv" not in fig510_source.get(
        "primary_evidence", ""
    ):
        raise SmokeFailure("Fig. 5.10 dedicated BCR4BP audit is not canonical evidence")
    if "paper_equivalence=false" not in fig510_source.get("boundary", ""):
        raise SmokeFailure("Fig. 5.10 per-figure paper-equivalence boundary is missing")
    if "paper_equivalence_false" not in fig510_source.get(
        "original_replacement_status", ""
    ):
        raise SmokeFailure("Fig. 5.10 replacement status overclaims paper equivalence")
    for diagnostic_name in (
        "fig_5_10_bcr4bp_extension.png",
        "fig_5_10_bcr4bp_extension.pdf",
    ):
        diagnostic = project_root / "outputs" / "diagnostics" / diagnostic_name
        if not diagnostic.is_file() or diagnostic.stat().st_size == 0:
            raise SmokeFailure(f"missing or empty Fig. 5.10 diagnostic: {diagnostic_name}")

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
        "chapter4_fixed_time_rows": len(chapter4_fixed_time_rows),
        "chapter4_projection_rows": len(projection_rows),
        "chapter4_projection_alerts": projection_alerts,
        "fig510_bcr4bp_numerical": sum(
            row["numerical_acceptance"] == "true" for row in fig510_rows
        ),
        "fig510_bcr4bp_paper_equivalence": sum(
            row["paper_equivalence"] == "true" for row in fig510_rows
        ),
        "fig510_bcr4bp_endpoint_km": max(
            float(row["independent_endpoint_error_km"]) for row in fig510_rows
        ),
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
    print(
        f"chapter4_fixed_time={summary['chapter4_fixed_time_rows']}/16 "
        f"projection_diagnostic_rows={summary['chapter4_projection_rows']} "
        f"projection_alerts={summary['chapter4_projection_alerts']} "
        "paper_projection=not_run"
    )
    print(
        f"fig510_bcr4bp_numerical={summary['fig510_bcr4bp_numerical']}/2 "
        f"paper_equivalence={summary['fig510_bcr4bp_paper_equivalence']}/2 "
        f"endpoint_km={summary['fig510_bcr4bp_endpoint_km']:.6e}"
    )
    print(f"png={summary['png']} pdf={summary['pdf']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
