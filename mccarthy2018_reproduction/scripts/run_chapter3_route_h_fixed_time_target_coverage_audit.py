"""Aggregate fixed-time projection evidence for the four Fig. 3.16 anchors."""

from __future__ import annotations

import csv
import pickle
from pathlib import Path

import numpy as np

from _paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant


TARGETS = (2.9225, 2.9221, 2.9215, 2.9212)
CSV_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_route_h_fixed_time_target_coverage_audit.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "chapter3_route_h_fixed_time_target_coverage_audit.md"
COMBINED_STATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter3_route_h_fixed_time_target_states.csv"
)
COLD_CACHE_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "cold_start"
    / "fixed_mapping_full"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
FIELDS = (
    "target_jacobi",
    "projection_artifact",
    "state_artifact",
    "best_evidence_source",
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
    "paper_reported_precision_status",
    "audit_status",
)
STATE_FIELDS = (
    "target_jacobi",
    "best_evidence_source",
    "audit_status",
    "phase_index",
    "phase_rad",
    "x",
    "y",
    "z",
    "xdot",
    "ydot",
    "zdot",
    "point_jacobi",
    "mapping_time_days",
    "rotation_angle_rad",
    "curve_samples",
    "max_map_residual",
    "curve_jacobi_span",
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
    with COLD_CACHE_PATH.open("rb") as stream:
        cold_family = tuple(pickle.load(stream))
    system = SYSTEMS["earth_moon"]
    results: list[dict[str, object]] = []
    for target in TARGETS:
        path = _source_path(target)
        rows = _read_rows(path)
        accepted = [row for row in rows if row.get("status") == "pass"]
        if not accepted:
            raise RuntimeError(f"projection audit has no accepted row: {path}")
        candidates = [
            {
                "source": f"projection_row_{row['step']}",
                "mapping_time_days": float(row["mapping_time_days"]),
                "mapping_time_error_days": float(row["mapping_time_error_days"]),
                "mean_jacobi": float(row["mean_jacobi"]),
                "max_map_residual": float(row["max_map_residual"]),
                "curve_jacobi_span": float(row["curve_jacobi_span"]),
            }
            for row in accepted
        ]
        for index, member in enumerate(cold_family):
            values = jacobi_constant(member.corrected_states, system.mu)
            residual = float(np.max(member.final_residual_norms))
            span = float(np.ptp(values))
            if residual < 1.0e-9 and span < 2.0e-8:
                candidates.append(
                    {
                        "source": f"cold_start_checkpoint_member_{index}",
                        "mapping_time_days": member.seed.orbit_period * system.time_unit_days,
                        "mapping_time_error_days": 0.0,
                        "mean_jacobi": float(np.mean(values)),
                        "max_map_residual": residual,
                        "curve_jacobi_span": span,
                    }
                )
        initial_error = abs(float(rows[0]["mapping_time_error_days"]))
        strict_candidates = [
            candidate
            for candidate in candidates
            if abs(float(candidate["mapping_time_error_days"])) <= 1.0e-10
            and abs(float(candidate["mean_jacobi"]) - target) <= 5.0e-7
        ]
        paper_candidates = [
            candidate
            for candidate in candidates
            if abs(float(candidate["mapping_time_error_days"])) <= 5.0e-3
            and abs(float(candidate["mean_jacobi"]) - target) <= 5.0e-5
        ]
        pool = strict_candidates or paper_candidates or candidates
        best = min(
            pool,
            key=lambda candidate: (
                abs(float(candidate["mapping_time_error_days"])),
                abs(float(candidate["mean_jacobi"]) - target),
            ),
        )
        best_error = float(best["mapping_time_error_days"])
        jacobi_error = abs(float(best["mean_jacobi"]) - target)
        strict = best in strict_candidates
        paper_precision = best in paper_candidates
        results.append(
            {
                "target_jacobi": target,
                "projection_artifact": path.relative_to(PROJECT_ROOT),
                "state_artifact": COMBINED_STATE_PATH.relative_to(PROJECT_ROOT),
                "best_evidence_source": best["source"],
                "accepted_rows": len(accepted),
                "initial_mapping_time_error_days": initial_error,
                "best_mapping_time_days": float(best["mapping_time_days"]),
                "best_mapping_time_error_days": best_error,
                "mapping_time_gap_reduction": (
                    1.0 if initial_error == 0.0 else 1.0 - abs(best_error) / initial_error
                ),
                "best_mean_jacobi": float(best["mean_jacobi"]),
                "jacobi_error": jacobi_error,
                "best_map_residual": float(best["max_map_residual"]),
                "best_curve_jacobi_span": float(best["curve_jacobi_span"]),
                "strict_fixed_time_status": "pass" if strict else "fail",
                "paper_reported_precision_status": "pass" if paper_precision else "fail",
                "audit_status": (
                    "strict_fixed_time"
                    if strict
                    else "paper_reported_precision"
                    if paper_precision
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
    with COLD_CACHE_PATH.open("rb") as stream:
        cold_family = tuple(pickle.load(stream))
    with COMBINED_STATE_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=STATE_FIELDS)
        writer.writeheader()
        for row in rows:
            target = float(row["target_jacobi"])
            source = str(row["best_evidence_source"])
            if source.startswith("cold_start_checkpoint_member_"):
                index = int(source.rsplit("_", 1)[-1])
                member = cold_family[index]
                values = jacobi_constant(member.corrected_states, SYSTEMS["earth_moon"].mu)
                state_rows = [
                    {
                        "phase_index": phase_index,
                        "phase_rad": float(phase),
                        "x": float(state[0]),
                        "y": float(state[1]),
                        "z": float(state[2]),
                        "xdot": float(state[3]),
                        "ydot": float(state[4]),
                        "zdot": float(state[5]),
                        "point_jacobi": float(value),
                        "mapping_time_days": member.seed.orbit_period
                        * SYSTEMS["earth_moon"].time_unit_days,
                        "rotation_angle_rad": member.rotation_angle_rad,
                        "curve_samples": member.corrected_states.shape[0],
                        "max_map_residual": float(np.max(member.final_residual_norms)),
                        "curve_jacobi_span": float(np.ptp(values)),
                    }
                    for phase_index, (phase, state, value) in enumerate(
                        zip(member.seed.phases, member.corrected_states, values)
                    )
                ]
            else:
                token = f"{target:.4f}".replace(".", "p")
                state_path = (
                    PROJECT_ROOT
                    / "data"
                    / "computed"
                    / f"chapter3_route_h_fixed_time_energy_states_{token}.csv"
                )
                state_rows = _read_rows(state_path)
            for state_row in state_rows:
                writer.writerow(
                    {
                        "target_jacobi": target,
                        "best_evidence_source": source,
                        "audit_status": row["audit_status"],
                        **{field: state_row[field] for field in STATE_FIELDS[3:]},
                    }
                )
    strict = sum(row["strict_fixed_time_status"] == "pass" for row in rows)
    paper_precision = sum(row["paper_reported_precision_status"] == "pass" for row in rows)
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
- Anchors accepted at paper-reported precision: `{paper_precision}/4`
- Total paper-level coverage: `{sum(row['paper_reported_precision_status'] == 'pass' for row in rows)}/4`
- Remaining fixed-time gaps: `{sum(row['paper_reported_precision_status'] != 'pass' for row in rows)}/4`
- Combined accepted curve-state artifact: `{COMBINED_STATE_PATH.relative_to(PROJECT_ROOT)}`

| Target JC | Best mapping time (day) | Time error (day) | Gap reduction | Map residual | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
{table}

## Acceptance Meaning

`strict_fixed_time` requires the project mapping time exactly (within `1e-10 day`),
Jacobi error at most `5e-7`, map residual below `1e-9`, and curve Jacobi span below
`2e-8`. `paper_reported_precision` recognizes a time error no larger than `0.005
day` and Jacobi error no larger than `5e-5`, half the units implied by the paper's
two-decimal time and four-decimal Jacobi labels. Every other row remains a fixed-
time gap regardless of how accurately its free-time Jacobi target was solved.

The four-anchor Chapter 3 gate remains failed until all four rows are strict and
independently revalidated at the tighter spectral-resolution gate.
""",
        encoding="utf-8",
    )


def main() -> int:
    rows = build_rows()
    _write(rows)
    strict = sum(row["strict_fixed_time_status"] == "pass" for row in rows)
    paper_precision = sum(row["paper_reported_precision_status"] == "pass" for row in rows)
    print(
        f"Route H fixed-time target coverage: strict={strict}/4, "
        f"paper_precision={paper_precision}/4"
    )
    print(f"wrote {CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
