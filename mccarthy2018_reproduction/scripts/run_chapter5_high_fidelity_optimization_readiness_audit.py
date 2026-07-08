"""Audit Chapter 5 high-fidelity and optimization readiness.

This script does not claim a high-fidelity solution.  It records the concrete
gap between the current Route H / DE421 geometry baseline and the missing
BCR4BP, ephemeris-corrected shooting, and optimized-transfer layers.
"""

from __future__ import annotations

import ast
import csv
import re
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
DATA = PROJECT_ROOT / "data" / "computed"
DOCS = PROJECT_ROOT / "docs"

OUTPUT = DATA / "chapter5_high_fidelity_optimization_readiness_audit.csv"
DOC_OUTPUT = DOCS / "chapter5_high_fidelity_optimization_readiness_audit.md"

UPSTREAM_AUDIT = DATA / "chapter5_upstream_application_gate_audit.csv"
BCR4BP_AUDIT = DATA / "chapter5_bcr4bp_dynamics_audit.csv"
BCR4BP_CORRECTION_AUDIT = DATA / "chapter5_bcr4bp_segment_correction_audit.csv"
EPHEMERIS_CORRECTION_AUDIT = DATA / "chapter5_ephemeris_correction_audit.csv"
OPTIMIZED_TRANSFER_AUDIT = DATA / "chapter5_optimized_transfer_audit.csv"
OPTIMIZED_TRANSFER_FIGURE_PNG = PROJECT_ROOT / "outputs" / "figures_png" / "fig_5_bcr4bp_optimized_transfer.png"
OPTIMIZED_TRANSFER_FIGURE_PDF = PROJECT_ROOT / "outputs" / "figures_pdf" / "fig_5_bcr4bp_optimized_transfer.pdf"

FIELDS = (
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
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if np.isfinite(number):
            return f"{number:.16g}"
        return str(number)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _artifact(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _row(
    *,
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


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _files_matching(root: Path, pattern: str) -> list[Path]:
    regex = re.compile(pattern, flags=re.IGNORECASE)
    matches: list[Path] = []
    for path in _python_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        if regex.search(text):
            matches.append(path)
    return matches


def _function_names(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _symbol_files_matching(root: Path, pattern: str) -> list[Path]:
    regex = re.compile(pattern, flags=re.IGNORECASE)
    matches: list[Path] = []
    for path in _python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        names = [path.stem]
        names.extend(node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef)))
        if any(regex.search(name) for name in names):
            matches.append(path)
    return matches


def _accepted_rows(path: Path) -> int:
    rows = _read_rows(path)
    if not rows:
        return 0
    accepted_keys = (
        "accepted",
        "acceptance",
        "overall_acceptance",
        "strict_acceptance",
        "optimization_acceptance",
        "correction_acceptance",
    )
    count = 0
    for row in rows:
        values = {
            key: str(value).strip().lower()
            for key, value in row.items()
            if key and any(token in key.lower() for token in accepted_keys)
        }
        if any(value in {"true", "pass", "accepted"} for value in values.values()):
            count += 1
    return count


def _upstream_route_h_baseline_passes() -> tuple[bool, str, str]:
    rows = _read_rows(UPSTREAM_AUDIT)
    by_gate = {row.get("gate_id", ""): row for row in rows}
    baseline = by_gate.get("C5-ROUTE-H-DE421-BASELINE", {})
    route_h = by_gate.get("C5-UPSTREAM-ROUTE-H-INPUT", {})
    passes = baseline.get("status") == "pass" and route_h.get("status") == "pass"
    return passes, baseline.get("value", ""), route_h.get("value", "")


def _build_rows() -> list[dict[str, Any]]:
    baseline_passes, fig56_bytes, route_h_km = _upstream_route_h_baseline_passes()

    bcr4bp_sources = _symbol_files_matching(SRC, r"(BCR4BP|bicircular|four_body)")
    bcr4bp_audit_rows = _accepted_rows(BCR4BP_AUDIT)
    bcr4bp_passes = bool(bcr4bp_sources) and bcr4bp_audit_rows > 0

    ephemeris_functions = _function_names(SRC / "qp_orbits" / "ephemeris.py")
    ephemeris_shooting_functions = sorted(
        name
        for name in ephemeris_functions
        if re.search(r"(shoot|multiple|correct|residual|constraint|defect|optimi)", name, re.IGNORECASE)
        and name not in {"embed_corrected_dro_in_de421"}
    )
    ephemeris_accepted_rows = _accepted_rows(EPHEMERIS_CORRECTION_AUDIT)
    bcr4bp_correction_rows = _accepted_rows(BCR4BP_CORRECTION_AUDIT)
    dynamics_correction_rows = bcr4bp_correction_rows + ephemeris_accepted_rows
    dynamics_correction_passes = dynamics_correction_rows > 0

    optimization_sources = _files_matching(
        SRC,
        r"\b(minimize|least_squares|SLSQP|trust-constr|differential_evolution|objective)\b",
    )
    optimized_transfer_rows = _accepted_rows(OPTIMIZED_TRANSFER_AUDIT)
    optimized_transfer_figure_passes = (
        OPTIMIZED_TRANSFER_FIGURE_PNG.exists()
        and OPTIMIZED_TRANSFER_FIGURE_PDF.exists()
        and OPTIMIZED_TRANSFER_FIGURE_PNG.stat().st_size > 0
        and OPTIMIZED_TRANSFER_FIGURE_PDF.stat().st_size > 0
    )
    optimized_transfer_passes = optimized_transfer_rows > 0 and optimized_transfer_figure_passes

    missing_capabilities = int(not bcr4bp_passes)
    missing_capabilities += int(not dynamics_correction_passes)
    missing_capabilities += int(not optimized_transfer_passes)

    rows = [
        _row(
            gate_id="C5-HF-ROUTE-H-BASELINE",
            requirement="High-fidelity work must start from an accepted Route H quasi-DRO and regenerated Chapter 5 DE421 baseline.",
            status="pass" if baseline_passes else "fail",
            metric="fig_5_6_png_bytes",
            value=fig56_bytes,
            threshold="> 0 with C5 upstream Route H pass",
            evidence_artifact=_artifact(UPSTREAM_AUDIT),
            decision="use_route_h_de421_baseline_as_initial_guess" if baseline_passes else "regenerate_upstream_chapter5_baseline",
            notes=f"Upstream Route H max abs z from gate audit is {route_h_km} km.",
        ),
        _row(
            gate_id="C5-HF-BCR4BP-DYNAMICS",
            requirement="Chapter 5 high-fidelity upgrade needs a BCR4BP or equivalent Sun-Earth-Moon dynamics model with an audit artifact.",
            status="pass" if bcr4bp_passes else "blocked_missing_bcr4bp_model",
            metric="accepted_bcr4bp_audit_rows",
            value=bcr4bp_audit_rows,
            threshold="> 0 accepted audit rows and >= 1 source module",
            evidence_artifact=(
                ";".join([*(str(_artifact(path)) for path in bcr4bp_sources), _artifact(BCR4BP_AUDIT)])
                if bcr4bp_sources
                else "none"
            ),
            decision="use_bcr4bp_kernel_for_next_correction_layer" if bcr4bp_passes else "implement_bcr4bp_model_before_claiming_high_fidelity",
            notes=f"Accepted BCR4BP audit rows: {bcr4bp_audit_rows}.",
        ),
        _row(
            gate_id="C5-HF-DYNAMICS-CORRECTION",
            requirement="Chapter 5 needs a BCR4BP or ephemeris defect-constrained correction layer before high-fidelity trajectory claims.",
            status=(
                "pass"
                if dynamics_correction_passes
                else "blocked_missing_dynamics_defect_correction"
            ),
            metric="accepted_dynamics_correction_rows",
            value=dynamics_correction_rows,
            threshold="> 0 accepted BCR4BP or ephemeris correction rows",
            evidence_artifact=f"{_artifact(BCR4BP_CORRECTION_AUDIT)};{_artifact(SRC / 'qp_orbits' / 'ephemeris.py')}",
            decision=(
                "use_bcr4bp_segment_correction_as_first_high_fidelity_correction_layer"
                if bcr4bp_correction_rows > 0
                else "add_ephemeris_defect_constraints_and_audit"
            ),
            notes=(
                f"Accepted BCR4BP correction rows: {bcr4bp_correction_rows}; "
                f"accepted ephemeris correction rows: {ephemeris_accepted_rows}; "
                f"detected ephemeris correction functions: {','.join(ephemeris_shooting_functions) or 'none'}."
            ),
        ),
        _row(
            gate_id="C5-HF-TRANSFER-OPTIMIZATION",
            requirement="Application-layer transfer figures need an explicit objective, optimizer settings, constraints, and accepted optimized rows.",
            status="pass" if optimized_transfer_passes else "blocked_missing_optimized_transfer_audit",
            metric="accepted_optimized_transfer_rows",
            value=optimized_transfer_rows,
            threshold="> 0 accepted optimized rows and figure artifacts exist",
            evidence_artifact=(
                f"{_artifact(OPTIMIZED_TRANSFER_AUDIT)};{_artifact(OPTIMIZED_TRANSFER_FIGURE_PNG)};"
                f"{_artifact(OPTIMIZED_TRANSFER_FIGURE_PDF)}"
            ),
            decision="route_h_bcr4bp_optimized_transfer_source_layer_ready" if optimized_transfer_passes else "define_transfer_objective_and_accepted_row_schema",
            notes=(
                "Accepted Route H/BCR4BP transfer rows are available and rendered as a source-layer figure."
                if optimized_transfer_passes
                else f"Candidate optimization source files detected: {len(optimization_sources)}."
            ),
        ),
        _row(
            gate_id="C5-HF-INTERFACE-CONTRACT",
            requirement="Next implementation must define model, free variables, constraints, objective, and acceptance thresholds before figure promotion.",
            status="interface_required",
            metric="required_interface_fields",
            value=5,
            threshold="model;free_variables;constraints;objective;acceptance_thresholds",
            evidence_artifact=f"{_artifact(OUTPUT)};{_artifact(DOC_OUTPUT)}",
            decision="implement_bcr4bp_ephemeris_optimization_interface",
            notes="Minimum interface: dynamics model, state/time/control variables, defect and event constraints, cost function, and accepted-row gates.",
        ),
        _row(
            gate_id="C5-HF-READINESS-STATUS",
            requirement="Record whether Chapter 5 can be promoted from Route H / DE421 baseline to high-fidelity or optimized reproduction.",
            status=(
                "pass"
                if baseline_passes and missing_capabilities == 0
                else "bounded_blocker_documented"
                if baseline_passes and missing_capabilities
                else "not_ready"
            ),
            metric="missing_high_fidelity_capabilities",
            value=missing_capabilities,
            threshold="0 for completed high-fidelity/optimization layer",
            evidence_artifact=f"{_artifact(OUTPUT)};{_artifact(DOC_OUTPUT)}",
            decision=(
                "chapter5_high_fidelity_optimization_source_layer_ready"
                if baseline_passes and missing_capabilities == 0
                else
                "implement_transfer_optimization_audit_next"
                if bcr4bp_passes and dynamics_correction_passes and not optimized_transfer_passes
                else
                "do_not_claim_high_fidelity_chapter5_until_interface_is_implemented"
                if missing_capabilities
                else "run_high_fidelity_figures"
            ),
            notes="A bounded blocker is acceptable evidence for planning, not a completed Chapter 5 high-fidelity result.",
        ),
    ]
    return rows


def _write_doc(rows: list[dict[str, Any]]) -> None:
    row_lines = "\n".join(
        f"- `{row['gate_id']}`: status `{row['status']}`, metric "
        f"`{row['metric']}` = `{_fmt(row['value'])}`, decision `{row['decision']}`"
        for row in rows
    )
    readiness = next(row for row in rows if row["gate_id"] == "C5-HF-READINESS-STATUS")
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 High-Fidelity / Optimization Readiness Audit

## Purpose

This audit records the remaining implementation boundary after the Route H
quasi-DRO branch became available to Chapter 5. It is intentionally stricter
than the DE421 geometry baseline: a plotted DE421 embedding is not a
BCR4BP/ephemeris-corrected or optimized trajectory.

## Gate Rows

{row_lines}

## Interface Required Next

The next implementation should introduce a small, auditable Chapter 5 interface
before regenerating application figures:

1. Dynamics model: BCR4BP or ephemeris-corrected Earth-Moon-Sun propagation.
2. Free variables: initial state, segment times, insertion phase, and optional
   impulse/control variables.
3. Constraints: segment continuity, endpoint/event targets, Jacobi or energy
   diagnostics where meaningful, eclipse/line-of-sight constraints when used.
4. Objective: transfer cost, defect norm, eclipse exposure, or a documented
   multi-objective scalarization.
5. Acceptance thresholds: residual, endpoint error, frame consistency,
   optimizer convergence, and figure-source provenance.

## Decision

Readiness status is `{readiness['status']}` with
`{readiness['metric']}` = `{_fmt(readiness['value'])}`. Chapter 5 can use the
Route H / DE421 baseline as an initial guess layer. The BCR4BP short-segment
defect-correction and transfer-optimization source layers now provide accepted
audit rows and rendered figure artifacts, but they remain source-layer evidence
rather than a full replacement of every original thesis application figure.
""",
        encoding="utf-8",
    )


def main() -> None:
    rows = _build_rows()
    _write_rows(rows)
    _write_doc(rows)
    readiness = next(row for row in rows if row["gate_id"] == "C5-HF-READINESS-STATUS")
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "chapter5 high-fidelity readiness audit: "
        f"status={readiness['status']}, missing_capabilities={readiness['value']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
