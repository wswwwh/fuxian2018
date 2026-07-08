"""Probe an augmented amplitude/rho/Jacobi PALC chart.

This is the next bounded diagnostic after the full-vector PALC continuation
only produced a tiny local improvement.  The PALC row is written in three
physical coordinates: signed amplitude, rotation angle, and target Jacobi.  It
keeps the fixed-time map, Jacobi, phase, second-phase, and conditioning gates.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
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
OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_augmented_coordinate_palc_probe.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_augmented_coordinate_palc_probe.md"

AMPLITUDE_SCALE_FLOOR_KM = 1.0
RHO_SCALE_FLOOR_RAD = 1.0e-7
JACOBI_SCALE_FLOOR = 1.0e-10

FIELDS = (
    "attempt_id",
    "pair_label",
    "step_scale",
    "anchor_index",
    "anchor_sign",
    "previous_max_abs_z_km",
    "current_max_abs_z_km",
    "predicted_max_abs_z_km",
    "solved_max_abs_z_km",
    "delta_max_abs_z_km",
    "previous_rho_rad",
    "current_rho_rad",
    "predicted_rho_rad",
    "solved_rho_rad",
    "delta_rho_rad",
    "predicted_target_jacobi",
    "solved_mean_jacobi",
    "coordinate_residual",
    "coordinate_scale_amplitude_km",
    "coordinate_scale_rho_rad",
    "coordinate_scale_jacobi",
    "converged",
    "coordinate_palc_acceptance",
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
    "failed_gates",
    "failure_reason",
    "newton_iterations",
    "max_newton_steps",
    "max_correction_norm",
)


@dataclass(frozen=True)
class CoordinatePALC:
    anchor_index: int
    anchor_sign: float
    predictor_coords: np.ndarray
    tangent_unit: np.ndarray
    scales: np.ndarray


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


def _archive_count() -> int:
    with np.load(STATE_INPUT, allow_pickle=True) as data:
        return int(data["states"].shape[0])


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


def _amplitude_anchor(states: np.ndarray) -> tuple[int, float]:
    index = int(np.argmax(np.abs(states[:, 2])))
    sign = float(np.sign(states[index, 2]))
    if sign == 0.0:
        sign = 1.0
    return index, sign


def _coordinate_values(
    *,
    states: np.ndarray,
    rho: float,
    target_jacobi: float,
    anchor_index: int,
    anchor_sign: float,
) -> np.ndarray:
    length_unit = campaign.fixed_time.SYSTEM.length_unit_km or 1.0
    signed_amplitude_km = float(anchor_sign * states[anchor_index, 2] * length_unit)
    return np.array([signed_amplitude_km, rho, target_jacobi], dtype=float)


def _coordinate_constraint(
    *,
    states: np.ndarray,
    rho: float,
    target_jacobi: float,
    context: CoordinatePALC,
) -> tuple[float, np.ndarray, np.ndarray]:
    state_size = states.size
    coords = _coordinate_values(
        states=states,
        rho=rho,
        target_jacobi=target_jacobi,
        anchor_index=context.anchor_index,
        anchor_sign=context.anchor_sign,
    )
    scaled_delta = (coords - context.predictor_coords) / context.scales
    residual = float(np.dot(scaled_delta, context.tangent_unit))
    row = np.zeros(state_size + 2, dtype=float)
    length_unit = campaign.fixed_time.SYSTEM.length_unit_km or 1.0
    row[6 * context.anchor_index + 2] = (
        context.tangent_unit[0] * context.anchor_sign * length_unit / context.scales[0]
    )
    row[state_size] = context.tangent_unit[1] / context.scales[1]
    row[state_size + 1] = context.tangent_unit[2] / context.scales[2]
    return residual, row, coords


def _make_coordinate_palc(
    *,
    previous: campaign.CampaignMember,
    current: campaign.CampaignMember,
    step_scale: float,
) -> CoordinatePALC:
    anchor_index, anchor_sign = _amplitude_anchor(current.states)
    previous_coords = _coordinate_values(
        states=previous.states,
        rho=previous.rho,
        target_jacobi=previous.mean_jacobi,
        anchor_index=anchor_index,
        anchor_sign=anchor_sign,
    )
    current_coords = _coordinate_values(
        states=current.states,
        rho=current.rho,
        target_jacobi=current.mean_jacobi,
        anchor_index=anchor_index,
        anchor_sign=anchor_sign,
    )
    secant = current_coords - previous_coords
    scales = np.maximum(
        np.abs(secant),
        np.array(
            [AMPLITUDE_SCALE_FLOOR_KM, RHO_SCALE_FLOOR_RAD, JACOBI_SCALE_FLOOR],
            dtype=float,
        ),
    )
    scaled_secant = secant / scales
    tangent_norm = max(float(np.linalg.norm(scaled_secant)), 1.0e-14)
    return CoordinatePALC(
        anchor_index=anchor_index,
        anchor_sign=anchor_sign,
        predictor_coords=current_coords + step_scale * secant,
        tangent_unit=scaled_secant / tangent_norm,
        scales=scales,
    )


def _solve_augmented_coordinate_palc(
    *,
    case_id: str,
    predictor: np.ndarray,
    phases: np.ndarray,
    reference_states: np.ndarray,
    context: CoordinatePALC,
    max_newton_steps: int,
) -> tuple[
    campaign.fixed_time.FixedTimeAssembly,
    list[float],
    bool,
    str,
    float,
    float,
    float,
]:
    sample_count = phases.size
    vector = predictor.copy()
    correction_norms: list[float] = []
    assembly: campaign.fixed_time.FixedTimeAssembly | None = None
    final_jacobian: np.ndarray | None = None
    coordinate_residual = float("nan")
    converged = False
    failure_reason = "maximum iterations reached"
    for _ in range(max_newton_steps):
        states, rho, target_jacobi = campaign.fixed_time._unpack_fixed_unknown(vector, sample_count)
        assembly = campaign.fixed_time._assemble_fixed_time_bvp(
            case_id=case_id,
            states=states,
            phases=phases,
            rho=rho,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            include_second_phase=True,
            palc=None,
        )
        coordinate_residual, coordinate_row, _ = _coordinate_constraint(
            states=states,
            rho=rho,
            target_jacobi=target_jacobi,
            context=context,
        )
        residual = np.concatenate(
            [assembly.residual, np.array([coordinate_residual], dtype=float)]
        )
        final_jacobian = np.zeros(
            (assembly.jacobian.shape[0] + 1, assembly.jacobian.shape[1]),
            dtype=float,
        )
        final_jacobian[:-1, :] = assembly.jacobian
        final_jacobian[-1, :] = coordinate_row
        map_max = float(np.max(assembly.map_residual_norms))
        if (
            map_max < campaign.fixed_time.AUDIT_TOLERANCE
            and abs(assembly.mean_jacobi_residual) < campaign.fixed_time.AUDIT_TOLERANCE
            and abs(assembly.phase_residual) < campaign.fixed_time.AUDIT_TOLERANCE
            and abs(assembly.second_phase_residual) < campaign.fixed_time.SECOND_PHASE_TOLERANCE
            and abs(coordinate_residual) < campaign.fixed_time.AUDIT_TOLERANCE
        ):
            converged = True
            failure_reason = ""
            break
        correction = campaign.bvp._solve_scaled_correction(final_jacobian, residual)
        correction_norm = float(np.linalg.norm(correction))
        if correction_norm > campaign.fixed_time.CORRECTION_NORM_CAP:
            correction *= campaign.fixed_time.CORRECTION_NORM_CAP / correction_norm
            correction_norm = campaign.fixed_time.CORRECTION_NORM_CAP
        correction_norms.append(correction_norm)
        vector += correction

    if assembly is None or final_jacobian is None:
        states, rho, target_jacobi = campaign.fixed_time._unpack_fixed_unknown(vector, sample_count)
        assembly = campaign.fixed_time._assemble_fixed_time_bvp(
            case_id=case_id,
            states=states,
            phases=phases,
            rho=rho,
            target_jacobi=target_jacobi,
            reference_states=reference_states,
            include_second_phase=True,
            palc=None,
        )
        coordinate_residual, coordinate_row, _ = _coordinate_constraint(
            states=states,
            rho=rho,
            target_jacobi=target_jacobi,
            context=context,
        )
        final_jacobian = np.zeros(
            (assembly.jacobian.shape[0] + 1, assembly.jacobian.shape[1]),
            dtype=float,
        )
        final_jacobian[:-1, :] = assembly.jacobian
        final_jacobian[-1, :] = coordinate_row

    raw_condition = campaign.fixed_time._condition(
        np.linalg.svd(final_jacobian, compute_uv=False)
    )
    condition = campaign._scaled_condition(final_jacobian)
    return (
        assembly,
        correction_norms,
        converged,
        failure_reason,
        condition,
        raw_condition,
        coordinate_residual,
    )


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


def _attempt_pair(
    *,
    pair_offset: int,
    step_scale: float,
    attempt_id: str,
    max_newton_steps: int,
) -> dict[str, Any]:
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
    context = _make_coordinate_palc(
        previous=previous,
        current=current,
        step_scale=step_scale,
    )
    (
        assembly,
        correction_norms,
        converged,
        solver_failure,
        condition,
        raw_condition,
        coordinate_residual,
    ) = _solve_augmented_coordinate_palc(
        case_id=attempt_id,
        predictor=predictor,
        phases=current.phases,
        reference_states=current.states,
        context=context,
        max_newton_steps=max_newton_steps,
    )
    validation = campaign.fixed_time._validation_for(assembly)
    member = campaign._member_from_assembly(
        member_id=4000 + pair_offset,
        assembly=assembly,
        source="augmented_coordinate_palc_probe",
        source_member_id=current.source_member_id,
    )
    gates = campaign._evaluate_gates(
        member=member,
        previous=current,
        assembly=assembly,
        validation=validation,
        converged=converged,
        step_source="augmented_coordinate_palc_probe",
        macro_step=pair_offset,
        substep_index=1,
        substep_count=1,
        condition_override=condition,
        raw_condition_override=raw_condition,
    )
    failed = _failed_gates(
        member=member,
        previous=current,
        gates=gates,
        converged=converged,
    )
    length_unit = campaign.fixed_time.SYSTEM.length_unit_km or 1.0
    return {
        "attempt_id": attempt_id,
        "pair_label": f"{previous.source_member_id}->{current.source_member_id}",
        "step_scale": step_scale,
        "anchor_index": context.anchor_index,
        "anchor_sign": context.anchor_sign,
        "previous_max_abs_z_km": previous.max_abs_z_km,
        "current_max_abs_z_km": current.max_abs_z_km,
        "predicted_max_abs_z_km": float(np.max(np.abs(predicted_states[:, 2])) * length_unit),
        "solved_max_abs_z_km": member.max_abs_z_km,
        "delta_max_abs_z_km": member.max_abs_z_km - current.max_abs_z_km,
        "previous_rho_rad": previous.rho,
        "current_rho_rad": current.rho,
        "predicted_rho_rad": predicted_rho,
        "solved_rho_rad": member.rho,
        "delta_rho_rad": member.rho - current.rho,
        "predicted_target_jacobi": predicted_jacobi,
        "solved_mean_jacobi": member.mean_jacobi,
        "coordinate_residual": coordinate_residual,
        "coordinate_scale_amplitude_km": context.scales[0],
        "coordinate_scale_rho_rad": context.scales[1],
        "coordinate_scale_jacobi": context.scales[2],
        "converged": converged,
        "coordinate_palc_acceptance": converged and not failed,
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
        "original_gate_4_rho_monotone": gates.row["gate_4_rho_monotone"],
        "turn_gate_4_amplitude_monotone": member.max_abs_z_km > current.max_abs_z_km + 1.0e-6,
        "gate_5_amplitude": gates.row["gate_5_amplitude"],
        "gate_6_mapping_time": gates.row["gate_6_mapping_time"],
        "gate_7_condition": gates.row["gate_7_condition"],
        "failed_gates": "; ".join(failed),
        "failure_reason": solver_failure if solver_failure else "; ".join(failed),
        "newton_iterations": len(correction_norms),
        "max_newton_steps": max_newton_steps,
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
    }


def _write_doc(rows: list[dict[str, Any]]) -> None:
    accepted = [row for row in rows if bool(row["coordinate_palc_acceptance"])]
    best = max(rows, key=lambda row: float(row["solved_max_abs_z_km"])) if rows else None
    lines = "\n".join(
        f"- `{row['attempt_id']}`: solved max z "
        f"`{float(row['solved_max_abs_z_km']):.12g}` km, dz "
        f"`{float(row['delta_max_abs_z_km']):.12g}` km, accepted "
        f"`{row['coordinate_palc_acceptance']}`, failed `{row['failed_gates']}`"
        for row in rows
    ) or "- none"
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Augmented Coordinate PALC Probe

## Scope

This diagnostic tests an augmented arclength row in signed amplitude, rho, and
target-Jacobi coordinates. It is seeded from the archived turn-aware amplitude
states and does not update Fig. 3.16 / Fig. 3.17.

## Outcome

- Attempts: `{len(rows)}`
- Accepted coordinate-PALC steps: `{len(accepted)}`
- Best solved max abs z: `{best['solved_max_abs_z_km'] if best else 'N/A'}` km
- Minimum target: `{campaign.TARGET_MIN_KM}` km
- Max Newton steps per row: `{best['max_newton_steps'] if best else 'N/A'}`
- Scale floors: amplitude `{AMPLITUDE_SCALE_FLOOR_KM}` km, rho `{RHO_SCALE_FLOOR_RAD}` rad, Jacobi `{JACOBI_SCALE_FLOOR}`

## Rows

{lines}

## Interpretation

Accepted rows would justify promoting this coordinate chart into a longer
continuation with independent revalidation. If the rows gain amplitude but do
not converge after the configured Newton budget, the explicit
amplitude/rho/Jacobi arclength chart is not producing auditable fixed-time
quasi-DRO members and remains bounded below the 10,500 km requirement.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step-scales", type=_parse_float_list, default=(1.0, 0.5, 0.25, 0.1))
    parser.add_argument("--pair-offsets", type=_parse_float_list, default=(1.0, 2.0))
    parser.add_argument("--max-newton-steps", type=int, default=campaign.fixed_time.MAX_NEWTON_STEPS)
    args = parser.parse_args()
    if args.max_newton_steps <= 0:
        raise SystemExit("--max-newton-steps must be positive")
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
                max_newton_steps=args.max_newton_steps,
            )
            _append_row(row)
            rows.append(row)
            print(
                f"{attempt_id}: accepted={row['coordinate_palc_acceptance']} "
                f"z={float(row['solved_max_abs_z_km']):.6f} "
                f"dz={float(row['delta_max_abs_z_km']):.6f} "
                f"failed={row['failed_gates']}",
                flush=True,
            )

    _write_doc(rows)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "augmented coordinate PALC probe: "
        f"rows={len(rows)}, "
        f"accepted={sum(bool(row['coordinate_palc_acceptance']) for row in rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
