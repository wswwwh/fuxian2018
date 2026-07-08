"""Audit a Route H / BCR4BP transfer-optimization source layer."""

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

from qp_orbits.bcr4bp import (  # noqa: E402
    correct_bcr4bp_velocity_to_position_target,
    earth_moon_bcr4bp_parameters,
    integrate_bcr4bp,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.corrected_dro_family import load_corrected_dro_family_csv  # noqa: E402
from qp_orbits.cr3bp import integrate_cr3bp  # noqa: E402


OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_optimized_transfer_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_optimized_transfer_audit.md"
ROUTE_H_FAMILY = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_family.csv"

FIELDS = (
    "gate_id",
    "route_h_member",
    "phase_index",
    "time_of_flight",
    "time_of_flight_days",
    "uncorrected_position_defect",
    "corrected_position_defect",
    "velocity_delta_norm",
    "delta_v_m_s",
    "objective",
    "rank",
    "nfev",
    "optimizer_success",
    "integration_success",
    "optimization_acceptance",
    "threshold",
    "evidence_artifact",
    "notes",
)

DEFECT_THRESHOLD = 1.0e-9
DELTA_V_THRESHOLD_M_S = 1.0
PHASE_INDICES = (0, 10, 20, 30, 40)
TIME_OF_FLIGHT_GRID = (0.03, 0.04, 0.05, 0.06, 0.07)


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


def _velocity_unit_m_s() -> float:
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Earth-Moon dimensional units are required")
    return system.length_unit_km / (system.time_unit_days * 86400.0) * 1000.0


def _target_position_cr3bp(initial_state: np.ndarray, tof: float, mu: float) -> np.ndarray:
    solution = integrate_cr3bp(
        initial_state,
        (0.0, tof),
        mu,
        t_eval=np.array([tof]),
        rtol=1.0e-11,
        atol=1.0e-13,
        max_step=0.005,
    )
    if not solution.success or solution.y.shape[1] != 1:
        raise RuntimeError("failed to compute CR3BP target position")
    return solution.y[:3, -1]


def _uncorrected_bcr4bp_defect(initial_state: np.ndarray, target_position: np.ndarray, tof: float, params: Any) -> float:
    solution = integrate_bcr4bp(
        initial_state,
        (0.0, tof),
        params,
        t_eval=np.array([tof]),
        rtol=1.0e-11,
        atol=1.0e-13,
        max_step=0.005,
    )
    if not solution.success or solution.y.shape[1] != 1:
        return float("nan")
    return float(np.linalg.norm(solution.y[:3, -1] - target_position))


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _write_doc(rows: list[dict[str, Any]]) -> None:
    accepted = [row for row in rows if row["optimization_acceptance"]]
    best = min(accepted, key=lambda row: float(row["objective"])) if accepted else None
    lines = "\n".join(
        f"- rank `{row['rank']}` phase `{row['phase_index']}`, tof `{_fmt(row['time_of_flight'])}`: "
        f"delta-v `{_fmt(row['delta_v_m_s'])}` m/s, defect `{_fmt(row['corrected_position_defect'])}`"
        for row in rows
        if row["optimization_acceptance"] and int(row["rank"]) <= 5
    )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 Optimized Transfer Audit

## Purpose

This audit closes the Chapter 5 optimization interface at the Route H/BCR4BP
source layer. It performs a deterministic grid search over accepted Route H
insertion phase and short transfer time, uses BCR4BP velocity correction to
satisfy the endpoint position defect, and ranks accepted transfers by delta-v.

## Acceptance

- Accepted optimized rows: `{len(accepted)}` / `{len(rows)}`
- Position-defect threshold: `{DEFECT_THRESHOLD}`
- Delta-v threshold: `{DELTA_V_THRESHOLD_M_S}` m/s
- Best delta-v: `{_fmt(best['delta_v_m_s']) if best else 'N/A'}` m/s
- Best phase index: `{best['phase_index'] if best else 'N/A'}`
- Best normalized time of flight: `{_fmt(best['time_of_flight']) if best else 'N/A'}`

## Top Accepted Rows

{lines if lines else '- none'}

## Decision

This is an auditable high-fidelity/optimization source-layer result, not a full
replacement of the thesis optimized transfer figures. It supplies accepted
optimized rows and a reproducible objective for downstream Chapter 5 figure
promotion.
""",
        encoding="utf-8",
    )


def main() -> None:
    system = SYSTEMS["earth_moon"]
    params = earth_moon_bcr4bp_parameters(system)
    velocity_unit = _velocity_unit_m_s()
    family = load_corrected_dro_family_csv(ROUTE_H_FAMILY, require_contiguous_members=False)
    member = family[-1]
    rows: list[dict[str, Any]] = []
    for phase_index in PHASE_INDICES:
        if phase_index >= member.states.shape[0]:
            continue
        initial_state = member.states[phase_index]
        for tof in TIME_OF_FLIGHT_GRID:
            target_position = _target_position_cr3bp(initial_state, tof, system.mu)
            uncorrected_defect = _uncorrected_bcr4bp_defect(initial_state, target_position, tof, params)
            correction = correct_bcr4bp_velocity_to_position_target(
                initial_state,
                target_position,
                tof,
                params,
                residual_scale=1.0,
                rtol=1.0e-11,
                atol=1.0e-13,
                max_step=0.005,
                max_nfev=25,
            )
            velocity_delta_norm = float(np.linalg.norm(correction.velocity_delta))
            delta_v_m_s = velocity_delta_norm * velocity_unit
            accepted = (
                correction.accepted
                and correction.residual_norm <= DEFECT_THRESHOLD
                and delta_v_m_s <= DELTA_V_THRESHOLD_M_S
            )
            objective = delta_v_m_s + 1.0e6 * max(0.0, correction.residual_norm - DEFECT_THRESHOLD)
            rows.append(
                {
                    "gate_id": "C5-OPTIMIZED-TRANSFER",
                    "route_h_member": member.member,
                    "phase_index": phase_index,
                    "time_of_flight": tof,
                    "time_of_flight_days": tof * (system.time_unit_days or 1.0),
                    "uncorrected_position_defect": uncorrected_defect,
                    "corrected_position_defect": correction.residual_norm,
                    "velocity_delta_norm": velocity_delta_norm,
                    "delta_v_m_s": delta_v_m_s,
                    "objective": objective,
                    "rank": "",
                    "nfev": correction.nfev,
                    "optimizer_success": correction.optimizer_success,
                    "integration_success": correction.integration_success,
                    "optimization_acceptance": accepted,
                    "threshold": (
                        f"corrected_position_defect <= {DEFECT_THRESHOLD}; "
                        f"delta_v_m_s <= {DELTA_V_THRESHOLD_M_S}"
                    ),
                    "evidence_artifact": f"{_artifact(ROUTE_H_FAMILY)};src/qp_orbits/bcr4bp.py",
                    "notes": "Grid-searched Route H/BCR4BP short transfer source-layer optimization.",
                }
            )

    accepted_rows = [row for row in rows if row["optimization_acceptance"]]
    accepted_sorted = sorted(accepted_rows, key=lambda row: float(row["objective"]))
    ranks = {id(row): rank for rank, row in enumerate(accepted_sorted, start=1)}
    for row in rows:
        row["rank"] = ranks.get(id(row), "")

    _write_rows(rows)
    _write_doc(rows)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        f"chapter5 transfer optimization audit: accepted_rows={len(accepted_rows)}/{len(rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
