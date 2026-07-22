"""Generate and verify the read-only McCarthy 2018 reproduction baseline v1."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import io
import json
import os
from pathlib import Path
import re
import sys
from typing import Iterable, Mapping, Sequence

from _paths import PROJECT_ROOT, find_thesis_pdf
from qp_orbits.artifact_fingerprints import artifact_fingerprint


LOCK_PATH = PROJECT_ROOT / "data" / "computed" / "reproduction_baseline_v1_lock.json"
SUMMARY_PATH = (
    PROJECT_ROOT / "data" / "computed" / "reproduction_baseline_v1_summary.csv"
)
MANIFEST_PATH = (
    PROJECT_ROOT / "data" / "computed" / "reproduction_baseline_v1_manifest.csv"
)
DOCUMENT_PATH = PROJECT_ROOT / "docs" / "reproduction_baseline_v1.md"

EXPECTED_EVIDENCE_COUNTS = {
    "accepted": 3,
    "boundary": 34,
    "diagnostic": 5,
    "proxy": 12,
}

INPUT_SPECS = (
    (
        "data/reproduction_targets.csv",
        "54-figure target registry",
        "canonical",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/figure_validation_table.csv",
        "per-figure validation status",
        "canonical",
        "promotion_audit_only",
    ),
    (
        "data/computed/figure_evidence_gap_audit.csv",
        "conservative evidence classification",
        "canonical_derived",
        "generator_only",
    ),
    (
        "data/computed/mccarthy2018_staged_goal_gate_status.csv",
        "staged gate status",
        "canonical",
        "generator_only",
    ),
    (
        "docs/mccarthy2018_staged_goal_gate_status.md",
        "readable staged gate rendering",
        "generated_rendering",
        "generator_only",
    ),
    (
        "docs/figure_evidence_gap_audit.md",
        "readable evidence-gap rendering",
        "generated_rendering",
        "generator_only",
    ),
    (
        "docs/reproduction_execution_plan_2026-07-13.md",
        "current reproduction execution boundary",
        "current_plan",
        "validated_updates_only",
    ),
    (
        "docs/chapter4_per_figure_source_layer_audit.md",
        "Chapter 4 readable per-figure audit",
        "generated_rendering",
        "generator_only",
    ),
    (
        "docs/chapter4_projection_failure_root_cause.md",
        "bounded Chapter 4 diagnosis",
        "development_plan",
        "preserve_frozen_holdout",
    ),
    (
        "docs/chapter5_active_geometry_application_independent_rerun_audit.md",
        "Chapter 5 independent rerun record",
        "supporting_audit",
        "validated_updates_only",
    ),
    (
        "README.md",
        "project summary",
        "summary_only",
        "never_use_as_numeric_authority",
    ),
    (
        "data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv",
        "Route H accepted source validation",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter3_route_h_fixed_time_target_coverage_audit.csv",
        "Route H fixed-time target coverage",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter4_fig41_reported_precision_audit.csv",
        "Figure 4.1 reported-precision audit",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter4_fig42_digitized_comparison_audit.csv",
        "Figure 4.2 digitized overlap audit",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter4_fig43_fig44_global_manifold_audit.csv",
        "halo fixed-time manifold audit",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter4_fig43_fig44_global_manifold_audit.npz",
        "halo fixed-time manifold arrays",
        "supporting_arrays",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter4_fig45_fig48_vertical_manifold_audit.csv",
        "vertical fixed-time manifold audit",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter4_fig45_fig48_vertical_manifold_audit.npz",
        "vertical fixed-time manifold arrays",
        "supporting_arrays",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter4_fig43_fig46_camera_holdout_protocol.csv",
        "frozen Chapter 4 evaluation protocol",
        "protection_lock",
        "never_reselect_from_holdout",
    ),
    (
        "data/computed/chapter4_fig43_fig46_camera_static_metrics.csv",
        "frozen camera static metrics",
        "protection_lock",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter4_fig43_fig46_projection_fit_lock.json",
        "frozen projection fit",
        "protection_lock",
        "never_retune_from_holdout",
    ),
    (
        "data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv",
        "frozen projection holdout",
        "protection_lock",
        "immutable_failed_boundary",
    ),
    (
        "data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv",
        "post-hoc halo source diagnostic",
        "development_only",
        "cannot_promote_holdout",
    ),
    (
        "data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.npz",
        "post-hoc halo source arrays",
        "development_only",
        "cannot_promote_holdout",
    ),
    (
        "data/computed/chapter4_real_hyperbolic_scan.csv",
        "Route H real-hyperbolic boundary scan",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "src/qp_orbits/chapter4_reproduction_lock.py",
        "Chapter 4 lock implementation",
        "protection_lock",
        "tests_required_for_change",
    ),
    (
        "src/qp_orbits/artifact_fingerprints.py",
        "portable text and binary artifact fingerprinting",
        "infrastructure",
        "tests_required_for_change",
    ),
    (
        "scripts/register_chapter4_camera_holdout_protocol.py",
        "frozen camera protocol generator",
        "protection_generator",
        "tests_required_for_change",
    ),
    (
        "scripts/run_chapter4_fig43_fig46_projection_holdout_audit.py",
        "frozen projection holdout evaluator",
        "protection_generator",
        "tests_required_for_change",
    ),
    (
        "scripts/_paths.py",
        "approved workspace source locator",
        "infrastructure",
        "tests_required_for_change",
    ),
    (
        "data/computed/chapter5_sun_earth_l1_active_geometry_family_audit.csv",
        "accepted Sun-Earth active geometry",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter5_active_geometry_stable_manifold_tight_target_audit.csv",
        "stable-manifold application audit",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter5_active_geometry_leo_transfer_audit.csv",
        "LEO transfer application audit",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "data/computed/chapter5_fig510_bcr4bp_transfer_audit.csv",
        "Figure 5.10 BCR4BP extension audit",
        "supporting_numeric",
        "read_only_frozen_v1",
    ),
    (
        "environment.yml",
        "compatible conda environment",
        "environment",
        "validated_updates_only",
    ),
    (
        "environment-lock.yml",
        "tested direct-dependency version lock",
        "environment",
        "validated_updates_only",
    ),
    (
        "pyproject.toml",
        "installable Python dependency declaration",
        "environment",
        "validated_updates_only",
    ),
    (
        "scripts/run_reproduction_baseline_freeze.py",
        "baseline generator and verifier",
        "generator",
        "tests_required_for_change",
    ),
    (
        "data/computed/reproduction_baseline_v1_lock.json",
        "baseline provenance lock",
        "baseline_lock",
        "immutable_without_v2",
    ),
)


class BaselineError(RuntimeError):
    """Raised when a frozen baseline invariant is not satisfied."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BaselineError(message)


def read_csv(relative_path: str) -> list[dict[str, str]]:
    path = PROJECT_ROOT / relative_path
    require(path.is_file(), f"missing required CSV: {relative_path}")
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_lock() -> dict[str, str]:
    require(LOCK_PATH.is_file(), f"missing baseline lock: {LOCK_PATH}")
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    require(lock.get("schema_version") == "reproduction_baseline_v1_lock", "invalid lock schema")
    require(lock.get("baseline_version") == "v1", "baseline lock must remain v1")
    require(
        re.fullmatch(r"[0-9a-f]{40}", str(lock.get("source_git_commit", ""))) is not None,
        "source_git_commit must be a full lowercase Git hash",
    )
    return {str(key): str(value) for key, value in lock.items()}


def relative_display(path: Path) -> str:
    return Path(os.path.relpath(path, PROJECT_ROOT)).as_posix()


def fingerprint_fields(path: Path) -> dict[str, str]:
    fingerprint = artifact_fingerprint(path)
    return {
        "hash_mode": fingerprint.hash_mode,
        "bytes": str(fingerprint.bytes),
        "sha256": fingerprint.sha256,
    }


def one(rows: Sequence[Mapping[str, str]], label: str) -> Mapping[str, str]:
    require(len(rows) == 1, f"{label} must contain exactly one row, found {len(rows)}")
    return rows[0]


def figure_sort_key(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def csv_render(fieldnames: Sequence[str], rows: Iterable[Mapping[str, object]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def build_outputs() -> tuple[str, str, str]:
    lock = read_lock()
    targets = read_csv("data/reproduction_targets.csv")
    validation = read_csv("data/computed/figure_validation_table.csv")
    gaps = read_csv("data/computed/figure_evidence_gap_audit.csv")
    staged = read_csv("data/computed/mccarthy2018_staged_goal_gate_status.csv")

    require(len(targets) == 54, f"target registry must have 54 rows, found {len(targets)}")
    require(len(validation) == 54, f"validation table must have 54 rows, found {len(validation)}")
    require(len(gaps) == 54, f"evidence audit must have 54 rows, found {len(gaps)}")

    target_ids = [row["figure_id"] for row in targets]
    validation_ids = [row["figure_id"] for row in validation]
    gap_ids = [row["figure_id"] for row in gaps]
    require(len(set(target_ids)) == 54, "target registry has duplicate figure IDs")
    require(set(target_ids) == set(validation_ids) == set(gap_ids), "54-figure ID sets differ")

    tier_counts = Counter(row["acceptance_tier"] for row in targets)
    type_counts = Counter(row["figure_type"] for row in targets)
    level_counts = Counter(row["current_repro_level"] for row in targets)
    evidence_counts = Counter(row["evidence_status"] for row in gaps)
    require(tier_counts == Counter({"V2": 41, "V0": 13}), f"unexpected tier counts: {tier_counts}")
    require(type_counts["schematic"] == 13, f"expected 13 schematics, found {type_counts['schematic']}")
    require(
        type_counts["numeric"] + type_counts["application"] == 41,
        "numeric/application target count must remain 41",
    )
    require(
        level_counts["numerical reproduction"] == 11,
        "current exact numerical-reproduction count must remain 11 in baseline v1",
    )
    require(
        evidence_counts == Counter(EXPECTED_EVIDENCE_COUNTS),
        f"unexpected evidence counts: {evidence_counts}",
    )

    missing_gap_rows = [
        row
        for row in gaps
        if row["script_exists"] != "true"
        or row["png_exists"] != "true"
        or row["pdf_exists"] != "true"
        or row["missing_artifacts"].strip()
    ]
    require(not missing_gap_rows, f"{len(missing_gap_rows)} evidence rows have missing artifacts")

    png_paths = []
    pdf_paths = []
    for figure_id in target_ids:
        stem = f"fig_{figure_id.replace('.', '_')}"
        png = PROJECT_ROOT / "outputs" / "figures_png" / f"{stem}.png"
        pdf = PROJECT_ROOT / "outputs" / "figures_pdf" / f"{stem}.pdf"
        require(png.is_file() and png.stat().st_size > 0, f"missing or empty PNG: {png}")
        require(pdf.is_file() and pdf.stat().st_size > 0, f"missing or empty PDF: {pdf}")
        png_paths.append(png)
        pdf_paths.append(pdf)

    gate_by_id = {row["gate_id"]: row for row in staged}
    staged_goal = gate_by_id["STAGED-GOAL-STATUS"]
    require(
        staged_goal["status"] == "chapter3_passed_chapter4_ready",
        f"unexpected staged goal: {staged_goal['status']}",
    )
    require(gate_by_id["C3-ROUTE-H"]["status"] == "pass", "Route H source gate must pass")
    require(
        gate_by_id["C3-ROUTE-H-COLD-START"]["status"] == "fail",
        "monolithic Route H cold-start failure must remain visible",
    )
    require(
        gate_by_id["C3-ROUTE-H-HYBRID-COLD-START"]["status"] == "pass",
        "hybrid Route H cold-start chain must pass",
    )
    require(
        gate_by_id["C4-ROUTE-H-DG-MANIFOLD"]["status"] == "not_run_or_fail",
        "Route H DG/manifold boundary must not be promoted",
    )

    route_h = read_csv("data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv")
    route_h_coverage = read_csv(
        "data/computed/chapter3_route_h_fixed_time_target_coverage_audit.csv"
    )
    require(len(route_h) == 30, f"Route H accepted validation must have 30 rows, found {len(route_h)}")
    route_h_max_z = max(route_h, key=lambda row: float(row["max_abs_z_km"]))["max_abs_z_km"]
    paper_precision_count = sum(
        row["paper_reported_precision_status"] == "pass" for row in route_h_coverage
    )
    strict_fixed_time_count = sum(
        row["strict_fixed_time_status"] == "pass" for row in route_h_coverage
    )
    require(paper_precision_count == 4, "Route H paper-precision target count must remain 4")
    require(strict_fixed_time_count == 3, "Route H strict fixed-time target count must remain 3")

    fig41_rows = read_csv("data/computed/chapter4_fig41_reported_precision_audit.csv")
    fig41 = one([row for row in fig41_rows if row["acceptance"] == "pass"], "Fig. 4.1 pass row")

    fig42 = one(
        read_csv("data/computed/chapter4_fig42_digitized_comparison_audit.csv"),
        "Fig. 4.2 audit",
    )
    require(fig42["pointwise_overlap_acceptance"] == "true", "Fig. 4.2 overlap must pass")
    require(fig42["full_curve_coverage"] == "false", "Fig. 4.2 tail boundary must remain")

    halo_fixed = read_csv("data/computed/chapter4_fig43_fig44_global_manifold_audit.csv")
    vertical_fixed = read_csv("data/computed/chapter4_fig45_fig48_vertical_manifold_audit.csv")
    fixed_rows = halo_fixed + vertical_fixed
    require(len(fixed_rows) == 16, f"fixed-time audits must have 16 rows, found {len(fixed_rows)}")
    require(
        all(
            row["numerical_acceptance"] == "pass"
            and row["configuration_reach_acceptance"] == "pass"
            and row["paper_projection_acceptance"] == "fail"
            and row["paper_3d_equivalence"] == "false"
            for row in fixed_rows
        ),
        "fixed-time rows must preserve numerical pass and paper-projection failure",
    )

    static_camera = read_csv("data/computed/chapter4_fig43_fig46_camera_static_metrics.csv")
    require(
        len(static_camera) == 16
        and all(row["static_camera_gate"] == "pass" for row in static_camera),
        "static camera gate must remain 16/16",
    )

    holdout = read_csv("data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv")
    require(len(holdout) == 4, f"projection holdout must have 4 rows, found {len(holdout)}")
    require(
        all(
            row["holdout_gate"] == "fail"
            and row["paper_projection_acceptance"] == "fail"
            and row["paper_3d_equivalence"] == "false"
            for row in holdout
        ),
        "frozen Chapter 4 holdout failure must remain 0/4 with paper_3d=false",
    )

    halo_posthoc = read_csv(
        "data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv"
    )
    halo_candidate_rows = [
        row for row in halo_posthoc if row["source_variant"] == "thesis_12p40_n21"
    ]
    require(len(halo_candidate_rows) == 2, "post-hoc N21 candidate must have two branch rows")
    require(
        all(
            row["posthoc_projection_gate"] == "fail"
            and row["paper_projection_acceptance"] == "fail"
            and row["paper_3d_equivalence"] == "false"
            for row in halo_candidate_rows
        ),
        "post-hoc N21 candidate must not be promoted",
    )
    halo_candidate = halo_candidate_rows[0]

    real_scan = read_csv("data/computed/chapter4_real_hyperbolic_scan.csv")
    real_pass = [row for row in real_scan if row["real_hyperbolic_status"] == "pass"]
    require(
        len(real_scan) == 31 and len(real_pass) == 1 and real_pass[0]["member_index"] == "68",
        "Route H real-hyperbolic baseline must remain member 68 only (1/31)",
    )

    active_geometry = one(
        read_csv("data/computed/chapter5_sun_earth_l1_active_geometry_family_audit.csv"),
        "active geometry audit",
    )
    stable_target = one(
        read_csv(
            "data/computed/chapter5_active_geometry_stable_manifold_tight_target_audit.csv"
        ),
        "stable manifold target audit",
    )
    leo_target = one(
        read_csv("data/computed/chapter5_active_geometry_leo_transfer_audit.csv"),
        "LEO transfer audit",
    )
    require(active_geometry["target_pair_accepted"] == "True", "active geometry target must pass")
    require(stable_target["acceptance"] == "true", "stable manifold target must pass")
    require(leo_target["acceptance"] == "true", "LEO transfer target must pass")

    bcr4bp = read_csv("data/computed/chapter5_fig510_bcr4bp_transfer_audit.csv")
    bcr_numerical = sum(row["numerical_acceptance"] == "true" for row in bcr4bp)
    bcr_paper = sum(row["paper_equivalence"] == "true" for row in bcr4bp)
    require(len(bcr4bp) == 2 and bcr_numerical == 2, "Fig. 5.10 BCR4BP numerical gate must be 2/2")
    require(bcr_paper == 0, "Fig. 5.10 paper equivalence must remain 0/2")

    category_figures = {
        status: sorted(
            (row["figure_id"] for row in gaps if row["evidence_status"] == status),
            key=figure_sort_key,
        )
        for status in EXPECTED_EVIDENCE_COUNTS
    }
    chapter_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in gaps:
        chapter_counts[row["figure_id"].split(".", 1)[0]][row["evidence_status"]] += 1

    summary_rows: list[dict[str, str]] = []

    def add(metric_id: str, value: object, evidence: str, interpretation: str) -> None:
        summary_rows.append(
            {
                "metric_id": metric_id,
                "value": str(value),
                "evidence": evidence,
                "interpretation": interpretation,
            }
        )

    add("baseline_version", lock["baseline_version"], relative_display(LOCK_PATH), "frozen baseline version")
    add("freeze_date", lock["freeze_date"], relative_display(LOCK_PATH), "baseline lock date")
    add(
        "source_git_commit",
        lock["source_git_commit"],
        relative_display(LOCK_PATH),
        "pre-baseline source snapshot",
    )
    add("target_rows", len(targets), "data/reproduction_targets.csv", "engineering target coverage")
    add("v0_targets", tier_counts["V0"], "data/reproduction_targets.csv", "schematic tier")
    add("v2_targets", tier_counts["V2"], "data/reproduction_targets.csv", "numeric/application tier")
    add("schematic_targets", type_counts["schematic"], "data/reproduction_targets.csv", "schematic targets")
    add(
        "numeric_application_targets",
        type_counts["numeric"] + type_counts["application"],
        "data/reproduction_targets.csv",
        "numeric plus application targets",
    )
    add(
        "numerical_reproduction_rows",
        level_counts["numerical reproduction"],
        "data/reproduction_targets.csv",
        "rows carrying exact numerical reproduction label",
    )
    for status in ("accepted", "boundary", "diagnostic", "proxy"):
        add(
            f"evidence_{status}",
            evidence_counts[status],
            "data/computed/figure_evidence_gap_audit.csv",
            "conservative evidence-gap classification",
        )
    add("missing_artifact_rows", len(missing_gap_rows), "data/computed/figure_evidence_gap_audit.csv", "missing script/data/render rows")
    add("png_count", len(png_paths), "outputs/figures_png", "nonempty engineering PNG outputs")
    add("pdf_count", len(pdf_paths), "outputs/figures_pdf", "nonempty engineering PDF outputs")
    for chapter in ("2", "3", "4", "5"):
        for status in ("accepted", "boundary", "diagnostic", "proxy"):
            add(
                f"chapter{chapter}_{status}",
                chapter_counts[chapter][status],
                "data/computed/figure_evidence_gap_audit.csv",
                f"Chapter {chapter} {status} count",
            )
    add("route_h_validation_rows", len(route_h), "data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv", "accepted Route H rows")
    add("route_h_max_abs_z_km", route_h_max_z, "data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv", "largest accepted Route H vertical extent")
    add("route_h_paper_precision_targets", paper_precision_count, "data/computed/chapter3_route_h_fixed_time_target_coverage_audit.csv", "paper-reported Jacobi anchors")
    add("route_h_strict_fixed_time_targets", strict_fixed_time_count, "data/computed/chapter3_route_h_fixed_time_target_coverage_audit.csv", "strict fixed-time anchors")
    add("chapter4_fig41_stability_index", fig41["stability_index"], "data/computed/chapter4_fig41_reported_precision_audit.csv", "accepted reported-precision nu row")
    add("chapter4_fig42_overlap_rows", fig42["overlap_comparison_rows"], "data/computed/chapter4_fig42_digitized_comparison_audit.csv", "common-interval points")
    add("chapter4_fig42_coverage_fraction", fig42["reference_time_coverage_fraction"], "data/computed/chapter4_fig42_digitized_comparison_audit.csv", "digitized reference interval coverage")
    add("chapter4_fig42_tail_gap_days", fig42["computed_tail_time_gap_days"], "data/computed/chapter4_fig42_digitized_comparison_audit.csv", "uncovered fold-tail duration")
    add("chapter4_fixed_time_numerical_pass", len(fixed_rows), "data/computed/chapter4_fig43_fig44_global_manifold_audit.csv;data/computed/chapter4_fig45_fig48_vertical_manifold_audit.csv", "state-space and local-STM rows")
    add("chapter4_static_camera_pass", len(static_camera), "data/computed/chapter4_fig43_fig46_camera_static_metrics.csv", "static camera rows")
    add("chapter4_frozen_holdout_pass", 0, "data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv", "frozen paper projection passes")
    add("chapter4_frozen_holdout_total", len(holdout), "data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv", "frozen paper projection rows")
    add("chapter4_halo_candidate_period_days", halo_candidate["source_period_days"], "data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv", "post-hoc N21 candidate only")
    add("chapter4_halo_candidate_samples", halo_candidate["curve_samples"], "data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv", "post-hoc candidate spectral samples")
    add("chapter4_halo_candidate_ay_km", halo_candidate["source_ay_km"], "data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv", "post-hoc candidate scale")
    add("chapter4_halo_candidate_az_km", halo_candidate["source_az_km"], "data/computed/chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv", "post-hoc candidate scale")
    add("route_h_real_hyperbolic_pass", len(real_pass), "data/computed/chapter4_real_hyperbolic_scan.csv", "strict nearly-real hyperbolic rows")
    add("route_h_real_hyperbolic_total", len(real_scan), "data/computed/chapter4_real_hyperbolic_scan.csv", "scanned Route H rows")
    add("route_h_real_positive_member", real_pass[0]["member_index"], "data/computed/chapter4_real_hyperbolic_scan.csv", "positive control candidate")
    add("chapter5_active_member", active_geometry["accepted_members"], "data/computed/chapter5_sun_earth_l1_active_geometry_family_audit.csv", "accepted active-geometry checkpoint")
    add("chapter5_active_max_y_km", active_geometry["max_abs_y_km"], "data/computed/chapter5_sun_earth_l1_active_geometry_family_audit.csv", "full-torus extent")
    add("chapter5_active_max_z_km", active_geometry["max_abs_z_km"], "data/computed/chapter5_sun_earth_l1_active_geometry_family_audit.csv", "full-torus extent")
    add("chapter5_stable_periapsis_km", stable_target["best_7033_radius_km"], "data/computed/chapter5_active_geometry_stable_manifold_tight_target_audit.csv", "accepted stable-manifold application")
    add("chapter5_leo_periapsis_km", leo_target["periapsis_radius_km"], "data/computed/chapter5_active_geometry_leo_transfer_audit.csv", "accepted LEO transfer application")
    add("chapter5_bcr4bp_numerical_pass", bcr_numerical, "data/computed/chapter5_fig510_bcr4bp_transfer_audit.csv", "numerical extension rows")
    add("chapter5_bcr4bp_paper_equivalence_pass", bcr_paper, "data/computed/chapter5_fig510_bcr4bp_transfer_audit.csv", "paper-equivalent rows")
    add("staged_goal_status", staged_goal["status"], "data/computed/mccarthy2018_staged_goal_gate_status.csv", "current reproduction staged gate")

    summary_text = csv_render(
        ("metric_id", "value", "evidence", "interpretation"),
        summary_rows,
    )

    goal_path = (PROJECT_ROOT / lock["goal_path"]).resolve()
    require(goal_path.is_file(), f"missing goal file: {goal_path}")
    thesis_path = find_thesis_pdf().resolve()
    dynamic_specs = (
        (goal_path, "goal invariant bundle", "governing_goal", "immutable_without_user_change"),
        (thesis_path, "McCarthy 2018 source PDF", "primary_source", "read_only"),
    )

    manifest_rows: list[dict[str, str]] = []
    for relative_path, role, authority, policy in INPUT_SPECS:
        path = PROJECT_ROOT / relative_path
        require(path.is_file(), f"missing baseline input: {relative_path}")
        manifest_rows.append(
            {
                "path": relative_display(path),
                "role": role,
                "authority": authority,
                "freeze_policy": policy,
                **fingerprint_fields(path),
            }
        )
    for path, role, authority, policy in dynamic_specs:
        manifest_rows.append(
            {
                "path": relative_display(path),
                "role": role,
                "authority": authority,
                "freeze_policy": policy,
                **fingerprint_fields(path),
            }
        )
    manifest_text = csv_render(
        (
            "path",
            "role",
            "authority",
            "freeze_policy",
            "hash_mode",
            "bytes",
            "sha256",
        ),
        manifest_rows,
    )

    metric = {row["metric_id"]: row["value"] for row in summary_rows}
    category_lines = [
        f"- **{status} ({len(category_figures[status])})**: "
        + ", ".join(f"Fig. {figure_id}" for figure_id in category_figures[status])
        for status in ("accepted", "boundary", "diagnostic", "proxy")
    ]
    chapter_table = [
        "| Chapter | accepted | boundary | diagnostic | proxy |",
        "|---|---:|---:|---:|---:|",
    ]
    for chapter in ("2", "3", "4", "5"):
        chapter_table.append(
            "| "
            + chapter
            + " | "
            + " | ".join(
                f"{metric[f'chapter{chapter}_{status}']} [S:chapter{chapter}_{status}]"
                for status in ("accepted", "boundary", "diagnostic", "proxy")
            )
            + " |"
        )

    document_lines = [
        "# McCarthy 2018 复现基线 v1",
        "",
        "> 由 scripts/run_reproduction_baseline_freeze.py 从当前 CSV/gate 和冻结证据生成。",
        "> 文中的 S:metric_id 对应 data/computed/reproduction_baseline_v1_summary.csv；",
        "> 输入文件哈希见 data/computed/reproduction_baseline_v1_manifest.csv。",
        "",
        "## 冻结声明",
        "",
        "**本基线用于支持后续原创方法研究，不代表 McCarthy 2018 全文严格数值等价复现。**",
        "",
        f"- 基线版本：{metric['baseline_version']} [S:baseline_version]",
        f"- 冻结日期：{metric['freeze_date']} [S:freeze_date]",
        f"- 源快照 Git commit：{metric['source_git_commit']} [S:source_git_commit]",
        f"- 当前 staged gate：{metric['staged_goal_status']} [S:staged_goal_status]",
        "",
        "复现层从此作为可重运行、可审计的工程基线保留。后续研究代码可以复用 shared numerical library 和已登记 benchmark，但不得把研究结果自动回写为原论文图级 accepted，也不得改变冻结的 Chapter 4 v1 holdout。",
        "",
        "## 54 图工程覆盖与保守分类",
        "",
        f"- 目标注册表：{metric['target_rows']}/54 [S:target_rows]。",
        f"- V0：{metric['v0_targets']} [S:v0_targets]；V2：{metric['v2_targets']} [S:v2_targets]。",
        f"- 示意目标：{metric['schematic_targets']} [S:schematic_targets]；数值/应用目标：{metric['numeric_application_targets']} [S:numeric_application_targets]。",
        f"- 当前 exact label 为 numerical reproduction 的行：{metric['numerical_reproduction_rows']} [S:numerical_reproduction_rows]。",
        f"- 非空 PNG/PDF：{metric['png_count']}/{metric['pdf_count']} [S:png_count; S:pdf_count]；缺失证据路径行：{metric['missing_artifact_rows']} [S:missing_artifact_rows]。",
        "",
        "accepted/boundary/diagnostic/proxy 是 evidence-gap 保守分类，不等同于 V0/V2，也不等同于论文整体等价。",
        "",
        *category_lines,
        "",
        "### 分章分类计数",
        "",
        *chapter_table,
        "",
        "## 分章最强结果与边界",
        "",
        "### Chapter 2",
        "",
        "Chapter 2 已保存 CR3BP 基础、周期轨道、流形以及 L2 halo/NRHO 分支等工程化数值输出。Fig. 2.15 位于 accepted 分类；其余数值图仍按逐图 CSV 中的 physical-consistency 或 boundary 文案解释，V0 示意图不再作为主线升级任务。",
        "",
        "### Chapter 3",
        "",
        f"- Route H accepted validation 有 {metric['route_h_validation_rows']} 行 [S:route_h_validation_rows]，最大 |z| 为 {float(metric['route_h_max_abs_z_km']):.6f} km [S:route_h_max_abs_z_km]。",
        f"- 四个论文报告精度 Jacobi 锚点为 {metric['route_h_paper_precision_targets']}/4 [S:route_h_paper_precision_targets]；严格 fixed-time 行为 {metric['route_h_strict_fixed_time_targets']}/4 [S:route_h_strict_fixed_time_targets]。完整 monolithic cold-start 的失败仍保留，hybrid chain 为通过。",
        "- Fig. 3.5、3.6、3.12–3.15 是当前 accepted 组；Fig. 3.10 的 q=8 仍是 single-shoot closure boundary；Fig. 3.17 的参考趋势仍是低权威 context。",
        "",
        "### Chapter 4",
        "",
        f"- Fig. 4.1 的 reported-precision 通过行为 nu={float(metric['chapter4_fig41_stability_index']):.9f} [S:chapter4_fig41_stability_index]，但有限振幅 torus geometry 未证明。",
        f"- Fig. 4.2 在共同区间比较 {metric['chapter4_fig42_overlap_rows']} 点 [S:chapter4_fig42_overlap_rows]，覆盖率 {100.0 * float(metric['chapter4_fig42_coverage_fraction']):.6f}% [S:chapter4_fig42_coverage_fraction]；fold 后仍缺 {float(metric['chapter4_fig42_tail_gap_days']):.6f} day [S:chapter4_fig42_tail_gap_days]。",
        f"- Fig. 4.3–4.6 fixed-time state-space/local STM 与 configuration-reach 共 {metric['chapter4_fixed_time_numerical_pass']}/{metric['chapter4_fixed_time_numerical_pass']} 行通过 [S:chapter4_fixed_time_numerical_pass]；静态相机为 {metric['chapter4_static_camera_pass']}/{metric['chapter4_static_camera_pass']} [S:chapter4_static_camera_pass]。",
        f"- 冻结 panel-(d) holdout 为 {metric['chapter4_frozen_holdout_pass']}/{metric['chapter4_frozen_holdout_total']} [S:chapter4_frozen_holdout_pass; S:chapter4_frozen_holdout_total]，paper_projection=fail 且 paper_3d=false；该结论不可被 post-hoc 结果覆盖。",
        f"- 12.40-day halo 候选当前仅是 post-hoc N={metric['chapter4_halo_candidate_samples']} 诊断 [S:chapter4_halo_candidate_samples]，T0={float(metric['chapter4_halo_candidate_period_days']):.12f} day [S:chapter4_halo_candidate_period_days]，Ay={float(metric['chapter4_halo_candidate_ay_km']):.3f} km、Az={float(metric['chapter4_halo_candidate_az_km']):.3f} km [S:chapter4_halo_candidate_ay_km; S:chapter4_halo_candidate_az_km]；阶段 B 的 N33/N45 重建尚未完成。",
        f"- Route H 近实双曲严格扫描仍仅 {metric['route_h_real_hyperbolic_pass']}/{metric['route_h_real_hyperbolic_total']} [S:route_h_real_hyperbolic_pass; S:route_h_real_hyperbolic_total]，阳性成员为 {metric['route_h_real_positive_member']} [S:route_h_real_positive_member]。复特征对不得伪装为一维实流形方向。",
        "",
        "### Chapter 5",
        "",
        f"- Sun–Earth active-geometry checkpoint 为 member {metric['chapter5_active_member']} [S:chapter5_active_member]，全环面 max|y|={float(metric['chapter5_active_max_y_km']):.3f} km、max|z|={float(metric['chapter5_active_max_z_km']):.3f} km [S:chapter5_active_max_y_km; S:chapter5_active_max_z_km]。",
        f"- 稳定流形近地点为 {float(metric['chapter5_stable_periapsis_km']):.6f} km [S:chapter5_stable_periapsis_km]；LEO 转移近地点为 {float(metric['chapter5_leo_periapsis_km']):.6f} km [S:chapter5_leo_periapsis_km]。这些是 CR3BP 应用门结果，不是完整 ephemeris/论文面板等价。",
        f"- Fig. 5.10 BCR4BP 数值扩展为 {metric['chapter5_bcr4bp_numerical_pass']}/2 [S:chapter5_bcr4bp_numerical_pass]，论文等价为 {metric['chapter5_bcr4bp_paper_equivalence_pass']}/2 [S:chapter5_bcr4bp_paper_equivalence_pass]。",
        "",
        "## 明确失败、不可证明和冻结边界",
        "",
        "- 整篇 McCarthy 2018 不是完整论文级数值等价复现。",
        "- Chapter 4 v1 holdout 维持 paper_projection=fail、paper_3d=false；禁止按 panel (d) 回调 camera、epsilon、crop、renderer 或 threshold。",
        "- Route H 大多数成员呈明显复方向；当前只能把 member 68 当近实双曲阳性控制，不能把 derived Route H 图称为原 Fig. 4.3–4.8 replacement。",
        "- Fig. 4.2 fold-tail、Fig. 4.7–4.8 legacy projection semantics、Chapter 5 原始高保真状态/优化/逐点论文几何仍是 evidence boundary。",
        "- 原作者未公开的 3D 状态、扰动设置或原始数据不能靠视觉相似补造。",
        "",
        "## 进入原创研究时可引用的 benchmark 候选",
        "",
        "- Earth–Moon L1 halo：12.397983-day N21 是阶段 B 固定起点；N33/N45 未完成前不得注册为收敛 benchmark。",
        "- Earth–Moon L1 quasi-vertical：12.6647965-day N33 是固定起点；N45/N57 未完成前不得宣称 N 收敛。",
        "- Route H quasi-DRO：member 68 是近实双曲阳性控制；member 17、32 是明显复方向负控制；最大振幅成员保留为复杂谱案例。",
        "- Sun–Earth L1：accepted active-geometry member 468 可在阶段 C 注册，但必须引用保存 checkpoint，不重新盲目扩振幅。",
        "",
        "## 从复现主线冻结的任务",
        "",
        "- 不再以消灭全部 boundary 或 54 图逐像素等价作为当前主目标。",
        "- 不继续无限扩展 Route B，不强行让 Chapter 4 holdout 通过，不追索不存在的原始作者数据。",
        "- V0 示意图和已受控的低影响 boundary 仅保留维护与可重跑责任。",
        "- 只有直接服务 invariant-bundle 方法验证的 Chapter 4 halo/vertical N 收敛与冻结负对照进入阶段 B。",
        "",
        "## 权威读取顺序",
        "",
        "1. data/computed/mccarthy2018_staged_goal_gate_status.csv 与 figure_validation_table.csv。",
        "2. data/computed/figure_evidence_gap_audit.csv 及 Chapter 4/5 per-figure audit CSV/NPZ。",
        "3. 本基线的 summary/manifest。",
        "4. 生成的 Markdown rendering。",
        "5. README、旧阶段报告和旧 roadmap 仅作导航或历史背景，禁止反向覆盖 CSV gate。",
        "",
        "阶段 A 的结构与切换规则见 docs/repository_architecture.md 和 docs/research_transition_plan.md。阶段 B 未完成前，research/invariant_bundles 不得承载可发表结论。",
        "",
    ]
    document_text = "\n".join(document_lines)
    return summary_text, manifest_text, document_text


def check_text(path: Path, expected: str) -> str | None:
    if not path.is_file():
        return f"missing generated baseline artifact: {relative_display(path)}"
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        return f"stale generated baseline artifact: {relative_display(path)}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify the McCarthy 2018 reproduction baseline v1."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify frozen inputs and generated outputs without writing.",
    )
    args = parser.parse_args()

    try:
        summary_text, manifest_text, document_text = build_outputs()
    except (BaselineError, KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"BASELINE FREEZE FAIL: {exc}", file=sys.stderr)
        return 1

    outputs = (
        (SUMMARY_PATH, summary_text),
        (MANIFEST_PATH, manifest_text),
        (DOCUMENT_PATH, document_text),
    )
    if args.check:
        failures = [
            failure
            for path, expected in outputs
            if (failure := check_text(path, expected)) is not None
        ]
        if failures:
            for failure in failures:
                print(failure, file=sys.stderr)
            return 1
        print(
            "BASELINE FREEZE CHECK PASS "
            "targets=54 v0=13 v2=41 accepted=3 boundary=34 "
            "diagnostic=5 proxy=12 holdout=0/4"
        )
        return 0

    for path, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    print(
        "BASELINE FREEZE WRITE PASS "
        f"summary={relative_display(SUMMARY_PATH)} "
        f"manifest={relative_display(MANIFEST_PATH)} "
        f"document={relative_display(DOCUMENT_PATH)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
