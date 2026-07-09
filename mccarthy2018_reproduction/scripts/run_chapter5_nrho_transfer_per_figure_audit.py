"""Audit Fig. 5.10 / Fig. 5.11 NRHO transfer rows.

The existing Chapter 5 NRHO scene generator computes corrected periodic
boundaries and direct-shooting CR3BP two-impulse transfers at the thesis flight
times. This script exports those transfers as per-original-figure audit rows so
the repository records endpoint error, delta-v, Jacobi drift, and the remaining
model boundary explicitly.
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

from qp_orbits.application_scenarios import (  # noqa: E402
    TwoImpulseTransfer,
    earth_moon_nrho_transfer_baseline,
)

OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_nrho_transfer_per_figure_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_nrho_transfer_per_figure_audit.md"

FIELDS = (
    "figure_id",
    "case_id",
    "direction",
    "source_model",
    "departure_phase",
    "arrival_phase",
    "time_of_flight_days",
    "departure_delta_v_m_s",
    "arrival_delta_v_m_s",
    "total_delta_v_m_s",
    "endpoint_position_error_km",
    "minimum_moon_radius_km",
    "jacobi_span",
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

ENDPOINT_THRESHOLD_KM = 1.0e-3
JACOBI_SPAN_THRESHOLD = 1.0e-8
DELTA_V_THRESHOLD_M_S = 250.0


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


def _row(
    *,
    figure_id: str,
    case_id: int,
    direction: str,
    transfer: TwoImpulseTransfer,
    baseline: Any,
) -> dict[str, Any]:
    accepted = (
        transfer.endpoint_position_error_km <= ENDPOINT_THRESHOLD_KM
        and transfer.jacobi_span <= JACOBI_SPAN_THRESHOLD
        and transfer.total_delta_v_m_s <= DELTA_V_THRESHOLD_M_S
    )
    return {
        "figure_id": figure_id,
        "case_id": case_id,
        "direction": direction,
        "source_model": "Earth-Moon CR3BP direct shooting between corrected NRHO boundaries",
        "departure_phase": transfer.departure_phase,
        "arrival_phase": transfer.arrival_phase,
        "time_of_flight_days": transfer.time_of_flight_days,
        "departure_delta_v_m_s": transfer.departure_delta_v_m_s,
        "arrival_delta_v_m_s": transfer.arrival_delta_v_m_s,
        "total_delta_v_m_s": transfer.total_delta_v_m_s,
        "endpoint_position_error_km": transfer.endpoint_position_error_km,
        "minimum_moon_radius_km": transfer.minimum_moon_radius_km,
        "jacobi_span": transfer.jacobi_span,
        "departure_perilune_radius_km": baseline.departure_perilune_radius_km,
        "destination_perilune_radius_km": baseline.destination_perilune_radius_km,
        "departure_stability_index": baseline.departure_stability_index,
        "destination_stability_index": baseline.destination_stability_index,
        "departure_periodicity_error": baseline.departure_periodicity_error,
        "destination_periodicity_error": baseline.destination_periodicity_error,
        "acceptance": accepted,
        "threshold": (
            f"endpoint_position_error_km <= {ENDPOINT_THRESHOLD_KM}; "
            f"jacobi_span <= {JACOBI_SPAN_THRESHOLD}; total_delta_v_m_s <= {DELTA_V_THRESHOLD_M_S}"
        ),
        "evidence_artifact": "src/qp_orbits/application_scenarios.py;data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv",
        "boundary": (
            "Accepted CR3BP endpoint-corrected transfer row; not a BCR4BP/ephemeris "
            "high-fidelity replacement and not original McCarthy raw initial data."
        ),
        "notes": "Direct-shooting transfer exported for per-figure Fig. 5.10/5.11 audit.",
    }


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _write_doc(rows: list[dict[str, Any]]) -> None:
    accepted = [row for row in rows if row["acceptance"]]
    best = min(accepted, key=lambda row: float(row["total_delta_v_m_s"])) if accepted else None
    best_row = f"{best['figure_id']} case {best['case_id']}" if best else "N/A"
    table_lines = [
        "| figure | case | direction | TOF days | total delta-v m/s | endpoint error km | Jacobi span |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        table_lines.append(
            f"| {row['figure_id']} | {row['case_id']} | {row['direction']} | "
            f"{_fmt(row['time_of_flight_days'])} | {_fmt(row['total_delta_v_m_s'])} | "
            f"{_fmt(row['endpoint_position_error_km'])} | {_fmt(row['jacobi_span'])} |"
        )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 NRHO Transfer Per-Figure Audit

Generated by `scripts/run_chapter5_nrho_transfer_per_figure_audit.py`.

## Purpose

This audit promotes Fig. 5.10 and Fig. 5.11 from generic CR3BP baseline status
to explicit per-figure endpoint-corrected transfer rows. The rows are generated
from `qp_orbits.application_scenarios.earth_moon_nrho_transfer_baseline()`.

## Acceptance

- Accepted rows: `{len(accepted)}` / `{len(rows)}`
- Endpoint threshold: `{ENDPOINT_THRESHOLD_KM}` km
- Jacobi-span threshold: `{JACOBI_SPAN_THRESHOLD}`
- Total delta-v threshold: `{DELTA_V_THRESHOLD_M_S}` m/s
- Best total delta-v: `{_fmt(best['total_delta_v_m_s']) if best else 'N/A'}` m/s
- Best row: `{best_row}`

## Rows

{chr(10).join(table_lines)}

## Boundary

These rows are accepted CR3BP direct-shooting transfers between corrected NRHO
boundaries. They are stronger than a visual baseline because endpoint position
error, delta-v, and Jacobi span are recorded per figure. They are not yet
BCR4BP/ephemeris high-fidelity replacements for the original thesis transfers.
""",
        encoding="utf-8",
    )


def main() -> None:
    baseline = earth_moon_nrho_transfer_baseline()
    rows: list[dict[str, Any]] = []
    for index, transfer in enumerate(baseline.forward_transfers, start=1):
        rows.append(
            _row(
                figure_id="5.10",
                case_id=index,
                direction="forward",
                transfer=transfer,
                baseline=baseline,
            )
        )
    for index, transfer in enumerate(baseline.reverse_transfers, start=1):
        rows.append(
            _row(
                figure_id="5.11",
                case_id=index,
                direction="reverse_by_cr3bp_symmetry",
                transfer=transfer,
                baseline=baseline,
            )
        )
    _write_rows(rows)
    _write_doc(rows)
    accepted = sum(bool(row["acceptance"]) for row in rows)
    best = min(rows, key=lambda row: float(row["total_delta_v_m_s"]))
    print(f"updated {_artifact(OUTPUT)}")
    print(f"updated {_artifact(DOC_OUTPUT)}")
    print(
        "chapter5_nrho_transfer_per_figure_audit: "
        f"accepted={accepted}/{len(rows)}, best_delta_v={_fmt(best['total_delta_v_m_s'])} m/s, "
        f"best_endpoint_error={_fmt(best['endpoint_position_error_km'])} km"
    )


if __name__ == "__main__":
    main()
