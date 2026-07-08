"""Local turn diagnostics for the Chapter 3 integrated quasi-DRO frontier.

The integrated breakthrough campaign found a high-quality fixed-time member at
about 10,272 km, but attempts to continue with monotone rho either reduce
amplitude or fail residual/Jacobi/phase gates.  This script makes that local
turn evidence auditable without modifying the Fig. 3.16 / Fig. 3.17 source
branch.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter3_integrated_breakthrough as campaign

OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_integrated_turn_diagnostics.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_integrated_turn_diagnostics.md"

AMPLITUDE_STEPS_KM = (25.0, 10.0, 5.0, 2.0, 1.0, 0.5)
RHO_DELTAS = (8.333333333333334e-6, 2.0e-6, 2.0e-7, 1.0e-7, 2.0e-8, 1.0e-8)

FIELDS = (
    "attempt_id",
    "probe_type",
    "target_increment",
    "target_value",
    "source_member_id",
    "previous_max_abs_z_km",
    "previous_rho_rad",
    "converged",
    "overall_acceptance",
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
    "gate_4_rho_monotone",
    "gate_5_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "failed_gates",
    "failure_reason",
    "newton_iterations",
    "max_correction_norm",
    "interpretation",
)


def _fmt(value: Any) -> str:
    return campaign._fmt(value)


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _frontier() -> tuple[campaign.CampaignMember, campaign.CampaignMember, campaign.CampaignMember]:
    fixed_family = campaign.load_corrected_dro_family_csv(campaign.FAMILY_PATH)
    endpoint = campaign._member_from_fixed(fixed_family[-1])
    previous = campaign._member_from_fixed(fixed_family[-2])
    bootstrap, gates, _ = campaign._bootstrap_candidate(endpoint)
    if bootstrap is not None and gates is not None and gates.overall_acceptance:
        return previous, endpoint, bootstrap
    return previous, endpoint, endpoint


def _interpret(*, probe_type: str, result: campaign.AttemptResult, previous: campaign.CampaignMember) -> str:
    delta_z = result.member.max_abs_z_km - previous.max_abs_z_km
    delta_rho = result.member.rho - previous.rho
    failed = set(result.gates.failed_gates)
    closure_failed = bool({"gate_1_residual", "gate_2_jacobi", "gate_3_phase"} & failed)
    if result.gates.overall_acceptance and delta_z > 0.0 and delta_rho > 0.0:
        return "accepted_forward_candidate"
    if probe_type == "amplitude_target" and result.converged and delta_z > 0.0 and delta_rho < 0.0:
        return "higher_amplitude_closed_only_with_lower_rho"
    if probe_type == "rho_target" and delta_rho > 0.0 and delta_z > 0.0 and closure_failed:
        return "positive_rho_higher_amplitude_fails_closure_gates"
    if probe_type == "rho_target" and result.converged and delta_rho > 0.0 and delta_z <= 0.0:
        return "positive_rho_closed_but_amplitude_recedes"
    if delta_z <= 0.0:
        return "amplitude_recedes"
    return "unaccepted_probe"


def _row(
    *,
    attempt_id: str,
    probe_type: str,
    target_increment: float,
    target_value: float,
    previous: campaign.CampaignMember,
    result: campaign.AttemptResult,
) -> dict[str, Any]:
    gate_row = result.gates.row
    return {
        "attempt_id": attempt_id,
        "probe_type": probe_type,
        "target_increment": target_increment,
        "target_value": target_value,
        "source_member_id": result.member.source_member_id,
        "previous_max_abs_z_km": previous.max_abs_z_km,
        "previous_rho_rad": previous.rho,
        "converged": result.converged,
        "overall_acceptance": result.gates.overall_acceptance,
        "max_abs_z_km": result.member.max_abs_z_km,
        "delta_max_abs_z_km": result.member.max_abs_z_km - previous.max_abs_z_km,
        "rho_rad": result.member.rho,
        "delta_rho_rad": result.member.rho - previous.rho,
        "mean_jacobi": result.member.mean_jacobi,
        "map_residual_max": gate_row["map_residual_max"],
        "jacobi_mean_span": gate_row["jacobi_mean_span"],
        "jacobi_one_map_drift": gate_row["jacobi_one_map_drift"],
        "jacobi_ten_return_span": gate_row["jacobi_ten_return_span"],
        "phase_return_error": gate_row["phase_return_error"],
        "condition_number": gate_row["condition_number"],
        "raw_condition_number": gate_row["raw_condition_number"],
        "gate_1_residual": gate_row["gate_1_residual"],
        "gate_2_jacobi": gate_row["gate_2_jacobi"],
        "gate_3_phase": gate_row["gate_3_phase"],
        "gate_4_rho_monotone": gate_row["gate_4_rho_monotone"],
        "gate_5_amplitude": gate_row["gate_5_amplitude"],
        "gate_6_mapping_time": gate_row["gate_6_mapping_time"],
        "gate_7_condition": gate_row["gate_7_condition"],
        "failed_gates": "; ".join(result.gates.failed_gates),
        "failure_reason": result.failure_reason,
        "newton_iterations": len(result.correction_norms),
        "max_correction_norm": max(result.correction_norms) if result.correction_norms else 0.0,
        "interpretation": _interpret(probe_type=probe_type, result=result, previous=previous),
    }


def _write_doc(*, previous: campaign.CampaignMember, current: campaign.CampaignMember, rows: list[dict[str, Any]]) -> None:
    higher_amp_reversed = [
        row
        for row in rows
        if row["interpretation"] == "higher_amplitude_closed_only_with_lower_rho"
    ]
    rho_closure_failures = [
        row
        for row in rows
        if row["interpretation"] == "positive_rho_higher_amplitude_fails_closure_gates"
    ]
    rho_receded = [
        row
        for row in rows
        if row["interpretation"] == "positive_rho_closed_but_amplitude_recedes"
    ]
    accepted_forward = [
        row
        for row in rows
        if row["interpretation"] == "accepted_forward_candidate"
    ]
    accepted_text = "\n".join(
        f"- `{row['attempt_id']}`: dz `{row['delta_max_abs_z_km']:.12g}` km, "
        f"drho `{row['delta_rho_rad']:.12g}`"
        for row in accepted_forward
    ) or "- none"
    reversed_text = "\n".join(
        f"- `{row['attempt_id']}`: target dz `{row['target_increment']}` km, "
        f"solved dz `{row['delta_max_abs_z_km']:.12g}` km, "
        f"drho `{row['delta_rho_rad']:.12g}`, failed `{row['failed_gates']}`"
        for row in higher_amp_reversed
    ) or "- none"
    rho_failure_text = "\n".join(
        f"- `{row['attempt_id']}`: target drho `{row['target_increment']}`, "
        f"solved dz `{row['delta_max_abs_z_km']:.12g}` km, "
        f"failed `{row['failed_gates']}`"
        for row in rho_closure_failures
    ) or "- none"
    rho_receded_text = "\n".join(
        f"- `{row['attempt_id']}`: target drho `{row['target_increment']}`, "
        f"solved dz `{row['delta_max_abs_z_km']:.12g}` km, "
        f"overall acceptance `{row['overall_acceptance']}`"
        for row in rho_receded
    ) or "- none"
    best_attempt = max(rows, key=lambda row: float(row["max_abs_z_km"]))
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Integrated Turn Diagnostics

## Scope

This diagnostic probes the local fixed-time frontier after the integrated
breakthrough campaign. It tests whether higher max-z solutions near the current
frontier require decreasing rho, and whether positive-rho micro-steps can close
while preserving amplitude growth.

## Frontier

- Previous source member: `{previous.member_id}`
- Current probe member: `{current.member_id}`
- Current max abs z: `{current.max_abs_z_km:.12g}` km
- Current rho: `{current.rho:.12g}`
- Fixed mapping time: `{campaign.T_FIXED_DAYS}` days

## Probe Summary

- Accepted forward candidates: `{len(accepted_forward)}`
- Higher-amplitude closed probes with lower rho: `{len(higher_amp_reversed)}`
- Positive-rho higher-amplitude closure failures: `{len(rho_closure_failures)}`
- Positive-rho closed probes with receding amplitude: `{len(rho_receded)}`
- Best attempted max abs z: `{best_attempt['max_abs_z_km']:.12g}` km

## Accepted Forward Candidates

{accepted_text}

## Higher Amplitude With Lower Rho

{reversed_text}

## Positive Rho Closure Failures

{rho_failure_text}

## Positive Rho With Receding Amplitude

{rho_receded_text}

A probe can pass the current gate set while still receding by less than the
1 km Gate 5 tolerance. Such rows are useful numerical evidence, but they are not
frontier upgrades.

## Bounded Decision

Under the current Part 5 fixed-time gates, monotone-rho continuation is a
bounded blocker for updating Fig. 3.16 / Fig. 3.17. The local probes show that
closed higher-amplitude fixed-time states exist near the frontier, but the
closed probes move to lower rho and fail Gate 4. Positive-rho probes that gain
amplitude fail the closure/Jacobi/phase gates instead. This does not prove that
10,500 km fixed-time solutions are impossible; it proves that the current
monotone-rho parameterization is not a valid upgrade path.

Next viable route: replace Gate 4 with an explicit arclength/turn-aware branch
parameter and require independent revalidation, or restart from the free-time
high-amplitude branch and project onto fixed mapping time with a separate
continuation parameter.

## Output

- `data/computed/chapter3_integrated_turn_diagnostics.csv`
""",
        encoding="utf-8",
    )


def main() -> None:
    predictor_previous, endpoint, current = _frontier()
    source_previous = endpoint if current.member_id != endpoint.member_id else predictor_previous
    rows: list[dict[str, Any]] = []

    for index, step_km in enumerate(AMPLITUDE_STEPS_KM, start=1):
        target = current.max_abs_z_km + step_km
        result = campaign._attempt_amplitude_target(
            current=current,
            member_id=current.member_id + index,
            target_max_abs_z_km=target,
            step_size_km=step_km,
            macro_step=0,
            rescue_step=index,
        )
        rows.append(
            _row(
                attempt_id=f"amplitude_target_{step_km:g}km",
                probe_type="amplitude_target",
                target_increment=step_km,
                target_value=target,
                previous=current,
                result=result,
            )
        )

    for index, rho_delta in enumerate(RHO_DELTAS, start=1):
        result = campaign._attempt_substep(
            previous=source_previous,
            current=current,
            member_id=current.member_id + len(AMPLITUDE_STEPS_KM) + index,
            target_rho_delta=rho_delta,
            macro_step=0,
            substep_index=index,
            substep_count=1,
            retry_level=f"rho_target_{rho_delta:g}",
            step_source=f"rho_target_{rho_delta:g}",
            solver_mode="rho_target",
        )
        rows.append(
            _row(
                attempt_id=f"rho_target_{rho_delta:g}",
                probe_type="rho_target",
                target_increment=rho_delta,
                target_value=current.rho + rho_delta,
                previous=current,
                result=result,
            )
        )

    _write_rows(OUTPUT, rows)
    _write_doc(previous=source_previous, current=current, rows=rows)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(
        "turn diagnostics: "
        f"rows={len(rows)}, "
        f"accepted_forward={sum(row['interpretation'] == 'accepted_forward_candidate' for row in rows)}, "
        f"higher_amp_lower_rho={sum(row['interpretation'] == 'higher_amplitude_closed_only_with_lower_rho' for row in rows)}"
    )


if __name__ == "__main__":
    main()
