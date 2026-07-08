"""Audit variable-time projections back to the fixed Chapter 3 mapping time.

The accepted Route B free-time branch reaches thesis-scale amplitudes, but the
mapping time drifts away from the Fig. 3.16 / Fig. 3.17 fixed-time requirement.
This diagnostic gives the projection one more degree of freedom than the older
direct fixed-time audit: states, rho, target Jacobi, and mapping time are solved
together while residual rows enforce fixed mapping time and target amplitude.
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
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
for candidate in (SRC, SCRIPTS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_chapter3_integrated_breakthrough as campaign
from qp_orbits.corrected_dro_family import CorrectedDROFamilyMember, chapter3_quasi_dro_validation_row
from qp_orbits.cr3bp import cr3bp_rhs, jacobi_constant

ARCHIVE_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_free_time_branch_states.npz"
OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_variable_time_fixed_time_projection_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_variable_time_fixed_time_projection_audit.md"

AMPLITUDE_TARGET_TOL_KM = 0.25
TIME_TARGET_TOL_DAYS = 1.0e-10
DEFAULT_MAX_NEWTON_STEPS = 32

FIELDS = (
    "attempt_id",
    "source_case_id",
    "source_max_abs_z_km",
    "source_mapping_time_days",
    "source_rho_rad",
    "source_mean_jacobi",
    "target_mapping_time_days",
    "target_max_abs_z_km",
    "solved_max_abs_z_km",
    "anchor_amplitude_error_km",
    "max_abs_z_error_km",
    "solved_mapping_time_days",
    "mapping_time_error_days",
    "solved_rho_rad",
    "delta_rho_from_source",
    "solved_mean_jacobi",
    "delta_mean_jacobi_from_source",
    "converged",
    "accepted_projection",
    "reaches_10500_km",
    "reaches_11000_km",
    "map_residual_max",
    "mean_jacobi_residual",
    "jacobi_mean_span",
    "jacobi_one_map_drift",
    "jacobi_ten_return_span",
    "phase_residual",
    "second_phase_residual",
    "phase_return_error",
    "condition_number",
    "raw_condition_number",
    "gate_1_residual",
    "gate_2_jacobi",
    "gate_3_phase",
    "gate_4_rho_monotone_vs_endpoint",
    "gate_5_amplitude_vs_endpoint",
    "target_amplitude_gate",
    "gate_6_mapping_time",
    "gate_7_condition",
    "failed_gates",
    "failure_reason",
    "newton_iterations",
    "max_newton_steps",
    "max_correction_norm",
)


@dataclass(frozen=True)
class FreeTimeSource:
    case_id: str
    states: np.ndarray
    phases: np.ndarray
    mapping_time_days: float
    rho: float
    mean_jacobi: float
    max_abs_z_km: float


@dataclass(frozen=True)
class VariableTimeAssembly:
    case_id: str
    states: np.ndarray
    phases: np.ndarray
    rho: float
    target_jacobi: float
    mapping_time_days: float
    reference_states: np.ndarray
    mapped_states: np.ndarray
    target_states: np.ndarray
    map_residuals: np.ndarray
    map_residual_norms: np.ndarray
    jacobi_values: np.ndarray
    mean_jacobi_residual: float
    phase_residual: float
    second_phase_residual: float
    time_residual_days: float
    amplitude_residual_nd: float
    amplitude_error_km: float
    residual: np.ndarray
    jacobian: np.ndarray
    singular_values: np.ndarray
    max_abs_z_km: float


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


def _fixed_unknown_vector(
    states: np.ndarray,
    rho: float,
    target_jacobi: float,
    mapping_time_days: float,
) -> np.ndarray:
    return np.concatenate(
        [
            states.reshape(-1),
            np.array([rho, target_jacobi, mapping_time_days], dtype=float),
        ]
    )


def _unpack_unknown(vector: np.ndarray, sample_count: int) -> tuple[np.ndarray, float, float, float]:
    state_size = 6 * sample_count
    states = vector[:state_size].reshape(sample_count, 6)
    return (
        states,
        float(vector[state_size]),
        float(vector[state_size + 1]),
        float(vector[state_size + 2]),
    )


def _amplitude_anchor(states: np.ndarray) -> tuple[int, float]:
    index = int(np.argmax(np.abs(states[:, 2])))
    sign = float(np.sign(states[index, 2]))
    if sign == 0.0:
        sign = 1.0
    return index, sign


def _load_sources(*, min_source_z_km: float, max_sources: int | None) -> list[FreeTimeSource]:
    with np.load(ARCHIVE_PATH, allow_pickle=False) as data:
        rows: list[FreeTimeSource] = []
        for idx, case_id in enumerate(data["case_ids"]):
            max_z = float(data["max_abs_z_km"][idx])
            if max_z < min_source_z_km:
                continue
            rows.append(
                FreeTimeSource(
                    case_id=str(case_id),
                    states=np.asarray(data["states"][idx], dtype=float),
                    phases=np.asarray(data["phase_grid"], dtype=float),
                    mapping_time_days=float(data["mapping_time_days"][idx]),
                    rho=float(data["rho"][idx]),
                    mean_jacobi=float(data["mean_jacobi"][idx]),
                    max_abs_z_km=max_z,
                )
            )
    rows.sort(key=lambda row: row.max_abs_z_km)
    if max_sources is not None:
        return rows[:max_sources]
    return rows


def _endpoint_member() -> campaign.CampaignMember:
    fixed_family = campaign.load_corrected_dro_family_csv(campaign.FAMILY_PATH)
    return campaign._member_from_fixed(fixed_family[-1])


def _assemble_variable_time_bvp(
    *,
    case_id: str,
    states: np.ndarray,
    phases: np.ndarray,
    rho: float,
    target_jacobi: float,
    mapping_time_days: float,
    reference_states: np.ndarray,
    target_mapping_time_days: float,
    target_max_abs_z_km: float,
    amplitude_index: int,
    amplitude_sign: float,
) -> VariableTimeAssembly:
    time_unit = campaign.fixed_time.SYSTEM.time_unit_days or 1.0
    length_unit = campaign.fixed_time.SYSTEM.length_unit_km or 1.0
    sample_count = states.shape[0]
    state_size = states.size
    mapping_time_nd = mapping_time_days / time_unit
    interpolation = campaign.bvp._trigonometric_interpolation_matrix(phases, phases + rho)
    interpolation_derivative = campaign.bvp._trigonometric_interpolation_derivative_matrix(
        phases,
        phases + rho,
    )
    mapped, stms = campaign.bvp._stroboscopic_map_and_stms(
        states,
        period=mapping_time_nd,
        mu=campaign.fixed_time.SYSTEM.mu,
        max_step=campaign.bvp.INTEGRATION_MAX_STEP,
    )
    target_states = interpolation @ states
    map_residuals = mapped - target_states
    map_residual_norms = np.linalg.norm(map_residuals, axis=1)
    jacobi_values = np.asarray(jacobi_constant(states, campaign.fixed_time.SYSTEM.mu), dtype=float)
    mean_jacobi_residual = float(np.mean(jacobi_values) - target_jacobi)
    delta = states - reference_states
    phase_residual = float(np.sum(delta * campaign.bvp._phase_direction(phases, reference_states)))
    second_phase_residual = float(
        np.sum(delta * campaign.bvp._second_phase_direction(phases, reference_states))
    )
    time_residual_days = float(mapping_time_days - target_mapping_time_days)
    target_z_nd = amplitude_sign * target_max_abs_z_km / length_unit
    amplitude_residual_nd = float(states[amplitude_index, 2] - target_z_nd)
    amplitude_error_km = abs(amplitude_residual_nd) * length_unit
    residual = np.concatenate(
        [
            map_residuals.reshape(-1),
            np.array(
                [
                    mean_jacobi_residual,
                    phase_residual,
                    second_phase_residual,
                    time_residual_days,
                    amplitude_residual_nd,
                ],
                dtype=float,
            ),
        ]
    )
    jacobian = np.zeros((state_size + 5, state_size + 3), dtype=float)
    for row in range(sample_count):
        row_slice = slice(6 * row, 6 * row + 6)
        for col in range(sample_count):
            col_slice = slice(6 * col, 6 * col + 6)
            block = -interpolation[row, col] * np.eye(6)
            if row == col:
                block = block + stms[row]
            jacobian[row_slice, col_slice] = block
        jacobian[row_slice, state_size + 2] = (
            cr3bp_rhs(mapping_time_nd, mapped[row], campaign.fixed_time.SYSTEM.mu) / time_unit
        )
    rho_col = state_size
    jacobi_col = state_size + 1
    time_col = state_size + 2
    jacobian[:state_size, rho_col] = -(interpolation_derivative @ states).reshape(-1)
    jacobi_row = state_size
    phase_row = state_size + 1
    second_phase_row = state_size + 2
    time_row = state_size + 3
    amplitude_row = state_size + 4
    jacobian[jacobi_row, :state_size] = (
        campaign.bvp._jacobi_gradient(states, campaign.fixed_time.SYSTEM.mu) / sample_count
    ).reshape(-1)
    jacobian[jacobi_row, jacobi_col] = -1.0
    jacobian[phase_row, :state_size] = campaign.bvp._phase_direction(
        phases,
        reference_states,
    ).reshape(-1)
    jacobian[second_phase_row, :state_size] = campaign.bvp._second_phase_direction(
        phases,
        reference_states,
    ).reshape(-1)
    jacobian[time_row, time_col] = 1.0
    jacobian[amplitude_row, 6 * amplitude_index + 2] = 1.0
    singular_values = np.linalg.svd(jacobian, compute_uv=False)
    return VariableTimeAssembly(
        case_id=case_id,
        states=states.copy(),
        phases=phases.copy(),
        rho=float(rho),
        target_jacobi=float(target_jacobi),
        mapping_time_days=float(mapping_time_days),
        reference_states=reference_states.copy(),
        mapped_states=mapped,
        target_states=target_states,
        map_residuals=map_residuals,
        map_residual_norms=map_residual_norms,
        jacobi_values=jacobi_values,
        mean_jacobi_residual=mean_jacobi_residual,
        phase_residual=phase_residual,
        second_phase_residual=second_phase_residual,
        time_residual_days=time_residual_days,
        amplitude_residual_nd=amplitude_residual_nd,
        amplitude_error_km=amplitude_error_km,
        residual=residual,
        jacobian=jacobian,
        singular_values=singular_values,
        max_abs_z_km=float(np.max(np.abs(states[:, 2])) * length_unit),
    )


def _solve_projection(
    *,
    case_id: str,
    source: FreeTimeSource,
    target_mapping_time_days: float,
    max_newton_steps: int,
) -> tuple[VariableTimeAssembly, list[float], bool, str, float, float]:
    vector = _fixed_unknown_vector(
        source.states,
        source.rho,
        source.mean_jacobi,
        source.mapping_time_days,
    )
    amplitude_index, amplitude_sign = _amplitude_anchor(source.states)
    correction_norms: list[float] = []
    assembly: VariableTimeAssembly | None = None
    converged = False
    failure_reason = "maximum iterations reached"
    for _ in range(max_newton_steps):
        states, rho, target_jacobi, mapping_time_days = _unpack_unknown(vector, source.phases.size)
        assembly = _assemble_variable_time_bvp(
            case_id=case_id,
            states=states,
            phases=source.phases,
            rho=rho,
            target_jacobi=target_jacobi,
            mapping_time_days=mapping_time_days,
            reference_states=source.states,
            target_mapping_time_days=target_mapping_time_days,
            target_max_abs_z_km=source.max_abs_z_km,
            amplitude_index=amplitude_index,
            amplitude_sign=amplitude_sign,
        )
        map_max = float(np.max(assembly.map_residual_norms))
        if (
            map_max < campaign.fixed_time.AUDIT_TOLERANCE
            and abs(assembly.mean_jacobi_residual) < campaign.fixed_time.AUDIT_TOLERANCE
            and abs(assembly.phase_residual) < campaign.fixed_time.AUDIT_TOLERANCE
            and abs(assembly.second_phase_residual) < campaign.fixed_time.SECOND_PHASE_TOLERANCE
            and abs(assembly.time_residual_days) < TIME_TARGET_TOL_DAYS
            and assembly.amplitude_error_km < AMPLITUDE_TARGET_TOL_KM
        ):
            converged = True
            failure_reason = ""
            break
        correction = campaign.bvp._solve_scaled_correction(assembly.jacobian, assembly.residual)
        correction_norm = float(np.linalg.norm(correction))
        state_size = source.states.size
        state_delta = correction[:state_size].reshape(source.states.shape)
        block_norms = np.linalg.norm(state_delta, axis=1)
        scale = 1.0
        if block_norms.max() > campaign.fixed_time.CORRECTION_NORM_CAP:
            scale = min(scale, campaign.fixed_time.CORRECTION_NORM_CAP / float(block_norms.max()))
        if abs(correction[state_size]) > 4.0e-3:
            scale = min(scale, 4.0e-3 / abs(float(correction[state_size])))
        if abs(correction[state_size + 1]) > 5.0e-6:
            scale = min(scale, 5.0e-6 / abs(float(correction[state_size + 1])))
        if abs(correction[state_size + 2]) > 2.5e-3:
            scale = min(scale, 2.5e-3 / abs(float(correction[state_size + 2])))
        correction *= scale
        correction_norms.append(correction_norm * scale)
        vector += correction
    if assembly is None:
        states, rho, target_jacobi, mapping_time_days = _unpack_unknown(vector, source.phases.size)
        assembly = _assemble_variable_time_bvp(
            case_id=case_id,
            states=states,
            phases=source.phases,
            rho=rho,
            target_jacobi=target_jacobi,
            mapping_time_days=mapping_time_days,
            reference_states=source.states,
            target_mapping_time_days=target_mapping_time_days,
            target_max_abs_z_km=source.max_abs_z_km,
            amplitude_index=amplitude_index,
            amplitude_sign=amplitude_sign,
        )
    raw_condition = campaign.fixed_time._condition(assembly.singular_values)
    condition = campaign._scaled_condition(assembly.jacobian)
    return assembly, correction_norms, converged, failure_reason, condition, raw_condition


def _validation_for(assembly: VariableTimeAssembly) -> dict[str, str] | None:
    length_unit = campaign.fixed_time.SYSTEM.length_unit_km or 1.0
    try:
        jacobi_values = np.asarray(jacobi_constant(assembly.states, campaign.fixed_time.SYSTEM.mu), dtype=float)
        member = CorrectedDROFamilyMember(
            member=999,
            curve_indices=np.arange(assembly.states.shape[0]),
            phases_rad=assembly.phases.copy(),
            states=assembly.states.copy(),
            jacobi_values=jacobi_values,
            target_vertical_amplitude_nd=float(np.sqrt(2.0 * np.mean(assembly.states[:, 2] ** 2))),
            target_vertical_amplitude_km=float(
                np.sqrt(2.0 * np.mean(assembly.states[:, 2] ** 2)) * length_unit
            ),
            max_abs_z_km=assembly.max_abs_z_km,
            rotation_angle_rad=assembly.rho,
            mapping_time_days=assembly.mapping_time_days,
            map_residual_norm=float(np.max(assembly.map_residual_norms)),
            amplitude_residual=0.0,
            phase_residual=assembly.phase_residual,
            curve_jacobi_span=float(np.ptp(jacobi_values)),
        )
        return chapter3_quasi_dro_validation_row(
            member,
            campaign.fixed_time.SYSTEM,
            one_map_time_samples=7,
            ten_return_samples=401,
            max_step=campaign.bvp.INTEGRATION_MAX_STEP,
        )
    except (RuntimeError, ValueError, FloatingPointError):
        return None


def _attempt_row(
    *,
    attempt_id: str,
    source: FreeTimeSource,
    endpoint: campaign.CampaignMember,
    target_mapping_time_days: float,
    max_newton_steps: int,
) -> dict[str, Any]:
    assembly, correction_norms, converged, solver_failure, condition, raw_condition = _solve_projection(
        case_id=attempt_id,
        source=source,
        target_mapping_time_days=target_mapping_time_days,
        max_newton_steps=max_newton_steps,
    )
    validation = _validation_for(assembly)
    map_residual = float(np.max(assembly.map_residual_norms))
    jacobi_span = float(np.ptp(assembly.jacobi_values))
    one_map_drift = campaign._float_from_validation(validation, "one_map_sweep_jacobi_drift")
    ten_return = campaign._float_from_validation(validation, "ten_return_jacobi_span")
    phase_return = campaign._float_from_validation(validation, "one_map_phase_return_error")
    gate_1 = converged and map_residual < campaign.GATE_1_MAP_RESIDUAL
    gate_2 = (
        converged
        and jacobi_span < campaign.GATE_2_CURVE_JACOBI_SPAN
        and one_map_drift is not None
        and one_map_drift < campaign.GATE_2_ONE_MAP_JACOBI_DRIFT
        and ten_return is not None
        and ten_return < campaign.GATE_2_TEN_RETURN_JACOBI
    )
    gate_3 = converged and phase_return is not None and phase_return < campaign.GATE_3_PHASE_RETURN
    gate_4 = assembly.rho > endpoint.rho
    gate_5 = assembly.max_abs_z_km >= endpoint.max_abs_z_km - campaign.GATE_5_AMPLITUDE_TOL_KM
    max_abs_z_error_km = abs(assembly.max_abs_z_km - source.max_abs_z_km)
    target_amplitude_gate = max_abs_z_error_km < campaign.GATE_5_AMPLITUDE_TOL_KM
    gate_6 = abs(assembly.mapping_time_days - target_mapping_time_days) < campaign.GATE_6_MAPPING_TIME_DAYS
    gate_7 = condition < campaign.GATE_7_SCALED_CONDITION
    failed = [
        name
        for name, passed in (
            ("converged", converged),
            ("gate_1_residual", gate_1),
            ("gate_2_jacobi", gate_2),
            ("gate_3_phase", gate_3),
            ("gate_4_rho_monotone_vs_endpoint", gate_4),
            ("gate_5_amplitude_vs_endpoint", gate_5),
            ("target_amplitude_gate", target_amplitude_gate),
            ("gate_6_mapping_time", gate_6),
            ("gate_7_condition", gate_7),
        )
        if not passed
    ]
    accepted = not failed
    return {
        "attempt_id": attempt_id,
        "source_case_id": source.case_id,
        "source_max_abs_z_km": source.max_abs_z_km,
        "source_mapping_time_days": source.mapping_time_days,
        "source_rho_rad": source.rho,
        "source_mean_jacobi": source.mean_jacobi,
        "target_mapping_time_days": target_mapping_time_days,
        "target_max_abs_z_km": source.max_abs_z_km,
        "solved_max_abs_z_km": assembly.max_abs_z_km,
        "anchor_amplitude_error_km": assembly.amplitude_error_km,
        "max_abs_z_error_km": max_abs_z_error_km,
        "solved_mapping_time_days": assembly.mapping_time_days,
        "mapping_time_error_days": assembly.mapping_time_days - target_mapping_time_days,
        "solved_rho_rad": assembly.rho,
        "delta_rho_from_source": assembly.rho - source.rho,
        "solved_mean_jacobi": float(np.mean(assembly.jacobi_values)),
        "delta_mean_jacobi_from_source": float(np.mean(assembly.jacobi_values)) - source.mean_jacobi,
        "converged": converged,
        "accepted_projection": accepted,
        "reaches_10500_km": accepted and assembly.max_abs_z_km >= campaign.TARGET_MIN_KM,
        "reaches_11000_km": accepted and assembly.max_abs_z_km >= campaign.TARGET_STRETCH_KM,
        "map_residual_max": map_residual,
        "mean_jacobi_residual": assembly.mean_jacobi_residual,
        "jacobi_mean_span": jacobi_span,
        "jacobi_one_map_drift": one_map_drift,
        "jacobi_ten_return_span": ten_return,
        "phase_residual": assembly.phase_residual,
        "second_phase_residual": assembly.second_phase_residual,
        "phase_return_error": phase_return,
        "condition_number": condition,
        "raw_condition_number": raw_condition,
        "gate_1_residual": gate_1,
        "gate_2_jacobi": gate_2,
        "gate_3_phase": gate_3,
        "gate_4_rho_monotone_vs_endpoint": gate_4,
        "gate_5_amplitude_vs_endpoint": gate_5,
        "target_amplitude_gate": target_amplitude_gate,
        "gate_6_mapping_time": gate_6,
        "gate_7_condition": gate_7,
        "failed_gates": "; ".join(failed),
        "failure_reason": solver_failure if solver_failure else "; ".join(failed),
        "newton_iterations": len(correction_norms),
        "max_newton_steps": max_newton_steps,
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
    }


def _write_doc(rows: list[dict[str, Any]]) -> None:
    accepted = [row for row in rows if bool(row["accepted_projection"])]
    reached = [row for row in accepted if bool(row["reaches_10500_km"])]
    best = max(rows, key=lambda row: float(row["solved_max_abs_z_km"])) if rows else None
    lines = "\n".join(
        f"- `{row['attempt_id']}` from `{row['source_case_id']}`: source "
        f"`{float(row['source_max_abs_z_km']):.12g}` km -> solved "
        f"`{float(row['solved_max_abs_z_km']):.12g}` km, T error "
        f"`{float(row['mapping_time_error_days']):.3e}` days, accepted "
        f"`{row['accepted_projection']}`, failed `{row['failed_gates']}`"
        for row in rows
    ) or "- none"
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Variable-Time Fixed-Time Projection Audit

## Scope

This audit starts from accepted high-amplitude free-time quasi-DRO states. It
solves states, rho, target Jacobi, and mapping time together while enforcing
the fixed Fig. 3.16 / Fig. 3.17 mapping time and the source amplitude.

## Outcome

- Attempts: `{len(rows)}`
- Accepted projections: `{len(accepted)}`
- Accepted projections above 10,500 km: `{len(reached)}`
- Best non-accepted trial max abs z: `{best['solved_max_abs_z_km'] if best else 'N/A'}` km
- Fixed target mapping time: `{campaign.T_FIXED_DAYS}` days

## Rows

{lines}

## Interpretation

Accepted rows above 10,500 km would reopen the Fig. 3.16 / Fig. 3.17 upgrade
path. The large trial amplitudes in this table are not breakthroughs unless the
fixed-time, residual, Jacobi, phase, and target-amplitude gates also pass. If
high-amplitude source rows cannot satisfy those gates even with mapping time
included as a solved variable, the free-time branch is evidence of a different
branch direction rather than an accepted fixed-time high-amplitude quasi-DRO
family.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-source-z-km", type=float, default=10500.0)
    parser.add_argument("--max-sources", type=int, default=None)
    parser.add_argument("--max-newton-steps", type=int, default=DEFAULT_MAX_NEWTON_STEPS)
    args = parser.parse_args()
    if args.max_sources is not None and args.max_sources <= 0:
        raise SystemExit("--max-sources must be positive")
    if args.max_newton_steps <= 0:
        raise SystemExit("--max-newton-steps must be positive")
    if not ARCHIVE_PATH.exists():
        raise SystemExit(f"missing free-time archive: {ARCHIVE_PATH}")

    endpoint = _endpoint_member()
    sources = _load_sources(min_source_z_km=args.min_source_z_km, max_sources=args.max_sources)
    _write_header(OUTPUT)
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(sources, start=1):
        attempt_id = f"variable_T_fixed_T_projection_{index:02d}"
        print(attempt_id, source.case_id, flush=True)
        row = _attempt_row(
            attempt_id=attempt_id,
            source=source,
            endpoint=endpoint,
            target_mapping_time_days=campaign.T_FIXED_DAYS,
            max_newton_steps=args.max_newton_steps,
        )
        _append_row(row)
        rows.append(row)
        print(
            f"{attempt_id}: accepted={row['accepted_projection']} "
            f"z={float(row['solved_max_abs_z_km']):.6f} "
            f"T_err={float(row['mapping_time_error_days']):.3e} "
            f"failed={row['failed_gates']}",
            flush=True,
        )

    _write_doc(rows)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "variable-time fixed-time projection audit: "
        f"rows={len(rows)}, accepted={sum(bool(row['accepted_projection']) for row in rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
