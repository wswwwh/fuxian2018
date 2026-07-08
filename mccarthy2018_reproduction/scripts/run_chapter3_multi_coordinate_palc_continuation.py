"""Short multi-coordinate PALC continuation from the turn-aware endpoint.

This audit promotes the successful one-step PALC probe into a bounded local
continuation.  It starts from the last two archived turn-aware amplitude states,
uses the full state/rho/Jacobi secant as the PALC tangent, and adaptively tries
smaller arclength scales when an attempted step fails to increase max |z|.
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
OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_multi_coordinate_palc_continuation.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_multi_coordinate_palc_continuation.md"

FIELDS = (
    "attempt_id",
    "stage",
    "step_scale",
    "accepted_step",
    "previous_max_abs_z_km",
    "current_max_abs_z_km",
    "solved_max_abs_z_km",
    "delta_max_abs_z_km",
    "current_rho_rad",
    "solved_rho_rad",
    "delta_rho_rad",
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


def _parse_float_list(value: str) -> tuple[float, ...]:
    parsed = tuple(float(item.strip()) for item in value.split(",") if item.strip())
    if not parsed:
        raise argparse.ArgumentTypeError("at least one value is required")
    return parsed


def _write_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=FIELDS).writeheader()


def _append_row(row: dict[str, Any]) -> None:
    with OUTPUT.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})
        stream.flush()


def _load_seed_pair() -> tuple[campaign.CampaignMember, campaign.CampaignMember]:
    with np.load(STATE_INPUT, allow_pickle=True) as data:
        phases = np.asarray(data["phase_grid"], dtype=float)
        previous = campaign.CampaignMember(
            member_id=int(data["member_ids"][-2]),
            states=np.asarray(data["states"][-2], dtype=float),
            phases=phases,
            rho=float(data["rho"][-2]),
            mean_jacobi=float(data["mean_jacobi"][-2]),
            max_abs_z_km=float(data["max_abs_z_km"][-2]),
            source="turn_aware_amplitude_archive",
            source_member_id=str(data["source_attempt_ids"][-2]),
        )
        current = campaign.CampaignMember(
            member_id=int(data["member_ids"][-1]),
            states=np.asarray(data["states"][-1], dtype=float),
            phases=phases,
            rho=float(data["rho"][-1]),
            mean_jacobi=float(data["mean_jacobi"][-1]),
            max_abs_z_km=float(data["max_abs_z_km"][-1]),
            source="turn_aware_amplitude_archive",
            source_member_id=str(data["source_attempt_ids"][-1]),
        )
    return previous, current


def _failed_gates(
    *,
    member: campaign.CampaignMember,
    previous: campaign.CampaignMember,
    gates: campaign.GateEvaluation,
    converged: bool,
) -> tuple[str, ...]:
    failed: list[str] = []
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
        if not bool(gates.row[name]):
            failed.append(name)
    if member.max_abs_z_km <= previous.max_abs_z_km + 1.0e-6:
        failed.append("turn_gate_4_amplitude_monotone")
    return tuple(failed)


def _attempt(
    *,
    previous: campaign.CampaignMember,
    current: campaign.CampaignMember,
    stage: int,
    step_scale: float,
) -> tuple[campaign.CampaignMember, dict[str, Any]]:
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
    attempt_id = f"stage_{stage}_scale_{step_scale:g}"
    assembly, correction_norms, converged, solver_failure = campaign.fixed_time._solve_fixed_time(
        case_id=attempt_id,
        predictor=predictor,
        tangent=secant,
        phases=current.phases,
        reference_states=current.states,
    )
    validation = campaign.fixed_time._validation_for(assembly)
    member = campaign._member_from_assembly(
        member_id=3000 + stage,
        assembly=assembly,
        source="multi_coordinate_palc_continuation",
        source_member_id=current.member_id,
    )
    gates = campaign._evaluate_gates(
        member=member,
        previous=current,
        assembly=assembly,
        validation=validation,
        converged=converged,
        step_source="multi_coordinate_palc_continuation",
        macro_step=stage,
        substep_index=1,
        substep_count=1,
    )
    failed = _failed_gates(member=member, previous=current, gates=gates, converged=converged)
    row = {
        "attempt_id": attempt_id,
        "stage": stage,
        "step_scale": step_scale,
        "accepted_step": converged and not failed,
        "previous_max_abs_z_km": previous.max_abs_z_km,
        "current_max_abs_z_km": current.max_abs_z_km,
        "solved_max_abs_z_km": member.max_abs_z_km,
        "delta_max_abs_z_km": member.max_abs_z_km - current.max_abs_z_km,
        "current_rho_rad": current.rho,
        "solved_rho_rad": member.rho,
        "delta_rho_rad": member.rho - current.rho,
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
    return member, row


def _write_doc(rows: list[dict[str, Any]], final: campaign.CampaignMember, stop_reason: str) -> None:
    accepted = [row for row in rows if bool(row["accepted_step"])]
    lines = "\n".join(
        f"- `{row['attempt_id']}`: z `{float(row['solved_max_abs_z_km']):.12g}` km, "
        f"dz `{float(row['delta_max_abs_z_km']):.12g}` km, accepted "
        f"`{row['accepted_step']}`, failed `{row['failed_gates']}`"
        for row in rows
    ) or "- none"
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Multi-Coordinate PALC Continuation

## Scope

This is a short continuation audit for the full-vector PALC chart seeded from
the turn-aware amplitude endpoint. It is diagnostic only and does not update
Fig. 3.16 / Fig. 3.17.

## Outcome

- Attempts: `{len(rows)}`
- Accepted steps: `{len(accepted)}`
- Final max abs z: `{final.max_abs_z_km:.12g}` km
- Stop reason: `{stop_reason}`

## Rows

{lines}

## Interpretation

This chart can step beyond the target-amplitude endpoint, but the local
amplitude gain collapses rapidly. If it stalls with only amplitude-monotonicity
failures, the next chart must change the continuation direction or add a more
explicit multi-coordinate constraint rather than only shrinking the PALC scale.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-stages", type=int, default=6)
    parser.add_argument("--step-scales", type=_parse_float_list, default=(1.0, 0.5, 0.25, 0.1))
    args = parser.parse_args()
    if args.max_stages <= 0:
        raise SystemExit("--max-stages must be positive")
    if not STATE_INPUT.exists():
        raise SystemExit(f"missing state archive: {STATE_INPUT}")

    _write_header(OUTPUT)
    previous, current = _load_seed_pair()
    rows: list[dict[str, Any]] = []
    stop_reason = "maximum stages reached"
    for stage in range(1, args.max_stages + 1):
        accepted_member: campaign.CampaignMember | None = None
        for step_scale in args.step_scales:
            member, row = _attempt(
                previous=previous,
                current=current,
                stage=stage,
                step_scale=step_scale,
            )
            _append_row(row)
            rows.append(row)
            print(
                f"{row['attempt_id']}: accepted={row['accepted_step']} "
                f"z={float(row['solved_max_abs_z_km']):.6f} "
                f"dz={float(row['delta_max_abs_z_km']):.6f} "
                f"failed={row['failed_gates']}",
                flush=True,
            )
            if bool(row["accepted_step"]):
                accepted_member = member
                break
        if accepted_member is None:
            stop_reason = f"no acceptable PALC step at stage {stage}"
            break
        previous, current = current, accepted_member
        if current.max_abs_z_km >= 10500.0:
            stop_reason = "target reached"
            break

    _write_doc(rows, current, stop_reason)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "multi-coordinate PALC continuation: "
        f"accepted={sum(bool(row['accepted_step']) for row in rows)}, "
        f"final_max_z={current.max_abs_z_km:.6f} km, stop_reason={stop_reason}",
        flush=True,
    )


if __name__ == "__main__":
    main()
