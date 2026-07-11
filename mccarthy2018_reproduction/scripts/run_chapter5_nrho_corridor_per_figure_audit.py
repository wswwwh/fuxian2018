"""Audit Fig. 5.9 corrected NRHO boundary and departure-marker evidence.

Figure 5.9 shows corrected 4,800 km and 12,610 km NRHO boundaries plus
candidate departure locations. The rendered grey corridor is still only a
linear corrected-boundary bridge, but the departure markers correspond to
CR3BP direct-shooting transfers with endpoint and Jacobi evidence. This script
exports those rows as a per-figure audit.
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
    )
    return {
        "figure_id": "5.9",
        "case_id": case_id,
        "source_model": "Earth-Moon CR3BP corrected NRHO boundaries with direct-shooting departure markers",
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
        "acceptance": accepted,
        "threshold": (
            f"endpoint_position_error_km <= {ENDPOINT_THRESHOLD_KM}; "
            f"jacobi_span <= {JACOBI_SPAN_THRESHOLD}; "
            f"periodicity_error <= {PERIODICITY_THRESHOLD}; "
            f"total_delta_v_m_s <= {DELTA_V_THRESHOLD_M_S}; "
            f"minimum_moon_radius_km >= {MIN_MOON_RADIUS_KM}; "
            f"perilune radii within {RADIUS_TOLERANCE_KM} km"
        ),
        "evidence_artifact": (
            "src/qp_orbits/application_scenarios.py;"
            "data/computed/chapter5_earth_moon_nrho_transfer_baseline.csv"
        ),
        "boundary": (
            "Accepted CR3BP corrected-boundary/departure-marker row; the grey "
            "corridor surface remains a linear bridge between corrected NRHO "
            "boundaries, not a corrected quasi-NRHO torus or ephemeris solution."
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

This audit promotes Fig. 5.9 from a visual corrected-boundary overlay to
explicit per-marker CR3BP evidence. The rows are generated from
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

## Rows

{chr(10).join(table_lines)}

## Boundary

The blue and red NRHO boundaries are corrected CR3BP periodic orbits, and the
two labeled departure markers now have endpoint, delta-v, and Jacobi evidence.
The grey corridor is still a linear bridge between corrected boundaries. It is
not a corrected quasi-NRHO torus, not a BCR4BP/ephemeris solution, and not
original McCarthy raw branch data.
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
