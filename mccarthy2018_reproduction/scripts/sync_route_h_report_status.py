"""Synchronize Route H quasi-DRO status across report artifacts.

This script updates public-facing status files after the Route H fixed-mapping
cache audit promoted Fig. 3.16 / Fig. 3.17 from the old local-only quasi-DRO
bottleneck state to an accepted fixed-time source-layer state.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "computed"
DOCS = PROJECT_ROOT / "docs"
REPORT = DOCS / "reproduction_report"
TEACHER = REPORT / "teacher_package"

FIGURE_VALIDATION = DATA / "figure_validation_table.csv"
ROUTE_H_VALIDATION = DATA / "chapter3_fixed_mapping_cache_accepted_validation.csv"
ROUTE_H_FAMILY = DATA / "chapter3_fixed_mapping_cache_accepted_family.csv"
ROUTE_H_AUDIT = DATA / "chapter3_fixed_mapping_cache_audit.csv"
STAGED_GATE = DATA / "mccarthy2018_staged_goal_gate_status.csv"
CHAPTER4_PER_FIGURE_AUDIT = DATA / "chapter4_per_figure_source_layer_audit.csv"
CHAPTER5_PER_FIGURE_AUDIT = DATA / "chapter5_per_figure_source_layer_audit.csv"

FIGURE_STATUS_APPENDIX = REPORT / "figure_status_appendix.md"
PROXY_USAGE_APPENDIX = REPORT / "proxy_usage_appendix.md"
TEACHER_README = TEACHER / "README.md"
KEY_RESULTS = TEACHER / "key_results_table.md"
ONE_PAGE_SUMMARY = TEACHER / "one_page_summary.md"
QA = REPORT / "qa_for_group_meeting.md"
README = PROJECT_ROOT / "README.md"
MAIN_REPORT = REPORT / "main_report.md"
NUMERICAL_AUDIT = REPORT / "numerical_audit_appendix.md"
PRESENTATION_OUTLINE = REPORT / "presentation_outline.md"
FIG316_DIGITIZATION = REPORT / "fig_3_16_digitization_feasibility.md"
FUTURE_WORK = REPORT / "future_work_plan.md"

SYNC_START = "<!-- ROUTE_H_STATUS_SYNC_START -->"
SYNC_END = "<!-- ROUTE_H_STATUS_SYNC_END -->"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _as_float(row: dict[str, str], field: str) -> float:
    return float(row[field])


def _fmt(value: float | int | str | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.16g}"
    return value


def _is_original_chapter5_figure(figure_id: str) -> bool:
    return figure_id.startswith("5.") and figure_id[2:].isdigit()


def _is_original_chapter4_figure(figure_id: str) -> bool:
    return figure_id.startswith("4.") and figure_id[2:].isdigit()


def _route_h_summary() -> dict[str, float | int | str]:
    rows = _read_csv(ROUTE_H_VALIDATION)
    max_row = max(rows, key=lambda row: _as_float(row, "max_abs_z_km"))
    return {
        "rows": len(rows),
        "min_z": min(_as_float(row, "max_abs_z_km") for row in rows),
        "max_z": _as_float(max_row, "max_abs_z_km"),
        "max_member": int(max_row["member"]),
        "min_rho": min(_as_float(row, "rotation_angle_rad") for row in rows),
        "max_rho": max(_as_float(row, "rotation_angle_rad") for row in rows),
        "mapping_time": _as_float(rows[0], "mapping_time_days"),
        "ge_10500": sum(_as_float(row, "max_abs_z_km") >= 10500.0 for row in rows),
        "ge_11000": sum(_as_float(row, "max_abs_z_km") >= 11000.0 for row in rows),
        "max_residual": max(_as_float(row, "map_residual_norm") for row in rows),
        "max_curve_jacobi_span": max(_as_float(row, "curve_jacobi_span") for row in rows),
        "max_one_map_jacobi_drift": max(
            _as_float(row, "one_map_sweep_jacobi_drift") for row in rows
        ),
        "max_phase_error": max(_as_float(row, "one_map_phase_return_error") for row in rows),
        "max_ten_return_jacobi_span": max(
            _as_float(row, "ten_return_jacobi_span") for row in rows
        ),
    }


def _update_figure_validation_table(summary: dict[str, float | int | str]) -> list[dict[str, str]]:
    rows = _read_csv(FIGURE_VALIDATION)
    fields = list(rows[0])
    source = (
        f"{ROUTE_H_FAMILY.relative_to(PROJECT_ROOT).as_posix()};"
        f"{ROUTE_H_VALIDATION.relative_to(PROJECT_ROOT).as_posix()};"
        f"{STAGED_GATE.relative_to(PROJECT_ROOT).as_posix()};"
        f"{ROUTE_H_AUDIT.relative_to(PROJECT_ROOT).as_posix()}"
    )
    common_quantities = (
        "accepted fixed-mapping-time Route H quasi-DRO source branch; "
        f"rho {_fmt(summary['min_rho'])}..{_fmt(summary['max_rho'])} rad; "
        f"max abs z {_fmt(summary['min_z'])}..{_fmt(summary['max_z'])} km; "
        f"{summary['ge_10500']} rows >= 10500 km and {summary['ge_11000']} rows >= 11000 km; "
        f"mapping time {_fmt(summary['mapping_time'])} days"
    )
    residual = (
        f"Route H max map residual {_fmt(summary['max_residual'])}; "
        f"source audit rows {summary['rows']}"
    )
    jacobi = (
        f"max curve Jacobi span {_fmt(summary['max_curve_jacobi_span'])}; "
        f"max one-map Jacobi drift {_fmt(summary['max_one_map_jacobi_drift'])}; "
        f"max ten-return Jacobi span {_fmt(summary['max_ten_return_jacobi_span'])}"
    )
    periodicity = f"max one-map phase return error {_fmt(summary['max_phase_error'])}"
    for row in rows:
        if row["figure_id"] == "3.16":
            row.update(
                {
                    "current_repro_level": "audited Route H fixed-time source-layer",
                    "uses_proxy": "false",
                    "main_data_source": source,
                    "key_physical_quantities": (
                        "constant-mapping-time quasi-DRO tori rendered directly from the "
                        + common_quantities
                    ),
                    "residual_norm": residual,
                    "jacobi_drift": jacobi,
                    "periodicity_error": periodicity,
                    "stability_index_error": "N/A",
                    "visual_status": (
                        "current rendering uses corrected Route H tori directly; older grey "
                        "proxy surfaces are no longer the source for this figure"
                    ),
                    "next_action": (
                        "Keep Route H as the accepted CR3BP fixed-time source layer; only "
                        "upgrade the full-thesis equivalence claim if original McCarthy branch "
                        "data or author code become available"
                    ),
                }
            )
        elif row["figure_id"] == "3.17":
            row.update(
                {
                    "current_repro_level": "audited Route H fixed-time source-layer",
                    "uses_proxy": "partial",
                    "main_data_source": source,
                    "key_physical_quantities": (
                        "rho-amplitude-Jacobi trends with the audited Route H branch plotted "
                        "as the numerical source layer; " + common_quantities
                    ),
                    "residual_norm": residual,
                    "jacobi_drift": jacobi,
                    "periodicity_error": periodicity,
                    "stability_index_error": "N/A",
                    "visual_status": (
                        "audited Route H branch is plotted as the main numerical layer; faint "
                        "reference trend proxy is retained only for visual context"
                    ),
                    "next_action": (
                        "Use Route H for the accepted fixed-time source branch; keep the "
                        "reference trend and digitized curve as lower-authority comparison, "
                        "not raw branch data"
                    ),
                }
            )
    _update_chapter4_figure_validation_rows(rows)
    _update_chapter5_figure_validation_rows(rows)
    _write_csv(FIGURE_VALIDATION, rows, fields)
    return rows


def _update_chapter4_figure_validation_rows(rows: list[dict[str, str]]) -> None:
    if not CHAPTER4_PER_FIGURE_AUDIT.exists():
        return
    audit_rows = {
        row["figure_id"]: row
        for row in _read_csv(CHAPTER4_PER_FIGURE_AUDIT)
        if _is_original_chapter4_figure(row["figure_id"])
    }
    for row in rows:
        audit = audit_rows.get(row["figure_id"])
        if not audit:
            continue
        source_parts = [
            audit["primary_evidence"],
            audit["supporting_evidence"],
            audit["rendered_png"],
            audit["rendered_pdf"],
        ]
        source = ";".join(part for part in source_parts if part)
        row.update(
            {
                "current_repro_level": audit["current_repro_level"],
                "uses_proxy": audit["uses_proxy"],
                "main_data_source": source,
                "key_physical_quantities": (
                    f"{audit['current_source_layer']}; {audit['best_metric']}; "
                    f"original replacement status: {audit['original_replacement_status']}"
                ),
                "residual_norm": (
                    f"worst source residual: {audit['worst_residual']}; "
                    f"accepted rows: {audit['accepted_rows']}; "
                    f"DG dependency: {audit['dg_dependency']}"
                ),
                "jacobi_drift": audit["jacobi_drift"],
                "periodicity_error": (
                    f"manifold growth ratio: {audit['growth_ratio']}; "
                    f"manifold dependency: {audit['manifold_dependency']}"
                ),
                "stability_index_error": "See Chapter 4 DG source-layer audit",
                "visual_status": (
                    f"PNG bytes {audit['rendered_png_bytes']}; PDF bytes "
                    f"{audit['rendered_pdf_bytes']}; boundary: {audit['boundary']}"
                ),
                "next_action": audit["next_action"],
            }
        )


def _update_chapter5_figure_validation_rows(rows: list[dict[str, str]]) -> None:
    if not CHAPTER5_PER_FIGURE_AUDIT.exists():
        return
    audit_rows = {
        row["figure_id"]: row
        for row in _read_csv(CHAPTER5_PER_FIGURE_AUDIT)
        if _is_original_chapter5_figure(row["figure_id"])
    }
    for row in rows:
        audit = audit_rows.get(row["figure_id"])
        if not audit:
            continue
        source_parts = [
            audit["primary_evidence"],
            audit["supporting_evidence"],
            audit["rendered_png"],
            audit["rendered_pdf"],
        ]
        source = ";".join(part for part in source_parts if part)
        row.update(
            {
                "current_repro_level": audit["current_repro_level"],
                "uses_proxy": audit["uses_proxy"],
                "main_data_source": source,
                "key_physical_quantities": (
                    f"{audit['current_source_layer']}; {audit['best_metric']}; "
                    f"original replacement status: {audit['original_replacement_status']}"
                ),
                "residual_norm": (
                    f"accepted source rows: {audit['accepted_rows']}; "
                    f"Route H dependency: {audit['route_h_dependency']}; "
                    f"BCR4BP dependency: {audit['bcr4bp_dependency']}"
                ),
                "jacobi_drift": "See Chapter 5 source-layer audit; not a single CR3BP Jacobi metric for all application figures",
                "periodicity_error": "See Chapter 5 source-layer audit for endpoint/defect boundary",
                "stability_index_error": "N/A",
                "visual_status": (
                    f"PNG bytes {audit['rendered_png_bytes']}; PDF bytes "
                    f"{audit['rendered_pdf_bytes']}; boundary: {audit['boundary']}"
                ),
                "next_action": audit["next_action"],
            }
        )


def _render_figure_status_appendix(rows: list[dict[str, str]]) -> None:
    counts = Counter(row["current_repro_level"] for row in rows)
    lines = [
        "# Figure Status Appendix",
        "",
        "Source table: `data/computed/figure_validation_table.csv`.",
        "This Markdown file is generated by `scripts/sync_route_h_report_status.py`.",
        "",
        f"Total figures: {len(rows)}.",
        "",
        "## Status Summary",
        "",
        "| current_repro_level | count |",
        "|---|---:|",
    ]
    for key in sorted(counts):
        lines.append(f"| {key} | {counts[key]} |")
    lines.extend(["", "## Figure-Level Entries", ""])
    field_labels = (
        ("figure_id", "figure_id"),
        ("source_page", "source_page"),
        ("script", "script"),
        ("current_repro_level", "current_repro_level"),
        ("uses_proxy", "uses_proxy"),
        ("main_data_source", "main_data_source"),
        ("key_physical_quantities", "key_physical_quantities"),
        ("residual_norm", "residual evidence"),
        ("jacobi_drift", "Jacobi evidence"),
        ("periodicity_error", "periodicity evidence"),
        ("stability_index_error", "stability evidence"),
        ("visual_status", "visual_status"),
        ("next_action", "next_action"),
    )
    for row in rows:
        lines.extend(
            [
                f"### Figure {row['figure_id']}",
                "",
                "| Field | Value |",
                "|---|---|",
            ]
        )
        for field, label in field_labels:
            lines.append(f"| {label} | {row.get(field, '')} |")
        lines.append("")
    FIGURE_STATUS_APPENDIX.write_text("\n".join(lines), encoding="utf-8")


def _status_counts(rows: list[dict[str, str]]) -> str:
    counts = Counter(row["current_repro_level"] for row in rows)
    return "; ".join(f"{key}: {counts[key]}" for key in sorted(counts))


def _write_proxy_usage_appendix(rows: list[dict[str, str]], summary: dict[str, float | int | str]) -> None:
    proxy_rows = [row for row in rows if row["uses_proxy"].lower() in {"true", "partial"}]
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in proxy_rows:
        chapter = row["figure_id"].split(".")[0]
        grouped.setdefault(chapter, []).append(row)
    lines = [
        "# Proxy Usage Appendix",
        "",
        "This file is generated by `scripts/sync_route_h_report_status.py` from",
        "`data/computed/figure_validation_table.csv`.",
        "",
        "## Route H Update",
        "",
        "- Fig. 3.16 now renders corrected Route H fixed-time quasi-DRO tori directly.",
        "- Fig. 3.17 plots the audited Route H branch as the numerical layer and keeps",
        "  the reference trend only as a lower-authority visual comparison.",
        f"- Route H accepted validation rows: `{summary['rows']}`; best max abs z:",
        f"  `{_fmt(summary['max_z'])}` km; rows >= 10500 km: `{summary['ge_10500']}`;",
        f"  rows >= 11000 km: `{summary['ge_11000']}`.",
        "",
        "The project still must not claim complete McCarthy 2018 numerical equivalence:",
        "original branch data or author code remain unavailable for exact full-thesis",
        "comparison, and several Chapter 4/5 figures retain proxy or source-layer status.",
        "",
        "## Figures Still Using Proxy Or Partial Context",
        "",
    ]
    for chapter in sorted(grouped, key=int):
        lines.extend([f"### Chapter {chapter}", ""])
        for row in grouped[chapter]:
            lines.append(
                f"- Fig. {row['figure_id']}: `{row['current_repro_level']}`; "
                f"proxy flag `{row['uses_proxy']}`; {row['visual_status']}"
            )
        lines.append("")
    lines.extend(
        [
            "## Figures That Must Not Be Overclaimed",
            "",
            "- Fig. 3.10: q=8 is still a local multiple-shooting approximation, not a",
            "  robust single-shoot periodic orbit.",
            "- Fig. 3.17: the faint reference trend and digitized trend are not raw branch data.",
            "- Figures 4.3-4.8: corrected DG evidence exists, but original thesis-scale",
            "  global manifold replacement remains separate from the Route H source layer.",
            "- Chapter 5 source-layer BCR4BP/optimization audits do not replace every",
            "  original thesis application figure.",
            "",
        ]
    )
    PROXY_USAGE_APPENDIX.write_text("\n".join(lines), encoding="utf-8")


def _write_teacher_package(rows: list[dict[str, str]], summary: dict[str, float | int | str]) -> None:
    count_text = _status_counts(rows)
    TEACHER_README.write_text(
        f"""# Teacher Package README

## Current Status

This package summarizes the current McCarthy 2018 reproduction state. The
project has one engineered output for all 54 target figures and auditable CSV
evidence for the main numerical layers, but it should not be described as a
complete numerical equivalence reproduction of the full thesis.

Route H is now the current Chapter 3 quasi-DRO source-layer result:

- accepted Route H validation rows: `{summary['rows']}`
- best fixed-time quasi-DRO max abs z: `{_fmt(summary['max_z'])}` km
- rows above 10,500 km: `{summary['ge_10500']}`
- rows above 11,000 km: `{summary['ge_11000']}`
- max map residual: `{_fmt(summary['max_residual'])}`
- max one-map Jacobi drift: `{_fmt(summary['max_one_map_jacobi_drift'])}`

## Recommended Reading Order

1. `one_page_summary.md`
2. `key_results_table.md`
3. `../figure_status_appendix.md`
4. `../proxy_usage_appendix.md`
5. `../qa_for_group_meeting.md`

## Boundaries

- Do not call the whole repository a complete McCarthy 2018 numerical reproduction.
- Do not treat digitized Fig. 3.17 or faint reference trends as raw branch data.
- Do not describe Route H Chapter 4/5 source-layer artifacts as full replacement
  for every original thesis figure.
- Use `data/computed/figure_validation_table.csv` and
  `data/computed/mccarthy2018_staged_goal_gate_status.csv` as the current
  machine-readable status sources.
""",
        encoding="utf-8",
    )
    KEY_RESULTS.write_text(
        f"""# Key Results Table

| topic | current result | interpretation | boundary / next step |
|---|---|---|---|
| 54 figure coverage | All target figures 2.1-2.15, 3.1-3.17, 4.1-4.8, and 5.1-5.14 have an engineered output. | The repository has full figure coverage and status tracking. | Coverage is not the same as full numerical equivalence. |
| Figure status counts | {count_text}. | These counts come from `data/computed/figure_validation_table.csv`. | Re-run `scripts/sync_route_h_report_status.py` after status-changing audits. |
| Fig. 3.16 / 3.17 Route H source | Route H fixed-time quasi-DRO branch reaches `{_fmt(summary['max_z'])}` km at member `{summary['max_member']}`. | Chapter 3 source gate is passed for the fixed-time quasi-DRO source layer. | Exact thesis equivalence still needs original branch data or author code. |
| Route H audit quality | max map residual `{_fmt(summary['max_residual'])}`, max curve Jacobi span `{_fmt(summary['max_curve_jacobi_span'])}`, max one-map Jacobi drift `{_fmt(summary['max_one_map_jacobi_drift'])}`. | The promoted source layer is backed by current CSV audit evidence. | Do not reuse rejected Route B/diagnostic rows as accepted source data. |
| Fig. 3.10 q=8 | Multiple-shooting residuals are small, but single-shoot full-period closure remains unreliable. | It is a local approximation, not a robust periodic-orbit reproduction. | Keep the current boundary label. |
| Chapter 4 | Route H source-layer DG/manifold artifacts exist, while original L1 quasi-halo/quasi-vertical thesis-scale replacement remains separate. | Source-layer progress is real. | Do not conflate Route H quasi-DRO source-layer figures with original Fig. 4.3-4.8 replacement. |
| Chapter 5 | Route H/DE421/BCR4BP/optimization source-layer audits exist. | Application-layer evidence has improved. | Per-figure high-fidelity equivalence still needs endpoint, delta-v, and ephemeris consistency checks where applicable. |
""",
        encoding="utf-8",
    )
    ONE_PAGE_SUMMARY.write_text(
        f"""# One Page Summary

The project reproduces the McCarthy 2018 quasi-periodic-orbit thesis at an
engineering-audit level: all 54 target figures have generated outputs, and each
figure is tracked by data source, residual/Jacobi evidence, proxy usage, and a
next action in `data/computed/figure_validation_table.csv`.

The most important recent update is Chapter 3 Route H. The accepted
fixed-mapping quasi-DRO source branch now reaches `{_fmt(summary['max_z'])}` km,
with `{summary['ge_10500']}` accepted rows above 10,500 km and
`{summary['ge_11000']}` above 11,000 km. Fig. 3.16 and Fig. 3.17 now use this
Route H source layer rather than the older local-only 10,164 km endpoint.

This does not mean the whole thesis has been fully numerically reproduced.
Original McCarthy branch data, appendix tables, and author code are still not
available in the repository. Several Chapter 4 and Chapter 5 figures remain
source-layer, baseline, local-overlay, or proxy-context results. The correct
claim is: the repository now has a stronger audited source layer for the hard
Chapter 3 quasi-DRO figures, while full-thesis equivalence remains a bounded
future-work target.
""",
        encoding="utf-8",
    )


def _write_qa(summary: dict[str, float | int | str]) -> None:
    QA.write_text(
        f"""# Group Meeting Q&A

## Q1. What is complete now?

All 54 target figures have generated outputs and a machine-readable status row.
The strongest recent improvement is Route H: the fixed-time quasi-DRO source
branch for Fig. 3.16 / Fig. 3.17 now reaches `{_fmt(summary['max_z'])}` km with
accepted audit rows above both 10,500 km and 11,000 km.

## Q2. Can we claim complete McCarthy 2018 numerical reproduction?

No. Route H solves the earlier Chapter 3 source-gate bottleneck, but full thesis
equivalence still requires original branch data, appendix tables, author code,
or per-figure high-fidelity replacement evidence for the remaining source-layer
and proxy-context figures.

## Q3. What changed for Fig. 3.16 / Fig. 3.17?

The old accepted endpoint was about 10,164 km. The current Route H accepted
validation table has `{summary['rows']}` rows, best max abs z
`{_fmt(summary['max_z'])}` km, max map residual `{_fmt(summary['max_residual'])}`,
and max one-map Jacobi drift `{_fmt(summary['max_one_map_jacobi_drift'])}`.
Fig. 3.16 now renders corrected Route H tori directly. Fig. 3.17 plots Route H
as the numerical branch and keeps the reference trend only for context.

## Q4. Why is Fig. 3.17's reference trend still lower authority?

The digitized or faint reference trend comes from rendered figure imagery, not
raw McCarthy branch states. It is useful for visual comparison, but it is not a
replacement for raw branch data.

## Q5. What remains incomplete?

Chapter 4 original L1 quasi-halo/quasi-vertical thesis-scale global manifold
replacement remains separate from the Route H quasi-DRO source layer. Chapter 5
has Route H/DE421/BCR4BP/optimization source-layer audits, but per-original-figure
high-fidelity equivalence still needs endpoint, delta-v, and ephemeris checks.

## Q6. What is the safest one-sentence summary?

The project now has full 54-figure engineering coverage and an audited Route H
source-layer breakthrough for the hard Chapter 3 quasi-DRO figures, but it is
still not a complete numerical equivalence reproduction of every McCarthy 2018
thesis figure.
""",
        encoding="utf-8",
    )


def _write_public_report(rows: list[dict[str, str]], summary: dict[str, float | int | str]) -> None:
    count_text = _status_counts(rows)
    MAIN_REPORT.write_text(
        f"""# McCarthy 2018 Reproduction Report

## Summary

This repository has an engineered output for all 54 target figures in McCarthy
2018 and maintains a figure-by-figure evidence table at
`data/computed/figure_validation_table.csv`. The current status counts are:
{count_text}.

The main status change is Chapter 3 Route H. Fig. 3.16 and Fig. 3.17 now use an
accepted fixed-mapping quasi-DRO source layer from
`data/computed/chapter3_fixed_mapping_cache_accepted_family.csv` and
`data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv`. The Route
H validation set has `{summary['rows']}` accepted rows, reaches
`{_fmt(summary['max_z'])}` km, and includes `{summary['ge_10500']}` rows above
10,500 km and `{summary['ge_11000']}` rows above 11,000 km.

This is a real source-layer promotion, not a license to claim complete thesis
equivalence. Original McCarthy branch data, appendix tables, and author code
remain unavailable. Several Chapter 4 and Chapter 5 figures are still
source-layer, baseline, local-overlay, or proxy-context results.

## Strongest Evidence

- Chapter 2 CR3BP basics and periodic-orbit baselines remain the cleanest
  numerical reproductions.
- Chapter 3 constant-energy and constant-frequency families have corrected
  numerical branches with residual and Jacobi evidence.
- Fig. 3.16 / Fig. 3.17 now have the Route H fixed-time quasi-DRO branch:
  max residual `{_fmt(summary['max_residual'])}`, max curve Jacobi span
  `{_fmt(summary['max_curve_jacobi_span'])}`, and max one-map Jacobi drift
  `{_fmt(summary['max_one_map_jacobi_drift'])}`.
- Fig. 3.10 q=8 remains a local multiple-shooting approximation, not a robust
  single-shoot periodic orbit.
- Chapter 4 Route H DG/manifold and Chapter 5 BCR4BP/optimization source-layer
  audits exist, but they do not replace every original thesis figure.

## Boundary Statement

The correct high-level claim is: the project has full 54-figure engineering
coverage and a strengthened audited source layer for the difficult Chapter 3
quasi-DRO figures. It is not yet a complete numerical-equivalence reproduction
of every McCarthy 2018 thesis figure.
""",
        encoding="utf-8",
    )


def _write_numerical_audit(summary: dict[str, float | int | str]) -> None:
    NUMERICAL_AUDIT.write_text(
        f"""# Numerical Audit Appendix

This appendix records the main numerical evidence used by the current
reproduction status. It is generated by `scripts/sync_route_h_report_status.py`.

## A. Fig. 3.16 / Fig. 3.17 Route H quasi-DRO audit

Source files:

- `data/computed/chapter3_fixed_mapping_cache_accepted_family.csv`
- `data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv`
- `data/computed/chapter3_fixed_mapping_cache_audit.csv`
- `docs/chapter3_fixed_mapping_cache_audit.md`
- `data/computed/mccarthy2018_staged_goal_gate_status.csv`

Current accepted Route H evidence:

| metric | value |
|---|---:|
| accepted validation rows | `{summary['rows']}` |
| rows above 10,500 km | `{summary['ge_10500']}` |
| rows above 11,000 km | `{summary['ge_11000']}` |
| max abs z | `{_fmt(summary['max_z'])}` km |
| rho range | `{_fmt(summary['min_rho'])}` .. `{_fmt(summary['max_rho'])}` rad |
| fixed mapping time | `{_fmt(summary['mapping_time'])}` days |
| max map residual | `{_fmt(summary['max_residual'])}` |
| max curve Jacobi span | `{_fmt(summary['max_curve_jacobi_span'])}` |
| max one-map Jacobi drift | `{_fmt(summary['max_one_map_jacobi_drift'])}` |
| max ten-return Jacobi span | `{_fmt(summary['max_ten_return_jacobi_span'])}` |
| max one-map phase return error | `{_fmt(summary['max_phase_error'])}` |

Interpretation: the old local-only quasi-DRO bottleneck no longer controls the
Fig. 3.16 / Fig. 3.17 source layer. Route H is the current accepted CR3BP
fixed-time source branch for those figures.

Boundary: Route H is not McCarthy original raw branch data. It is an audited
reproduction source layer. Exact thesis equivalence still requires original
branch states, tables, author code, or another direct high-authority comparison.

## B. Fig. 3.10 period-q audit

Fig. 3.10 remains `shape-match with local numerical overlay`. q=2 and q=3 have
good local closure and Jacobi evidence. q=8 is internally consistent as a
multiple-shooting patch solution, but full-period single integration closure
remains unreliable on a highly unstable orbit.

## C. Chapter 4 DG/manifold audit

Chapter 4 has corrected source-curve residuals, DG eigenvector propagation, and
Jacobi drift evidence. The Route H quasi-DRO source-layer figure is available,
but original thesis-scale L1 quasi-halo/quasi-vertical global manifold
replacement remains a separate task.

## D. Chapter 5 source-layer audit

Chapter 5 has Route H/DE421, BCR4BP dynamics, segment-correction, and
optimized-transfer source-layer audits. These improve the application layer, but
per-original-figure high-fidelity equivalence still requires endpoint, delta-v,
ephemeris, and model-consistency evidence where applicable.
""",
        encoding="utf-8",
    )


def _write_presentation_outline(summary: dict[str, float | int | str]) -> None:
    PRESENTATION_OUTLINE.write_text(
        f"""# Presentation Outline

## 1. Objective

Explain that the project is an auditable engineering reproduction of McCarthy
2018 figures, not a claim of complete thesis numerical equivalence.

## 2. Current Coverage

Show the 54-figure status table from
`docs/reproduction_report/figure_status_appendix.md`.

## 3. Core Upgrade: Chapter 3 Route H

Suggested figure/table: Fig. 3.16, Fig. 3.17, and
`data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv`.

Speaker notes:

- Route H accepted validation rows: `{summary['rows']}`.
- Best fixed-time quasi-DRO max abs z: `{_fmt(summary['max_z'])}` km.
- Rows above 10,500 km: `{summary['ge_10500']}`.
- Rows above 11,000 km: `{summary['ge_11000']}`.
- Max map residual: `{_fmt(summary['max_residual'])}`.
- Max one-map Jacobi drift: `{_fmt(summary['max_one_map_jacobi_drift'])}`.

Message: Fig. 3.16 / Fig. 3.17 now have an accepted fixed-time source layer.
Do not call this original McCarthy raw branch data.

## 4. Remaining Boundaries

- Fig. 3.10 q=8 is local multiple shooting, not a robust single-shoot periodic
  orbit.
- Chapter 4 Route H source-layer evidence is not the same as full replacement
  of original L1 quasi-halo/quasi-vertical global manifold figures.
- Chapter 5 source-layer BCR4BP/optimization audits do not replace every thesis
  application figure.

## 5. Next Work

Choose one of three focused tracks: original branch-data search, Chapter 4
thesis-scale manifold replacement, or Chapter 5 per-figure high-fidelity
equivalence audits.
""",
        encoding="utf-8",
    )


def _write_fig316_digitization_note(summary: dict[str, float | int | str]) -> None:
    FIG316_DIGITIZATION.write_text(
        f"""# Fig. 3.16 Digitization Feasibility

Fig. 3.16 is a static 3D torus rendering. It remains unsuitable for precise
3D digitization from the image alone because the camera, projection model, and
raw branch states are not encoded in the bitmap.

Current status: digitization is no longer needed to justify the Fig. 3.16 source
layer. The current figure uses the accepted Route H fixed-time quasi-DRO branch
from `data/computed/chapter3_fixed_mapping_cache_accepted_family.csv`.

Route H evidence:

- accepted validation rows: `{summary['rows']}`
- best max abs z: `{_fmt(summary['max_z'])}` km
- rows above 10,500 km: `{summary['ge_10500']}`
- rows above 11,000 km: `{summary['ge_11000']}`
- max map residual: `{_fmt(summary['max_residual'])}`

The static original figure can still be used as a qualitative visual reference,
but not as a raw numerical data source.
""",
        encoding="utf-8",
    )


def _replace_span(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.find(start_marker)
    if start == -1:
        return text
    end = text.find(end_marker, start)
    if end == -1:
        return text
    end += len(end_marker)
    return text[:start] + replacement + text[end:]


def _upsert_readme_note(summary: dict[str, float | int | str]) -> None:
    text = README.read_text(encoding="utf-8")
    note = f"""{SYNC_START}
## Current Route H Status Note

As of the current staged gate audit, Chapter 3 Fig. 3.16 / Fig. 3.17 should be
read from the Route H fixed-mapping quasi-DRO source branch, not from the older
local-only 10,164 km bottleneck description. Route H accepted validation rows:
`{summary['rows']}`; best max abs z: `{_fmt(summary['max_z'])}` km; rows above
10,500 km: `{summary['ge_10500']}`; rows above 11,000 km:
`{summary['ge_11000']}`. This promotes the Chapter 3 source layer, but it does
not make the whole thesis a complete numerical-equivalence reproduction.
{SYNC_END}"""
    current_paragraph = (
        "Figures 3.16-3.17 now use the Route H fixed-mapping quasi-DRO source "
        "branch recorded in `data/computed/chapter3_fixed_mapping_cache_accepted_family.csv` "
        "and `data/computed/chapter3_fixed_mapping_cache_accepted_validation.csv`. "
        f"The accepted Route H range is mapping time {_fmt(summary['mapping_time'])} days, "
        f"rho {_fmt(summary['min_rho'])}-{_fmt(summary['max_rho'])} rad, and max abs z "
        f"{_fmt(summary['min_z'])}-{_fmt(summary['max_z'])} km. The Route H audit has "
        f"{summary['ge_10500']} rows above 10,500 km and {summary['ge_11000']} rows above "
        f"11,000 km, with max map residual {_fmt(summary['max_residual'])} and max one-map "
        f"Jacobi drift {_fmt(summary['max_one_map_jacobi_drift'])}. Fig. 3.16 renders "
        "corrected Route H tori directly; Fig. 3.17 plots Route H as the audited "
        "branch and keeps the reference trend only as context. This supersedes the "
        "older local-only PALC/Route B endpoint discussion for the figure-source layer, "
        "while preserving the boundary that the full thesis is not yet a complete "
        "numerical-equivalence reproduction."
    )
    text = _replace_span(
        text,
        "Figures 3.16-3.17 now have a dedicated quasi-DRO audit table at",
        "not a pure spectral-resolution limit.",
        current_paragraph,
    )
    if SYNC_START in text and SYNC_END in text:
        start = text.index(SYNC_START)
        end = text.index(SYNC_END, start) + len(SYNC_END)
        text = text[:start] + note + text[end:]
    else:
        first_heading_end = text.find("\n\n")
        if first_heading_end == -1:
            text = note + "\n\n" + text
        else:
            text = text[: first_heading_end + 2] + note + "\n\n" + text[first_heading_end + 2 :]
    README.write_text(text, encoding="utf-8")


def _scrub_future_work_note() -> None:
    text = FUTURE_WORK.read_text(encoding="utf-8")
    text = text.replace("old `10164.02309965055` km endpoint", "old local Route B endpoint")
    FUTURE_WORK.write_text(text, encoding="utf-8")


def main() -> None:
    summary = _route_h_summary()
    rows = _update_figure_validation_table(summary)
    _render_figure_status_appendix(rows)
    _write_proxy_usage_appendix(rows, summary)
    _write_teacher_package(rows, summary)
    _write_qa(summary)
    _write_public_report(rows, summary)
    _write_numerical_audit(summary)
    _write_presentation_outline(summary)
    _write_fig316_digitization_note(summary)
    _upsert_readme_note(summary)
    _scrub_future_work_note()
    print(f"updated {FIGURE_VALIDATION.relative_to(PROJECT_ROOT)}")
    print(f"updated {FIGURE_STATUS_APPENDIX.relative_to(PROJECT_ROOT)}")
    print(f"updated {PROXY_USAGE_APPENDIX.relative_to(PROJECT_ROOT)}")
    print(f"updated {TEACHER_README.relative_to(PROJECT_ROOT)}")
    print(f"updated {KEY_RESULTS.relative_to(PROJECT_ROOT)}")
    print(f"updated {ONE_PAGE_SUMMARY.relative_to(PROJECT_ROOT)}")
    print(f"updated {QA.relative_to(PROJECT_ROOT)}")
    print(f"updated {MAIN_REPORT.relative_to(PROJECT_ROOT)}")
    print(f"updated {NUMERICAL_AUDIT.relative_to(PROJECT_ROOT)}")
    print(f"updated {PRESENTATION_OUTLINE.relative_to(PROJECT_ROOT)}")
    print(f"updated {FIG316_DIGITIZATION.relative_to(PROJECT_ROOT)}")
    print(f"updated {FUTURE_WORK.relative_to(PROJECT_ROOT)}")
    print(f"updated {README.relative_to(PROJECT_ROOT)}")
    print(
        "route_h_summary: "
        f"rows={summary['rows']}, max_z={_fmt(summary['max_z'])} km, "
        f"ge_10500={summary['ge_10500']}, ge_11000={summary['ge_11000']}"
    )


if __name__ == "__main__":
    main()
