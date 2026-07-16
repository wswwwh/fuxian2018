"""Generate the bounded Stage B conclusion from audited Chapter 4 artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"

HALO_CSV = DATA / "research_halo_12p40_resolution_audit.csv"
VERTICAL_CSV = DATA / "research_vertical_12p66_resolution_audit.csv"
CONTROL_CSV = DATA / "chapter4_projection_semantics_negative_controls.csv"
POSTHOC_CSV = DATA / "chapter4_fig43_fig44_halo_12p40_posthoc_diagnostic.csv"
HOLDOUT_CSV = DATA / "chapter4_fig43_fig46_projection_holdout_audit.csv"
OUTPUT_CSV = DATA / "chapter4_invariant_bundle_stage_b_conclusion.csv"
OUTPUT_DOC = DOCS / "chapter4_invariant_bundle_stage_b_conclusion.md"

SCHEMA_VERSION = "chapter4_invariant_bundle_stage_b_conclusion_v1"

CSV_COLUMNS = (
    "schema_version",
    "stage_b_status",
    "stage_c_transition_status",
    "halo_resolutions",
    "halo_source_gate_pass_rows",
    "halo_cross_resolution_pass_rows",
    "halo_posthoc_projection_pass_rows",
    "halo_highest_resolution_status",
    "halo_max_adjacent_principal_angle_deg",
    "halo_max_adjacent_sheet_hd95_normalized",
    "halo_ring_dispersion_fail_resolutions",
    "vertical_resolutions",
    "vertical_source_gate_pass_rows",
    "vertical_cross_resolution_pass_rows",
    "vertical_posthoc_projection_pass_rows",
    "vertical_highest_resolution_status",
    "vertical_max_adjacent_principal_angle_deg",
    "vertical_max_adjacent_sheet_hd95_normalized",
    "vertical_multiplier_fail_resolutions",
    "vertical_ring_dispersion_fail_resolutions",
    "halo_n21_improves_n9_f1_rows",
    "halo_n21_posthoc_projection_pass_rows",
    "panel_time_loss_improvement_rows",
    "mask_extraction_material_rows",
    "quad_rasterizer_material_rows",
    "surface_renderer_material_rows",
    "explicit_stm_transport_material_rows",
    "source_member_judgment",
    "spectral_resolution_judgment",
    "pointwise_eigenvector_judgment",
    "renderer_projection_judgment",
    "original_state_boundary_judgment",
    "primary_stage_b_judgment",
    "frozen_holdout_status",
    "paper_projection_acceptance",
    "paper_3d_equivalence",
    "evidence_artifacts",
    "evidence_sha256",
    "generator_sha256",
)


def _display(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise RuntimeError(f"missing Stage B evidence: {_display(path)}")
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _csv_text(rows: Sequence[Mapping[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.15g}"
    return str(value)


def build() -> tuple[list[dict[str, str]], str]:
    halo = _read_csv(HALO_CSV)
    vertical = _read_csv(VERTICAL_CSV)
    controls = _read_csv(CONTROL_CSV)
    posthoc = _read_csv(POSTHOC_CSV)
    holdout = _read_csv(HOLDOUT_CSV)

    if [int(row["spectral_samples"]) for row in halo] != [21, 33, 45]:
        raise RuntimeError("halo Stage B resolutions drifted")
    if [int(row["spectral_samples"]) for row in vertical] != [33, 45, 57]:
        raise RuntimeError("vertical Stage B resolutions drifted")
    if len(controls) != 24:
        raise RuntimeError("negative-control row count drifted")
    if len(holdout) != 4 or any(
        row["holdout_gate"] != "fail"
        or row["paper_projection_acceptance"] != "fail"
        or row["paper_3d_equivalence"] != "false"
        for row in holdout
    ):
        raise RuntimeError("frozen holdout boundary drifted")

    halo_nonbaseline = halo[1:]
    vertical_nonbaseline = vertical[1:]
    halo_source_pass = sum(row["source_gate"] == "pass" for row in halo)
    vertical_source_pass = sum(row["source_gate"] == "pass" for row in vertical)
    halo_convergence_pass = sum(
        row["cross_resolution_gate"] == "pass" for row in halo_nonbaseline
    )
    vertical_convergence_pass = sum(
        row["cross_resolution_gate"] == "pass" for row in vertical_nonbaseline
    )
    halo_projection_pass = sum(
        int(row["posthoc_projection_pass_count"]) for row in halo
    )
    vertical_projection_pass = sum(
        int(row["posthoc_projection_pass_count"]) for row in vertical
    )
    halo_ring_fail = [
        row["spectral_samples"]
        for row in halo
        if float(row["unstable_ring_relative_dispersion"]) > 0.06
    ]
    vertical_ring_fail = [
        row["spectral_samples"]
        for row in vertical
        if float(row["unstable_ring_relative_dispersion"]) > 0.06
    ]
    vertical_multiplier_fail = [
        row["spectral_samples"]
        for row in vertical_nonbaseline
        if float(row["multiplier_relative_change_to_previous"]) > 1.0e-3
    ]

    n9 = {
        row["figure_id"]: row
        for row in posthoc
        if row["source_variant"] == "current_n9"
    }
    n21 = {
        row["figure_id"]: row
        for row in posthoc
        if row["source_variant"] == "thesis_12p40_n21"
    }
    if set(n9) != {"4.3", "4.4"} or set(n21) != {"4.3", "4.4"}:
        raise RuntimeError("halo post-hoc source rows drifted")
    n21_improvements = sum(
        float(n21[figure]["f1_at_0p01_diagonal"])
        > float(n9[figure]["f1_at_0p01_diagonal"])
        for figure in n9
    )
    n21_projection_pass = sum(
        row["posthoc_projection_gate"] == "pass" for row in n21.values()
    )

    grouped = {
        control: [row for row in controls if row["control_id"] == control]
        for control in {
            "panel_time_mapping",
            "mask_extraction_order",
            "quad_rasterizer",
            "surface_renderer",
            "explicit_stm_transport",
        }
    }
    panel_improvements = sum(
        float(row["delta_projection_loss_from_canonical"]) < 0.0
        for row in grouped["panel_time_mapping"]
    )
    material_counts = {
        control: sum(
            row["semantic_similarity_gate"] == "material_difference"
            for row in grouped[control]
        )
        for control in (
            "mask_extraction_order",
            "quad_rasterizer",
            "surface_renderer",
            "explicit_stm_transport",
        )
    }

    evidence_paths = (HALO_CSV, VERTICAL_CSV, CONTROL_CSV, POSTHOC_CSV, HOLDOUT_CSV)
    evidence_artifacts = ";".join(_display(path) for path in evidence_paths)
    evidence_sha = ";".join(f"{_display(path)}={_sha256(path)}" for path in evidence_paths)

    values: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "stage_b_status": "complete_with_negative_and_boundary_results",
        "stage_c_transition_status": "eligible_for_research_only_reproduction_status_frozen",
        "halo_resolutions": "21;33;45",
        "halo_source_gate_pass_rows": f"{halo_source_pass}/3",
        "halo_cross_resolution_pass_rows": f"{halo_convergence_pass}/2",
        "halo_posthoc_projection_pass_rows": f"{halo_projection_pass}/6",
        "halo_highest_resolution_status": halo[-1]["overall_status"],
        "halo_max_adjacent_principal_angle_deg": max(
            float(row["principal_angle_max_to_previous_deg"])
            for row in halo_nonbaseline
        ),
        "halo_max_adjacent_sheet_hd95_normalized": max(
            float(row["sheet_hd95_normalized_max_to_previous"])
            for row in halo_nonbaseline
        ),
        "halo_ring_dispersion_fail_resolutions": (
            "none" if not halo_ring_fail else ";".join(halo_ring_fail)
        ),
        "vertical_resolutions": "33;45;57",
        "vertical_source_gate_pass_rows": f"{vertical_source_pass}/3",
        "vertical_cross_resolution_pass_rows": f"{vertical_convergence_pass}/2",
        "vertical_posthoc_projection_pass_rows": f"{vertical_projection_pass}/6",
        "vertical_highest_resolution_status": vertical[-1]["overall_status"],
        "vertical_max_adjacent_principal_angle_deg": max(
            float(row["principal_angle_max_to_previous_deg"])
            for row in vertical_nonbaseline
        ),
        "vertical_max_adjacent_sheet_hd95_normalized": max(
            float(row["sheet_hd95_normalized_max_to_previous"])
            for row in vertical_nonbaseline
        ),
        "vertical_multiplier_fail_resolutions": (
            "none"
            if not vertical_multiplier_fail
            else ";".join(vertical_multiplier_fail)
        ),
        "vertical_ring_dispersion_fail_resolutions": (
            "none" if not vertical_ring_fail else ";".join(vertical_ring_fail)
        ),
        "halo_n21_improves_n9_f1_rows": f"{n21_improvements}/2",
        "halo_n21_posthoc_projection_pass_rows": f"{n21_projection_pass}/2",
        "panel_time_loss_improvement_rows": f"{panel_improvements}/4",
        "mask_extraction_material_rows": (
            f"{material_counts['mask_extraction_order']}/4"
        ),
        "quad_rasterizer_material_rows": (
            f"{material_counts['quad_rasterizer']}/4"
        ),
        "surface_renderer_material_rows": (
            f"{material_counts['surface_renderer']}/4"
        ),
        "explicit_stm_transport_material_rows": (
            f"{material_counts['explicit_stm_transport']}/8"
        ),
        "source_member_judgment": (
            "contributing_not_sufficient: N21 improves both halo F1 rows over N9 "
            "but passes neither exposed projection row"
        ),
        "spectral_resolution_judgment": (
            "not_converged_under_frozen_gates: both families fail adjacent full-sheet "
            "HD95 and show nonmonotonic unstable-ring or multiplier failures"
        ),
        "pointwise_eigenvector_judgment": (
            "leading_method_hypothesis_not_unique_proof: phase-aligned pointwise "
            "directions are locally continuous while multiplier-ring/full-sheet "
            "convergence fails"
        ),
        "renderer_projection_judgment": (
            "simple_panel_time_mask_rasterizer_renderer_changes_do_not_rescue; "
            "explicit_STM_transport_semantics_are_material"
        ),
        "original_state_boundary_judgment": (
            "paper_exact_3D_states_perturbations_and_renderer_semantics_unavailable"
        ),
        "primary_stage_b_judgment": (
            "multi_factor_boundary: halo source mismatch contributes, but spectral/"
            "pointwise-direction transport and full-sheet nonconvergence remain; "
            "simple renderer controls are not the primary cause"
        ),
        "frozen_holdout_status": "fail_0_of_4_unchanged",
        "paper_projection_acceptance": "fail",
        "paper_3d_equivalence": False,
        "evidence_artifacts": evidence_artifacts,
        "evidence_sha256": evidence_sha,
        "generator_sha256": _sha256(Path(__file__)),
    }
    row = {column: _fmt(values[column]) for column in CSV_COLUMNS}

    document = "\n".join(
        [
            "# Chapter 4 Stage B invariant-bundle transition conclusion",
            "",
            "## Stage status",
            "",
            "- Stage B is complete with negative and boundary results. Completion here means the predeclared cases and controls were run and archived; it does not mean the numerical gates passed.",
            "- Stage C is eligible for research-only work. The reproduction baseline, canonical figure status, and frozen v1 holdout remain unchanged.",
            "",
            "## Resolution evidence",
            "",
            "| family | N | source-gate rows | adjacent convergence rows | exposed projection rows | highest-N status |",
            "|---|---|---:|---:|---:|---|",
            f"| halo | {row['halo_resolutions']} | {row['halo_source_gate_pass_rows']} | {row['halo_cross_resolution_pass_rows']} | {row['halo_posthoc_projection_pass_rows']} | {row['halo_highest_resolution_status']} |",
            f"| vertical | {row['vertical_resolutions']} | {row['vertical_source_gate_pass_rows']} | {row['vertical_cross_resolution_pass_rows']} | {row['vertical_posthoc_projection_pass_rows']} | {row['vertical_highest_resolution_status']} |",
            "",
            f"- Halo maximum adjacent principal angle: {float(row['halo_max_adjacent_principal_angle_deg']):.6f} deg; maximum normalized adjacent sheet HD95: {float(row['halo_max_adjacent_sheet_hd95_normalized']):.6f}.",
            f"- Vertical maximum adjacent principal angle: {float(row['vertical_max_adjacent_principal_angle_deg']):.6f} deg; maximum normalized adjacent sheet HD95: {float(row['vertical_max_adjacent_sheet_hd95_normalized']):.6f}.",
            f"- Halo unstable-ring dispersion fails at N={row['halo_ring_dispersion_fail_resolutions']}; vertical multiplier gate fails at N={row['vertical_multiplier_fail_resolutions']} and ring dispersion fails at N={row['vertical_ring_dispersion_fail_resolutions']}.",
            "",
            "## Frozen negative controls",
            "",
            f"- Adjacent panel-time lowers exposed loss in {row['panel_time_loss_improvement_rows']} rows.",
            f"- Material semantic differences: mask {row['mask_extraction_material_rows']}, triangle rasterizer {row['quad_rasterizer_material_rows']}, Matplotlib renderer {row['surface_renderer_material_rows']}.",
            f"- The two explicit STM transport variants differ materially from nonlinear tau+phase in {row['explicit_stm_transport_material_rows']} rows.",
            "",
            "## B4 judgment",
            "",
            f"1. Source member: {row['source_member_judgment']}.",
            f"2. Spectral resolution: {row['spectral_resolution_judgment']}.",
            f"3. Pointwise eigenselection: {row['pointwise_eigenvector_judgment']}.",
            f"4. Renderer/projection semantics: {row['renderer_projection_judgment']}.",
            f"5. Unavailable original evidence: {row['original_state_boundary_judgment']}.",
            "",
            f"Primary judgment: {row['primary_stage_b_judgment']}.",
            "",
            "This result motivates the invariant-bundle research layer without claiming that a new method has already been demonstrated. Ordered real-Schur and QR/SVD cocycle methods must still beat the frozen pointwise baseline on registered benchmarks.",
            "",
            "## Protection boundary",
            "",
            "- Frozen holdout: 0/4, paper_projection=fail, paper_3d=false.",
            "- No camera, epsilon, crop, red threshold, source member, or acceptance gate was selected from panel (d).",
            "- Research results may not write into figure_validation_table.csv without a separate promotion audit.",
            "",
            "## Evidence",
            "",
            f"- Machine conclusion: {_display(OUTPUT_CSV)}",
            f"- Inputs: {row['evidence_artifacts']}",
            "",
        ]
    )
    return [row], document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows, document = build()
    csv_text = _csv_text(rows)
    if args.check:
        if not OUTPUT_CSV.is_file() or OUTPUT_CSV.read_text(encoding="utf-8") != csv_text:
            raise RuntimeError("stored Stage B conclusion CSV drifted")
        if not OUTPUT_DOC.is_file() or OUTPUT_DOC.read_text(encoding="utf-8") != document:
            raise RuntimeError("stored Stage B conclusion report drifted")
        print("chapter4 Stage B conclusion CHECK PASS status=complete_with_negative_results")
        return 0
    OUTPUT_CSV.write_text(csv_text, encoding="utf-8", newline="\n")
    OUTPUT_DOC.write_text(document, encoding="utf-8", newline="\n")
    print("chapter4 Stage B conclusion WRITE PASS status=complete_with_negative_results")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
