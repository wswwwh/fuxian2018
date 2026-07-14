"""Build a per-figure Chapter 5 source-layer audit.

Chapter 5 now has aggregate Route H, DE421-oriented, BCR4BP, correction, and
optimized-transfer evidence. This script maps those aggregate gates back to the
original Fig. 5.1-5.14 targets without overclaiming that a source-layer result
replaces every original thesis application figure.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "computed"
DOCS = PROJECT_ROOT / "docs"
FIGURES_PNG = PROJECT_ROOT / "outputs" / "figures_png"
FIGURES_PDF = PROJECT_ROOT / "outputs" / "figures_pdf"

FIGURE_VALIDATION = DATA / "figure_validation_table.csv"
UPSTREAM_AUDIT = DATA / "chapter5_upstream_application_gate_audit.csv"
SUN_EARTH_L1_LONG_PROP_AUDIT = DATA / "chapter5_sun_earth_l1_long_propagation_per_figure_audit.csv"
READINESS_AUDIT = DATA / "chapter5_high_fidelity_optimization_readiness_audit.csv"
BCR4BP_DYNAMICS_AUDIT = DATA / "chapter5_bcr4bp_dynamics_audit.csv"
BCR4BP_CORRECTION_AUDIT = DATA / "chapter5_bcr4bp_segment_correction_audit.csv"
FIG510_BCR4BP_AUDIT = DATA / "chapter5_fig510_bcr4bp_transfer_audit.csv"
FIG510_BCR4BP_TRAJECTORIES = DATA / "chapter5_fig510_bcr4bp_transfer_trajectories.csv"
FIG510_BCR4BP_REPORT = DOCS / "chapter5_fig510_bcr4bp_transfer_audit.md"
FIG510_PUBLIC_SOURCE_NOTE = DOCS / "chapter5_fig510_public_source_anchors.md"
FIG510_BCR4BP_RERUN_REPORT = (
    DOCS / "chapter5_fig510_bcr4bp_independent_rerun_audit.md"
)
FIG510_BCR4BP_DIAGNOSTIC_PNG = (
    PROJECT_ROOT / "outputs" / "diagnostics" / "fig_5_10_bcr4bp_extension.png"
)
FIG510_BCR4BP_DIAGNOSTIC_PDF = (
    PROJECT_ROOT / "outputs" / "diagnostics" / "fig_5_10_bcr4bp_extension.pdf"
)
OPTIMIZED_TRANSFER_AUDIT = DATA / "chapter5_optimized_transfer_audit.csv"
HALO_LYAPUNOV_TRANSFER_AUDIT = DATA / "chapter5_halo_lyapunov_transfer_per_figure_audit.csv"
NRHO_CORRIDOR_AUDIT = DATA / "chapter5_nrho_corridor_per_figure_audit.csv"
NRHO_TRANSFER_AUDIT = DATA / "chapter5_nrho_transfer_per_figure_audit.csv"
NRHO_RENDEZVOUS_AUDIT = DATA / "chapter5_nrho_rendezvous_per_figure_audit.csv"
STABLE_MANIFOLD_AUDIT = DATA / "chapter5_stable_manifold_per_figure_audit.csv"
LISSAJOUS_TORUS_AUDIT = DATA / "chapter5_sun_earth_l1_lissajous_torus_audit.csv"
LISSAJOUS_MANIFOLD_AUDIT = DATA / "chapter5_sun_earth_l1_lissajous_stable_manifold_audit.csv"
LISSAJOUS_LEO_TRANSFER_AUDIT = DATA / "chapter5_sun_earth_l1_lissajous_leo_transfer_audit.csv"
LISSAJOUS_AMPLITUDE_AUDIT = DATA / "chapter5_sun_earth_l1_lissajous_amplitude_boundary_audit.csv"
ACTIVE_GEOMETRY_FAMILY_AUDIT = DATA / "chapter5_sun_earth_l1_active_geometry_family_audit.csv"
ACTIVE_GEOMETRY_MANIFOLD_AUDIT = DATA / "chapter5_active_geometry_stable_manifold_tight_target_audit.csv"
ACTIVE_GEOMETRY_LEO_TRANSFER_AUDIT = DATA / "chapter5_active_geometry_leo_transfer_audit.csv"
ACTIVE_GEOMETRY_APPLICATION_RERUN = DOCS / "chapter5_active_geometry_application_independent_rerun_audit.md"
ROUTE_H_FAMILY = DATA / "chapter3_fixed_mapping_cache_accepted_family.csv"
ROUTE_H_VALIDATION = DATA / "chapter3_fixed_mapping_cache_accepted_validation.csv"
CHAPTER4_ROUTE_H_FIGURE = PROJECT_ROOT / "outputs" / "figures_png" / "fig_4_route_h.png"

OUT_CSV = DATA / "chapter5_per_figure_source_layer_audit.csv"
OUT_MD = DOCS / "chapter5_per_figure_source_layer_audit.md"

FIELDS = [
    "figure_id",
    "source_page",
    "script",
    "current_source_layer",
    "current_repro_level",
    "original_replacement_status",
    "uses_proxy",
    "primary_evidence",
    "supporting_evidence",
    "rendered_png",
    "rendered_png_bytes",
    "rendered_pdf",
    "rendered_pdf_bytes",
    "route_h_dependency",
    "bcr4bp_dependency",
    "optimization_dependency",
    "accepted_rows",
    "best_metric",
    "boundary",
    "next_action",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def _rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _exists_rel(path: Path) -> str:
    return _rel(path) if path.exists() else ""


def _size(path: Path) -> str:
    return str(path.stat().st_size) if path.exists() else "0"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "pass", "passed", "1", "yes"}


def _is_original_chapter5_figure(figure_id: str) -> bool:
    return figure_id.startswith("5.") and figure_id[2:].isdigit()


def _md_cell(value: str) -> str:
    return value.replace("|", r"\|")


def _count_truthy(path: Path, field: str) -> int:
    return sum(_truthy(row.get(field)) for row in _read_csv(path))


def _best_optimized_transfer() -> dict[str, str]:
    accepted = [
        row for row in _read_csv(OPTIMIZED_TRANSFER_AUDIT) if _truthy(row.get("optimization_acceptance"))
    ]
    if not accepted:
        return {}
    return min(accepted, key=lambda row: float(row["delta_v_m_s"]))


def _route_h_summary() -> dict[str, str]:
    rows = _read_csv(ROUTE_H_VALIDATION)
    best = max(rows, key=lambda row: float(row["max_abs_z_km"]))
    return {
        "rows": str(len(rows)),
        "member": best["member"],
        "max_abs_z_km": f"{float(best['max_abs_z_km']):.16g}",
        "max_residual": f"{max(float(row['map_residual_norm']) for row in rows):.16g}",
    }


def _validation_lookup() -> dict[str, dict[str, str]]:
    return {row["figure_id"]: row for row in _read_csv(FIGURE_VALIDATION)}


def _figure_artifacts(figure_id: str) -> dict[str, str]:
    suffix = figure_id.replace(".", "_")
    png = FIGURES_PNG / f"fig_{suffix}.png"
    pdf = FIGURES_PDF / f"fig_{suffix}.pdf"
    return {
        "rendered_png": _exists_rel(png),
        "rendered_png_bytes": _size(png),
        "rendered_pdf": _exists_rel(pdf),
        "rendered_pdf_bytes": _size(pdf),
    }


def _source_metrics() -> dict[str, str]:
    best = _best_optimized_transfer()
    route_h = _route_h_summary()
    bcr4bp_rows = _count_truthy(BCR4BP_DYNAMICS_AUDIT, "acceptance")
    correction_rows = _count_truthy(BCR4BP_CORRECTION_AUDIT, "correction_acceptance")
    optimized_rows = _count_truthy(OPTIMIZED_TRANSFER_AUDIT, "optimization_acceptance")
    l1_long_rows = [row for row in _read_csv(SUN_EARTH_L1_LONG_PROP_AUDIT) if _truthy(row.get("acceptance"))] if SUN_EARTH_L1_LONG_PROP_AUDIT.exists() else []
    nrho_rows = [row for row in _read_csv(NRHO_TRANSFER_AUDIT) if _truthy(row.get("acceptance"))] if NRHO_TRANSFER_AUDIT.exists() else []
    nrho_by_figure: dict[str, list[dict[str, str]]] = {}
    for row in nrho_rows:
        nrho_by_figure.setdefault(row["figure_id"], []).append(row)
    rendezvous_rows = [row for row in _read_csv(NRHO_RENDEZVOUS_AUDIT) if _truthy(row.get("acceptance"))] if NRHO_RENDEZVOUS_AUDIT.exists() else []
    rendezvous_by_figure: dict[str, list[dict[str, str]]] = {}
    for row in rendezvous_rows:
        rendezvous_by_figure.setdefault(row["figure_id"], []).append(row)
    stable_rows = [row for row in _read_csv(STABLE_MANIFOLD_AUDIT) if _truthy(row.get("acceptance"))] if STABLE_MANIFOLD_AUDIT.exists() else []
    stable_by_figure: dict[str, list[dict[str, str]]] = {}
    for row in stable_rows:
        stable_by_figure.setdefault(row["figure_id"], []).append(row)
    halo_lyapunov_rows = [row for row in _read_csv(HALO_LYAPUNOV_TRANSFER_AUDIT) if _truthy(row.get("acceptance"))] if HALO_LYAPUNOV_TRANSFER_AUDIT.exists() else []
    nrho_corridor_rows = [row for row in _read_csv(NRHO_CORRIDOR_AUDIT) if _truthy(row.get("acceptance"))] if NRHO_CORRIDOR_AUDIT.exists() else []
    lissajous_rows = [row for row in _read_csv(LISSAJOUS_TORUS_AUDIT) if _truthy(row.get("source_acceptance"))] if LISSAJOUS_TORUS_AUDIT.exists() else []
    lissajous_manifold_rows = [row for row in _read_csv(LISSAJOUS_MANIFOLD_AUDIT) if _truthy(row.get("acceptance"))] if LISSAJOUS_MANIFOLD_AUDIT.exists() else []
    lissajous_leo_rows = [row for row in _read_csv(LISSAJOUS_LEO_TRANSFER_AUDIT) if _truthy(row.get("acceptance"))] if LISSAJOUS_LEO_TRANSFER_AUDIT.exists() else []
    active_family_rows = _read_csv(ACTIVE_GEOMETRY_FAMILY_AUDIT) if ACTIVE_GEOMETRY_FAMILY_AUDIT.exists() else []
    active_manifold_rows = [row for row in _read_csv(ACTIVE_GEOMETRY_MANIFOLD_AUDIT) if _truthy(row.get("acceptance"))] if ACTIVE_GEOMETRY_MANIFOLD_AUDIT.exists() else []
    active_leo_rows = [row for row in _read_csv(ACTIVE_GEOMETRY_LEO_TRANSFER_AUDIT) if _truthy(row.get("acceptance"))] if ACTIVE_GEOMETRY_LEO_TRANSFER_AUDIT.exists() else []
    fig510_bcr4bp_all = _read_csv(FIG510_BCR4BP_AUDIT) if FIG510_BCR4BP_AUDIT.exists() else []
    fig510_bcr4bp_rows = [
        row for row in fig510_bcr4bp_all if _truthy(row.get("numerical_acceptance"))
    ]
    fig510_bcr4bp_paper_rows = [
        row for row in fig510_bcr4bp_all if _truthy(row.get("paper_equivalence"))
    ]
    fig510_bcr4bp_ordered = sorted(
        fig510_bcr4bp_all,
        key=lambda row: int(row["case_id"]),
    )
    return {
        "route_h_rows": route_h["rows"],
        "route_h_member": route_h["member"],
        "route_h_max_abs_z_km": route_h["max_abs_z_km"],
        "route_h_max_residual": route_h["max_residual"],
        "bcr4bp_rows": str(bcr4bp_rows),
        "correction_rows": str(correction_rows),
        "optimized_rows": str(optimized_rows),
        "best_delta_v_m_s": f"{float(best['delta_v_m_s']):.16g}" if best else "N/A",
        "best_defect": f"{float(best['corrected_position_defect']):.16g}" if best else "N/A",
        "best_member": best.get("route_h_member", "N/A"),
        "best_phase": best.get("phase_index", "N/A"),
        "best_tof_days": best.get("time_of_flight_days", "N/A"),
        "l1_long_rows": str(len(l1_long_rows)),
        "l1_long_duration": _max_field(l1_long_rows, "duration_days"),
        "l1_long_max_jacobi": _max_field(l1_long_rows, "jacobi_span"),
        "l1_long_min_transverse_span": _min_field(l1_long_rows, "transverse_span"),
        "l1_long_max_l1_distance": _max_field(l1_long_rows, "max_l1_distance_km"),
        "nrho_5_10_rows": str(len(nrho_by_figure.get("5.10", []))),
        "nrho_5_11_rows": str(len(nrho_by_figure.get("5.11", []))),
        "nrho_5_10_best_delta_v": _best_delta_v(nrho_by_figure.get("5.10", [])),
        "nrho_5_11_best_delta_v": _best_delta_v(nrho_by_figure.get("5.11", [])),
        "nrho_5_10_worst_endpoint_error": _worst_endpoint_error(nrho_by_figure.get("5.10", [])),
        "nrho_5_11_worst_endpoint_error": _worst_endpoint_error(nrho_by_figure.get("5.11", [])),
        "nrho_5_10_max_jacobi_span": _max_jacobi_span(nrho_by_figure.get("5.10", [])),
        "nrho_5_11_max_jacobi_span": _max_jacobi_span(nrho_by_figure.get("5.11", [])),
        "fig510_bcr4bp_rows": str(len(fig510_bcr4bp_rows)),
        "fig510_bcr4bp_paper_rows": str(len(fig510_bcr4bp_paper_rows)),
        "fig510_bcr4bp_max_endpoint_km": _max_field(
            fig510_bcr4bp_rows,
            "independent_endpoint_error_km",
        ),
        "fig510_bcr4bp_max_segment_km": _max_field(
            fig510_bcr4bp_rows,
            "segment_max_position_defect_km",
        ),
        "fig510_bcr4bp_reset_control_km": _min_field(
            fig510_bcr4bp_rows,
            "reset_time_negative_control_position_defect_km",
        ),
        "fig510_bcr4bp_total_delta_v": "/".join(
            f"{float(row['total_delta_v_m_s']):.6f}"
            for row in fig510_bcr4bp_ordered
        ) or "N/A",
        "fig510_bcr4bp_paper_relative_error": "/".join(
            f"{100.0 * float(row['total_delta_v_relative_error']):+.4f}%"
            for row in fig510_bcr4bp_ordered
        ) or "N/A",
        "fig510_bcr4bp_sun_phase_deg": _max_field(
            fig510_bcr4bp_all,
            "sun_phase_deg",
        ),
        "rendezvous_5_12_rows": str(len(rendezvous_by_figure.get("5.12", []))),
        "rendezvous_5_12_left_coverage": _min_field(rendezvous_by_figure.get("5.12", []), "arrival_offset_hours"),
        "rendezvous_5_12_right_coverage": _max_field(rendezvous_by_figure.get("5.12", []), "arrival_offset_hours"),
        "rendezvous_5_12_min_delta_v_diff": _min_field(rendezvous_by_figure.get("5.12", []), "delta_v_difference_m_s"),
        "rendezvous_5_12_max_endpoint_error": _max_field(rendezvous_by_figure.get("5.12", []), "endpoint_position_error_km"),
        "stable_5_13_rows": str(len(stable_by_figure.get("5.13", []))),
        "stable_5_14_rows": str(len(stable_by_figure.get("5.14", []))),
        "stable_5_13_periapsis_error": _max_field(stable_by_figure.get("5.13", []), "periapsis_error_km"),
        "stable_5_14_periapsis_error": _max_field(stable_by_figure.get("5.14", []), "periapsis_error_km"),
        "stable_5_13_jacobi_span": _max_field(stable_by_figure.get("5.13", []), "jacobi_span"),
        "stable_5_14_jacobi_span": _max_field(stable_by_figure.get("5.14", []), "jacobi_span"),
        "stable_5_13_transfer_time": _max_field(stable_by_figure.get("5.13", []), "transfer_time_days"),
        "stable_5_14_transfer_time": _max_field(stable_by_figure.get("5.14", []), "transfer_time_days"),
        "stable_5_13_phase": _max_field(stable_by_figure.get("5.13", []), "selected_phase_deg"),
        "stable_5_14_phase": _max_field(stable_by_figure.get("5.14", []), "selected_phase_deg"),
        "halo_lyapunov_rows": str(len(halo_lyapunov_rows)),
        "halo_lyapunov_total_delta_v": _max_field(halo_lyapunov_rows, "total_delta_v_m_s"),
        "halo_lyapunov_endpoint_error": _max_field(halo_lyapunov_rows, "endpoint_position_error_km"),
        "halo_lyapunov_continuity": _max_field(halo_lyapunov_rows, "maximum_continuity_error"),
        "halo_lyapunov_jacobi_span": _max_field(halo_lyapunov_rows, "jacobi_span"),
        "halo_lyapunov_boundary_jacobi": _max_field(halo_lyapunov_rows, "boundary_jacobi_difference"),
        "nrho_corridor_rows": str(len(nrho_corridor_rows)),
        "nrho_corridor_best_delta_v": _best_delta_v(nrho_corridor_rows),
        "nrho_corridor_worst_endpoint_error": _worst_endpoint_error(nrho_corridor_rows),
        "nrho_corridor_max_jacobi_span": _max_jacobi_span(nrho_corridor_rows),
        "nrho_corridor_departure_perilune": _max_field(nrho_corridor_rows, "departure_perilune_radius_km"),
        "nrho_corridor_destination_perilune": _max_field(nrho_corridor_rows, "destination_perilune_radius_km"),
        "nrho_corridor_members": _max_field(nrho_corridor_rows, "corridor_family_members"),
        "nrho_corridor_max_periodicity": _max_field(nrho_corridor_rows, "corridor_max_periodicity_error"),
        "lissajous_source_rows": str(len(lissajous_rows)),
        "lissajous_points": _max_field(lissajous_rows, "rendered_torus_points"),
        "lissajous_residual": _max_field(lissajous_rows, "curve_residual_norm"),
        "lissajous_jacobi_span": _max_field(lissajous_rows, "torus_jacobi_span"),
        "lissajous_y_km": _max_field(lissajous_rows, "max_abs_y_km"),
        "lissajous_z_km": _max_field(lissajous_rows, "max_abs_z_km"),
        "lissajous_manifold_rows": str(len(lissajous_manifold_rows)),
        "lissajous_manifold_trajectories": _max_field(lissajous_manifold_rows, "manifold_trajectories"),
        "lissajous_manifold_target_error": _max_field(lissajous_manifold_rows, "best_7033_error_km"),
        "lissajous_manifold_jacobi_drift": _max_field(lissajous_manifold_rows, "maximum_jacobi_drift"),
        "lissajous_leo_rows": str(len(lissajous_leo_rows)),
        "lissajous_leo_samples": _max_field(lissajous_leo_rows, "trajectory_samples"),
        "lissajous_leo_time": _max_field(lissajous_leo_rows, "transfer_time_days"),
        "lissajous_leo_periapsis_error": _max_field(lissajous_leo_rows, "periapsis_target_error_km"),
        "lissajous_leo_jacobi_span": _max_field(lissajous_leo_rows, "jacobi_span"),
        "lissajous_leo_endpoint": _max_field(lissajous_leo_rows, "lissajous_endpoint_distance_km"),
        "active_geometry_source_rows": str(len(active_family_rows)),
        "active_geometry_points": (
            str(int(active_family_rows[0]["event_time_slices"]) * int(active_family_rows[0]["event_phase_samples"]))
            if active_family_rows else "N/A"
        ),
        "active_geometry_members": _max_field(active_family_rows, "accepted_members"),
        "active_geometry_y_km": _max_field(active_family_rows, "max_abs_y_km"),
        "active_geometry_z_km": _max_field(active_family_rows, "max_abs_z_km"),
        "active_geometry_y_error": _max_field(active_family_rows, "y_target_error_km"),
        "active_geometry_z_error": _max_field(active_family_rows, "z_target_error_km"),
        "active_geometry_jacobi_span": _max_field(active_family_rows, "jacobi_span"),
        "active_geometry_closure": _max_field(active_family_rows, "closure_residual"),
        "active_geometry_target_pair": (
            active_family_rows[0].get("target_pair_accepted", "false") if active_family_rows else "false"
        ),
        "active_manifold_rows": str(len(active_manifold_rows)),
        "active_manifold_trajectories": _max_field(active_manifold_rows, "manifold_trajectories"),
        "active_manifold_target": _max_field(active_manifold_rows, "best_7033_radius_km"),
        "active_manifold_target_error": _max_field(active_manifold_rows, "best_7033_error_km"),
        "active_manifold_jacobi_drift": _max_field(active_manifold_rows, "maximum_jacobi_drift"),
        "active_manifold_phase0": _max_field(active_manifold_rows, "best_theta0_deg"),
        "active_manifold_phase1": _max_field(active_manifold_rows, "best_theta1_deg"),
        "active_leo_rows": str(len(active_leo_rows)),
        "active_leo_samples": _max_field(active_leo_rows, "trajectory_samples"),
        "active_leo_time": _max_field(active_leo_rows, "transfer_time_days"),
        "active_leo_periapsis": _max_field(active_leo_rows, "periapsis_radius_km"),
        "active_leo_periapsis_error": _max_field(active_leo_rows, "periapsis_target_error_km"),
        "active_leo_jacobi_span": _max_field(active_leo_rows, "jacobi_span"),
        "active_leo_endpoint": _max_field(active_leo_rows, "lissajous_endpoint_distance_km"),
    }


def _best_delta_v(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "N/A"
    return f"{min(float(row['total_delta_v_m_s']) for row in rows):.16g}"


def _worst_endpoint_error(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "N/A"
    return f"{max(float(row['endpoint_position_error_km']) for row in rows):.16g}"


def _max_jacobi_span(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "N/A"
    return f"{max(float(row['jacobi_span']) for row in rows):.16g}"


def _max_field(rows: list[dict[str, str]], field: str) -> str:
    if not rows:
        return "N/A"
    return f"{max(float(row[field]) for row in rows):.16g}"


def _min_field(rows: list[dict[str, str]], field: str) -> str:
    if not rows:
        return "N/A"
    return f"{min(float(row[field]) for row in rows):.16g}"


def _specs(metrics: dict[str, str]) -> list[dict[str, str]]:
    route_h_source = f"{_rel(ROUTE_H_FAMILY)};{_rel(ROUTE_H_VALIDATION)}"
    bcr4bp_source = (
        f"{_rel(BCR4BP_DYNAMICS_AUDIT)};{_rel(BCR4BP_CORRECTION_AUDIT)};"
        f"{_rel(OPTIMIZED_TRANSFER_AUDIT)}"
    )
    route_h_metric = (
        f"Route H member {metrics['route_h_member']} max |z| "
        f"{metrics['route_h_max_abs_z_km']} km; residual <= {metrics['route_h_max_residual']}"
    )
    optimized_metric = (
        f"{metrics['optimized_rows']} accepted optimized rows; best delta-v "
        f"{metrics['best_delta_v_m_s']} m/s; corrected defect {metrics['best_defect']}; "
        f"member {metrics['best_member']} phase {metrics['best_phase']} TOF "
        f"{metrics['best_tof_days']} days"
    )
    return [
        {
            "figure_id": "5.1",
            "current_source_layer": "corrected Sun-Earth L1 two-frequency Lissajous torus trajectories",
            "current_repro_level": "numerical corrected Lissajous propagation reproduction",
            "original_replacement_status": "corrected_lissajous_torus_replaces_proxy_long_propagation_scene",
            "uses_proxy": "false",
            "primary_evidence": "data/computed/chapter5_sun_earth_l1_lissajous_torus_surface.csv",
            "supporting_evidence": f"{_rel(LISSAJOUS_TORUS_AUDIT)};{_rel(LISSAJOUS_AMPLITUDE_AUDIT)};{_rel(SUN_EARTH_L1_LONG_PROP_AUDIT)}",
            "route_h_dependency": "none",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": metrics["lissajous_source_rows"],
            "best_metric": (
                f"accepted corrected Lissajous source rows {metrics['lissajous_source_rows']}; "
                f"torus points {metrics['lissajous_points']}; "
                f"curve residual {metrics['lissajous_residual']}; "
                f"Jacobi span {metrics['lissajous_jacobi_span']}; "
                f"max |y|/|z| {metrics['lissajous_y_km']}/{metrics['lissajous_z_km']} km"
            ),
            "boundary": "The analytic torus and center-mode overlays are removed. Remaining boundaries are the source-torus y-amplitude excess and pointwise thesis comparison.",
            "next_action": "Reduce the corrected torus y-amplitude discrepancy and digitize the thesis panels for pointwise comparison.",
        },
        {
            "figure_id": "5.2",
            "current_source_layer": "mission-geometry schematic",
            "current_repro_level": "proxy/schematic only",
            "original_replacement_status": "schematic_complete",
            "uses_proxy": "true",
            "primary_evidence": "geometry schematic",
            "supporting_evidence": "",
            "route_h_dependency": "none",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": "0",
            "best_metric": "N/A",
            "boundary": "No numerical source-layer is required for the current schematic role.",
            "next_action": "No numerical upgrade needed unless the thesis artwork must be redrawn exactly.",
        },
        {
            "figure_id": "5.3",
            "current_source_layer": "mission-geometry schematic",
            "current_repro_level": "proxy/schematic only",
            "original_replacement_status": "schematic_complete",
            "uses_proxy": "true",
            "primary_evidence": "geometry schematic",
            "supporting_evidence": "",
            "route_h_dependency": "none",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": "0",
            "best_metric": "N/A",
            "boundary": "No numerical source-layer is required for the current schematic role.",
            "next_action": "No numerical upgrade needed unless the thesis artwork must be redrawn exactly.",
        },
        {
            "figure_id": "5.4",
            "current_source_layer": "mission-geometry schematic",
            "current_repro_level": "proxy/schematic only",
            "original_replacement_status": "schematic_complete",
            "uses_proxy": "true",
            "primary_evidence": "geometry schematic",
            "supporting_evidence": "",
            "route_h_dependency": "none",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": "0",
            "best_metric": "N/A",
            "boundary": "No numerical source-layer is required for the current schematic role.",
            "next_action": "No numerical upgrade needed unless the thesis artwork must be redrawn exactly.",
        },
        {
            "figure_id": "5.5",
            "current_source_layer": "corrected DRO and quasi-DRO return CR3BP baseline",
            "current_repro_level": "physical-consistency baseline",
            "original_replacement_status": "baseline_not_high_fidelity_replacement",
            "uses_proxy": "false",
            "primary_evidence": "data/computed/chapter5_corrected_dro_quasi_dro_return.csv",
            "supporting_evidence": route_h_source,
            "route_h_dependency": "supporting upstream only",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": metrics["route_h_rows"],
            "best_metric": route_h_metric,
            "boundary": "CR3BP return evidence does not yet provide a corrected ephemeris/BCR4BP trajectory replacement.",
            "next_action": "Promote only after a corrected ephemeris or BCR4BP return arc is accepted for this specific figure.",
        },
        {
            "figure_id": "5.6",
            "current_source_layer": "Route H quasi-DRO embedded in DE421-oriented Sun-Moon frame",
            "current_repro_level": "Route H / DE421 geometry baseline",
            "original_replacement_status": "source_layer_baseline_not_full_ephemeris_replacement",
            "uses_proxy": "false",
            "primary_evidence": "data/computed/chapter5_de421_quasi_dro_scenes.csv",
            "supporting_evidence": f"{route_h_source};{_rel(UPSTREAM_AUDIT)}",
            "route_h_dependency": "accepted Route H upstream member",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": metrics["route_h_rows"],
            "best_metric": route_h_metric,
            "boundary": "DE421-oriented frame embedding is a geometry baseline, not a fully corrected ephemeris shooting solution.",
            "next_action": "Add ephemeris/BCR4BP defect correction before claiming original application-figure replacement.",
        },
        {
            "figure_id": "5.7",
            "current_source_layer": "Route H quasi-DRO eclipse/occultation scene in DE421-oriented frame",
            "current_repro_level": "Route H / DE421 geometry baseline",
            "original_replacement_status": "source_layer_baseline_not_full_ephemeris_replacement",
            "uses_proxy": "false",
            "primary_evidence": "data/computed/chapter5_de421_quasi_dro_scenes.csv",
            "supporting_evidence": f"{route_h_source};{_rel(UPSTREAM_AUDIT)}",
            "route_h_dependency": "accepted Route H upstream member",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": metrics["route_h_rows"],
            "best_metric": route_h_metric,
            "boundary": "DE421-oriented event geometry is available, but not a fully corrected ephemeris trajectory.",
            "next_action": "Add ephemeris/BCR4BP defect correction before claiming original application-figure replacement.",
        },
        {
            "figure_id": "5.8",
            "current_source_layer": "Earth-Moon equal-Jacobi halo-to-Lyapunov multiple-shooting transfer",
            "current_repro_level": "numerical equal-Jacobi multiple-shooting transfer reproduction",
            "original_replacement_status": "computed_multiple_shooting_transfer_replaces_corridor_proxy_high_fidelity_pending",
            "uses_proxy": "false",
            "primary_evidence": "data/computed/chapter5_earth_moon_halo_lyapunov_transfer_baseline.csv",
            "supporting_evidence": f"{_rel(HALO_LYAPUNOV_TRANSFER_AUDIT)};{bcr4bp_source}",
            "route_h_dependency": "accepted Route H upstream member for separate source-layer figure",
            "bcr4bp_dependency": f"{metrics['bcr4bp_rows']} dynamics audit rows; {metrics['correction_rows']} correction rows",
            "optimization_dependency": f"{metrics['optimized_rows']} accepted optimized transfer rows",
            "accepted_rows": metrics["halo_lyapunov_rows"],
            "best_metric": (
                f"accepted CR3BP halo-Lyapunov transfer rows {metrics['halo_lyapunov_rows']}; "
                f"total delta-v {metrics['halo_lyapunov_total_delta_v']} m/s; "
                f"endpoint error {metrics['halo_lyapunov_endpoint_error']} km; "
                f"continuity {metrics['halo_lyapunov_continuity']}; "
                f"Jacobi span {metrics['halo_lyapunov_jacobi_span']}; "
                f"boundary Jacobi difference {metrics['halo_lyapunov_boundary_jacobi']}"
            ),
            "boundary": "The linear corridor proxy is removed and replaced by the accepted transfer trajectory and patch nodes. BCR4BP/ephemeris correction and original-thesis pointwise comparison remain pending.",
            "next_action": "Correct this specific 186.9-day transfer in BCR4BP/ephemeris and compare it with the thesis delta-v and geometry.",
        },
        {
            "figure_id": "5.9",
            "current_source_layer": "Earth-Moon corrected periodic-NRHO family with transfer departure markers",
            "current_repro_level": "CR3BP corrected periodic-family reproduction",
            "original_replacement_status": "corrected_periodic_nrho_family_replaces_linear_corridor_proxy",
            "uses_proxy": "false",
            "primary_evidence": "data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv",
            "supporting_evidence": f"{_rel(NRHO_CORRIDOR_AUDIT)};{bcr4bp_source}",
            "route_h_dependency": "indirect only",
            "bcr4bp_dependency": "available as separate source-layer audit",
            "optimization_dependency": "available as separate source-layer audit",
            "accepted_rows": metrics["nrho_corridor_rows"],
            "best_metric": (
                f"accepted CR3BP periodic-family marker rows {metrics['nrho_corridor_rows']}; "
                f"corrected family members {metrics['nrho_corridor_members']}; "
                f"maximum periodicity error {metrics['nrho_corridor_max_periodicity']}; "
                f"best total delta-v {metrics['nrho_corridor_best_delta_v']} m/s; "
                f"worst endpoint error {metrics['nrho_corridor_worst_endpoint_error']} km; "
                f"max Jacobi span {metrics['nrho_corridor_max_jacobi_span']}; "
                f"perilune radii {metrics['nrho_corridor_departure_perilune']} / "
                f"{metrics['nrho_corridor_destination_perilune']} km"
            ),
            "boundary": "The linear corridor proxy is removed. The displayed family is corrected CR3BP periodic NRHOs; BCR4BP/ephemeris correction and pointwise thesis comparison remain pending.",
            "next_action": "Correct representative family members in BCR4BP/ephemeris and compare the family geometry pointwise with the thesis panel.",
        },
        {
            "figure_id": "5.10",
            "current_source_layer": "Earth-Moon NRHO CR3BP transfers plus DE421-initialized planar BCR4BP correction",
            "current_repro_level": "CR3BP transfer reproduction with numerical BCR4BP extension and paper-equivalence boundary",
            "original_replacement_status": "cr3bp_transfer_plus_bcr4bp_extension_accepted_paper_equivalence_false",
            "uses_proxy": "false",
            "primary_evidence": (
                f"{_rel(FIG510_BCR4BP_AUDIT)};"
                f"{_rel(FIG510_BCR4BP_TRAJECTORIES)};"
                "data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv"
            ),
            "supporting_evidence": (
                f"{_rel(NRHO_TRANSFER_AUDIT)};{_rel(FIG510_BCR4BP_REPORT)};"
                f"{_rel(FIG510_PUBLIC_SOURCE_NOTE)};"
                f"{_rel(FIG510_BCR4BP_RERUN_REPORT)};"
                f"{_exists_rel(FIG510_BCR4BP_DIAGNOSTIC_PNG)};"
                f"{_exists_rel(FIG510_BCR4BP_DIAGNOSTIC_PDF)};{bcr4bp_source}"
            ),
            "route_h_dependency": "indirect only",
            "bcr4bp_dependency": (
                f"dedicated numerical correction {metrics['fig510_bcr4bp_rows']}/2; "
                f"paper equivalence {metrics['fig510_bcr4bp_paper_rows']}/2"
            ),
            "optimization_dependency": "velocity-corrected endpoint match accepted; thesis impulse agreement remains open",
            "accepted_rows": metrics["fig510_bcr4bp_rows"],
            "best_metric": (
                f"BCR4BP numerical acceptance {metrics['fig510_bcr4bp_rows']}/2; "
                f"paper equivalence {metrics['fig510_bcr4bp_paper_rows']}/2; "
                f"independent endpoint <= {metrics['fig510_bcr4bp_max_endpoint_km']} km; "
                f"absolute-time segment defect <= {metrics['fig510_bcr4bp_max_segment_km']} km; "
                f"reset-time negative control >= {metrics['fig510_bcr4bp_reset_control_km']} km; "
                f"total delta-v case 1/2 {metrics['fig510_bcr4bp_total_delta_v']} m/s; "
                f"paper-relative error {metrics['fig510_bcr4bp_paper_relative_error']}; "
                f"DE421 initial Sun phase {metrics['fig510_bcr4bp_sun_phase_deg']} deg"
            ),
            "boundary": "The dedicated planar BCR4BP extension is numerically accepted, but Figure 5.10 is an autonomous CR3BP case, so epoch is not applicable to the paper result and the project date belongs only to the extension. The paper-specific quasi-NRHO member, intersection phases, raw boundary states, impulse agreement, and pointwise geometry remain open, so paper_equivalence=false.",
            "next_action": "Continue the rp=8065 km, frequency-ratio=5.0305 constant-frequency quasi-NRHO family, recover the two intersection phases and boundary states, then optimize the impulse split and run a locked-projection audit.",
        },
        {
            "figure_id": "5.11",
            "current_source_layer": "Earth-Moon NRHO direct-transfer CR3BP baseline",
            "current_repro_level": "CR3BP endpoint-corrected NRHO transfer audit",
            "original_replacement_status": "endpoint_corrected_cr3bp_not_high_fidelity_replacement",
            "uses_proxy": "false",
            "primary_evidence": "data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv",
            "supporting_evidence": f"{_rel(NRHO_TRANSFER_AUDIT)};{bcr4bp_source}",
            "route_h_dependency": "indirect only",
            "bcr4bp_dependency": "available as separate source-layer audit",
            "optimization_dependency": "available as separate source-layer audit",
            "accepted_rows": metrics["nrho_5_11_rows"],
            "best_metric": (
                f"accepted CR3BP reverse-symmetry rows {metrics['nrho_5_11_rows']}; "
                f"best total delta-v {metrics['nrho_5_11_best_delta_v']} m/s; "
                f"worst endpoint error {metrics['nrho_5_11_worst_endpoint_error']} km; "
                f"max Jacobi span {metrics['nrho_5_11_max_jacobi_span']}"
            ),
            "boundary": "Per-figure endpoint-corrected CR3BP transfer rows are accepted by exact symmetry, but no BCR4BP/ephemeris high-fidelity replacement is claimed.",
            "next_action": "Promote further only after the specific Fig. 5.11 transfer is corrected in BCR4BP/ephemeris and compared to thesis delta-v.",
        },
        {
            "figure_id": "5.12",
            "current_source_layer": "Earth-Moon NRHO fixed-departure rendezvous arrival-offset branch",
            "current_repro_level": "numerical CR3BP rendezvous-branch reproduction",
            "original_replacement_status": "computed_branch_replaces_proxy_with_explicit_fold_boundary",
            "uses_proxy": "false",
            "primary_evidence": "data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv",
            "supporting_evidence": _rel(NRHO_RENDEZVOUS_AUDIT),
            "route_h_dependency": "none",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": metrics["rendezvous_5_12_rows"],
            "best_metric": (
                f"accepted CR3BP rendezvous scan rows {metrics['rendezvous_5_12_rows']}; "
                f"coverage {metrics['rendezvous_5_12_left_coverage']} to "
                f"{metrics['rendezvous_5_12_right_coverage']} h; "
                f"minimum delta-v difference {metrics['rendezvous_5_12_min_delta_v_diff']} m/s; "
                f"maximum endpoint error {metrics['rendezvous_5_12_max_endpoint_error']} km"
            ),
            "boundary": "The grey extrapolation is removed. The computed branch covers -24 to +11 h; +12 to +24 h remains an explicit fold/coverage boundary rather than plotted proxy data.",
            "next_action": "Develop a robust global quasi-NRHO continuation or high-fidelity ephemeris branch to cover the missing +12 to +24 h interval.",
        },
        {
            "figure_id": "5.13",
            "current_source_layer": "accepted active-geometry Sun-Earth L1 two-frequency torus DG tight stable-manifold periapsis map",
            "current_repro_level": "numerical two-angle stable-manifold reproduction",
            "original_replacement_status": "computed_lissajous_manifold_map_replaces_display_proxy_geometry_boundary_remains",
            "uses_proxy": "false",
            "primary_evidence": _rel(ACTIVE_GEOMETRY_MANIFOLD_AUDIT),
            "supporting_evidence": f"{_rel(ACTIVE_GEOMETRY_FAMILY_AUDIT)};{_rel(ACTIVE_GEOMETRY_APPLICATION_RERUN)};{_rel(ACTIVE_GEOMETRY_MANIFOLD_AUDIT)}",
            "route_h_dependency": "none",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": metrics["active_manifold_rows"],
            "best_metric": (
                f"accepted active-geometry family rows {metrics['active_geometry_source_rows']} "
                f"({metrics['active_geometry_members']} members, {metrics['active_geometry_points']} points); "
                f"full max |y|/|z| {metrics['active_geometry_y_km']}/{metrics['active_geometry_z_km']} km; "
                f"target errors {metrics['active_geometry_y_error']}/{metrics['active_geometry_z_error']} km; "
                f"Jacobi span {metrics['active_geometry_jacobi_span']}; closure {metrics['active_geometry_closure']}; "
                f"target pair {metrics['active_geometry_target_pair']}; "
                f"tight scan rows {metrics['active_manifold_rows']}; "
                f"phase ({metrics['active_manifold_phase0']}, {metrics['active_manifold_phase1']}) deg; "
                f"7033-km periapsis {metrics['active_manifold_target']} km; "
                f"error {metrics['active_manifold_target_error']} km; "
                f"propagated trajectories {metrics['active_manifold_trajectories']}; "
                f"manifold Jacobi drift {metrics['active_manifold_jacobi_drift']}"
            ),
            "boundary": "The display-function proxy is removed and the accepted 129x256 full-torus geometry plus 9x9 tight scan reaches the 7033-km target. Remaining boundaries are high-fidelity BCR4BP/ephemeris correction and pointwise comparison with the thesis heat map.",
            "next_action": "Use the active-geometry CR3BP source layer as the current target-mode result; add BCR4BP/ephemeris correction and digitize the thesis heat map before claiming full thesis equivalence.",
        },
        {
            "figure_id": "5.14",
            "current_source_layer": "accepted active-geometry Sun-Earth L1 stable-manifold LEO transfer",
            "current_repro_level": "numerical quasi-periodic stable-manifold transfer reproduction",
            "original_replacement_status": "computed_lissajous_transfer_replaces_analytic_scene_high_fidelity_pending",
            "uses_proxy": "false",
            "primary_evidence": _rel(ACTIVE_GEOMETRY_LEO_TRANSFER_AUDIT),
            "supporting_evidence": f"{_rel(ACTIVE_GEOMETRY_FAMILY_AUDIT)};{_rel(ACTIVE_GEOMETRY_MANIFOLD_AUDIT)};{_rel(ACTIVE_GEOMETRY_APPLICATION_RERUN)}",
            "route_h_dependency": "none",
            "bcr4bp_dependency": "none",
            "optimization_dependency": "none",
            "accepted_rows": metrics["active_leo_rows"],
            "best_metric": (
                f"accepted active-geometry transfer rows {metrics['active_leo_rows']}; "
                f"trajectory samples {metrics['active_leo_samples']}; "
                f"periapsis {metrics['active_leo_periapsis']} km; "
                f"target error {metrics['active_leo_periapsis_error']} km; "
                f"transfer time {metrics['active_leo_time']} days; "
                f"Jacobi span {metrics['active_leo_jacobi_span']}; "
                f"Lissajous endpoint distance {metrics['active_leo_endpoint']} km"
            ),
            "boundary": "The analytic transfer and torus scene is removed. The accepted active-geometry CR3BP trajectory reaches the 7033-km periapsis target and records the 185-km LEO endpoint; BCR4BP/ephemeris correction remains pending.",
            "next_action": "Correct this specific active-geometry stable-manifold transfer in BCR4BP/ephemeris and compare against thesis timing and geometry.",
        },
        {
            "figure_id": "5.bcr4bp_optimized_transfer",
            "source_page": "derived source-layer figure",
            "script": "figures/fig_5_bcr4bp_optimized_transfer.py",
            "current_source_layer": "Route H/BCR4BP optimized short-transfer source layer",
            "current_repro_level": "Route H / BCR4BP source-layer optimization audit",
            "original_replacement_status": "new_source_layer_not_original_figure",
            "uses_proxy": "false",
            "primary_evidence": _rel(OPTIMIZED_TRANSFER_AUDIT),
            "supporting_evidence": f"{route_h_source};{bcr4bp_source};{_rel(READINESS_AUDIT)};{_exists_rel(CHAPTER4_ROUTE_H_FIGURE)}",
            "route_h_dependency": "accepted Route H upstream member",
            "bcr4bp_dependency": f"{metrics['bcr4bp_rows']} dynamics audit rows; {metrics['correction_rows']} correction rows",
            "optimization_dependency": f"{metrics['optimized_rows']} accepted optimized transfer rows",
            "accepted_rows": metrics["optimized_rows"],
            "best_metric": optimized_metric,
            "boundary": "This is an auditable source-layer figure and must not be counted as one of the original Fig. 5.1-5.14 replacements.",
            "next_action": "Use this as the numerical source layer for future per-original-figure high-fidelity mapping.",
        },
    ]


def _rows() -> list[dict[str, str]]:
    metrics = _source_metrics()
    validation = _validation_lookup()
    rows: list[dict[str, str]] = []
    for spec in _specs(metrics):
        figure_id = spec["figure_id"]
        base = validation.get(figure_id, {})
        row = {
            "source_page": spec.get("source_page", base.get("source_page", "")),
            "script": spec.get("script", base.get("script", "")),
            **spec,
        }
        row.update(_figure_artifacts(figure_id))
        rows.append(row)
    return rows


def _render_markdown(rows: list[dict[str, str]]) -> None:
    originals = [row for row in rows if _is_original_chapter5_figure(row["figure_id"])]
    derived = [row for row in rows if not _is_original_chapter5_figure(row["figure_id"])]
    replaced = [
        row
        for row in originals
        if row["original_replacement_status"]
        in {"schematic_complete", "source_layer_replacement", "full_replacement"}
    ]
    lines = [
        "# Chapter 5 Per-Figure Source-Layer Audit",
        "",
        "Generated by `scripts/run_chapter5_per_figure_source_layer_audit.py`.",
        "",
        "## Summary",
        "",
        f"- Original Chapter 5 figures audited: `{len(originals)}`.",
        f"- Original figures with complete schematic status: `{len(replaced)}`.",
        f"- Derived source-layer figures audited separately: `{len(derived)}`.",
        "- A Route H/BCR4BP optimized-transfer source layer is available, but it is",
        "  not automatically counted as a replacement for every original thesis application figure.",
        "",
        "## Original Figure Mapping",
        "",
        "| figure | source layer | replacement status | proxy | accepted rows | best metric | next action |",
        "|---|---|---|---|---:|---|---|",
    ]
    for row in originals:
        lines.append(
            "| {figure_id} | {current_source_layer} | {original_replacement_status} | "
            "{uses_proxy} | {accepted_rows} | {best_metric} | {next_action} |".format(
                **{key: _md_cell(value) for key, value in row.items()}
            )
        )
    if derived:
        lines.extend(
            [
                "",
                "## Derived Source-Layer Figure",
                "",
                "| figure | source layer | accepted rows | best metric | boundary |",
                "|---|---|---:|---|---|",
            ]
        )
        for row in derived:
            lines.append(
                "| {figure_id} | {current_source_layer} | {accepted_rows} | "
                "{best_metric} | {boundary} |".format(
                    **{key: _md_cell(value) for key, value in row.items()}
                )
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The aggregate Chapter 5 gates pass at the source-layer level. Per-figure",
            "promotion still requires matching each original application's model,",
            "endpoints, constraints, objective, delta-v, and ephemeris or BCR4BP",
            "consistency checks where those quantities are part of the original figure.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = _rows()
    _write_csv(OUT_CSV, rows)
    _render_markdown(rows)
    optimized = next(row for row in rows if row["figure_id"] == "5.bcr4bp_optimized_transfer")
    print(f"updated {OUT_CSV.relative_to(PROJECT_ROOT)}")
    print(f"updated {OUT_MD.relative_to(PROJECT_ROOT)}")
    print(
        "chapter5_per_figure_audit: "
        f"originals=14, derived=1, optimized_rows={optimized['accepted_rows']}, "
        f"best={optimized['best_metric']}"
    )


if __name__ == "__main__":
    main()
