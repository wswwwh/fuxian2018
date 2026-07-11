"""Audit Fig. 5.8 halo-to-Lyapunov transfer rows.

Fig. 5.8 is currently generated from a CR3BP equal-Jacobi halo-to-Lyapunov
multiple-shooting baseline. This script exports the underlying transfer metrics
as a per-figure accepted row: delta-v, endpoint defect, segment continuity,
Jacobi span, boundary Jacobi match, and orbit periodicity.
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

from qp_orbits.application_scenarios import earth_moon_halo_to_lyapunov_transfer_baseline  # noqa: E402

OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_halo_lyapunov_transfer_per_figure_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_halo_lyapunov_transfer_per_figure_audit.md"

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
    "maximum_continuity_error",
    "minimum_moon_radius_km",
    "jacobi_span",
    "boundary_jacobi_difference",
    "halo_stability_index",
    "halo_periodicity_error",
    "lyapunov_periodicity_error",
    "acceptance",
    "threshold",
    "evidence_artifact",
    "boundary",
    "notes",
)

ENDPOINT_THRESHOLD_KM = 1.0e-3
CONTINUITY_THRESHOLD = 1.0e-9
JACOBI_SPAN_THRESHOLD = 1.0e-10
BOUNDARY_JACOBI_THRESHOLD = 1.0e-10
PERIODICITY_THRESHOLD = 1.0e-8
DELTA_V_THRESHOLD_M_S = 500.0


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


def _row() -> dict[str, Any]:
    baseline = earth_moon_halo_to_lyapunov_transfer_baseline()
    total_delta_v = baseline.total_delta_v_m_s
    accepted = (
        baseline.endpoint_position_error_km <= ENDPOINT_THRESHOLD_KM
        and baseline.maximum_continuity_error <= CONTINUITY_THRESHOLD
        and baseline.jacobi_span <= JACOBI_SPAN_THRESHOLD
        and baseline.boundary_jacobi_difference <= BOUNDARY_JACOBI_THRESHOLD
        and baseline.halo_periodicity_error <= PERIODICITY_THRESHOLD
        and baseline.lyapunov_periodicity_error <= PERIODICITY_THRESHOLD
        and total_delta_v <= DELTA_V_THRESHOLD_M_S
    )
    return {
        "figure_id": "5.8",
        "case_id": "halo_to_lyapunov_equal_jacobi_transfer",
        "source_model": "Earth-Moon CR3BP equal-Jacobi halo-to-Lyapunov multiple shooting",
        "departure_phase": baseline.departure_phase,
        "arrival_phase": baseline.arrival_phase,
        "time_of_flight_days": baseline.time_of_flight_days,
        "departure_delta_v_m_s": baseline.departure_delta_v_m_s,
        "arrival_delta_v_m_s": baseline.arrival_delta_v_m_s,
        "total_delta_v_m_s": total_delta_v,
        "endpoint_position_error_km": baseline.endpoint_position_error_km,
        "maximum_continuity_error": baseline.maximum_continuity_error,
        "minimum_moon_radius_km": baseline.minimum_moon_radius_km,
        "jacobi_span": baseline.jacobi_span,
        "boundary_jacobi_difference": baseline.boundary_jacobi_difference,
        "halo_stability_index": baseline.halo_stability_index,
        "halo_periodicity_error": baseline.halo_periodicity_error,
        "lyapunov_periodicity_error": baseline.lyapunov_periodicity_error,
        "acceptance": accepted,
        "threshold": (
            f"endpoint_position_error_km <= {ENDPOINT_THRESHOLD_KM}; "
            f"maximum_continuity_error <= {CONTINUITY_THRESHOLD}; "
            f"jacobi_span <= {JACOBI_SPAN_THRESHOLD}; "
            f"boundary_jacobi_difference <= {BOUNDARY_JACOBI_THRESHOLD}; "
            f"periodicity_error <= {PERIODICITY_THRESHOLD}; "
            f"total_delta_v_m_s <= {DELTA_V_THRESHOLD_M_S}"
        ),
        "evidence_artifact": (
            "src/qp_orbits/application_scenarios.py;"
            "data/computed/chapter5_earth_moon_halo_lyapunov_transfer_baseline.csv"
        ),
        "boundary": (
            "Accepted Earth-Moon CR3BP equal-Jacobi multiple-shooting transfer row; "
            "not the original McCarthy quasi-halo transfer initial-condition data and "
            "not a BCR4BP/ephemeris high-fidelity replacement."
        ),
        "notes": "Per-figure Fig. 5.8 transfer audit exported from the current baseline generator.",
    }


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _write_doc(row: dict[str, Any]) -> None:
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 Halo-Lyapunov Transfer Per-Figure Audit

Generated by `scripts/run_chapter5_halo_lyapunov_transfer_per_figure_audit.py`.

## Purpose

This audit records the numerical transfer metrics behind Fig. 5.8. It exports
the equal-Jacobi CR3BP halo-to-Lyapunov multiple-shooting result as a
per-figure accepted row.

## Acceptance

- Accepted: `{_fmt(row['acceptance'])}`
- Time of flight: `{_fmt(row['time_of_flight_days'])}` days
- Total delta-v: `{_fmt(row['total_delta_v_m_s'])}` m/s
- Endpoint position error: `{_fmt(row['endpoint_position_error_km'])}` km
- Maximum segment-continuity error: `{_fmt(row['maximum_continuity_error'])}`
- Jacobi span: `{_fmt(row['jacobi_span'])}`
- Boundary Jacobi difference: `{_fmt(row['boundary_jacobi_difference'])}`
- Halo periodicity error: `{_fmt(row['halo_periodicity_error'])}`
- Lyapunov periodicity error: `{_fmt(row['lyapunov_periodicity_error'])}`

## Boundary

This is a stronger per-figure source row than a visual transfer overlay. It is
still a reconstructed Earth-Moon CR3BP equal-Jacobi baseline, not the original
McCarthy raw transfer data and not a BCR4BP/ephemeris replacement.
""",
        encoding="utf-8",
    )


def main() -> None:
    row = _row()
    _write_rows([row])
    _write_doc(row)
    print(f"updated {_artifact(OUTPUT)}")
    print(f"updated {_artifact(DOC_OUTPUT)}")
    print(
        "chapter5_halo_lyapunov_transfer_per_figure_audit: "
        f"accepted={_fmt(row['acceptance'])}, "
        f"total_delta_v={_fmt(row['total_delta_v_m_s'])} m/s, "
        f"endpoint_error={_fmt(row['endpoint_position_error_km'])} km, "
        f"continuity={_fmt(row['maximum_continuity_error'])}"
    )


if __name__ == "__main__":
    main()
