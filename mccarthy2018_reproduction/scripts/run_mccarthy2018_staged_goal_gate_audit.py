"""Summarize staged McCarthy 2018 reproduction gates from audit artifacts.

This script is intentionally conservative: it separates figure-source evidence
from exploratory local branches.  A route that passes a diagnostic or
turn-aware gate does not unlock Fig. 3.16 / Fig. 3.17 unless it also satisfies
the fixed-time figure-source requirements and independent audit evidence.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter3_integrated_breakthrough as campaign

OUTPUT = PROJECT_ROOT / "data" / "computed" / "mccarthy2018_staged_goal_gate_status.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "mccarthy2018_staged_goal_gate_status.md"

FIELDS = (
    "scope",
    "gate_id",
    "requirement",
    "status",
    "metric",
    "value",
    "threshold",
    "evidence_artifact",
    "decision",
    "notes",
)


def _fmt(value: Any) -> str:
    return campaign._fmt(value)


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _as_bool(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def _as_float(value: str | None, default: float = float("nan")) -> float:
    if value is None or value == "" or value == "N/A":
        return default
    try:
        number = float(value)
    except ValueError:
        return default
    return number if np.isfinite(number) else default


def _is_original_chapter5_figure(figure_id: str) -> bool:
    return figure_id.startswith("5.") and figure_id[2:].isdigit()


def _is_original_chapter4_figure(figure_id: str) -> bool:
    return figure_id.startswith("4.") and figure_id[2:].isdigit()


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _row(
    *,
    scope: str,
    gate_id: str,
    requirement: str,
    status: str,
    metric: str,
    value: Any,
    threshold: str,
    evidence_artifact: str,
    decision: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "gate_id": gate_id,
        "requirement": requirement,
        "status": status,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "evidence_artifact": evidence_artifact,
        "decision": decision,
        "notes": notes,
    }


def _best_value(rows: list[dict[str, str]], value_field: str, accept_field: str) -> float | None:
    accepted = [_as_float(row.get(value_field)) for row in rows if _as_bool(row.get(accept_field))]
    accepted = [value for value in accepted if np.isfinite(value)]
    return max(accepted) if accepted else None


def _best_trial(rows: list[dict[str, str]], value_field: str) -> float | None:
    values = [_as_float(row.get(value_field)) for row in rows]
    values = [value for value in values if np.isfinite(value)]
    return max(values) if values else None


def _artifact(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _build_rows() -> list[dict[str, Any]]:
    data = PROJECT_ROOT / "data" / "computed"
    docs = PROJECT_ROOT / "docs"
    family_path = campaign.FAMILY_PATH
    family = campaign.load_corrected_dro_family_csv(family_path)
    baseline = max(member.max_abs_z_km for member in family)

    candidates_path = data / "chapter3_integrated_breakthrough_candidates.csv"
    revalidation_path = data / "chapter3_integrated_breakthrough_revalidation.csv"
    turn_path = data / "chapter3_turn_aware_amplitude_continuation.csv"
    turn_revalidation_path = data / "chapter3_turn_aware_amplitude_revalidation.csv"
    multi_path = data / "chapter3_multi_coordinate_palc_continuation.csv"
    free_projection_path = data / "chapter3_free_time_fixed_time_projection_audit.csv"
    augmented_path = data / "chapter3_augmented_coordinate_palc_probe.csv"
    variable_time_path = data / "chapter3_variable_time_fixed_time_projection_audit.csv"
    cache_audit_path = data / "chapter3_fixed_mapping_cache_audit.csv"
    cache_family_path = data / "chapter3_fixed_mapping_cache_accepted_family.csv"
    cache_validation_path = data / "chapter3_fixed_mapping_cache_accepted_validation.csv"
    chapter4_route_h_dg_path = data / "chapter4_route_h_quasi_dro_dg.csv"
    chapter4_route_h_manifold_path = data / "chapter4_route_h_quasi_dro_manifold_probe.csv"
    chapter4_route_h_figure_png = PROJECT_ROOT / "outputs" / "figures_png" / "fig_4_route_h.png"
    chapter4_route_h_figure_pdf = PROJECT_ROOT / "outputs" / "figures_pdf" / "fig_4_route_h.pdf"
    chapter4_per_figure_path = data / "chapter4_per_figure_source_layer_audit.csv"
    chapter4_per_figure_doc_path = docs / "chapter4_per_figure_source_layer_audit.md"
    chapter5_audit_path = data / "chapter5_upstream_application_gate_audit.csv"
    chapter5_doc_path = docs / "chapter5_upstream_application_gate_audit.md"
    chapter5_readiness_path = data / "chapter5_high_fidelity_optimization_readiness_audit.csv"
    chapter5_readiness_doc_path = docs / "chapter5_high_fidelity_optimization_readiness_audit.md"
    chapter5_nrho_transfer_path = data / "chapter5_nrho_transfer_per_figure_audit.csv"
    chapter5_nrho_transfer_doc_path = docs / "chapter5_nrho_transfer_per_figure_audit.md"
    chapter5_stable_manifold_path = data / "chapter5_stable_manifold_per_figure_audit.csv"
    chapter5_stable_manifold_doc_path = docs / "chapter5_stable_manifold_per_figure_audit.md"
    chapter5_per_figure_path = data / "chapter5_per_figure_source_layer_audit.csv"
    chapter5_per_figure_doc_path = docs / "chapter5_per_figure_source_layer_audit.md"
    chapter5_optimization_figure_png = PROJECT_ROOT / "outputs" / "figures_png" / "fig_5_bcr4bp_optimized_transfer.png"
    chapter5_optimization_figure_pdf = PROJECT_ROOT / "outputs" / "figures_pdf" / "fig_5_bcr4bp_optimized_transfer.pdf"
    decision_path = docs / "chapter3_quasi_dro_frontier_decision.md"

    candidates = _read_rows(candidates_path)
    revalidation = _read_rows(revalidation_path)
    turn = _read_rows(turn_path)
    turn_revalidation = _read_rows(turn_revalidation_path)
    multi = _read_rows(multi_path)
    free_projection = _read_rows(free_projection_path)
    augmented = _read_rows(augmented_path)
    variable_time = _read_rows(variable_time_path)
    cache_audit = _read_rows(cache_audit_path)
    cache_validation = _read_rows(cache_validation_path)
    chapter4_route_h_dg = _read_rows(chapter4_route_h_dg_path)
    chapter4_route_h_manifold = _read_rows(chapter4_route_h_manifold_path)
    chapter4_per_figure = _read_rows(chapter4_per_figure_path)
    chapter5_audit = _read_rows(chapter5_audit_path)
    chapter5_readiness = _read_rows(chapter5_readiness_path)
    chapter5_nrho_transfer = _read_rows(chapter5_nrho_transfer_path)
    chapter5_stable_manifold = _read_rows(chapter5_stable_manifold_path)
    chapter5_per_figure = _read_rows(chapter5_per_figure_path)

    best_campaign = _best_value(candidates, "max_abs_z_km", "overall_acceptance")
    best_campaign_revalidated = _best_value(
        revalidation,
        "max_abs_z_km",
        "revalidated_acceptance",
    )
    best_turn = _best_value(turn, "max_abs_z_km", "turn_aware_acceptance")
    best_turn_revalidated = _best_value(
        turn_revalidation,
        "max_abs_z_km",
        "revalidated_acceptance",
    )
    best_multi = _best_value(multi, "solved_max_abs_z_km", "accepted_step")
    best_free_projection = _best_value(
        free_projection,
        "projected_max_abs_z_km",
        "projection_acceptance",
    )
    best_augmented = _best_value(
        augmented,
        "solved_max_abs_z_km",
        "coordinate_palc_acceptance",
    )
    best_variable = _best_value(
        variable_time,
        "solved_max_abs_z_km",
        "accepted_projection",
    )
    best_cache = _best_value(
        cache_audit,
        "max_abs_z_km",
        "strict_acceptance",
    )
    best_cache_validation = _best_trial(cache_validation, "max_abs_z_km")
    best_variable_trial = _best_trial(variable_time, "solved_max_abs_z_km")
    best_projection = max(
        [value for value in (best_free_projection, best_variable) if value is not None],
        default=None,
    )
    chapter3_frontier_artifact = (
        f"{_artifact(cache_audit_path)};{_artifact(cache_family_path)};{_artifact(cache_validation_path)}"
        if best_cache is not None and best_cache >= campaign.TARGET_MIN_KM
        else _artifact(family_path)
    )

    route_values = [
        value
        for value in (
            best_campaign_revalidated,
            best_free_projection,
            best_augmented,
            best_variable,
            best_cache,
        )
        if value is not None
    ]
    # Turn-aware and multi-coordinate PALC rows use a diagnostic amplitude gate
    # rather than the original fixed-time figure-source gate set. Keep them out
    # of the figure-source frontier, but include them as experimental evidence.
    figure_source_frontier = max([baseline, *route_values])
    experimental_frontier = max(
        value
        for value in (
            baseline,
            best_campaign or float("nan"),
            best_turn or float("nan"),
            best_turn_revalidated or float("nan"),
            best_multi or float("nan"),
        )
        if np.isfinite(value)
    )
    chapter3_passes = figure_source_frontier >= campaign.TARGET_MIN_KM
    chapter4_route_h_dg_passes = (
        chapter3_passes
        and bool(chapter4_route_h_dg)
        and bool(chapter4_route_h_manifold)
        and all(_as_float(row.get("determinant_error_from_one"), 1.0) < 1.0e-9 for row in chapter4_route_h_dg)
        and all(_as_float(row.get("real_pair_reciprocity_error"), 1.0) < 1.0e-8 for row in chapter4_route_h_dg)
        and all(_as_float(row.get("jacobi_drift_max"), 1.0) < 1.0e-10 for row in chapter4_route_h_manifold)
    )
    chapter4_worst_determinant_error = max(
        (_as_float(row.get("determinant_error_from_one")) for row in chapter4_route_h_dg),
        default=None,
    )
    chapter4_worst_manifold_jacobi = max(
        (_as_float(row.get("jacobi_drift_max")) for row in chapter4_route_h_manifold),
        default=None,
    )
    chapter4_route_h_figure_passes = (
        chapter4_route_h_dg_passes
        and chapter4_route_h_figure_png.exists()
        and chapter4_route_h_figure_pdf.exists()
        and chapter4_route_h_figure_png.stat().st_size > 0
        and chapter4_route_h_figure_pdf.stat().st_size > 0
    )
    chapter4_original_figure_rows = [
        row for row in chapter4_per_figure if _is_original_chapter4_figure(row.get("figure_id", ""))
    ]
    chapter4_derived_source_rows = [
        row for row in chapter4_per_figure if not _is_original_chapter4_figure(row.get("figure_id", ""))
    ]
    chapter4_per_figure_audit_passes = (
        len(chapter4_original_figure_rows) == 8
        and any(row.get("figure_id") == "4.route_h" for row in chapter4_derived_source_rows)
        and chapter4_per_figure_doc_path.exists()
    )
    chapter5_by_gate = {row.get("gate_id", ""): row for row in chapter5_audit}
    chapter5_readiness_by_gate = {row.get("gate_id", ""): row for row in chapter5_readiness}
    chapter5_route_h_de421_passes = (
        chapter5_by_gate.get("C5-ROUTE-H-DE421-BASELINE", {}).get("status") == "pass"
    )
    chapter5_readiness_documented = (
        chapter5_readiness_by_gate.get("C5-HF-READINESS-STATUS", {}).get("status")
        == "bounded_blocker_documented"
    )
    chapter5_readiness_passes = (
        chapter5_readiness_by_gate.get("C5-HF-READINESS-STATUS", {}).get("status") == "pass"
    )
    chapter5_bcr4bp_passes = (
        chapter5_readiness_by_gate.get("C5-HF-BCR4BP-DYNAMICS", {}).get("status") == "pass"
    )
    chapter5_correction_passes = (
        chapter5_readiness_by_gate.get("C5-HF-DYNAMICS-CORRECTION", {}).get("status") == "pass"
    )
    chapter5_optimization_passes = (
        chapter5_readiness_by_gate.get("C5-HF-TRANSFER-OPTIMIZATION", {}).get("status") == "pass"
        and chapter5_optimization_figure_png.exists()
        and chapter5_optimization_figure_pdf.exists()
        and chapter5_optimization_figure_png.stat().st_size > 0
        and chapter5_optimization_figure_pdf.stat().st_size > 0
    )
    chapter5_missing_hf_capabilities = _as_float(
        chapter5_readiness_by_gate.get("C5-HF-READINESS-STATUS", {}).get("value"),
        0.0,
    )
    chapter5_high_fidelity_blocked = (
        not chapter5_readiness_passes
        and (
            chapter5_by_gate.get("C5-HIGH-FIDELITY-OPTIMIZATION", {}).get("status")
            == "blocked_missing_high_fidelity_optimization"
            or chapter5_readiness_documented
        )
    )
    chapter5_original_figure_rows = [
        row for row in chapter5_per_figure if _is_original_chapter5_figure(row.get("figure_id", ""))
    ]
    chapter5_derived_source_rows = [
        row for row in chapter5_per_figure if not _is_original_chapter5_figure(row.get("figure_id", ""))
    ]
    chapter5_per_figure_audit_passes = (
        len(chapter5_original_figure_rows) == 14
        and any(
            row.get("figure_id") == "5.bcr4bp_optimized_transfer"
            and _as_float(row.get("accepted_rows"), 0.0) > 0.0
            for row in chapter5_derived_source_rows
        )
        and chapter5_per_figure_doc_path.exists()
    )
    chapter5_nrho_transfer_accepted = [
        row for row in chapter5_nrho_transfer if _as_bool(row.get("acceptance"))
    ]
    chapter5_nrho_transfer_passes = (
        len(chapter5_nrho_transfer_accepted) >= 4
        and {row.get("figure_id") for row in chapter5_nrho_transfer_accepted} >= {"5.10", "5.11"}
        and chapter5_nrho_transfer_doc_path.exists()
    )
    chapter5_stable_manifold_accepted = [
        row for row in chapter5_stable_manifold if _as_bool(row.get("acceptance"))
    ]
    chapter5_stable_manifold_passes = (
        len(chapter5_stable_manifold_accepted) >= 2
        and {row.get("figure_id") for row in chapter5_stable_manifold_accepted} >= {"5.13", "5.14"}
        and chapter5_stable_manifold_doc_path.exists()
    )
    rows: list[dict[str, Any]] = [
        _row(
            scope="chapter3",
            gate_id="C3-FIGURE-SOURCE-FRONTIER",
            requirement="Fixed-time Fig. 3.16/3.17 source branch must have accepted, independently auditable evidence above 10,500 km.",
            status="fail" if not chapter3_passes else "pass",
            metric="figure_source_frontier_max_abs_z_km",
            value=figure_source_frontier,
            threshold=f">= {campaign.TARGET_MIN_KM}",
            evidence_artifact=chapter3_frontier_artifact,
            decision="do_not_update_fig_3_16_3_17" if not chapter3_passes else "figure_update_allowed",
            notes="Experimental routes beyond this value are excluded unless they preserve the original fixed-time figure-source gate semantics.",
        ),
        _row(
            scope="chapter3",
            gate_id="C3-EXPERIMENTAL-FRONTIER",
            requirement="Track the best local/diagnostic fixed-time amplitude even when it is not a figure source.",
            status="informational",
            metric="experimental_frontier_max_abs_z_km",
            value=experimental_frontier,
            threshold="not a figure-source threshold",
            evidence_artifact=_artifact(multi_path),
            decision="diagnostic_only",
            notes="Includes turn-aware and full-vector PALC rows that do not unlock downstream figure regeneration.",
        ),
        _row(
            scope="chapter3",
            gate_id="C3-ROUTE-A",
            requirement="Part 5 monotone-rho campaign must survive independent revalidation and all gates.",
            status="fail" if best_campaign_revalidated is None else "pass",
            metric="best_revalidated_max_abs_z_km",
            value=best_campaign_revalidated,
            threshold=f">= {campaign.TARGET_MIN_KM}",
            evidence_artifact=_artifact(revalidation_path),
            decision="bounded_route",
            notes=f"Best campaign CSV acceptance was {best_campaign}; independent revalidation does not support a figure update.",
        ),
        _row(
            scope="chapter3",
            gate_id="C3-ROUTE-C-E",
            requirement="Turn-aware/full-vector PALC must exceed 10,500 km and preserve audit semantics before downstream use.",
            status="fail",
            metric="best_diagnostic_palc_max_abs_z_km",
            value=max(value for value in (best_turn_revalidated or 0.0, best_multi or 0.0)),
            threshold=f">= {campaign.TARGET_MIN_KM}",
            evidence_artifact=f"{_artifact(turn_revalidation_path)};{_artifact(multi_path)}",
            decision="diagnostic_only",
            notes="Rows are useful local evidence but remain below the required minimum and do not preserve original rho monotonicity semantics.",
        ),
        _row(
            scope="chapter3",
            gate_id="C3-ROUTE-D-G",
            requirement="Free-time high-amplitude states must project back to fixed-time accepted members above 10,500 km.",
            status="fail",
            metric="best_accepted_projection_max_abs_z_km",
            value=best_projection,
            threshold=f">= {campaign.TARGET_MIN_KM}",
            evidence_artifact=f"{_artifact(free_projection_path)};{_artifact(variable_time_path)}",
            decision="bounded_projection_routes",
            notes=f"Best non-accepted variable-time trial was {best_variable_trial}; trial amplitude is not accepted evidence.",
        ),
        _row(
            scope="chapter3",
            gate_id="C3-ROUTE-H",
            requirement="Fixed-mapping cache candidates must pass the current seven-gate audit before becoming figure-source data.",
            status="pass" if best_cache is not None and best_cache >= campaign.TARGET_MIN_KM else "fail",
            metric="best_strict_cache_max_abs_z_km",
            value=best_cache,
            threshold=f">= {campaign.TARGET_MIN_KM}",
            evidence_artifact=f"{_artifact(cache_audit_path)};{_artifact(cache_family_path)};{_artifact(cache_validation_path)}",
            decision="use_route_h_for_chapter3_source" if best_cache is not None else "cache_not_accepted",
            notes=f"Best exported validation max abs z is {best_cache_validation}; accepted cache family is monotone-filtered.",
        ),
        _row(
            scope="chapter4",
            gate_id="C4-UPSTREAM-TORUS-DATA",
            requirement="Chapter 4 torus-scale DG/manifold figures require accepted Chapter 3 high-amplitude torus data.",
            status=(
                "route_h_figure_source_passed"
                if chapter4_route_h_figure_passes
                else "route_h_dg_source_passed"
                if chapter4_route_h_dg_passes
                else ("ready_for_regeneration" if chapter3_passes else "blocked_by_chapter3")
            ),
            metric="chapter3_figure_source_frontier_max_abs_z_km",
            value=figure_source_frontier,
            threshold=f">= {campaign.TARGET_MIN_KM}",
            evidence_artifact=f"{_artifact(cache_family_path)};{_artifact(chapter4_route_h_dg_path)};{_artifact(chapter4_route_h_manifold_path)};{_artifact(chapter4_per_figure_path)};{_artifact(chapter4_route_h_figure_png)}",
            decision=(
                "route_h_chapter4_figure_source_available"
                if chapter4_route_h_figure_passes
                else
                "build_route_h_chapter4_figures_or_continue_l1_families"
                if chapter4_route_h_dg_passes
                else ("regenerate_chapter4_from_route_h_source" if chapter3_passes else "do_not_regenerate_chapter4_manifolds")
            ),
            notes=(
                "Route H accepted quasi-DRO corrections now have a regenerated Chapter 4 source-layer DG/manifold figure; existing Fig. 4.3-4.8 L1 quasi-halo/vertical proxy backgrounds still need a separate thesis-figure replacement route."
                if chapter4_route_h_figure_passes
                else
                "Route H accepted quasi-DRO corrections now pass the Chapter 4 DG compatibility and local manifold probe layer; existing Fig. 4.3-4.8 L1 quasi-halo/vertical proxy backgrounds still need a separate figure-source decision."
                if chapter4_route_h_dg_passes
                else "Route H provides accepted high-amplitude fixed-time torus data; Chapter 4 can now be regenerated from this source."
                if chapter3_passes
                else "Upstream quasi-DRO frontier is below the minimum, so Chapter 4 remains gated."
            ),
        ),
        _row(
            scope="chapter4",
            gate_id="C4-ROUTE-H-DG-MANIFOLD",
            requirement="Accepted Route H quasi-DRO corrections must convert to DG spectra and local manifold probes with symplectic/energy consistency before downstream use.",
            status="pass" if chapter4_route_h_dg_passes else "not_run_or_fail",
            metric="worst_route_h_manifold_jacobi_drift",
            value=chapter4_worst_manifold_jacobi,
            threshold="< 1e-10",
            evidence_artifact=f"{_artifact(chapter4_route_h_dg_path)};{_artifact(chapter4_route_h_manifold_path)}",
            decision="route_h_source_layer_ready" if chapter4_route_h_dg_passes else "run_chapter4_route_h_dg_manifold_audit",
            notes=f"Worst determinant error is {chapter4_worst_determinant_error}; this is a source-layer audit, not a completed thesis-scale global manifold replacement.",
        ),
        _row(
            scope="chapter4",
            gate_id="C4-ROUTE-H-FIGURE-SOURCE",
            requirement="The Route H Chapter 4 source-layer must have regenerated PNG/PDF figure artifacts before being treated as a figure-source deliverable.",
            status="pass" if chapter4_route_h_figure_passes else "not_run_or_fail",
            metric="route_h_figure_png_bytes",
            value=chapter4_route_h_figure_png.stat().st_size if chapter4_route_h_figure_png.exists() else None,
            threshold="> 0 and PDF exists",
            evidence_artifact=f"{_artifact(chapter4_route_h_figure_png)};{_artifact(chapter4_route_h_figure_pdf)};{_artifact(chapter4_per_figure_path)}",
            decision="route_h_chapter4_figure_source_available" if chapter4_route_h_figure_passes else "run_fig_4_route_h_quasi_dro",
            notes="This figure is a Route H quasi-DRO Chapter 4 source-layer artifact; it does not claim to replace the original L1 quasi-halo/vertical thesis figures 4.3-4.8.",
        ),
        _row(
            scope="chapter4",
            gate_id="C4-PER-FIGURE-SOURCE-LAYER-AUDIT",
            requirement="Chapter 4 source-layer evidence must be mapped back to each original Fig. 4.1-4.8 and separated from the derived Route H quasi-DRO source-layer figure.",
            status="pass" if chapter4_per_figure_audit_passes else "not_run_or_incomplete",
            metric="original_chapter4_figure_rows",
            value=len(chapter4_original_figure_rows),
            threshold="8 original rows plus one derived Route H source-layer row",
            evidence_artifact=f"{_artifact(chapter4_per_figure_path)};{_artifact(chapter4_per_figure_doc_path)}",
            decision=(
                "use_per_figure_chapter4_status_table"
                if chapter4_per_figure_audit_passes
                else "run_chapter4_per_figure_source_layer_audit"
            ),
            notes=(
                f"Per-figure audit maps {len(chapter4_original_figure_rows)} original Chapter 4 figures and "
                f"{len(chapter4_derived_source_rows)} derived source-layer figure(s); the Route H quasi-DRO "
                "source layer is not counted as a direct replacement for original L1 quasi-halo/vertical thesis figures."
            ),
        ),
        _row(
            scope="chapter5",
            gate_id="C5-UPSTREAM-HIGH-FIDELITY-DATA",
            requirement="Chapter 5 high-fidelity/optimization figures require reliable Chapter 3 and Chapter 4 upstream data.",
            status=(
                "route_h_bcr4bp_optimization_source_layer_passed"
                if chapter5_route_h_de421_passes and chapter5_readiness_passes and chapter5_optimization_passes
                else
                "route_h_de421_baseline_ready_high_fidelity_blocked"
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked
                else ("blocked_by_chapter4" if chapter3_passes else "blocked_by_chapter3")
            ),
            metric="chapter3_figure_source_frontier_max_abs_z_km",
            value=figure_source_frontier,
            threshold=f">= {campaign.TARGET_MIN_KM}",
            evidence_artifact=f"{_artifact(decision_path)};{_artifact(chapter5_audit_path)};{_artifact(chapter5_readiness_path)};{_artifact(chapter5_per_figure_path)}",
            decision=(
                "chapter5_source_layer_optimization_available"
                if chapter5_route_h_de421_passes and chapter5_readiness_passes and chapter5_optimization_passes
                else
                "do_not_claim_high_fidelity_chapter5"
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked
                else ("wait_for_chapter4_regeneration" if chapter3_passes else "do_not_regenerate_chapter5_applications")
            ),
            notes=(
                "Route H / DE421 Chapter 5 baseline figures are regenerated; BCR4BP dynamics, short-segment defect correction, and transfer-optimization source-layer figure artifacts now have audit evidence."
                if chapter5_route_h_de421_passes and chapter5_readiness_passes and chapter5_optimization_passes
                else
                "Route H / DE421 Chapter 5 baseline figures are regenerated, and BCR4BP dynamics plus short-segment defect correction now have audit evidence; optimized transfer evidence is still missing."
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked and chapter5_bcr4bp_passes and chapter5_correction_passes
                else
                "Route H / DE421 Chapter 5 baseline figures are regenerated and the BCR4BP dynamics kernel now has model-level audit evidence, but ephemeris correction and optimized transfer evidence are still missing."
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked and chapter5_bcr4bp_passes
                else
                "Route H / DE421 Chapter 5 baseline figures are regenerated, but BCR4BP, ephemeris correction, and optimized transfer evidence are still missing."
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked
                else "Chapter 3 is available through Route H, but Chapter 5 remains gated until Chapter 4 manifold regeneration is complete."
                if chapter3_passes
                else "Chapter 5 remains gated until Chapter 3 and Chapter 4 have accepted source data."
            ),
        ),
        _row(
            scope="chapter5",
            gate_id="C5-ROUTE-H-DE421-BASELINE",
            requirement="Chapter 5 DE421-oriented quasi-DRO baseline figures should use the accepted Route H upstream member.",
            status="pass" if chapter5_route_h_de421_passes else "not_run_or_fail",
            metric="fig_5_6_png_bytes",
            value=_as_float(chapter5_by_gate.get("C5-ROUTE-H-DE421-BASELINE", {}).get("value")),
            threshold="> 0 and Fig. 5.7 exists",
            evidence_artifact=f"{_artifact(chapter5_audit_path)};outputs/figures_png/fig_5_6.png;outputs/figures_png/fig_5_7.png",
            decision="route_h_de421_baseline_available" if chapter5_route_h_de421_passes else "run_chapter5_upstream_application_gate_audit",
            notes="This is an application baseline upgrade only; it is not BCR4BP or optimized-transfer reproduction.",
        ),
        _row(
            scope="chapter5",
            gate_id="C5-HIGH-FIDELITY-OPTIMIZATION",
            requirement="Chapter 5 high-fidelity/optimization completion requires accepted BCR4BP/ephemeris correction or optimized transfer audit rows.",
            status="pass" if chapter5_readiness_passes and chapter5_optimization_passes else "blocked_missing_high_fidelity_optimization" if chapter5_high_fidelity_blocked else "not_audited",
            metric="missing_high_fidelity_capabilities",
            value=chapter5_missing_hf_capabilities,
            threshold="0 for completed high-fidelity/optimization layer",
            evidence_artifact=f"{_artifact(chapter5_audit_path)};{_artifact(chapter5_doc_path)};{_artifact(chapter5_readiness_path)};{_artifact(chapter5_readiness_doc_path)};{_artifact(chapter5_nrho_transfer_path)};{_artifact(chapter5_stable_manifold_path)};{_artifact(chapter5_per_figure_path)};{_artifact(chapter5_per_figure_doc_path)};{_artifact(chapter5_optimization_figure_png)};{_artifact(chapter5_optimization_figure_pdf)}",
            decision=(
                "chapter5_high_fidelity_optimization_source_layer_ready"
                if chapter5_readiness_passes and chapter5_optimization_passes
                else
                "implement_transfer_optimization_audit_next"
                if chapter5_readiness_documented and chapter5_bcr4bp_passes and chapter5_correction_passes
                else
                "implement_bcr4bp_ephemeris_optimization_interface"
                if chapter5_readiness_documented
                else "define_bcr4bp_or_optimization_audit_next"
            ),
            notes=(
                "Chapter 5 high-fidelity/optimization source layer now has accepted Route H/BCR4BP dynamics, defect-correction, optimized-transfer rows, and rendered optimization figure artifacts."
                if chapter5_readiness_passes and chapter5_optimization_passes
                else
                "Chapter 5 high-fidelity/optimization blocker is now documented by a readiness audit: BCR4BP dynamics and short-segment defect correction pass, while optimized transfer rows are still missing."
                if chapter5_readiness_documented and chapter5_bcr4bp_passes and chapter5_correction_passes
                else
                "Chapter 5 high-fidelity/optimization blocker is now documented by a readiness audit: the BCR4BP dynamics kernel passes a model-level audit, while ephemeris correction and optimized transfer rows are still missing."
                if chapter5_readiness_documented and chapter5_bcr4bp_passes
                else
                "Chapter 5 high-fidelity/optimization blocker is now documented by a readiness audit: BCR4BP dynamics, ephemeris correction, and optimized transfer rows are still missing."
                if chapter5_readiness_documented
                else "Current repository evidence supports Route H/DE421 baseline figures, not full high-fidelity application reproduction."
            ),
        ),
        _row(
            scope="chapter5",
            gate_id="C5-STABLE-MANIFOLD-PER-FIGURE-AUDIT",
            requirement="Figures 5.13 and 5.14 should have per-figure stable-manifold rows with periapsis targeting, transfer time, Jacobi span, and periodicity evidence before being promoted beyond generic overlay status.",
            status="pass" if chapter5_stable_manifold_passes else "not_run_or_incomplete",
            metric="accepted_stable_manifold_rows",
            value=len(chapter5_stable_manifold_accepted),
            threshold=">= 2 accepted rows covering Fig. 5.13 and Fig. 5.14",
            evidence_artifact=f"{_artifact(chapter5_stable_manifold_path)};{_artifact(chapter5_stable_manifold_doc_path)}",
            decision=(
                "use_stable_manifold_per_figure_rows"
                if chapter5_stable_manifold_passes
                else "run_chapter5_stable_manifold_per_figure_audit"
            ),
            notes=(
                "Accepted rows are Sun-Earth CR3BP stable-manifold baseline rows; "
                "they record periapsis targeting and transfer-scene evidence but do not "
                "claim full quasi-periodic Lissajous-torus or ephemeris replacement."
            ),
        ),
        _row(
            scope="chapter5",
            gate_id="C5-NRHO-PER-FIGURE-TRANSFER-AUDIT",
            requirement="Figures 5.10 and 5.11 should have per-figure accepted transfer rows with endpoint error, delta-v, and Jacobi-span evidence before being promoted beyond generic baseline status.",
            status="pass" if chapter5_nrho_transfer_passes else "not_run_or_incomplete",
            metric="accepted_nrho_transfer_rows",
            value=len(chapter5_nrho_transfer_accepted),
            threshold=">= 4 accepted rows covering Fig. 5.10 and Fig. 5.11",
            evidence_artifact=f"{_artifact(chapter5_nrho_transfer_path)};{_artifact(chapter5_nrho_transfer_doc_path)}",
            decision=(
                "use_nrho_per_figure_transfer_rows"
                if chapter5_nrho_transfer_passes
                else "run_chapter5_nrho_transfer_per_figure_audit"
            ),
            notes=(
                "Accepted rows are CR3BP endpoint-corrected direct-shooting transfers; "
                "they record per-figure delta-v and endpoint defects but do not claim "
                "BCR4BP/ephemeris high-fidelity thesis replacement."
            ),
        ),
        _row(
            scope="chapter5",
            gate_id="C5-PER-FIGURE-SOURCE-LAYER-AUDIT",
            requirement="Chapter 5 aggregate source-layer gates must be mapped back to each original Fig. 5.1-5.14 before status is reported.",
            status="pass" if chapter5_per_figure_audit_passes else "not_run_or_incomplete",
            metric="original_chapter5_figure_rows",
            value=len(chapter5_original_figure_rows),
            threshold="14 original rows plus one derived optimized-transfer source-layer row",
            evidence_artifact=f"{_artifact(chapter5_per_figure_path)};{_artifact(chapter5_per_figure_doc_path)}",
            decision=(
                "use_per_figure_chapter5_status_table"
                if chapter5_per_figure_audit_passes
                else "run_chapter5_per_figure_source_layer_audit"
            ),
            notes=(
                f"Per-figure audit maps {len(chapter5_original_figure_rows)} original Chapter 5 figures and "
                f"{len(chapter5_derived_source_rows)} derived source-layer figure(s); the optimized-transfer "
                "source layer is not counted as a direct replacement for every original thesis figure."
            ),
        ),
        _row(
            scope="goal",
            gate_id="STAGED-GOAL-STATUS",
            requirement="Advance all three fronts or record bounded blockers with CSV evidence.",
            status=(
                "staged_route_h_source_layers_complete"
                if chapter5_route_h_de421_passes and chapter5_readiness_passes and chapter5_optimization_passes
                else
                "chapter3_chapter4_passed_chapter5_baseline_ready_high_fidelity_blocked"
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked
                else
                "chapter3_passed_chapter4_route_h_figure_source_passed"
                if chapter4_route_h_figure_passes
                else "chapter3_passed_chapter4_source_layer_passed"
                if chapter4_route_h_dg_passes
                else ("chapter3_passed_chapter4_ready" if chapter3_passes else "bounded_at_chapter3")
            ),
            metric="chapter3_gate_passes",
            value=chapter3_passes,
            threshold="True",
            evidence_artifact=f"{_artifact(OUTPUT)};{_artifact(decision_path)}",
            decision=(
                "staged_goal_source_layers_complete"
                if chapter5_route_h_de421_passes and chapter5_readiness_passes and chapter5_optimization_passes
                else
                "continue_to_chapter5_transfer_optimization_audit"
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked and chapter5_bcr4bp_passes and chapter5_correction_passes
                else
                "continue_to_chapter5_bcr4bp_or_optimization_audit"
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked
                else
                "continue_to_chapter4_l1_thesis_figure_replacement_or_chapter5_gate_design"
                if chapter4_route_h_figure_passes
                else
                "continue_to_chapter4_figure_source_decision"
                if chapter4_route_h_dg_passes
                else ("continue_to_chapter4_regeneration" if chapter3_passes else "keep_goal_active_or_request_bounded_acceptance")
            ),
            notes=(
                "Chapter 3 Route H, Chapter 4 Route H figure source, and Chapter 5 Route H/BCR4BP optimization source-layer artifacts are all available with CSV audit evidence. Original thesis-scale figure replacements remain documented separately where applicable."
                if chapter5_route_h_de421_passes and chapter5_readiness_passes and chapter5_optimization_passes
                else
                "Chapter 3, Route H Chapter 4 source figure, and Route H/DE421 Chapter 5 baseline are available; BCR4BP dynamics and short-segment defect correction now pass audit, but high-fidelity/optimization completion remains blocked by missing optimized-transfer audit evidence."
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked and chapter5_bcr4bp_passes and chapter5_correction_passes
                else
                "Chapter 3, Route H Chapter 4 source figure, and Route H/DE421 Chapter 5 baseline are available; the BCR4BP dynamics kernel now passes a model-level audit, but high-fidelity/optimization completion remains blocked by missing ephemeris-correction and optimized-transfer audit evidence."
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked and chapter5_bcr4bp_passes
                else
                "Chapter 3, Route H Chapter 4 source figure, and Route H/DE421 Chapter 5 baseline are available; high-fidelity/optimization completion remains blocked by missing BCR4BP or optimized-transfer audit evidence."
                if chapter5_route_h_de421_passes and chapter5_high_fidelity_blocked
                else
                "Chapter 3 and a regenerated Route H Chapter 4 source-layer figure are available; original L1 Chapter 4 thesis-figure replacement and Chapter 5 application upgrades remain incomplete."
                if chapter4_route_h_figure_passes
                else
                "Chapter 3 and the Route H Chapter 4 source/DG layer are available; Chapter 4 figure replacement and Chapter 5 application upgrades remain incomplete."
                if chapter4_route_h_dg_passes
                else "Current evidence unlocks Chapter 4 regeneration but does not complete Chapter 4/5 upgrades."
                if chapter3_passes
                else "Current evidence supports a Chapter 3 bounded-blocker decision under the existing gates; it does not complete Chapter 4/5 upgrades."
            ),
        ),
    ]
    return rows


def _write_doc(rows: list[dict[str, Any]]) -> None:
    by_gate = {row["gate_id"]: row for row in rows}
    c3 = by_gate["C3-FIGURE-SOURCE-FRONTIER"]
    experimental = by_gate["C3-EXPERIMENTAL-FRONTIER"]
    c4 = by_gate["C4-UPSTREAM-TORUS-DATA"]
    c4_route_h = by_gate["C4-ROUTE-H-DG-MANIFOLD"]
    c4_per_figure = by_gate.get("C4-PER-FIGURE-SOURCE-LAYER-AUDIT", {})
    c5 = by_gate["C5-UPSTREAM-HIGH-FIDELITY-DATA"]
    c5_baseline = by_gate.get("C5-ROUTE-H-DE421-BASELINE", {})
    c5_high_fidelity = by_gate.get("C5-HIGH-FIDELITY-OPTIMIZATION", {})
    c5_nrho_transfer = by_gate.get("C5-NRHO-PER-FIGURE-TRANSFER-AUDIT", {})
    c5_stable_manifold = by_gate.get("C5-STABLE-MANIFOLD-PER-FIGURE-AUDIT", {})
    c5_per_figure = by_gate.get("C5-PER-FIGURE-SOURCE-LAYER-AUDIT", {})
    lines = "\n".join(
        f"- `{row['gate_id']}` ({row['scope']}): status `{row['status']}`, "
        f"metric `{row['metric']}` = `{_fmt(row['value'])}`, decision `{row['decision']}`"
        for row in rows
    )
    DOC_OUTPUT.write_text(
        f"""# McCarthy 2018 Staged Goal Gate Status

## Purpose

This file is generated from current CSV audit artifacts. It records whether the
staged goal can move from Chapter 3 quasi-DRO continuation into Chapter 4
torus-scale DG/manifolds and Chapter 5 high-fidelity/optimization applications.

## Current Decision

- Chapter 3 figure-source frontier: `{_fmt(c3['value'])}` km
- Chapter 3 required minimum: `{campaign.TARGET_MIN_KM}` km
- Best experimental/local frontier: `{_fmt(experimental['value'])}` km
- Fig. 3.16 / Fig. 3.17 update allowed: `{bool(c3['status'] == 'pass')}`
- Chapter 4 Route H DG source layer passed: `{bool(c4_route_h['status'] == 'pass')}`
- Chapter 4 next decision: `{c4['decision']}`
- Chapter 4 per-figure source-layer audit: `{c4_per_figure.get('status')}`
- Chapter 5 Route H / DE421 baseline passed: `{bool(c5_baseline.get('status') == 'pass')}`
- Chapter 5 high-fidelity/optimization status: `{c5_high_fidelity.get('status')}`
- Chapter 5 NRHO per-figure transfer audit: `{c5_nrho_transfer.get('status')}`
- Chapter 5 stable-manifold per-figure audit: `{c5_stable_manifold.get('status')}`
- Chapter 5 per-figure source-layer audit: `{c5_per_figure.get('status')}`
- Chapter 5 regeneration allowed: `{bool(c5['status'] != 'blocked_missing_high_fidelity_optimization' and c5_high_fidelity.get('status') != 'blocked_missing_high_fidelity_optimization')}`

## Gate Rows

{lines}

## Interpretation

Route H contributes accepted fixed-time figure-source members above 10,500 km.
Those cached corrections now also pass the Chapter 4 source-layer DG/manifold
probe in `data/computed/chapter4_route_h_quasi_dro_dg.csv` and
`data/computed/chapter4_route_h_quasi_dro_manifold_probe.csv`.
The corresponding regenerated source-layer figure artifacts are
`outputs/figures_png/fig_4_route_h.png` and
`outputs/figures_pdf/fig_4_route_h.pdf` when gate `C4-ROUTE-H-FIGURE-SOURCE`
passes.

This unlocks a Chapter 4 Route H figure-source artifact, not a completed
replacement of Fig. 4.3-4.8: those existing figures target L1 quasi-halo and
quasi-vertical families and still retain proxy backgrounds.
The Chapter 4 per-original-figure mapping is recorded in
`data/computed/chapter4_per_figure_source_layer_audit.csv` and
`docs/chapter4_per_figure_source_layer_audit.md`; gate
`C4-PER-FIGURE-SOURCE-LAYER-AUDIT` must pass before Chapter 4 status summaries
are treated as figure-by-figure rather than aggregate-only.

The Chapter 5 Route H / DE421 baseline audit is recorded in
`data/computed/chapter5_upstream_application_gate_audit.csv`. Passing this gate
means Figures 5.6 and 5.7 use the accepted Route H quasi-DRO branch in the
DE421 Sun-Moon frame. It does not complete the high-fidelity/optimization
layer. The BCR4BP model-level audit is recorded in
`data/computed/chapter5_bcr4bp_dynamics_audit.csv`. The stricter readiness audit in
`data/computed/chapter5_high_fidelity_optimization_readiness_audit.csv`
records `{_fmt(c5_high_fidelity.get('value'))}` missing high-fidelity
capabilities. When this value is zero, the available Chapter 5 result should be
read as a Route H/BCR4BP source-layer promotion with rendered figure artifacts,
not a claim that every original thesis application figure has been replaced.
The per-original-figure mapping is recorded in
`data/computed/chapter5_per_figure_source_layer_audit.csv` and
`docs/chapter5_per_figure_source_layer_audit.md`; gate
`C5-PER-FIGURE-SOURCE-LAYER-AUDIT` must pass before Chapter 5 status summaries
are treated as figure-by-figure rather than aggregate-only.
For Fig. 5.10 and Fig. 5.11 specifically, the CR3BP endpoint-corrected transfer
rows are recorded in `data/computed/chapter5_nrho_transfer_per_figure_audit.csv`
and `docs/chapter5_nrho_transfer_per_figure_audit.md`; these rows strengthen
the per-figure transfer evidence without claiming BCR4BP/ephemeris equivalence.
For Fig. 5.13 and Fig. 5.14, the Sun-Earth CR3BP stable-manifold periapsis and
transfer-scene rows are recorded in
`data/computed/chapter5_stable_manifold_per_figure_audit.csv` and
`docs/chapter5_stable_manifold_per_figure_audit.md`; these rows strengthen the
per-figure application evidence without claiming full quasi-periodic Lissajous
or ephemeris equivalence.
""",
        encoding="utf-8",
    )


def main() -> None:
    rows = _build_rows()
    _write_rows(rows)
    _write_doc(rows)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    c3 = next(row for row in rows if row["gate_id"] == "C3-FIGURE-SOURCE-FRONTIER")
    c4 = next(row for row in rows if row["gate_id"] == "C4-UPSTREAM-TORUS-DATA")
    goal = next(row for row in rows if row["gate_id"] == "STAGED-GOAL-STATUS")
    print(
        "staged goal gate audit: "
        f"chapter3_frontier={float(c3['value']):.6f} km, "
        f"chapter4_status={c4['status']}, goal_status={goal['status']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
