"""Audit Fig. 5.1 Sun-Earth L1 CR3BP long-propagation rows.

Figure 5.1 currently overlays CR3BP-propagated local center-mode traces on a
proxy torus context. This script exports the propagated traces as per-figure
audit rows with duration, spatial extent, and Jacobi-conservation evidence.
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

from qp_orbits.application_scenarios import sun_earth_l1_cr3bp_long_propagation  # noqa: E402
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.libration_points import compute_libration_points  # noqa: E402

OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_sun_earth_l1_long_propagation_per_figure_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_sun_earth_l1_long_propagation_per_figure_audit.md"

FIELDS = (
    "figure_id",
    "curve_id",
    "source_model",
    "duration_days",
    "sample_count",
    "x_min",
    "x_max",
    "y_span",
    "z_span",
    "transverse_span",
    "max_l1_distance_km",
    "jacobi_span",
    "acceptance",
    "threshold",
    "evidence_artifact",
    "boundary",
    "notes",
)

CURVE_COUNT = 5
SAMPLES = 260
DURATION_THRESHOLD_DAYS = 70.0
JACOBI_SPAN_THRESHOLD = 1.0e-10
TRANSVERSE_SPAN_THRESHOLD = 2.0e-3
Z_SPAN_THRESHOLD = 2.0e-3
MAX_L1_DISTANCE_THRESHOLD_KM = 2.0e6


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
    system = SYSTEMS["sun_earth"]
    if system.length_unit_km is None:
        raise ValueError("Sun-Earth length units are required")
    l1_x = compute_libration_points(system.mu)["L1"].x
    l1 = np.array([l1_x, 0.0, 0.0], dtype=float)
    scene = sun_earth_l1_cr3bp_long_propagation(CURVE_COUNT, samples=SAMPLES)
    rows: list[dict[str, Any]] = []
    for curve_id, states in enumerate(scene.states):
        points = states[:, :3]
        y_span = float(np.ptp(points[:, 1]))
        z_span = float(np.ptp(points[:, 2]))
        transverse_span = float(np.hypot(y_span, z_span))
        max_l1_distance_km = float(
            np.linalg.norm(points - l1, axis=1).max() * system.length_unit_km
        )
        jacobi_span = float(scene.jacobi_spans[curve_id])
        accepted = (
            scene.duration_days >= DURATION_THRESHOLD_DAYS
            and jacobi_span <= JACOBI_SPAN_THRESHOLD
            and transverse_span >= TRANSVERSE_SPAN_THRESHOLD
            and z_span >= Z_SPAN_THRESHOLD
            and max_l1_distance_km <= MAX_L1_DISTANCE_THRESHOLD_KM
        )
        rows.append(
            {
                "figure_id": "5.1",
                "curve_id": curve_id,
                "source_model": "Sun-Earth L1 CR3BP propagated linear center-mode seed",
                "duration_days": scene.duration_days,
                "sample_count": states.shape[0],
                "x_min": float(points[:, 0].min()),
                "x_max": float(points[:, 0].max()),
                "y_span": y_span,
                "z_span": z_span,
                "transverse_span": transverse_span,
                "max_l1_distance_km": max_l1_distance_km,
                "jacobi_span": jacobi_span,
                "acceptance": accepted,
                "threshold": (
                    f"duration_days >= {DURATION_THRESHOLD_DAYS}; "
                    f"jacobi_span <= {JACOBI_SPAN_THRESHOLD}; "
                    f"transverse_span >= {TRANSVERSE_SPAN_THRESHOLD}; "
                    f"z_span >= {Z_SPAN_THRESHOLD}; "
                    f"max_l1_distance_km <= {MAX_L1_DISTANCE_THRESHOLD_KM}"
                ),
                "evidence_artifact": (
                    "src/qp_orbits/application_scenarios.py;"
                    "data/computed/chapter5_sun_earth_l1_cr3bp_long_propagation.csv"
                ),
                "boundary": (
                    "Accepted local Sun-Earth L1 CR3BP center-mode propagation row; "
                    "the surrounding torus surface remains proxy context and is not a "
                    "corrected quasi-periodic thesis Lissajous torus."
                ),
                "notes": "Per-curve Fig. 5.1 long-propagation audit row from the current baseline generator.",
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
    accepted = [row for row in rows if row["acceptance"]]
    max_jacobi = max((float(row["jacobi_span"]) for row in accepted), default=np.nan)
    min_transverse_span = min((float(row["transverse_span"]) for row in accepted), default=np.nan)
    min_z_span = min((float(row["z_span"]) for row in accepted), default=np.nan)
    max_l1_distance = max((float(row["max_l1_distance_km"]) for row in accepted), default=np.nan)
    table_lines = [
        "| curve | duration days | transverse span | z span | max L1 distance km | Jacobi span | accepted |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        table_lines.append(
            f"| {row['curve_id']} | {_fmt(row['duration_days'])} | {_fmt(row['transverse_span'])} | "
            f"{_fmt(row['z_span'])} | {_fmt(row['max_l1_distance_km'])} | "
            f"{_fmt(row['jacobi_span'])} | {_fmt(row['acceptance'])} |"
        )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 Sun-Earth L1 Long-Propagation Per-Figure Audit

Generated by `scripts/run_chapter5_sun_earth_l1_long_propagation_per_figure_audit.py`.

## Purpose

This audit promotes Fig. 5.1 from a visual local overlay to explicit CR3BP
long-propagation rows. Rows are generated from
`qp_orbits.application_scenarios.sun_earth_l1_cr3bp_long_propagation()`.

## Acceptance

- Accepted rows: `{len(accepted)}` / `{len(rows)}`
- Duration threshold: `{DURATION_THRESHOLD_DAYS}` days
- Jacobi-span threshold: `{JACOBI_SPAN_THRESHOLD}`
- Transverse-span threshold: `{TRANSVERSE_SPAN_THRESHOLD}`
- Minimum accepted transverse span: `{_fmt(min_transverse_span)}`
- Minimum accepted z span: `{_fmt(min_z_span)}`
- Maximum accepted L1 distance: `{_fmt(max_l1_distance)}` km
- Maximum accepted Jacobi span: `{_fmt(max_jacobi)}`

## Rows

{chr(10).join(table_lines)}

## Boundary

These accepted rows are local Sun-Earth L1 CR3BP propagated linear center-mode
seeds. They give auditable duration, spatial extent, and Jacobi-conservation
evidence for the green propagated overlays in Fig. 5.1. The surrounding
quasi-vertical torus surface remains proxy context, not a corrected
two-frequency Lissajous torus or BCR4BP/ephemeris thesis replacement.
""",
        encoding="utf-8",
    )


def main() -> None:
    rows = _rows()
    _write_rows(rows)
    _write_doc(rows)
    accepted = sum(bool(row["acceptance"]) for row in rows)
    max_jacobi = max(float(row["jacobi_span"]) for row in rows)
    print(f"updated {_artifact(OUTPUT)}")
    print(f"updated {_artifact(DOC_OUTPUT)}")
    print(
        "chapter5_sun_earth_l1_long_propagation_per_figure_audit: "
        f"accepted={accepted}/{len(rows)}, "
        f"duration={_fmt(rows[0]['duration_days'])} days, "
        f"max_jacobi_span={_fmt(max_jacobi)}"
    )


if __name__ == "__main__":
    main()
