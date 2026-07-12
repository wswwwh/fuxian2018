"""Audit Fig. 5.9 corrected NRHO boundary and departure-marker evidence.

Figure 5.9 shows a corrected periodic-NRHO family spanning the 4,800 km and
12,610 km boundaries plus candidate departure locations. This script audits
both the full family and the direct-shooting departure markers.
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

OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_nrho_corridor_per_figure_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_nrho_corridor_per_figure_audit.md"

FIELDS = (
    "figure_id",
    "case_id",
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
    "corridor_surface_samples",
    "corridor_family_members",
    "corridor_min_perilune_radius_km",
    "corridor_max_perilune_radius_km",
    "corridor_max_periodicity_error",
    "acceptance",
    "threshold",
    "evidence_artifact",
    "boundary",
    "notes",
)

ENDPOINT_THRESHOLD_KM = 1.0e-3
JACOBI_SPAN_THRESHOLD = 1.0e-8
PERIODICITY_THRESHOLD = 1.0e-8
DELTA_V_THRESHOLD_M_S = 250.0
MIN_MOON_RADIUS_KM = 2_000.0
RADIUS_TOLERANCE_KM = 0.1


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


def _row(case_id: int, transfer: TwoImpulseTransfer, baseline: Any) -> dict[str, Any]:
    accepted = (
        transfer.endpoint_position_error_km <= ENDPOINT_THRESHOLD_KM
        and transfer.jacobi_span <= JACOBI_SPAN_THRESHOLD
        and transfer.total_delta_v_m_s <= DELTA_V_THRESHOLD_M_S
        and transfer.minimum_moon_radius_km >= MIN_MOON_RADIUS_KM
        and baseline.departure_periodicity_error <= PERIODICITY_THRESHOLD
        and baseline.destination_periodicity_error <= PERIODICITY_THRESHOLD
        and abs(baseline.departure_perilune_radius_km - 4_800.0) <= RADIUS_TOLERANCE_KM
        and abs(baseline.destination_perilune_radius_km - 12_610.0) <= RADIUS_TOLERANCE_KM
        and len(baseline.corridor_orbits) >= 16
        and np.all(np.diff(baseline.corridor_perilune_radius_km) > 0.0)
        and np.max(baseline.corridor_periodicity_error) <= PERIODICITY_THRESHOLD
    )
    return {
        "figure_id": "5.9",
        "case_id": case_id,
        "source_model": "Earth-Moon CR3BP corrected periodic NRHO family with direct-shooting departure markers",
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
        "corridor_surface_samples": int(np.prod(baseline.corridor_surface.shape[:2])),
        "corridor_family_members": len(baseline.corridor_orbits),
        "corridor_min_perilune_radius_km": float(np.min(baseline.corridor_perilune_radius_km)),
        "corridor_max_perilune_radius_km": float(np.max(baseline.corridor_perilune_radius_km)),
        "corridor_max_periodicity_error": float(np.max(baseline.corridor_periodicity_error)),
        "acceptance": accepted,
        "threshold": (
            f"endpoint_position_error_km <= {ENDPOINT_THRESHOLD_KM}; "
            f"jacobi_span <= {JACOBI_SPAN_THRESHOLD}; "
            f"periodicity_error <= {PERIODICITY_THRESHOLD}; "
            f"total_delta_v_m_s <= {DELTA_V_THRESHOLD_M_S}; "
            f"minimum_moon_radius_km >= {MIN_MOON_RADIUS_KM}; "
            f"perilune radii within {RADIUS_TOLERANCE_KM} km; "
            f"corridor family members >= 16; corridor periodicity <= {PERIODICITY_THRESHOLD}"
        ),
        "evidence_artifact": (
            "src/qp_orbits/application_scenarios.py;"
            "data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv"
        ),
        "boundary": (
            "Accepted CR3BP corrected periodic-NRHO family/departure-marker row; "
            "BCR4BP or ephemeris correction remains outside this figure layer."
        ),
        "notes": "Per-marker Fig. 5.9 audit row from the current NRHO transfer baseline.",
    }


def _rows() -> list[dict[str, Any]]:
    baseline = earth_moon_nrho_transfer_baseline()
    return [
        _row(case_id=index, transfer=transfer, baseline=baseline)
        for index, transfer in enumerate(baseline.forward_transfers, start=1)
    ]


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
    worst_endpoint = max((float(row["endpoint_position_error_km"]) for row in accepted), default=np.nan)
    max_jacobi = max((float(row["jacobi_span"]) for row in accepted), default=np.nan)
    table_lines = [
        "| case | departure phase | arrival phase | TOF days | total delta-v m/s | endpoint error km | Jacobi span | accepted |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        table_lines.append(
            f"| {row['case_id']} | {_fmt(row['departure_phase'])} | "
            f"{_fmt(row['arrival_phase'])} | {_fmt(row['time_of_flight_days'])} | "
            f"{_fmt(row['total_delta_v_m_s'])} | {_fmt(row['endpoint_position_error_km'])} | "
            f"{_fmt(row['jacobi_span'])} | {_fmt(row['acceptance'])} |"
        )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 NRHO Corridor Per-Figure Audit

Generated by `scripts/run_chapter5_nrho_corridor_per_figure_audit.py`.

## Purpose

This audit promotes Fig. 5.9 from a linear corridor proxy to a corrected
periodic-NRHO family with explicit per-marker CR3BP evidence. The rows are generated from
`qp_orbits.application_scenarios.earth_moon_nrho_transfer_baseline()`.

## Acceptance

- Accepted rows: `{len(accepted)}` / `{len(rows)}`
- Endpoint threshold: `{ENDPOINT_THRESHOLD_KM}` km
- Jacobi-span threshold: `{JACOBI_SPAN_THRESHOLD}`
- Periodicity threshold: `{PERIODICITY_THRESHOLD}`
- Total delta-v threshold: `{DELTA_V_THRESHOLD_M_S}` m/s
- Best total delta-v: `{_fmt(best['total_delta_v_m_s']) if best else 'N/A'}` m/s
- Worst endpoint error: `{_fmt(worst_endpoint)}` km
- Maximum Jacobi span: `{_fmt(max_jacobi)}`
- Corrected corridor members: `{rows[0]['corridor_family_members'] if rows else 0}`
- Corridor periodicity maximum: `{_fmt(rows[0]['corridor_max_periodicity_error']) if rows else 'N/A'}`

## Rows

{chr(10).join(table_lines)}

## Boundary

The displayed surface is formed from sixteen independently corrected CR3BP
periodic NRHOs with monotonically increasing perilune radii, rather than a
linear interpolation between two boundary curves. The two departure markers
also retain endpoint, delta-v, and Jacobi evidence. Remaining boundaries are
BCR4BP/ephemeris correction and the absence of original McCarthy raw data.
""",
        encoding="utf-8",
    )


def main() -> None:
    rows = _rows()
    _write_rows(rows)
    _write_doc(rows)
    accepted = sum(bool(row["acceptance"]) for row in rows)
    best = min(rows, key=lambda row: float(row["total_delta_v_m_s"]))
    print(f"updated {_artifact(OUTPUT)}")
    print(f"updated {_artifact(DOC_OUTPUT)}")
    print(
        "chapter5_nrho_corridor_per_figure_audit: "
        f"accepted={accepted}/{len(rows)}, "
        f"best_delta_v={_fmt(best['total_delta_v_m_s'])} m/s, "
        f"best_endpoint_error={_fmt(best['endpoint_position_error_km'])} km"
    )


if __name__ == "__main__":
    main()
