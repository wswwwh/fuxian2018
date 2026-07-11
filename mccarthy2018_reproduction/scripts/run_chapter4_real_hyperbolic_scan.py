"""Scan strict Route H members for valid real hyperbolic DG directions."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np

from _paths import PROJECT_ROOT
from run_chapter4_route_h_dg_manifold_audit import (
    DEFAULT_CACHE,
    ROUTE_H_AUDIT,
    _load_cache,
)
from qp_orbits.torus_stability import corrected_curve_dg, real_hyperbolic_eigen_index


OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter4_real_hyperbolic_scan.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter4_real_hyperbolic_scan.md"
FIELDS = (
    "member_index",
    "max_abs_z_km",
    "curve_samples",
    "dg_dimension",
    "determinant_error_from_one",
    "minimum_unstable_relative_imaginary",
    "minimum_stable_relative_imaginary",
    "selected_unstable_eigenvalue",
    "selected_stable_eigenvalue",
    "complex_reciprocity_error",
    "real_hyperbolic_status",
    "failure_reason",
)


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return f"{number:.16g}" if np.isfinite(number) else "N/A"
    return str(value)


def _strict_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return [row for row in rows if row.get("strict_acceptance", "").lower() == "true"]


def _minimum_relative_imaginary(eigenvalues: np.ndarray, *, branch: str) -> float:
    magnitudes = np.abs(eigenvalues)
    if branch == "unstable":
        candidates = eigenvalues[magnitudes > 1.0 + 1.0e-3]
    else:
        candidates = eigenvalues[magnitudes < 1.0 - 1.0e-3]
    if candidates.size == 0:
        return float("inf")
    return float(np.min(np.abs(np.imag(candidates)) / np.abs(candidates)))


def scan_member(
    member_index: int,
    correction: Any,
    *,
    max_abs_z_km: float,
    max_step: float,
    relative_imaginary_tolerance: float,
) -> dict[str, Any]:
    dg = corrected_curve_dg(correction, max_step=max_step)
    unstable_min = _minimum_relative_imaginary(dg.eigenvalues, branch="unstable")
    stable_min = _minimum_relative_imaginary(dg.eigenvalues, branch="stable")
    failure_reason = ""
    unstable_value: complex | None = None
    stable_value: complex | None = None
    reciprocity = float("nan")
    try:
        unstable_index = real_hyperbolic_eigen_index(
            dg,
            branch="unstable",
            relative_imaginary_tolerance=relative_imaginary_tolerance,
        )
        stable_index = real_hyperbolic_eigen_index(
            dg,
            branch="stable",
            relative_imaginary_tolerance=relative_imaginary_tolerance,
        )
        unstable_value = complex(dg.eigenvalues[unstable_index])
        stable_value = complex(dg.eigenvalues[stable_index])
        reciprocity = float(abs(unstable_value * stable_value - 1.0))
    except RuntimeError as error:
        failure_reason = str(error)
    accepted = bool(
        not failure_reason
        and abs(dg.determinant - 1.0) < 1.0e-9
        and reciprocity < 1.0e-8
    )
    return {
        "member_index": member_index,
        "max_abs_z_km": max_abs_z_km,
        "curve_samples": correction.corrected_states.shape[0],
        "dg_dimension": dg.map_jacobian.shape[0],
        "determinant_error_from_one": abs(dg.determinant - 1.0),
        "minimum_unstable_relative_imaginary": unstable_min,
        "minimum_stable_relative_imaginary": stable_min,
        "selected_unstable_eigenvalue": unstable_value or "N/A",
        "selected_stable_eigenvalue": stable_value or "N/A",
        "complex_reciprocity_error": reciprocity,
        "real_hyperbolic_status": "pass" if accepted else "fail",
        "failure_reason": failure_reason,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field, "")) for field in FIELDS})


def _write_doc(path: Path, rows: list[dict[str, Any]], tolerance: float) -> None:
    accepted = [row for row in rows if row["real_hyperbolic_status"] == "pass"]
    failed = [row for row in rows if row["real_hyperbolic_status"] != "pass"]
    accepted_indices = [int(row["member_index"]) for row in accepted]
    accepted_z = [float(row["max_abs_z_km"]) for row in accepted]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Chapter 4 Real-Hyperbolic Route H Scan

## Summary

- Strict Route H members scanned: `{len(rows)}`
- Real-hyperbolic passes: `{len(accepted)}`
- Failures: `{len(failed)}`
- Relative-imaginary tolerance: `{tolerance}`
- Passing member indices: `{accepted_indices}`
- Passing max-abs-z range: `{min(accepted_z) if accepted_z else 'N/A'}..{max(accepted_z) if accepted_z else 'N/A'} km`

## Decision Rule

A member passes only when both stable and unstable hyperbolic eigenvalues have
relative imaginary part at or below the stated tolerance, the DG determinant
error is below `1e-9`, and the selected complex pair has reciprocity error below
`1e-8`. A magnitude-only reciprocal pair is insufficient.

This scan selects candidates for a subsequent manifold audit. It does not itself
promote Chapter 4 or replace original Fig. 4.1-4.8.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--route-h-audit", type=Path, default=ROUTE_H_AUDIT)
    parser.add_argument("--max-step", type=float, default=0.02)
    parser.add_argument("--relative-imaginary-tolerance", type=float, default=1.0e-6)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--doc-output", type=Path, default=DOC_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    strict_rows = _strict_rows(args.route_h_audit)
    cached = _load_cache(args.cache)
    results: list[dict[str, Any]] = []
    for position, audit_row in enumerate(strict_rows, start=1):
        member_index = int(audit_row["member_index"])
        print(
            f"scan {position}/{len(strict_rows)}: member {member_index}",
            flush=True,
        )
        results.append(
            scan_member(
                member_index,
                cached[member_index],
                max_abs_z_km=float(audit_row["max_abs_z_km"]),
                max_step=args.max_step,
                relative_imaginary_tolerance=args.relative_imaginary_tolerance,
            )
        )
    _write_csv(args.output, results)
    _write_doc(args.doc_output, results, args.relative_imaginary_tolerance)
    accepted = sum(row["real_hyperbolic_status"] == "pass" for row in results)
    print(
        f"real-hyperbolic scan: {accepted}/{len(results)} pass; wrote {args.output}",
        flush=True,
    )
    return 0 if accepted > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
