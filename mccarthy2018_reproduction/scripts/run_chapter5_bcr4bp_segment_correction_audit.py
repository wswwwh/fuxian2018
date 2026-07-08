"""Audit BCR4BP short-segment defect correction from Route H initial states."""

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


OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_bcr4bp_segment_correction_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_bcr4bp_segment_correction_audit.md"
ROUTE_H_FAMILY = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_family.csv"

FIELDS = (
    "gate_id",
    "route_h_member",
    "phase_index",
    "time_of_flight",
    "uncorrected_position_defect",
    "corrected_position_defect",
    "velocity_delta_norm",
    "nfev",
    "optimizer_success",
    "integration_success",
    "correction_acceptance",
    "threshold",
    "evidence_artifact",
    "notes",
)

DEFECT_THRESHOLD = 1.0e-9
TOF = 0.05


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


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _write_doc(rows: list[dict[str, Any]]) -> None:
    accepted = sum(1 for row in rows if row["correction_acceptance"])
    worst_defect = max(float(row["corrected_position_defect"]) for row in rows)
    worst_delta = max(float(row["velocity_delta_norm"]) for row in rows)
    lines = "\n".join(
        f"- phase `{row['phase_index']}`: corrected defect "
        f"`{_fmt(row['corrected_position_defect'])}`, velocity delta "
        f"`{_fmt(row['velocity_delta_norm'])}`, accepted `{_fmt(row['correction_acceptance'])}`"
        for row in rows
    )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 BCR4BP Segment Correction Audit

## Purpose

This audit adds the first defect-correction layer above the BCR4BP dynamics
kernel. It corrects only short BCR4BP segments from accepted Route H quasi-DRO
states, using initial velocity as the free variable and CR3BP Route H short-arc
positions as the target.

## Results

- Accepted rows: `{accepted}` / `{len(rows)}`
- Defect threshold: `{DEFECT_THRESHOLD}`
- Worst corrected position defect: `{worst_defect}`
- Worst velocity delta norm: `{worst_delta}`

## Rows

{lines}

## Decision

The BCR4BP defect-correction interface is now available as a short-segment
building block. It is not yet a full ephemeris multiple-shooting trajectory and
does not optimize transfer cost; those remain downstream Chapter 5 tasks.
""",
        encoding="utf-8",
    )


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


def main() -> None:
    system = SYSTEMS["earth_moon"]
    params = earth_moon_bcr4bp_parameters(system)
    family = load_corrected_dro_family_csv(ROUTE_H_FAMILY, require_contiguous_members=False)
    member = family[-1]
    phase_indices = sorted({0, member.states.shape[0] // 3, 2 * member.states.shape[0] // 3})
    rows: list[dict[str, Any]] = []
    for phase_index in phase_indices:
        initial_state = member.states[phase_index]
        target_position = _target_position_cr3bp(initial_state, TOF, system.mu)
        uncorrected_defect = _uncorrected_bcr4bp_defect(initial_state, target_position, TOF, params)
        correction = correct_bcr4bp_velocity_to_position_target(
            initial_state,
            target_position,
            TOF,
            params,
            residual_scale=1.0,
            rtol=1.0e-11,
            atol=1.0e-13,
            max_step=0.005,
            max_nfev=25,
        )
        accepted = (
            correction.accepted
            and correction.residual_norm <= DEFECT_THRESHOLD
            and float(np.linalg.norm(correction.velocity_delta)) < 1.0e-2
        )
        rows.append(
            {
                "gate_id": "C5-BCR4BP-SEGMENT-CORRECTION",
                "route_h_member": member.member,
                "phase_index": phase_index,
                "time_of_flight": TOF,
                "uncorrected_position_defect": uncorrected_defect,
                "corrected_position_defect": correction.residual_norm,
                "velocity_delta_norm": float(np.linalg.norm(correction.velocity_delta)),
                "nfev": correction.nfev,
                "optimizer_success": correction.optimizer_success,
                "integration_success": correction.integration_success,
                "correction_acceptance": accepted,
                "threshold": f"corrected_position_defect <= {DEFECT_THRESHOLD}; velocity_delta_norm < 1e-2",
                "evidence_artifact": f"{_artifact(ROUTE_H_FAMILY)};src/qp_orbits/bcr4bp.py",
                "notes": f"Route H max abs z {member.max_abs_z_km} km; short-segment correction only.",
            }
        )

    _write_rows(rows)
    _write_doc(rows)
    accepted_count = sum(1 for row in rows if row["correction_acceptance"])
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        f"chapter5 BCR4BP segment correction audit: accepted_rows={accepted_count}/{len(rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
