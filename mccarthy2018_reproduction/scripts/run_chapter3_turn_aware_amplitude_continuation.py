"""Turn-aware fixed-time quasi-DRO amplitude continuation.

This script explores the next route after the integrated Part 5 monotone-rho
campaign hit a local turn.  It keeps the fixed mapping time and the residual /
Jacobi / phase / condition gates, but replaces the rho-monotonicity gate with a
local branch-parameter gate: max |z| must increase.

The output is intentionally separate from the Fig. 3.16 / Fig. 3.17 source
branch.  It is an experimental route audit, not a figure update.
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

ATTEMPTS_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_turn_aware_amplitude_continuation.csv"
)
REVALIDATION_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_turn_aware_amplitude_revalidation.csv"
)
STATE_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_turn_aware_amplitude_states.npz"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_turn_aware_amplitude_continuation.md"

DEFAULT_STEP_OPTIONS_KM = (10.0, 5.0, 2.0, 1.0, 0.5)
TARGET_MIN_KM = 10500.0

ATTEMPT_FIELDS = (
    "attempt_id",
    "stage",
    "step_option_km",
    "target_max_abs_z_km",
    "source_member_id",
    "previous_max_abs_z_km",
    "previous_rho_rad",
    "converged",
    "turn_aware_acceptance",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "rho_rad",
    "delta_rho_rad",
    "mean_jacobi",
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
    "original_gate_4_rho_monotone",
    "turn_gate_4_amplitude_monotone",
    "gate_5_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "original_failed_gates",
    "turn_failed_gates",
    "failure_reason",
    "newton_iterations",
    "max_correction_norm",
)

REVALIDATION_FIELDS = (
    "member_id",
    "source_attempt_id",
    "revalidated_acceptance",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "rho_rad",
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
    "original_gate_4_rho_monotone",
    "turn_gate_4_amplitude_monotone",
    "gate_5_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "turn_failed_gates",
    "failure_reason",
    "newton_iterations",
    "max_correction_norm",
)


def _fmt(value: Any) -> str:
    return campaign._fmt(value)


def _write_header(path: Path, fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()


def _append_row(path: Path, fields: tuple[str, ...], row: dict[str, Any]) -> None:
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writerow({field: _fmt(row.get(field)) for field in fields})
        stream.flush()


def _parse_step_options(value: str) -> tuple[float, ...]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("at least one step option is required")
    options = tuple(float(part) for part in parts)
    if any(option <= 0.0 for option in options):
        raise argparse.ArgumentTypeError("step options must be positive")
    return options


def _frontier() -> tuple[campaign.CampaignMember, campaign.CampaignMember]:
    fixed_family = campaign.load_corrected_dro_family_csv(campaign.FAMILY_PATH)
    endpoint = campaign._member_from_fixed(fixed_family[-1])
    bootstrap, gates, _ = campaign._bootstrap_candidate(endpoint)
    if bootstrap is not None and gates is not None and gates.overall_acceptance:
        return endpoint, bootstrap
    return campaign._member_from_fixed(fixed_family[-2]), endpoint


def _turn_failed_gates(
    *,
    result: campaign.AttemptResult,
    previous: campaign.CampaignMember,
) -> tuple[str, ...]:
    row = result.gates.row
    failed: list[str] = []
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
    if result.member.max_abs_z_km <= previous.max_abs_z_km + 1.0e-6:
        failed.append("turn_gate_4_amplitude_monotone")
    if not result.converged:
        failed.insert(0, "converged")
    return tuple(failed)


def _turn_acceptance(*, result: campaign.AttemptResult, previous: campaign.CampaignMember) -> bool:
    return result.converged and not _turn_failed_gates(result=result, previous=previous)


def _attempt_row(
    *,
    attempt_id: str,
    stage: int,
    step_option_km: float,
    target_max_abs_z_km: float,
    previous: campaign.CampaignMember,
    result: campaign.AttemptResult,
) -> dict[str, Any]:
    row = result.gates.row
    turn_failed = _turn_failed_gates(result=result, previous=previous)
    return {
        "attempt_id": attempt_id,
        "stage": stage,
        "step_option_km": step_option_km,
        "target_max_abs_z_km": target_max_abs_z_km,
        "source_member_id": result.member.source_member_id,
        "previous_max_abs_z_km": previous.max_abs_z_km,
        "previous_rho_rad": previous.rho,
        "converged": result.converged,
        "turn_aware_acceptance": result.converged and not turn_failed,
        "max_abs_z_km": result.member.max_abs_z_km,
        "delta_max_abs_z_km": result.member.max_abs_z_km - previous.max_abs_z_km,
        "rho_rad": result.member.rho,
        "delta_rho_rad": result.member.rho - previous.rho,
        "mean_jacobi": result.member.mean_jacobi,
        "map_residual_max": row["map_residual_max"],
        "jacobi_mean_span": row["jacobi_mean_span"],
        "jacobi_one_map_drift": row["jacobi_one_map_drift"],
        "jacobi_ten_return_span": row["jacobi_ten_return_span"],
        "phase_return_error": row["phase_return_error"],
        "condition_number": row["condition_number"],
        "raw_condition_number": row["raw_condition_number"],
        "gate_1_residual": row["gate_1_residual"],
        "gate_2_jacobi": row["gate_2_jacobi"],
        "gate_3_phase": row["gate_3_phase"],
        "original_gate_4_rho_monotone": row["gate_4_rho_monotone"],
        "turn_gate_4_amplitude_monotone": result.member.max_abs_z_km > previous.max_abs_z_km + 1.0e-6,
        "gate_5_amplitude": row["gate_5_amplitude"],
        "gate_6_mapping_time": row["gate_6_mapping_time"],
        "gate_7_condition": row["gate_7_condition"],
        "original_failed_gates": "; ".join(result.gates.failed_gates),
        "turn_failed_gates": "; ".join(turn_failed),
        "failure_reason": result.failure_reason,
        "newton_iterations": len(result.correction_norms),
        "max_correction_norm": max(result.correction_norms) if result.correction_norms else 0.0,
    }


def _revalidate_member(
    *,
    member: campaign.CampaignMember,
    previous: campaign.CampaignMember,
    source_attempt_id: str,
) -> dict[str, Any]:
    predictor = campaign.fixed_time._fixed_unknown_vector(
        member.states,
        member.rho,
        member.mean_jacobi,
    )
    (
        assembly,
        correction_norms,
        converged,
        solver_failure,
        condition,
        raw_condition,
    ) = campaign._solve_fixed_time_target_amplitude(
        case_id=f"turn_aware_revalidation_member_{member.member_id}",
        predictor=predictor,
        target_max_abs_z_km=member.max_abs_z_km,
        phases=member.phases,
        reference_states=member.states,
    )
    validation = campaign.fixed_time._validation_for(assembly)
    revalidated = campaign._member_from_assembly(
        member_id=member.member_id,
        assembly=assembly,
        source=f"turn_aware_revalidation_of_{member.source}",
        source_member_id=member.source_member_id,
    )
    gates = campaign._evaluate_gates(
        member=revalidated,
        previous=previous,
        assembly=assembly,
        validation=validation,
        converged=converged,
        step_source="turn_aware_target_amplitude_revalidation",
        macro_step=-1,
        substep_index=-1,
        substep_count=-1,
        condition_override=condition,
        raw_condition_override=raw_condition,
    )
    result = campaign.AttemptResult(
        member=revalidated,
        assembly=assembly,
        validation=validation,
        gates=gates,
        converged=converged,
        failure_reason=solver_failure if solver_failure else "; ".join(gates.failed_gates),
        correction_norms=correction_norms,
        predictor_alpha=0.0,
    )
    turn_failed = _turn_failed_gates(result=result, previous=previous)
    row = gates.row
    return {
        "member_id": member.member_id,
        "source_attempt_id": source_attempt_id,
        "revalidated_acceptance": converged and not turn_failed,
        "max_abs_z_km": revalidated.max_abs_z_km,
        "delta_max_abs_z_km": revalidated.max_abs_z_km - previous.max_abs_z_km,
        "rho_rad": revalidated.rho,
        "delta_rho_rad": revalidated.rho - previous.rho,
        "map_residual_max": row["map_residual_max"],
        "jacobi_mean_span": row["jacobi_mean_span"],
        "jacobi_one_map_drift": row["jacobi_one_map_drift"],
        "jacobi_ten_return_span": row["jacobi_ten_return_span"],
        "phase_return_error": row["phase_return_error"],
        "condition_number": row["condition_number"],
        "raw_condition_number": row["raw_condition_number"],
        "gate_1_residual": row["gate_1_residual"],
        "gate_2_jacobi": row["gate_2_jacobi"],
        "gate_3_phase": row["gate_3_phase"],
        "original_gate_4_rho_monotone": row["gate_4_rho_monotone"],
        "turn_gate_4_amplitude_monotone": revalidated.max_abs_z_km > previous.max_abs_z_km + 1.0e-6,
        "gate_5_amplitude": row["gate_5_amplitude"],
        "gate_6_mapping_time": row["gate_6_mapping_time"],
        "gate_7_condition": row["gate_7_condition"],
        "turn_failed_gates": "; ".join(turn_failed),
        "failure_reason": solver_failure if solver_failure else "; ".join(turn_failed),
        "newton_iterations": len(correction_norms),
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
    }


def _write_doc(
    *,
    start: campaign.CampaignMember,
    final: campaign.CampaignMember,
    accepted_rows: list[dict[str, Any]],
    revalidation_rows: list[dict[str, Any]],
    stop_reason: str,
    target_km: float,
) -> None:
    accepted_lines = "\n".join(
        f"- `{row['attempt_id']}`: max z `{float(row['max_abs_z_km']):.12g}` km, "
        f"dz `{float(row['delta_max_abs_z_km']):.12g}` km, "
        f"drho `{float(row['delta_rho_rad']):.12g}`"
        for row in accepted_rows
    ) or "- none"
    revalidation_passed = (
        bool(revalidation_rows)
        and all(str(row["revalidated_acceptance"]) == "True" or row["revalidated_acceptance"] is True for row in revalidation_rows)
    )
    route_status = (
        "bounded_blocker_for_current_amplitude_chart"
        if final.max_abs_z_km < target_km and stop_reason.startswith("no turn-aware acceptable")
        else "incomplete_run"
        if final.max_abs_z_km < target_km
        else "target_reached"
    )
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Turn-Aware Amplitude Continuation

## Scope

This is an experimental continuation route after the monotone-rho Part 5
campaign reached a local turn. It keeps fixed mapping time and the residual,
Jacobi, phase, amplitude-growth, mapping-time, and condition gates. It replaces
the original rho-monotonicity gate with a turn-aware branch parameter:
`max_abs_z_km` must increase.

This artifact does not update Fig. 3.16 / Fig. 3.17 unless the minimum target is
reached and the turn-aware revalidation rows pass.

## Start

- Start member: `{start.member_id}`
- Start max abs z: `{start.max_abs_z_km:.12g}` km
- Start rho: `{start.rho:.12g}`
- Fixed mapping time: `{campaign.T_FIXED_DAYS}` days

## Outcome

- Final max abs z: `{final.max_abs_z_km:.12g}` km
- Target max abs z: `{target_km:.12g}` km
- Target reached: `{final.max_abs_z_km >= target_km}`
- Accepted turn-aware steps: `{len(accepted_rows)}`
- Revalidation all passed: `{revalidation_passed}`
- Route status: `{route_status}`
- Stop reason: `{stop_reason}`

## Accepted Steps

{accepted_lines}

## Output Files

- `data/computed/chapter3_turn_aware_amplitude_continuation.csv`
- `data/computed/chapter3_turn_aware_amplitude_revalidation.csv`
- `data/computed/chapter3_turn_aware_amplitude_states.npz`

## Interpretation

If this route reaches 10,500 km with revalidation, it supports replacing rho
monotonicity with a turn-aware branch coordinate for the high-amplitude
fixed-time family. If the route status is
`bounded_blocker_for_current_amplitude_chart`, the current amplitude chart is not
enough and the next attempt should change the continuation chart rather than
only shrinking the step size.
""",
        encoding="utf-8",
    )


def _write_state_archive(
    *,
    start: campaign.CampaignMember,
    accepted_members: list[campaign.CampaignMember],
    accepted_rows: list[dict[str, Any]],
) -> None:
    members = [start, *accepted_members]
    source_attempt_ids = ["start", *(str(row["attempt_id"]) for row in accepted_rows)]
    STATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        STATE_OUTPUT,
        schema_version=np.asarray("1.0"),
        created_by_script=np.asarray(Path(__file__).name),
        source_attempt_ids=np.asarray(source_attempt_ids),
        member_ids=np.asarray([member.member_id for member in members], dtype=int),
        states=np.stack([member.states for member in members]),
        phase_grid=members[0].phases,
        fixed_mapping_time_days=np.asarray([campaign.T_FIXED_DAYS for _ in members], dtype=float),
        rho=np.asarray([member.rho for member in members], dtype=float),
        mean_jacobi=np.asarray([member.mean_jacobi for member in members], dtype=float),
        max_abs_z_km=np.asarray([member.max_abs_z_km for member in members], dtype=float),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-km", type=float, default=TARGET_MIN_KM)
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument(
        "--step-options-km",
        type=_parse_step_options,
        default=DEFAULT_STEP_OPTIONS_KM,
        help="comma-separated amplitude step options, tried in order",
    )
    args = parser.parse_args()

    if args.max_steps <= 0:
        raise SystemExit("--max-steps must be positive")

    _write_header(ATTEMPTS_OUTPUT, ATTEMPT_FIELDS)
    _write_header(REVALIDATION_OUTPUT, REVALIDATION_FIELDS)

    source_previous, current = _frontier()
    start = current
    accepted_members: list[campaign.CampaignMember] = []
    accepted_rows: list[dict[str, Any]] = []
    revalidation_rows: list[dict[str, Any]] = []
    stop_reason = "maximum steps reached"

    print(
        f"start member={current.member_id}, max_z={current.max_abs_z_km:.6f} km, "
        f"rho={current.rho:.12g}",
        flush=True,
    )
    for stage in range(1, args.max_steps + 1):
        accepted_result: campaign.AttemptResult | None = None
        accepted_attempt_row: dict[str, Any] | None = None
        accepted_attempt_id = ""
        for option_index, step_option_km in enumerate(args.step_options_km, start=1):
            target = min(args.target_km, current.max_abs_z_km + step_option_km)
            attempt_id = f"stage_{stage}_step_{step_option_km:g}km"
            result = campaign._attempt_amplitude_target(
                current=current,
                member_id=1000 + stage,
                target_max_abs_z_km=target,
                step_size_km=step_option_km,
                macro_step=stage,
                rescue_step=option_index,
            )
            row = _attempt_row(
                attempt_id=attempt_id,
                stage=stage,
                step_option_km=step_option_km,
                target_max_abs_z_km=target,
                previous=current,
                result=result,
            )
            _append_row(ATTEMPTS_OUTPUT, ATTEMPT_FIELDS, row)
            print(
                f"{attempt_id}: turn_accept={row['turn_aware_acceptance']} "
                f"max_z={float(row['max_abs_z_km']):.6f} "
                f"dz={float(row['delta_max_abs_z_km']):.6f} "
                f"drho={float(row['delta_rho_rad']):.3e} "
                f"failed={row['turn_failed_gates']}",
                flush=True,
            )
            if bool(row["turn_aware_acceptance"]):
                accepted_result = result
                accepted_attempt_row = row
                accepted_attempt_id = attempt_id
                break
        if accepted_result is None or accepted_attempt_row is None:
            stop_reason = f"no turn-aware acceptable amplitude step at stage {stage}"
            break

        revalidation_row = _revalidate_member(
            member=accepted_result.member,
            previous=current,
            source_attempt_id=accepted_attempt_id,
        )
        _append_row(REVALIDATION_OUTPUT, REVALIDATION_FIELDS, revalidation_row)
        revalidation_rows.append(revalidation_row)
        accepted_rows.append(accepted_attempt_row)
        accepted_members.append(accepted_result.member)
        current = accepted_result.member
        if not bool(revalidation_row["revalidated_acceptance"]):
            stop_reason = f"turn-aware revalidation failed at stage {stage}"
            break
        if current.max_abs_z_km >= args.target_km:
            stop_reason = "target reached"
            break

    _write_doc(
        start=start,
        final=current,
        accepted_rows=accepted_rows,
        revalidation_rows=revalidation_rows,
        stop_reason=stop_reason,
        target_km=args.target_km,
    )
    _write_state_archive(
        start=start,
        accepted_members=accepted_members,
        accepted_rows=accepted_rows,
    )
    print(f"wrote {ATTEMPTS_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {REVALIDATION_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {STATE_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "turn-aware amplitude continuation: "
        f"accepted_steps={len(accepted_rows)}, "
        f"final_max_z={current.max_abs_z_km:.6f} km, "
        f"target_reached={current.max_abs_z_km >= args.target_km}, "
        f"stop_reason={stop_reason}",
        flush=True,
    )


if __name__ == "__main__":
    main()
