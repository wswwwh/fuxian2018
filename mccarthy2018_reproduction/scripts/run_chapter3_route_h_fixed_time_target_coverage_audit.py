"""Aggregate fixed-time projection evidence for the four Fig. 3.16 anchors."""

from __future__ import annotations

import csv
from pathlib import Path

from _paths import PROJECT_ROOT


TARGETS = (2.9225, 2.9221, 2.9215, 2.9212)
CSV_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_route_h_fixed_time_target_coverage_audit.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "chapter3_route_h_fixed_time_target_coverage_audit.md"
FIELDS = (
    "target_jacobi",
    "projection_artifact",
    "accepted_rows",
    "initial_mapping_time_error_days",
    "best_mapping_time_days",
    "best_mapping_time_error_days",
    "mapping_time_gap_reduction",
    "best_mean_jacobi",
    "jacobi_error",
    "best_map_residual",
    "best_curve_jacobi_span",
    "strict_fixed_time_status",
    "paper_rounding_boundary_status",
    "audit_status",
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _source_path(target: float) -> Path:
    token = f"{target:.4f}".replace(".", "p")
    return (
        PROJECT_ROOT
        / "data"
        / "computed"
        / f"chapter3_route_h_fixed_time_energy_projection_{token}.csv"
    )


def build_rows() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for target in TARGETS:
        path = _source_path(target)
        rows = _read_rows(path)
        accepted = [row for row in rows if row.get("status") == "pass"]
        if not accepted:
            raise RuntimeError(f"projection audit has no accepted row: {path}")
        best = min(accepted, key=lambda row: abs(float(row["mapping_time_error_days"])))
        initial_error = abs(float(rows[0]["mapping_time_error_days"]))
        best_error = float(best["mapping_time_error_days"])
        jacobi_error = abs(float(best["mean_jacobi"]) - target)
        strict = bool(abs(best_error) <= 1.0e-10 and jacobi_error <= 5.0e-7)
        rounding_boundary = bool(
            not strict
            and abs(best_error) <= 5.0e-3
            and jacobi_error <= 5.0e-7
            and float(best["max_map_residual"]) < 1.0e-9
            and float(best["curve_jacobi_span"]) < 2.0e-8
        )
        results.append(
            {
                "target_jacobi": target,
                "projection_artifact": path.relative_to(PROJECT_ROOT),
                "accepted_rows": len(accepted),
                "initial_mapping_time_error_days": initial_error,
                "best_mapping_time_days": float(best["mapping_time_days"]),
                "best_mapping_time_error_days": best_error,
                "mapping_time_gap_reduction": 1.0 - abs(best_error) / initial_error,
                "best_mean_jacobi": float(best["mean_jacobi"]),
                "jacobi_error": jacobi_error,
                "best_map_residual": float(best["max_map_residual"]),
                "best_curve_jacobi_span": float(best["curve_jacobi_span"]),
                "strict_fixed_time_status": "pass" if strict else "fail",
                "paper_rounding_boundary_status": "pass" if rounding_boundary else "fail",
                "audit_status": (
                    "strict_fixed_time"
                    if strict
                    else "paper_rounding_boundary"
                    if rounding_boundary
                    else "fixed_time_gap"
                ),
            }
        )
    return results


def _write(rows: list[dict[str, object]]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    strict = sum(row["strict_fixed_time_status"] == "pass" for row in rows)
    boundary = sum(row["paper_rounding_boundary_status"] == "pass" for row in rows)
    table = "\n".join(
        "| {target:.4f} | {time:.9f} | {error:.3e} | {reduction:.3%} | {residual:.3e} | {status} |".format(
            target=float(row["target_jacobi"]),
            time=float(row["best_mapping_time_days"]),
            error=float(row["best_mapping_time_error_days"]),
            reduction=float(row["mapping_time_gap_reduction"]),
            residual=float(row["best_map_residual"]),
            status=row["audit_status"],
        )
        for row in rows
    )
    DOC_PATH.write_text(
        f"""# Chapter 3 Route H Fixed-Time Target Coverage Audit

## Result

- Strict fixed-time anchors: `{strict}/4`
- Paper-rounding boundary anchors: `{boundary}/4`
- Remaining fixed-time gaps: `{4 - strict - boundary}/4`

| Target JC | Best mapping time (day) | Time error (day) | Gap reduction | Map residual | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
{table}

## Acceptance Meaning

`strict_fixed_time` requires the project mapping time exactly (within `1e-10 day`),
Jacobi error at most `5e-7`, map residual below `1e-9`, and curve Jacobi span below
`2e-8`. `paper_rounding_boundary` additionally recognizes a time error no larger
than `0.005 day`, half the unit implied by the paper's two-decimal mapping-time
label, but it is not counted as strict reproduction. Every other row remains a
fixed-time gap regardless of how accurately its free-time Jacobi target was solved.

The four-anchor Chapter 3 gate remains failed until all four rows are strict and
independently revalidated at the tighter spectral-resolution gate.
""",
        encoding="utf-8",
    )


def main() -> int:
    rows = build_rows()
    _write(rows)
    strict = sum(row["strict_fixed_time_status"] == "pass" for row in rows)
    boundary = sum(row["paper_rounding_boundary_status"] == "pass" for row in rows)
    print(f"Route H fixed-time target coverage: strict={strict}/4, boundary={boundary}/4")
    print(f"wrote {CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
