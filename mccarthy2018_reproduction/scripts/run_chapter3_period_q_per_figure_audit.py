"""Audit Fig. 3.10 period-q halo evidence at per-figure scope.

The underlying Fig. 3.10 script already exports the corrected period-q halo
examples and the independent closure audit. This script converts those source
tables into a compact figure-level audit that separates robust single-shoot
periodic closure from local multiple-shooting consistency.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "computed"
DOCS = PROJECT_ROOT / "docs"

EXAMPLES = DATA / "period_q_halo_examples.csv"
CLOSURE_AUDIT = DATA / "period_q_halo_closure_audit.csv"
OUTPUT = DATA / "chapter3_period_q_per_figure_audit.csv"
DOC_OUTPUT = DOCS / "chapter3_period_q_per_figure_audit.md"

FIELDS = (
    "figure_id",
    "resonance",
    "source_model",
    "period_days",
    "frequency_ratio",
    "resonance_angle_error_rad",
    "multiple_shooting_residual_norm",
    "patch_to_patch_continuity_residual_norm",
    "max_patch_to_patch_continuity_residual",
    "terminal_symmetry_residual_norm",
    "full_period_single_shoot_closure_error",
    "half_period_single_shoot_symmetry_error",
    "trajectory_jacobi_drift",
    "max_monodromy_multiplier_abs",
    "strict_acceptance",
    "local_multiple_shooting_acceptance",
    "acceptance_class",
    "threshold",
    "evidence_artifact",
    "boundary",
    "notes",
)

MS_RESIDUAL_THRESHOLD = 1.0e-10
CONTINUITY_THRESHOLD = 1.0e-10
JACOBI_THRESHOLD = 1.0e-10
RESONANCE_ANGLE_THRESHOLD = 1.0e-6
STRICT_SINGLE_SHOOT_CLOSURE_THRESHOLD = 1.0e-6


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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _as_float(row: dict[str, str], field: str) -> float:
    value = float(row[field])
    if not np.isfinite(value):
        raise ValueError(f"{field} is not finite in row {row!r}")
    return value


def _rows() -> list[dict[str, Any]]:
    examples = {row["resonance"]: row for row in _read_csv(EXAMPLES)}
    closure_rows = _read_csv(CLOSURE_AUDIT)
    rows: list[dict[str, Any]] = []
    for closure in closure_rows:
        resonance = closure["resonance"]
        example = examples[resonance]
        ms_residual = _as_float(closure, "multiple_shooting_residual_norm")
        continuity = _as_float(closure, "patch_to_patch_continuity_residual_norm")
        angle_error = abs(_as_float(example, "resonance_angle_error_rad"))
        jacobi_drift = _as_float(closure, "trajectory_jacobi_drift")
        single_shoot_closure = _as_float(closure, "full_period_single_shoot_closure_error")
        local_acceptance = (
            ms_residual <= MS_RESIDUAL_THRESHOLD
            and continuity <= CONTINUITY_THRESHOLD
            and jacobi_drift <= JACOBI_THRESHOLD
            and angle_error <= RESONANCE_ANGLE_THRESHOLD
        )
        strict_acceptance = (
            local_acceptance
            and single_shoot_closure <= STRICT_SINGLE_SHOOT_CLOSURE_THRESHOLD
        )
        if strict_acceptance:
            acceptance_class = "strict_single_shoot_periodic"
            boundary = (
                "Accepted as a robust Fig. 3.10 period-q periodic-orbit row at "
                "the current audit thresholds."
            )
        elif local_acceptance:
            acceptance_class = "local_multiple_shooting_only"
            boundary = (
                "Accepted only as a local multiple-shooting row; full-period "
                "single-shoot closure is not reliable enough for a robust "
                "periodic-orbit reproduction claim."
            )
        else:
            acceptance_class = "not_accepted"
            boundary = "Fails the local multiple-shooting consistency threshold."
        rows.append(
            {
                "figure_id": "3.10",
                "resonance": resonance,
                "source_model": "Earth-Moon CR3BP period-q halo multiple-shooting audit",
                "period_days": _as_float(example, "period_days"),
                "frequency_ratio": _as_float(example, "frequency_ratio"),
                "resonance_angle_error_rad": _as_float(example, "resonance_angle_error_rad"),
                "multiple_shooting_residual_norm": ms_residual,
                "patch_to_patch_continuity_residual_norm": continuity,
                "max_patch_to_patch_continuity_residual": _as_float(
                    closure,
                    "max_patch_to_patch_continuity_residual",
                ),
                "terminal_symmetry_residual_norm": _as_float(
                    closure,
                    "terminal_symmetry_residual_norm",
                ),
                "full_period_single_shoot_closure_error": single_shoot_closure,
                "half_period_single_shoot_symmetry_error": _as_float(
                    closure,
                    "half_period_single_shoot_symmetry_error",
                ),
                "trajectory_jacobi_drift": jacobi_drift,
                "max_monodromy_multiplier_abs": _as_float(
                    closure,
                    "max_monodromy_multiplier_abs",
                ),
                "strict_acceptance": strict_acceptance,
                "local_multiple_shooting_acceptance": local_acceptance,
                "acceptance_class": acceptance_class,
                "threshold": (
                    f"multiple_shooting_residual_norm <= {MS_RESIDUAL_THRESHOLD}; "
                    f"patch_to_patch_continuity_residual_norm <= {CONTINUITY_THRESHOLD}; "
                    f"trajectory_jacobi_drift <= {JACOBI_THRESHOLD}; "
                    f"abs(resonance_angle_error_rad) <= {RESONANCE_ANGLE_THRESHOLD}; "
                    f"strict full_period_single_shoot_closure_error <= "
                    f"{STRICT_SINGLE_SHOOT_CLOSURE_THRESHOLD}"
                ),
                "evidence_artifact": f"{_artifact(EXAMPLES)};{_artifact(CLOSURE_AUDIT)}",
                "boundary": boundary,
                "notes": closure["diagnosis"],
            }
        )
    return rows


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _write_doc(rows: list[dict[str, Any]]) -> None:
    strict = [row for row in rows if row["strict_acceptance"]]
    local = [row for row in rows if row["local_multiple_shooting_acceptance"]]
    q8 = next((row for row in rows if str(row["resonance"]) == "8"), None)
    worst_local_residual = max(
        (float(row["multiple_shooting_residual_norm"]) for row in local),
        default=np.nan,
    )
    worst_local_jacobi = max(
        (float(row["trajectory_jacobi_drift"]) for row in local),
        default=np.nan,
    )
    table_lines = [
        "| q | period days | frequency ratio | angle error rad | MS residual | single-shoot closure | Jacobi drift | class |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        table_lines.append(
            f"| {row['resonance']} | {_fmt(row['period_days'])} | "
            f"{_fmt(row['frequency_ratio'])} | {_fmt(row['resonance_angle_error_rad'])} | "
            f"{_fmt(row['multiple_shooting_residual_norm'])} | "
            f"{_fmt(row['full_period_single_shoot_closure_error'])} | "
            f"{_fmt(row['trajectory_jacobi_drift'])} | {row['acceptance_class']} |"
        )
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Period-Q Per-Figure Audit

Generated by `scripts/run_chapter3_period_q_per_figure_audit.py`.

## Purpose

This audit maps the Fig. 3.10 q=2, q=3, and q=8 halo examples to explicit
per-figure evidence. It preserves the boundary between robust single-shoot
periodic closure and local multiple-shooting consistency.

## Acceptance

- Strict single-shoot accepted rows: `{len(strict)}` / `{len(rows)}`
- Local multiple-shooting accepted rows: `{len(local)}` / `{len(rows)}`
- Worst accepted local multiple-shooting residual: `{_fmt(worst_local_residual)}`
- Worst accepted local Jacobi drift: `{_fmt(worst_local_jacobi)}`
- q=8 full-period single-shoot closure error: `{_fmt(q8['full_period_single_shoot_closure_error']) if q8 else 'N/A'}`

## Rows

{chr(10).join(table_lines)}

## Boundary

q=2 and q=3 pass the stricter single-shoot periodic-orbit threshold in this
audit. q=8 passes the local multiple-shooting and Jacobi-consistency checks,
but it must not be promoted to a robust single-shoot full-period closure claim
until a high-instability validation path or an alternate closure audit is added.
""",
        encoding="utf-8",
    )


def main() -> None:
    rows = _rows()
    _write_rows(rows)
    _write_doc(rows)
    strict = sum(bool(row["strict_acceptance"]) for row in rows)
    local = sum(bool(row["local_multiple_shooting_acceptance"]) for row in rows)
    q8 = next((row for row in rows if str(row["resonance"]) == "8"), None)
    print(f"updated {_artifact(OUTPUT)}")
    print(f"updated {_artifact(DOC_OUTPUT)}")
    print(
        "chapter3_period_q_per_figure_audit: "
        f"strict={strict}/{len(rows)}, local={local}/{len(rows)}, "
        f"q8_single_shoot_closure={_fmt(q8['full_period_single_shoot_closure_error']) if q8 else 'N/A'}"
    )


if __name__ == "__main__":
    main()
