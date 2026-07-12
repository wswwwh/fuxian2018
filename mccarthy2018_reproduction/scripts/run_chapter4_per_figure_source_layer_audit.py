"""Build a per-figure Chapter 4 source-layer audit.

Chapter 4 has two different kinds of evidence in this repository:

1. Original Fig. 4.1-4.8 replacements based on L1 quasi-halo / quasi-vertical
   corrected curves, DG spectra, and finite manifold sheets.
2. A newer Route H quasi-DRO source-layer DG/manifold figure that supports the
   staged goal but is not an original Fig. 4.3-4.8 replacement.

This script keeps those layers separate and writes machine-readable evidence for
the current per-figure status.
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
CURVE_DG = DATA / "chapter4_corrected_curve_dg.csv"
FIG41_AUDIT = DATA / "chapter4_fig41_reported_precision_audit.csv"
FIG41_SPECTRUM = DATA / "chapter4_fig41_reported_precision_spectrum.csv"
FIG41_STATES = DATA / "chapter4_fig41_reported_precision_states.csv"
FIG42_AUDIT = DATA / "chapter4_fig42_stability_family_audit.csv"
VERTICAL_DG = DATA / "chapter4_corrected_vertical_curve_dg.csv"
HALO_DG_FAMILY = DATA / "chapter4_corrected_l1_constant_energy_halo_dg_family.csv"
HALO_HIGH_ORDER_DG = DATA / "chapter4_corrected_l1_constant_energy_halo_high_order_dg.csv"
HALO_PALC_DG = DATA / "chapter4_corrected_l1_constant_energy_halo_pseudo_arclength_dg.csv"
MANIFOLD_VALIDATION = DATA / "chapter4_manifold_validation.csv"
HALO_MANIFOLDS = DATA / "chapter4_corrected_l1_constant_energy_halo_unstable_manifolds.csv"
VERTICAL_PLUS = DATA / "chapter4_corrected_vertical_curve_unstable_manifold_plus.csv"
VERTICAL_MINUS = DATA / "chapter4_corrected_vertical_curve_unstable_manifold_minus.csv"
VERTICAL_GLOBAL = DATA / "chapter4_corrected_vertical_global_unstable_manifold.csv"
ROUTE_H_DG = DATA / "chapter4_route_h_quasi_dro_dg.csv"
ROUTE_H_MANIFOLD = DATA / "chapter4_route_h_quasi_dro_manifold_probe.csv"
ROUTE_H_FAMILY = DATA / "chapter3_fixed_mapping_cache_accepted_family.csv"
ROUTE_H_VALIDATION = DATA / "chapter3_fixed_mapping_cache_accepted_validation.csv"

OUT_CSV = DATA / "chapter4_per_figure_source_layer_audit.csv"
OUT_MD = DOCS / "chapter4_per_figure_source_layer_audit.md"

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
    "dg_dependency",
    "manifold_dependency",
    "accepted_rows",
    "worst_residual",
    "jacobi_drift",
    "growth_ratio",
    "best_metric",
    "boundary",
    "next_action",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def _as_float(row: dict[str, str], field: str, default: float = 0.0) -> float:
    value = row.get(field, "")
    if value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _fmt(value: float | int | str | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.16g}"
    return value


def _max_fmt(*values: str) -> str:
    numbers: list[float] = []
    for value in values:
        try:
            numbers.append(float(value))
        except ValueError:
            continue
    return _fmt(max(numbers)) if numbers else "N/A"


def _is_original_chapter4_figure(figure_id: str) -> bool:
    return figure_id.startswith("4.") and figure_id[2:].isdigit()


def _md_cell(value: str) -> str:
    return value.replace("|", r"\|")


def _validation_lookup() -> dict[str, dict[str, str]]:
    return {row["figure_id"]: row for row in _read_csv(FIGURE_VALIDATION)}


def _figure_artifacts(figure_id: str) -> dict[str, str]:
    if figure_id == "4.route_h":
        suffix = "4_route_h"
    else:
        suffix = figure_id.replace(".", "_")
    png = FIGURES_PNG / f"fig_{suffix}.png"
    pdf = FIGURES_PDF / f"fig_{suffix}.pdf"
    return {
        "rendered_png": _exists_rel(png),
        "rendered_png_bytes": _size(png),
        "rendered_pdf": _exists_rel(pdf),
        "rendered_pdf_bytes": _size(pdf),
    }


def _max(rows: list[dict[str, str]], field: str) -> float | None:
    values = [_as_float(row, field, float("nan")) for row in rows]
    values = [value for value in values if value == value]
    return max(values) if values else None


def _min(rows: list[dict[str, str]], field: str) -> float | None:
    values = [_as_float(row, field, float("nan")) for row in rows]
    values = [value for value in values if value == value]
    return min(values) if values else None


def _validation_row(figure_id: str) -> dict[str, str]:
    rows = [row for row in _read_csv(MANIFOLD_VALIDATION) if row.get("figure_id") == figure_id]
    return rows[0] if rows else {}


def _route_h_metrics() -> dict[str, str]:
    dg = _read_csv(ROUTE_H_DG)
    manifold = _read_csv(ROUTE_H_MANIFOLD)
    return {
        "dg_rows": str(len(dg)),
        "manifold_rows": str(len(manifold)),
        "max_abs_z_km": _fmt(_max(dg, "max_abs_z_km")),
        "max_map_residual": _fmt(_max(dg, "map_residual_norm")),
        "max_det_error": _fmt(_max(dg, "determinant_error_from_one")),
        "max_jacobi_drift": _fmt(_max(manifold, "jacobi_drift_max")),
    }


def _metrics() -> dict[str, str]:
    curve_dg = _read_csv(CURVE_DG)
    fig41 = _read_csv(FIG41_AUDIT)
    fig41_pass = [row for row in fig41 if row.get("acceptance") == "pass"]
    fig42 = _read_csv(FIG42_AUDIT)
    fig42_pass = [row for row in fig42 if row.get("kind") == "quasi_halo" and row.get("acceptance") == "pass"]
    vertical_dg = _read_csv(VERTICAL_DG)
    halo_dg = _read_csv(HALO_DG_FAMILY)
    halo_high = _read_csv(HALO_HIGH_ORDER_DG)
    halo_palc = _read_csv(HALO_PALC_DG)
    manifold_rows = _read_csv(MANIFOLD_VALIDATION)
    route_h = _route_h_metrics()
    return {
        "fig41_pass_rows": str(len(fig41_pass)),
        "fig41_residual": _fmt(_max(fig41_pass, "curve_residual_norm")),
        "fig41_jacobi_span": _fmt(_max(fig41_pass, "curve_jacobi_span")),
        "fig41_nu_error": _fmt(_max(fig41_pass, "stability_index_error")),
        "fig41_ring_span": _fmt(_max(fig41_pass, "unstable_ring_relative_span")),
        "fig42_pass_rows": str(len(fig42_pass)),
        "fig42_max_time": _fmt(_max(fig42_pass, "mapping_time_days")),
        "fig42_max_nu": _fmt(_max(fig42_pass, "stability_index")),
        "fig42_residual": _fmt(_max(fig42_pass, "curve_residual_norm")),
        "curve_dg_rows": str(len(curve_dg)),
        "curve_dg_residual": _fmt(_max(curve_dg, "curve_residual_norm")),
        "curve_dg_det_error": _fmt(abs((_max(curve_dg, "determinant") or 1.0) - 1.0)),
        "vertical_dg_rows": str(len(vertical_dg)),
        "vertical_dg_residual": _fmt(_max(vertical_dg, "curve_residual_norm")),
        "halo_dg_rows": str(len(halo_dg)),
        "halo_high_order_rows": str(len(halo_high)),
        "halo_palc_rows": str(len(halo_palc)),
        "halo_dg_residual": _fmt(_max(halo_dg, "curve_residual_norm")),
        "manifold_rows": str(len(manifold_rows)),
        "max_manifold_residual": _fmt(_max(manifold_rows, "source_curve_residual")),
        "max_manifold_jacobi": _fmt(_max(manifold_rows, "jacobi_drift_max")),
        **{f"route_h_{key}": value for key, value in route_h.items()},
    }


def _manifold_metric(figure_id: str) -> dict[str, str]:
    row = _validation_row(figure_id)
    if not row:
        return {
            "accepted_rows": "0",
            "worst_residual": "N/A",
            "jacobi_drift": "N/A",
            "growth_ratio": "N/A",
            "best_metric": "N/A",
        }
    return {
        "accepted_rows": "1",
        "worst_residual": _fmt(_as_float(row, "source_curve_residual")),
        "jacobi_drift": _fmt(_as_float(row, "jacobi_drift_max")),
        "growth_ratio": _fmt(_as_float(row, "growth_ratio")),
        "best_metric": (
            f"{row['family']} {row['branch']}; duration {row['duration_days']} days; "
            f"growth ratio {row['growth_ratio']}; Jacobi drift {row['jacobi_drift_max']}"
        ),
    }


def _specs(metrics: dict[str, str]) -> list[dict[str, str]]:
    route_h_source = f"{_rel(ROUTE_H_FAMILY)};{_rel(ROUTE_H_VALIDATION)}"
    halo_dg_source = f"{_rel(HALO_DG_FAMILY)};{_rel(HALO_HIGH_ORDER_DG)};{_rel(HALO_PALC_DG)}"
    route_h_metric = (
        f"{metrics['route_h_dg_rows']} Route H DG rows; {metrics['route_h_manifold_rows']} "
        f"manifold probes; max |z| {metrics['route_h_max_abs_z_km']} km; "
        f"max det error {metrics['route_h_max_det_error']}; max Jacobi drift "
        f"{metrics['route_h_max_jacobi_drift']}"
    )
    specs = [
        {
            "figure_id": "4.1",
            "current_source_layer": "N=25 corrected L2 quasi-halo DG at paper-reported Jacobi precision",
            "current_repro_level": "quantitative DG reproduction with torus-geometry boundary",
            "original_replacement_status": "dg_target_reproduced_geometry_not_yet_thesis_equivalent",
            "uses_proxy": "false",
            "primary_evidence": f"{_rel(FIG41_AUDIT)};{_rel(FIG41_SPECTRUM)}",
            "supporting_evidence": _rel(FIG41_STATES),
            "route_h_dependency": "none",
            "dg_dependency": "150 raw DG eigenvalues; 25 unstable, 100 unit, 25 stable",
            "manifold_dependency": "none",
            "accepted_rows": metrics["fig41_pass_rows"],
            "worst_residual": metrics["fig41_residual"],
            "jacobi_drift": metrics["fig41_jacobi_span"],
            "growth_ratio": "N/A",
            "best_metric": (
                f"nu error {metrics['fig41_nu_error']}; unstable-ring relative span "
                f"{metrics['fig41_ring_span']}; N=25"
            ),
            "boundary": "The raw N=25 DG spectrum and nu=1.3837 target are reproduced at an internal Jacobi value that rounds to the paper's 3.044, but the accepted member is a near-periodic small-amplitude torus and does not yet prove the finite-amplitude geometry in panel (a).",
            "next_action": "Continue a finite-amplitude L2 quasi-halo branch while retaining the reported-precision Jacobi and DG stability gates before claiming full panel replacement.",
        },
        {
            "figure_id": "4.2",
            "current_source_layer": "accepted L1 constant-energy quasi-halo DG stability family",
            "current_repro_level": "numerical DG family reproduction with paper-digitization boundary",
            "original_replacement_status": "computed_family_replaces_proxy_curve_pointwise_paper_comparison_pending",
            "uses_proxy": "false",
            "primary_evidence": _rel(FIG42_AUDIT),
            "supporting_evidence": halo_dg_source,
            "route_h_dependency": "none",
            "dg_dependency": (
                f"{metrics['halo_dg_rows']} halo rows; {metrics['halo_high_order_rows']} "
                f"high-order rows; {metrics['halo_palc_rows']} PALC rows; "
                f"{metrics['vertical_dg_rows']} vertical rows"
            ),
            "manifold_dependency": "none",
            "accepted_rows": metrics["fig42_pass_rows"],
            "worst_residual": metrics["fig42_residual"],
            "jacobi_drift": "N/A",
            "growth_ratio": "N/A",
            "best_metric": (
                f"mapping time <= {metrics['fig42_max_time']} days; stability index <= "
                f"{metrics['fig42_max_nu']}"
            ),
            "boundary": "The analytic proxy curve has been removed and the accepted N=9/15/21 DG family reaches its mapping-time fold; direct digitization of the paper curve is still required for a pointwise visual-equivalence score.",
            "next_action": "Digitize the paper curve and compare it pointwise against the accepted DG family without extrapolating beyond the computed fold.",
        },
    ]
    manifold_specs = {
        "4.3": (
            "corrected L1 quasi-halo +x unstable manifold sheet",
            "corrected DG finite-amplitude manifold source layer",
            "corrected_finite_manifold_not_thesis_scale_global_replacement",
            _rel(HALO_MANIFOLDS),
            "Continue the corrected branch to a denser thesis-scale global torus manifold.",
        ),
        "4.4": (
            "corrected L1 quasi-halo -x unstable manifold sheet",
            "corrected DG finite-amplitude manifold source layer",
            "corrected_finite_manifold_not_thesis_scale_global_replacement",
            _rel(HALO_MANIFOLDS),
            "Continue the corrected branch to a denser thesis-scale global torus manifold.",
        ),
        "4.5": (
            "corrected quasi-vertical local +x unstable manifold branch",
            "local corrected DG manifold source layer",
            "local_branch_not_global_sheet_replacement",
            _rel(VERTICAL_PLUS),
            "Promote from local branch diagnostic to continued thesis-scale vertical manifold.",
        ),
        "4.6": (
            "corrected quasi-vertical local -x unstable manifold branch",
            "local corrected DG manifold source layer",
            "local_branch_not_global_sheet_replacement",
            _rel(VERTICAL_MINUS),
            "Promote from local branch diagnostic to continued thesis-scale vertical manifold.",
        ),
        "4.7": (
            "corrected quasi-halo manifold with periodic-halo comparison",
            "corrected DG manifold source layer with proxy comparison",
            "source_layer_comparison_not_full_original_replacement",
            _rel(HALO_MANIFOLDS),
            "Extend the corrected quasi-halo sheet across a thesis-scale continued torus family.",
        ),
        "4.8": (
            "corrected quasi-vertical global unstable manifold with comparison context",
            "corrected DG global manifold source layer with proxy comparison",
            "global_sheet_audited_but_source_family_not_thesis_scale_complete",
            _rel(VERTICAL_GLOBAL),
            "Continue the source quasi-vertical torus family before treating the global sheet as thesis-equivalent.",
        ),
    }
    for figure_id, values in manifold_specs.items():
        current_source_layer, level, replacement, primary, next_action = values
        metric = _manifold_metric(figure_id)
        specs.append(
            {
                "figure_id": figure_id,
                "current_source_layer": current_source_layer,
                "current_repro_level": level,
                "original_replacement_status": replacement,
                "uses_proxy": "partial",
                "primary_evidence": primary,
                "supporting_evidence": f"{_rel(MANIFOLD_VALIDATION)};{halo_dg_source};{_rel(VERTICAL_DG)}",
                "route_h_dependency": "none for original figure; Route H tracked separately",
                "dg_dependency": "corrected L1 DG eigenvectors and manifold validation row",
                "manifold_dependency": primary,
                **metric,
                "boundary": "Corrected numerical manifold evidence exists, but proxy/background context and missing original raw branch data prevent a full thesis-equivalence claim.",
                "next_action": next_action,
            }
        )
    specs.append(
        {
            "figure_id": "4.route_h",
            "source_page": "derived source-layer figure",
            "script": "figures/fig_4_route_h_quasi_dro.py",
            "current_source_layer": "Route H quasi-DRO discrete-curve DG and local manifold probe",
            "current_repro_level": "Route H quasi-DRO Chapter 4 source-layer audit",
            "original_replacement_status": "new_source_layer_not_original_figure",
            "uses_proxy": "false",
            "primary_evidence": f"{_rel(ROUTE_H_DG)};{_rel(ROUTE_H_MANIFOLD)}",
            "supporting_evidence": route_h_source,
            "route_h_dependency": "accepted Route H upstream quasi-DRO source branch",
            "dg_dependency": f"{metrics['route_h_dg_rows']} Route H DG rows",
            "manifold_dependency": f"{metrics['route_h_manifold_rows']} local Route H manifold probes",
            "accepted_rows": metrics["route_h_manifold_rows"],
            "worst_residual": metrics["route_h_max_map_residual"],
            "jacobi_drift": metrics["route_h_max_jacobi_drift"],
            "growth_ratio": "local probe only",
            "best_metric": route_h_metric,
            "boundary": "This is a derived Route H quasi-DRO source-layer figure, not a replacement for original Fig. 4.3-4.8 L1 quasi-halo/quasi-vertical manifolds.",
            "next_action": "Use as upstream/source-layer evidence while continuing original L1 thesis-scale manifold replacement separately.",
        }
    )
    return specs


def _rows() -> list[dict[str, str]]:
    validation = _validation_lookup()
    rows: list[dict[str, str]] = []
    for spec in _specs(_metrics()):
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
    originals = [row for row in rows if _is_original_chapter4_figure(row["figure_id"])]
    derived = [row for row in rows if not _is_original_chapter4_figure(row["figure_id"])]
    lines = [
        "# Chapter 4 Per-Figure Source-Layer Audit",
        "",
        "Generated by `scripts/run_chapter4_per_figure_source_layer_audit.py`.",
        "",
        "## Summary",
        "",
        f"- Original Chapter 4 figures audited: `{len(originals)}`.",
        f"- Derived source-layer figures audited separately: `{len(derived)}`.",
        "- Corrected L1 quasi-halo / quasi-vertical DG and manifold evidence exists",
        "  for the original figure set, but the Route H quasi-DRO source-layer figure",
        "  is tracked separately and is not counted as a Fig. 4.3-4.8 replacement.",
        "",
        "## Original Figure Mapping",
        "",
        "| figure | source layer | replacement status | proxy | accepted rows | residual | Jacobi drift | growth ratio | next action |",
        "|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for row in originals:
        escaped = {key: _md_cell(value) for key, value in row.items()}
        lines.append(
            "| {figure_id} | {current_source_layer} | {original_replacement_status} | "
            "{uses_proxy} | {accepted_rows} | {worst_residual} | {jacobi_drift} | "
            "{growth_ratio} | {next_action} |".format(**escaped)
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
            escaped = {key: _md_cell(value) for key, value in row.items()}
            lines.append(
                "| {figure_id} | {current_source_layer} | {accepted_rows} | "
                "{best_metric} | {boundary} |".format(**escaped)
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Chapter 4 currently has corrected numerical source-layer evidence. Full",
            "original thesis-equivalence remains unproven for the L1 quasi-halo and",
            "quasi-vertical global manifold figures because the original raw branch",
            "data are unavailable and several rendered figures still retain proxy or",
            "comparison context.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = _rows()
    _write_csv(OUT_CSV, rows)
    _render_markdown(rows)
    route_h = next(row for row in rows if row["figure_id"] == "4.route_h")
    print(f"updated {OUT_CSV.relative_to(PROJECT_ROOT)}")
    print(f"updated {OUT_MD.relative_to(PROJECT_ROOT)}")
    print(
        "chapter4_per_figure_audit: "
        f"originals=8, derived=1, route_h_rows={route_h['accepted_rows']}, "
        f"route_h={route_h['best_metric']}"
    )


if __name__ == "__main__":
    main()
