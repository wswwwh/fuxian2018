"""Audit Fig. 5.13 / Fig. 5.14 Sun-Earth stable-manifold rows.

The figure scripts currently render a thesis-shaped heat map and a local
transfer scene. This audit records the underlying numerical Sun-Earth CR3BP
stable-manifold baseline as per-figure accepted rows: a phase-to-periapsis scan
for Fig. 5.13 and a selected LEO-targeting stable-manifold arc for Fig. 5.14.
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

from qp_orbits.application_scenarios import sun_earth_l1_stable_manifold_baseline  # noqa: E402
from qp_orbits.constants import SYSTEMS  # noqa: E402

OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_stable_manifold_per_figure_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_stable_manifold_per_figure_audit.md"

FIELDS = (
    "figure_id",
    "case_id",
    "source_model",
    "selected_phase_deg",
    "target_periapsis_radius_km",
    "selected_periapsis_radius_km",
    "periapsis_error_km",
    "transfer_time_days",
    "jacobi_span",
    "periodicity_error",
    "stable_eigenvalue_magnitude",
    "scan_samples",
    "trajectory_samples",
    "minimum_scan_periapsis_km",
    "maximum_scan_periapsis_km",
    "parking_orbit_radius_km",
    "parking_orbit_error_km",
    "acceptance",
    "threshold",
    "evidence_artifact",
    "boundary",
    "notes",
)

PERIAPSIS_ERROR_THRESHOLD_KM = 1.0e-3
JACOBI_SPAN_THRESHOLD = 1.0e-10
PERIODICITY_THRESHOLD = 1.0e-8
PARKING_ORBIT_ERROR_THRESHOLD_KM = 1.0e-3


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


def _parking_radius_error_km(baseline: Any) -> tuple[float, float]:
    system = SYSTEMS["sun_earth"]
    if system.length_unit_km is None:
        raise ValueError("Sun-Earth dimensional units are required")
    center = np.array([(1.0 - system.mu) * system.length_unit_km, 0.0, 0.0])
    radii = np.linalg.norm(baseline.parking_orbit_km - center, axis=1)
    radius = float(np.mean(radii))
    error = float(abs(radius - baseline.target_periapsis_radius_km))
    return radius, error


def _base_values(baseline: Any) -> dict[str, Any]:
    periapsis_error = abs(
        baseline.selected_periapsis_radius_km - baseline.target_periapsis_radius_km
    )
    parking_radius, parking_error = _parking_radius_error_km(baseline)
    return {
        "source_model": "Sun-Earth CR3BP planar L1 Lyapunov stable-manifold baseline",
        "selected_phase_deg": baseline.selected_phase_deg,
        "target_periapsis_radius_km": baseline.target_periapsis_radius_km,
        "selected_periapsis_radius_km": baseline.selected_periapsis_radius_km,
        "periapsis_error_km": periapsis_error,
        "transfer_time_days": abs(baseline.transfer_time_days),
        "jacobi_span": baseline.jacobi_span,
        "periodicity_error": baseline.periodicity_error,
        "stable_eigenvalue_magnitude": baseline.stable_eigenvalue_magnitude,
        "scan_samples": len(baseline.scan_phase_deg),
        "trajectory_samples": len(baseline.selected_times_days),
        "minimum_scan_periapsis_km": float(np.min(baseline.scan_periapsis_radius_km)),
        "maximum_scan_periapsis_km": float(np.max(baseline.scan_periapsis_radius_km)),
        "parking_orbit_radius_km": parking_radius,
        "parking_orbit_error_km": parking_error,
    }


def _row(figure_id: str, case_id: str, baseline: Any, *, notes: str) -> dict[str, Any]:
    values = _base_values(baseline)
    acceptance = (
        values["periapsis_error_km"] <= PERIAPSIS_ERROR_THRESHOLD_KM
        and values["jacobi_span"] <= JACOBI_SPAN_THRESHOLD
        and values["periodicity_error"] <= PERIODICITY_THRESHOLD
        and values["parking_orbit_error_km"] <= PARKING_ORBIT_ERROR_THRESHOLD_KM
    )
    return {
        "figure_id": figure_id,
        "case_id": case_id,
        **values,
        "acceptance": acceptance,
        "threshold": (
            f"periapsis_error_km <= {PERIAPSIS_ERROR_THRESHOLD_KM}; "
            f"jacobi_span <= {JACOBI_SPAN_THRESHOLD}; "
            f"periodicity_error <= {PERIODICITY_THRESHOLD}; "
            f"parking_orbit_error_km <= {PARKING_ORBIT_ERROR_THRESHOLD_KM}"
        ),
        "evidence_artifact": (
            "src/qp_orbits/application_scenarios.py;"
            "data/computed/chapter5_sun_earth_stable_manifold_baseline.csv"
        ),
        "boundary": (
            "Accepted Sun-Earth CR3BP stable-manifold baseline row; not a "
            "two-frequency quasi-periodic Lissajous-torus manifold replacement "
            "and not ephemeris high-fidelity evidence."
        ),
        "notes": notes,
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
    table = [
        "| figure | case | phase deg | target km | selected km | error km | time days | Jacobi span | periodicity |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        table.append(
            f"| {row['figure_id']} | {row['case_id']} | {_fmt(row['selected_phase_deg'])} | "
            f"{_fmt(row['target_periapsis_radius_km'])} | {_fmt(row['selected_periapsis_radius_km'])} | "
            f"{_fmt(row['periapsis_error_km'])} | {_fmt(row['transfer_time_days'])} | "
            f"{_fmt(row['jacobi_span'])} | {_fmt(row['periodicity_error'])} |"
        )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 Stable-Manifold Per-Figure Audit

Generated by `scripts/run_chapter5_stable_manifold_per_figure_audit.py`.

## Purpose

This audit records the numerical Sun-Earth CR3BP stable-manifold baseline used
behind Fig. 5.13 and Fig. 5.14. It supplies per-figure rows for the targeted
Earth periapsis and the selected LEO-transfer scene.

## Acceptance

- Accepted rows: `{len(accepted)}` / `{len(rows)}`
- Periapsis error threshold: `{PERIAPSIS_ERROR_THRESHOLD_KM}` km
- Jacobi-span threshold: `{JACOBI_SPAN_THRESHOLD}`
- Periodicity threshold: `{PERIODICITY_THRESHOLD}`
- Parking-orbit radius threshold: `{PARKING_ORBIT_ERROR_THRESHOLD_KM}` km

## Rows

{chr(10).join(table)}

## Boundary

These rows strengthen Fig. 5.13 and Fig. 5.14 beyond visual overlays by
recording phase targeting, periapsis error, transfer time, Jacobi span, and
periodicity evidence. They remain CR3BP periodic-orbit stable-manifold evidence,
not a full quasi-periodic Lissajous-torus manifold or ephemeris replacement.
""",
        encoding="utf-8",
    )


def main() -> None:
    baseline = sun_earth_l1_stable_manifold_baseline()
    rows = [
        _row(
            "5.13",
            "periapsis_phase_scan",
            baseline,
            notes="Selected phase targets the requested Earth periapsis within tolerance.",
        ),
        _row(
            "5.14",
            "leo_to_l1_selected_arc",
            baseline,
            notes="Selected stable-manifold arc and parking orbit exported for transfer-scene audit.",
        ),
    ]
    _write_rows(rows)
    _write_doc(rows)
    accepted = sum(bool(row["acceptance"]) for row in rows)
    print(f"updated {_artifact(OUTPUT)}")
    print(f"updated {_artifact(DOC_OUTPUT)}")
    print(
        "chapter5_stable_manifold_per_figure_audit: "
        f"accepted={accepted}/{len(rows)}, "
        f"phase={_fmt(rows[0]['selected_phase_deg'])} deg, "
        f"periapsis_error={_fmt(rows[0]['periapsis_error_km'])} km, "
        f"jacobi_span={_fmt(rows[0]['jacobi_span'])}"
    )


if __name__ == "__main__":
    main()
