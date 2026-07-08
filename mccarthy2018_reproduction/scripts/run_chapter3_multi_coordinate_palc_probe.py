"""Probe a multi-coordinate PALC chart from the turn-aware endpoint.

The simple target-amplitude chart stalled at about 10,293 km.  This diagnostic
uses the archived turn-aware states to build a full-vector PALC secant
(state/rho/Jacobi) and tests whether a local arclength chart can step past that
endpoint while keeping the fixed-time residual, Jacobi, phase, amplitude, and
conditioning gates.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter3_integrated_breakthrough as campaign

STATE_INPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_turn_aware_amplitude_states.npz"
)
OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_multi_coordinate_palc_probe.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_multi_coordinate_palc_probe.md"

FIELDS = (
    "attempt_id",
    "pair_label",
    "step_scale",
    "previous_max_abs_z_km",
    "current_max_abs_z_km",
    "predicted_max_abs_z_km",
    "solved_max_abs_z_km",
    "delta_max_abs_z_km",
    "previous_rho_rad",
    "current_rho_rad",
    "solved_rho_rad",
    "delta_rho_rad",
    "mean_jacobi",
    "converged",
    "turn_palc_acceptance",
    "map_residual_max",
    "jacobi_mean_span",
    "jacobi_one_map_drift",
    "jacobi_ten_return_span",
    "phase_return_error",
    "condition_number",
    "raw_condition_number",
    "gate_1_residual",
    "gate_2_jacobi",
    "gate_3_phase",
    "turn_gate_4_amplitude_monotone",
    "gate_5_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "failed_gates",
    "failure_reason",
    "newton_iterations",
    "max_correction_norm",
)


def _fmt(value: Any) -> str:
    return campaign._fmt(value)


def _write_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=FIELDS).writeheader()


def _append_row(row: dict[str, Any]) -> None:
    with OUTPUT.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})
        stream.flush()


def _parse_float_list(value: str) -> tuple[float, ...]:
    parsed = tuple(float(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise argparse.ArgumentTypeError("at least one value is required")
    return parsed


def _load_member(index: int) -> campaign.CampaignMember:
    with np.load(STATE_INPUT, allow_pickle=True) as data:
        return campaign.CampaignMember(
            member_id=int(data["member_ids"][index]),
            states=np.asarray(data["states"][index], dtype=float),
            phases=np.asarray(data["phase_grid"], dtype=float),
            rho=float(data["rho"][index]),
            mean_jacobi=float(data["mean_jacobi"][index]),
            max_abs_z_km=float(data["max_abs_z_km"][index]),
            source="turn_aware_amplitude_archive",
            source_member_id=str(data["source_attempt_ids"][index]),
        )


def _archive_count() -> int:
    with np.load(STATE_INPUT, allow_pickle=True) as data:
        return int(data["states"].shape[0])


def _turn_failed_gates(
    *,
    member: campaign.CampaignMember,
    previous: campaign.CampaignMember,
    gates: campaign.GateEvaluation,
    converged: bool,
) -> tuple[str, ...]:
    failed: list[str] = []
    row = gates.row
    if not converged:
        failed.append("converged")
    for name in (
        "gate_1_residual",
        "gate_2_jacobi",
        "gate_3_phase",
        "gate_5_amplitude",
        "gate_6_mapping_time",
        "gate_7_condition",
    ):
        if not bool(row[name]):
            failed.append(name)
    if member.max_abs_z_km <= previous.max_abs_z_km + 1.0e-6:
        failed.append("turn_gate_4_amplitude_monotone")
    return tuple(failed)


def _attempt_pair(*, pair_offset: int, step_scale: float, attempt_id: str) -> dict[str, Any]:
    count = _archive_count()
    previous = _load_member(count - pair_offset - 1)
    current = _load_member(count - pair_offset)
    previous_vector = campaign.fixed_time._fixed_unknown_vector(
        previous.states,
        previous.rho,
        previous.mean_jacobi,
    )
    current_vector = campaign.fixed_time._fixed_unknown_vector(
        current.states,
        current.rho,
        current.mean_jacobi,
    )
    secant = current_vector - previous_vector
    predictor = current_vector + step_scale * secant
    predicted_states, predicted_rho, predicted_jacobi = campaign.fixed_time._unpack_fixed_unknown(
        predictor,
        current.phases.size,
    )
    (
        assembly,
        correction_norms,
        converged,
        solver_failure,
    ) = campaign.fixed_time._solve_fixed_time(
        case_id=attempt_id,
        predictor=predictor,
        tangent=secant,
        phases=current.phases,
        reference_states=current.states,
    )
    validation = campaign.fixed_time._validation_for(assembly)
    member = campaign._member_from_assembly(
        member_id=2000 + pair_offset,
        assembly=assembly,
        source=f"multi_coordinate_palc_pair_{pair_offset}",
        source_member_id=current.source_member_id,
    )
    gates = campaign._evaluate_gates(
        member=member,
        previous=current,
        assembly=assembly,
        validation=validation,
        converged=converged,
        step_source="multi_coordinate_palc_probe",
        macro_step=pair_offset,
        substep_index=1,
        substep_count=1,
    )
    failed = _turn_failed_gates(
        member=member,
        previous=current,
        gates=gates,
        converged=converged,
    )
    return {
        "attempt_id": attempt_id,
        "pair_label": f"{previous.source_member_id}->{current.source_member_id}",
        "step_scale": step_scale,
        "previous_max_abs_z_km": previous.max_abs_z_km,
        "current_max_abs_z_km": current.max_abs_z_km,
        "predicted_max_abs_z_km": float(
            np.max(np.abs(predicted_states[:, 2])) * (campaign.fixed_time.SYSTEM.length_unit_km or 1.0)
        ),
        "solved_max_abs_z_km": member.max_abs_z_km,
        "delta_max_abs_z_km": member.max_abs_z_km - current.max_abs_z_km,
        "previous_rho_rad": previous.rho,
        "current_rho_rad": current.rho,
        "solved_rho_rad": member.rho,
        "delta_rho_rad": member.rho - current.rho,
        "mean_jacobi": member.mean_jacobi,
        "converged": converged,
        "turn_palc_acceptance": converged and not failed,
        "map_residual_max": gates.row["map_residual_max"],
        "jacobi_mean_span": gates.row["jacobi_mean_span"],
        "jacobi_one_map_drift": gates.row["jacobi_one_map_drift"],
        "jacobi_ten_return_span": gates.row["jacobi_ten_return_span"],
        "phase_return_error": gates.row["phase_return_error"],
        "condition_number": gates.row["condition_number"],
        "raw_condition_number": gates.row["raw_condition_number"],
        "gate_1_residual": gates.row["gate_1_residual"],
        "gate_2_jacobi": gates.row["gate_2_jacobi"],
        "gate_3_phase": gates.row["gate_3_phase"],
        "turn_gate_4_amplitude_monotone": member.max_abs_z_km > current.max_abs_z_km + 1.0e-6,
        "gate_5_amplitude": gates.row["gate_5_amplitude"],
        "gate_6_mapping_time": gates.row["gate_6_mapping_time"],
        "gate_7_condition": gates.row["gate_7_condition"],
        "failed_gates": "; ".join(failed),
        "failure_reason": solver_failure if solver_failure else "; ".join(failed),
        "newton_iterations": len(correction_norms),
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
    }


def _write_doc(rows: list[dict[str, Any]]) -> None:
    accepted = [row for row in rows if bool(row["turn_palc_acceptance"])]
    best = max(rows, key=lambda row: float(row["solved_max_abs_z_km"])) if rows else None
    lines = "\n".join(
        f"- `{row['attempt_id']}`: solved max z "
        f"`{float(row['solved_max_abs_z_km']):.12g}` km, dz "
        f"`{float(row['delta_max_abs_z_km']):.12g}` km, accepted "
        f"`{row['turn_palc_acceptance']}`, failed `{row['failed_gates']}`"
        for row in rows
    ) or "- none"
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Multi-Coordinate PALC Probe

## Scope

This diagnostic tests a full-vector PALC chart seeded from the archived
turn-aware amplitude states. It is the first probe of the proposed
multi-coordinate continuation route and does not update Fig. 3.16 / Fig. 3.17.

## Outcome

- Attempts: `{len(rows)}`
- Accepted PALC steps: `{len(accepted)}`
- Best solved max abs z: `{best['solved_max_abs_z_km'] if best else 'N/A'}` km

## Rows

{lines}

## Interpretation

Accepted rows would justify promoting this chart into a longer continuation
campaign with independent revalidation. If all rows fail residual/Jacobi/phase
or fail to increase amplitude, the simple full-vector PALC chart is not enough
to escape the current 10,293 km fixed-time frontier.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step-scales", type=_parse_float_list, default=(0.25, 0.5, 1.0))
    parser.add_argument("--pair-offsets", type=_parse_float_list, default=(1.0, 2.0))
    args = parser.parse_args()
    if not STATE_INPUT.exists():
        raise SystemExit(f"missing state archive: {STATE_INPUT}")

    _write_header(OUTPUT)
    rows: list[dict[str, Any]] = []
    for pair_offset_value in args.pair_offsets:
        pair_offset = int(pair_offset_value)
        for step_scale in args.step_scales:
            attempt_id = f"pair_{pair_offset}_scale_{step_scale:g}"
            print(attempt_id, flush=True)
            row = _attempt_pair(
                pair_offset=pair_offset,
                step_scale=step_scale,
                attempt_id=attempt_id,
            )
            _append_row(row)
            rows.append(row)
            print(
                f"{attempt_id}: accepted={row['turn_palc_acceptance']} "
                f"z={float(row['solved_max_abs_z_km']):.6f} "
                f"dz={float(row['delta_max_abs_z_km']):.6f} "
                f"failed={row['failed_gates']}",
                flush=True,
            )

    _write_doc(rows)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "multi-coordinate PALC probe: "
        f"rows={len(rows)}, accepted={sum(bool(row['turn_palc_acceptance']) for row in rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
