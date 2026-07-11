"""Audit Fig. 5.12 NRHO rendezvous arrival-time branch.

Figure 5.12 plots a fixed-departure, fixed-time-of-flight arrival-offset scan
from the Chapter 5 NRHO transfer baseline. This script exports the converged
CR3BP shooting branch as per-figure audit rows so the repository records
coverage, delta-v variation, and endpoint residual evidence explicitly.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.application_scenarios import earth_moon_nrho_transfer_baseline  # noqa: E402

OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_nrho_rendezvous_per_figure_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_nrho_rendezvous_per_figure_audit.md"

FIELDS = (
    "figure_id",
    "sample",
    "source_model",
    "fixed_departure_phase",
    "arrival_phase",
    "arrival_offset_hours",
    "time_of_flight_days",
    "total_delta_v_m_s",
    "delta_v_difference_m_s",
    "endpoint_position_error_km",
    "baseline_total_delta_v_m_s",
    "departure_perilune_radius_km",
    "destination_perilune_radius_km",
    "departure_stability_index",
    "destination_stability_index",
    "departure_periodicity_error",
    "destination_periodicity_error",
    "acceptance",
    "threshold",
    "evidence_artifact",
    "boundary",
    "notes",
)

RENDEZVOUS_SAMPLES = 49
MIN_ACCEPTED_ROWS = 35
MIN_RIGHT_COVERAGE_HOURS = 10.0
MAX_LEFT_COVERAGE_HOURS = -20.0
ENDPOINT_THRESHOLD_KM = 1.0e-3
DELTA_V_DIFFERENCE_THRESHOLD_M_S = 300.0


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


def _rows() -> list[dict[str, Any]]:
    baseline = earth_moon_nrho_transfer_baseline(rendezvous_samples=RENDEZVOUS_SAMPLES)
    reference = baseline.forward_transfers[0]
    rows: list[dict[str, Any]] = []
    for sample, (offset, arrival_phase, total_delta_v, delta_v_difference, endpoint_error) in enumerate(
        zip(
            baseline.rendezvous_offsets_hours,
            baseline.rendezvous_arrival_phases,
            baseline.rendezvous_total_delta_v_m_s,
            baseline.rendezvous_delta_v_difference_m_s,
            baseline.rendezvous_endpoint_error_km,
        )
    ):
        accepted = (
            endpoint_error <= ENDPOINT_THRESHOLD_KM
            and abs(delta_v_difference) <= DELTA_V_DIFFERENCE_THRESHOLD_M_S
        )
        rows.append(
            {
                "figure_id": "5.12",
                "sample": sample,
                "source_model": "Earth-Moon CR3BP fixed-departure NRHO rendezvous arrival-offset shooting",
                "fixed_departure_phase": reference.departure_phase,
                "arrival_phase": arrival_phase,
                "arrival_offset_hours": offset,
                "time_of_flight_days": reference.time_of_flight_days,
                "total_delta_v_m_s": total_delta_v,
                "delta_v_difference_m_s": delta_v_difference,
                "endpoint_position_error_km": endpoint_error,
                "baseline_total_delta_v_m_s": reference.total_delta_v_m_s,
                "departure_perilune_radius_km": baseline.departure_perilune_radius_km,
                "destination_perilune_radius_km": baseline.destination_perilune_radius_km,
                "departure_stability_index": baseline.departure_stability_index,
                "destination_stability_index": baseline.destination_stability_index,
                "departure_periodicity_error": baseline.departure_periodicity_error,
                "destination_periodicity_error": baseline.destination_periodicity_error,
                "acceptance": accepted,
                "threshold": (
                    f"endpoint_position_error_km <= {ENDPOINT_THRESHOLD_KM}; "
                    f"|delta_v_difference_m_s| <= {DELTA_V_DIFFERENCE_THRESHOLD_M_S}; "
                    f"branch accepted rows >= {MIN_ACCEPTED_ROWS}; "
                    f"left coverage <= {MAX_LEFT_COVERAGE_HOURS} h; "
                    f"right coverage >= {MIN_RIGHT_COVERAGE_HOURS} h"
                ),
                "evidence_artifact": (
                    "src/qp_orbits/application_scenarios.py;"
                    "data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv"
                ),
                "boundary": (
                    "Accepted local CR3BP fixed-departure rendezvous branch row; "
                    "not the thesis quasi-NRHO global continuation curve and not a "
                    "BCR4BP/ephemeris high-fidelity replacement."
                ),
                "notes": "Per-sample Fig. 5.12 rendezvous branch row from the current baseline generator.",
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


def _branch_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["acceptance"]]
    if not accepted:
        return {
            "accepted_rows": 0,
            "left_coverage": np.nan,
            "right_coverage": np.nan,
            "minimum_delta_v_difference": np.nan,
            "minimum_delta_v_offset": np.nan,
            "maximum_endpoint_error": np.nan,
            "branch_acceptance": False,
        }
    minimum = min(accepted, key=lambda row: float(row["delta_v_difference_m_s"]))
    left = min(float(row["arrival_offset_hours"]) for row in accepted)
    right = max(float(row["arrival_offset_hours"]) for row in accepted)
    max_endpoint = max(float(row["endpoint_position_error_km"]) for row in accepted)
    branch_acceptance = (
        len(accepted) >= MIN_ACCEPTED_ROWS
        and left <= MAX_LEFT_COVERAGE_HOURS
        and right >= MIN_RIGHT_COVERAGE_HOURS
        and max_endpoint <= ENDPOINT_THRESHOLD_KM
    )
    return {
        "accepted_rows": len(accepted),
        "left_coverage": left,
        "right_coverage": right,
        "minimum_delta_v_difference": float(minimum["delta_v_difference_m_s"]),
        "minimum_delta_v_offset": float(minimum["arrival_offset_hours"]),
        "maximum_endpoint_error": max_endpoint,
        "branch_acceptance": branch_acceptance,
    }


def _write_doc(rows: list[dict[str, Any]]) -> None:
    metrics = _branch_metrics(rows)
    table_lines = [
        "| sample | offset h | arrival phase | total delta-v m/s | delta-v diff m/s | endpoint error km | accepted |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        table_lines.append(
            f"| {row['sample']} | {_fmt(row['arrival_offset_hours'])} | "
            f"{_fmt(row['arrival_phase'])} | {_fmt(row['total_delta_v_m_s'])} | "
            f"{_fmt(row['delta_v_difference_m_s'])} | "
            f"{_fmt(row['endpoint_position_error_km'])} | {_fmt(row['acceptance'])} |"
        )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 NRHO Rendezvous Per-Figure Audit

Generated by `scripts/run_chapter5_nrho_rendezvous_per_figure_audit.py`.

## Purpose

This audit promotes Fig. 5.12 from a visual local overlay to an explicit
fixed-departure CR3BP arrival-offset branch. Rows are generated from
`qp_orbits.application_scenarios.earth_moon_nrho_transfer_baseline()` with
`rendezvous_samples={RENDEZVOUS_SAMPLES}`.

## Acceptance

- Accepted rows: `{metrics['accepted_rows']}` / `{len(rows)}`
- Branch accepted: `{_fmt(metrics['branch_acceptance'])}`
- Left coverage: `{_fmt(metrics['left_coverage'])}` h
- Right coverage: `{_fmt(metrics['right_coverage'])}` h
- Minimum delta-v difference: `{_fmt(metrics['minimum_delta_v_difference'])}` m/s
- Minimum delta-v offset: `{_fmt(metrics['minimum_delta_v_offset'])}` h
- Maximum endpoint error: `{_fmt(metrics['maximum_endpoint_error'])}` km
- Endpoint threshold: `{ENDPOINT_THRESHOLD_KM}` km
- Delta-v-difference threshold: `{DELTA_V_DIFFERENCE_THRESHOLD_M_S}` m/s

## Rows

{chr(10).join(table_lines)}

## Boundary

The accepted branch is a local CR3BP fixed-departure, fixed-time-of-flight
arrival-offset shooting branch. It replaces the prior un-audited blue curve with
machine-readable endpoint and delta-v evidence, but it does not replace the
grey thesis-shaped proxy beyond the fold and does not claim BCR4BP/ephemeris
or original McCarthy raw-data equivalence.
""",
        encoding="utf-8",
    )


def main() -> None:
    rows = _rows()
    _write_rows(rows)
    _write_doc(rows)
    metrics = _branch_metrics(rows)
    print(f"updated {_artifact(OUTPUT)}")
    print(f"updated {_artifact(DOC_OUTPUT)}")
    print(
        "chapter5_nrho_rendezvous_per_figure_audit: "
        f"accepted={metrics['accepted_rows']}/{len(rows)}, "
        f"branch_acceptance={_fmt(metrics['branch_acceptance'])}, "
        f"coverage=[{_fmt(metrics['left_coverage'])}, {_fmt(metrics['right_coverage'])}] h, "
        f"min_delta_v_diff={_fmt(metrics['minimum_delta_v_difference'])} m/s, "
        f"max_endpoint_error={_fmt(metrics['maximum_endpoint_error'])} km"
    )


if __name__ == "__main__":
    main()
