"""Route B BVP/PALC stabilization diagnostics.

This runner is deliberately local. It reuses the bounded BVP/PALC prototype,
checks N=41/N=61 consistency, diagnoses rank and near-null directions, retries
known-neighbor PALC with a bounded substep, checks a smaller quasi-vertical
family, and then allows at most three tiny forward diagnostics from member 10.

It does not update accepted branch data, figure scripts, Figure 3.16/3.17
status, Chapter 5, or teacher-facing packages.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
for candidate in (SRC, SCRIPTS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import prototype_chapter3_route_b_bvp_palc_neighborhood as bvp
from qp_orbits.corrected_dro_family import CorrectedDROFamilyMember
from qp_orbits.cr3bp import jacobi_constant


N_CONSISTENCY_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_n_consistency.csv"
)
RANK_DIAGNOSTICS_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_rank_diagnostics.csv"
)
KNOWN_NEIGHBOR_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_known_neighbor_retry.csv"
)
SMALL_FAMILY_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_small_family_sanity.csv"
)
TINY_FORWARD_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_stabilized_tiny_forward.csv"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_route_b_bvp_stabilization.md"

SMALL_VERTICAL_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_vertical_stroboscopic_torus_family.csv"
)
SMALL_HALO_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_stroboscopic_torus.csv"
)

SYSTEM = bvp.SYSTEMS["earth_moon"]
AUDIT_TOLERANCE = 1.0e-8
TARGET_AMPLITUDE_TOL_KM = 50.0
TARGET_RHO_TOL = 1.0e-4
TARGET_MEAN_JACOBI_TOL = 2.0e-6
BRANCH_JUMP_TINY_KM = 10.0


N_CONSISTENCY_FIELDS = (
    "member_id",
    "variant",
    "native_N",
    "target_N",
    "max_abs_z_km",
    "rho",
    "mean_jacobi",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "curve_jacobi_span",
    "fourier_tail_energy_state",
    "fourier_tail_energy_z",
    "jacobian_shape",
    "rank_estimate",
    "unknown_size",
    "rank_deficiency",
    "condition_estimate",
    "min_singular_value",
    "max_singular_value",
    "classification",
    "diagnosis",
)

RANK_DIAGNOSTIC_FIELDS = (
    "case_id",
    "member_id",
    "variant",
    "jacobian_shape",
    "rank_estimate",
    "unknown_size",
    "rank_deficiency",
    "condition_estimate",
    "min_singular_value",
    "near_null_count",
    "state_component_norm",
    "rho_component_norm",
    "low_mode_component_norm",
    "high_mode_component_norm",
    "phase_residual_sensitivity",
    "jacobi_residual_sensitivity",
    "map_residual_sensitivity",
    "dominant_phase_gauge_signature",
    "dominant_spectral_tail_signature",
    "classification",
    "diagnosis",
)

KNOWN_NEIGHBOR_FIELDS = (
    "case_id",
    "source_members",
    "target_member",
    "N_strategy",
    "solve_variant",
    "substep_index",
    "substep_count",
    "step_size",
    "palc_constraint_residual",
    "converged",
    "accepted",
    "max_abs_z_km",
    "target_max_abs_z_km",
    "amplitude_error_km",
    "rho",
    "target_rho",
    "rho_error",
    "mean_jacobi",
    "target_mean_jacobi",
    "mean_jacobi_error",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "curve_jacobi_span",
    "phase_residual",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "fourier_tail_energy_state",
    "fourier_tail_energy_z",
    "condition_estimate",
    "rank_estimate",
    "failure_reason",
    "classification",
    "diagnosis",
)

SMALL_FAMILY_FIELDS = (
    "case_id",
    "family",
    "source_file",
    "checked_files",
    "operation",
    "source_members",
    "target_member",
    "N",
    "mapping_time_days",
    "rho",
    "converged",
    "accepted",
    "max_abs_z_km",
    "target_max_abs_z_km",
    "amplitude_error_km",
    "mean_jacobi",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "curve_jacobi_span",
    "phase_residual",
    "fourier_tail_energy_state",
    "condition_estimate",
    "rank_estimate",
    "failure_reason",
    "classification",
    "diagnosis",
)

TINY_FORWARD_FIELDS = (
    "case_id",
    "step_index",
    "source_members",
    "N_strategy",
    "solve_variant",
    "step_size",
    "converged",
    "accepted",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "rho",
    "mean_jacobi",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "curve_jacobi_span",
    "phase_residual",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "fourier_tail_energy_state",
    "fourier_tail_energy_z",
    "condition_estimate",
    "rank_estimate",
    "stop_trigger",
    "classification",
    "diagnosis",
)


def _fmt(value: Any) -> str:
    return bvp._fmt(value)


def _write_rows(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    bvp._write_rows(path, fields, rows)


def _mean_jacobi(states: np.ndarray) -> float:
    return float(np.mean(jacobi_constant(states, SYSTEM.mu)))


def _resample_to(member: CorrectedDROFamilyMember, phases: np.ndarray) -> np.ndarray:
    if member.phases_rad.shape == phases.shape and np.allclose(member.phases_rad, phases):
        return member.states.copy()
    return bvp._resample_states(member.states, member.phases_rad, phases)


def _assemble_member(
    member: CorrectedDROFamilyMember,
    *,
    phases: np.ndarray | None,
    case_id: str,
    include_second_phase: bool,
) -> bvp.BVPAssembly:
    target_phases = member.phases_rad if phases is None else phases
    states = _resample_to(member, target_phases)
    return bvp._assemble_bvp(
        case_id=case_id,
        member_id=member.member,
        states=states,
        phases=target_phases,
        rho=member.rotation_angle_rad,
        mapping_time_days=member.mapping_time_days,
        target_jacobi=_mean_jacobi(states),
        reference_states=states,
        include_second_phase=include_second_phase,
    )


def _condition_and_classification(assembly: bvp.BVPAssembly) -> tuple[float, str]:
    condition = bvp._condition(assembly.singular_values)
    return condition, bvp._classification(assembly.rank_estimate, assembly.jacobian.shape, condition)


def _row_rank_deficiency(assembly: bvp.BVPAssembly) -> int:
    return int(assembly.jacobian.shape[1] - assembly.rank_estimate)


def _member_from_assembly(member_id: int, assembly: bvp.BVPAssembly) -> CorrectedDROFamilyMember:
    return bvp._member_like(
        member_id=member_id,
        states=assembly.states,
        phases=assembly.phases,
        rho=assembly.rho,
        mapping_time_days=assembly.mapping_time_days,
        map_residual_norm=float(np.max(assembly.map_residual_norms)),
        phase_residual=assembly.phase_residual,
    )


def _build_lifted_members(
    by_id: dict[int, CorrectedDROFamilyMember],
    target_phases: np.ndarray,
) -> dict[int, CorrectedDROFamilyMember]:
    lifted: dict[int, CorrectedDROFamilyMember] = {}
    for member_id in (7, 8, 9, 10):
        assembly = _assemble_member(
            by_id[member_id],
            phases=target_phases,
            case_id=f"lifted_member_{member_id}_to_N61",
            include_second_phase=True,
        )
        lifted[member_id] = _member_from_assembly(member_id, assembly)
    return lifted


def _n_consistency_rows(
    by_id: dict[int, CorrectedDROFamilyMember],
    target_phases: np.ndarray,
) -> tuple[list[dict[str, Any]], dict[str, bvp.BVPAssembly]]:
    rows: list[dict[str, Any]] = []
    assemblies: dict[str, bvp.BVPAssembly] = {}
    for member_id in (7, 8, 9, 10):
        member = by_id[member_id]
        variants = [
            ("native_N", None),
            ("lifted_to_N61", target_phases),
        ]
        for variant, phases in variants:
            target_N = member.states.shape[0] if phases is None else target_phases.size
            key = f"member_{member_id}_{variant}"
            assembly = _assemble_member(
                member,
                phases=phases,
                case_id=key,
                include_second_phase=True,
            )
            one_phase = _assemble_member(
                member,
                phases=phases,
                case_id=f"{key}_one_phase_check",
                include_second_phase=False,
            )
            condition, classification = _condition_and_classification(assembly)
            one_condition, one_classification = _condition_and_classification(one_phase)
            lifted_note = (
                "already N=61; no interpolation applied"
                if variant == "lifted_to_N61" and member.states.shape[0] == target_phases.size
                else "trigonometric interpolation to N=61"
                if variant == "lifted_to_N61"
                else "native representation"
            )
            if member_id in (8, 9):
                diagnosis = (
                    f"{lifted_note}; two_phase_overdetermined full rank; "
                    f"one_phase={one_classification} cond={one_condition:.6g}; "
                    "N lift preserves audit residual but does not by itself remove the one-phase null direction"
                )
            else:
                diagnosis = (
                    f"{lifted_note}; two_phase_overdetermined remains full rank; "
                    f"one_phase={one_classification} cond={one_condition:.6g}"
                )
            row = {
                "member_id": member_id,
                "variant": variant,
                "native_N": member.states.shape[0],
                "target_N": target_N,
                "max_abs_z_km": assembly.max_abs_z_km,
                "rho": assembly.rho,
                "mean_jacobi": _mean_jacobi(assembly.states),
                "map_residual_max_norm": float(np.max(assembly.map_residual_norms)),
                "map_residual_rms_norm": float(np.sqrt(np.mean(assembly.map_residual_norms**2))),
                "curve_jacobi_span": float(np.ptp(assembly.jacobi_values)),
                "fourier_tail_energy_state": assembly.fourier_tail_state,
                "fourier_tail_energy_z": assembly.fourier_tail_z,
                "jacobian_shape": f"{assembly.jacobian.shape[0]}x{assembly.jacobian.shape[1]}",
                "rank_estimate": assembly.rank_estimate,
                "unknown_size": assembly.jacobian.shape[1],
                "rank_deficiency": _row_rank_deficiency(assembly),
                "condition_estimate": condition,
                "min_singular_value": float(assembly.singular_values[-1]),
                "max_singular_value": float(assembly.singular_values[0]),
                "classification": classification,
                "diagnosis": diagnosis,
            }
            rows.append(row)
            assemblies[key] = assembly
            assemblies[f"{key}_one_phase"] = one_phase
    return rows, assemblies


def _mode_norms(state_vector: np.ndarray, sample_count: int) -> tuple[float, float, float]:
    state_matrix = state_vector.reshape(sample_count, 6)
    coefficients = np.fft.rfft(state_matrix, axis=0)
    total = float(np.sum(np.abs(coefficients) ** 2))
    if total <= 0.0:
        return 0.0, 0.0, 0.0
    split = max(1, int(np.ceil(0.25 * coefficients.shape[0])))
    low = float(np.sqrt(np.sum(np.abs(coefficients[:split]) ** 2) / total))
    high = float(np.sqrt(np.sum(np.abs(coefficients[split:]) ** 2) / total))
    return low, high, total


def _phase_alignment(assembly: bvp.BVPAssembly, state_vector: np.ndarray) -> tuple[float, float]:
    phase_direction = bvp._phase_direction(assembly.phases, assembly.reference_states).reshape(-1)
    second_direction = bvp._second_phase_direction(assembly.phases, assembly.reference_states).reshape(-1)
    state_norm = max(float(np.linalg.norm(state_vector)), 1.0e-14)
    phase = abs(float(np.dot(state_vector, phase_direction))) / (
        state_norm * max(float(np.linalg.norm(phase_direction)), 1.0e-14)
    )
    second = abs(float(np.dot(state_vector, second_direction))) / (
        state_norm * max(float(np.linalg.norm(second_direction)), 1.0e-14)
    )
    return phase, second


def _rank_diagnostic_row(
    *,
    case_id: str,
    member_id: int | None,
    variant: str,
    assembly: bvp.BVPAssembly,
    diagnosis_hint: str,
) -> dict[str, Any]:
    condition, classification = _condition_and_classification(assembly)
    vector = assembly.vh[-1]
    state_size = assembly.states.size
    state_vector = vector[:state_size]
    rho_component = float(abs(vector[state_size])) if vector.size > state_size else 0.0
    low_mode, high_mode, _ = _mode_norms(state_vector, assembly.states.shape[0])
    phase_alignment, second_alignment = _phase_alignment(assembly, state_vector)
    map_sensitivity = float(np.linalg.norm(assembly.jacobian[:state_size] @ vector))
    jacobi_sensitivity = (
        float(abs(assembly.jacobian[state_size] @ vector))
        if assembly.jacobian.shape[0] > state_size
        else None
    )
    phase_sensitivity = (
        float(abs(assembly.jacobian[state_size + 1] @ vector))
        if assembly.jacobian.shape[0] > state_size + 1
        else None
    )
    near_null_count = int(np.sum(assembly.singular_values / assembly.singular_values[0] < 1.0e-10))
    rho_fraction = rho_component / max(float(np.linalg.norm(vector)), 1.0e-14)
    if "one_phase" in variant and assembly.rank_estimate < assembly.jacobian.shape[1]:
        mechanism = "phase gauge / missing second phase row"
    elif high_mode > 0.50:
        mechanism = "high Fourier modes"
    elif rho_fraction > 0.50:
        mechanism = "rho column weakness"
    elif "palc_failed" in variant:
        mechanism = "branch geometry / oversized PALC predictor"
    else:
        mechanism = "scaled local branch geometry"
    return {
        "case_id": case_id,
        "member_id": member_id,
        "variant": variant,
        "jacobian_shape": f"{assembly.jacobian.shape[0]}x{assembly.jacobian.shape[1]}",
        "rank_estimate": assembly.rank_estimate,
        "unknown_size": assembly.jacobian.shape[1],
        "rank_deficiency": _row_rank_deficiency(assembly),
        "condition_estimate": condition,
        "min_singular_value": float(assembly.singular_values[-1]),
        "near_null_count": near_null_count,
        "state_component_norm": float(np.linalg.norm(state_vector)),
        "rho_component_norm": rho_component,
        "low_mode_component_norm": low_mode,
        "high_mode_component_norm": high_mode,
        "phase_residual_sensitivity": phase_sensitivity,
        "jacobi_residual_sensitivity": jacobi_sensitivity,
        "map_residual_sensitivity": map_sensitivity,
        "dominant_phase_gauge_signature": (
            f"phase_alignment={phase_alignment:.6g}; "
            f"second_phase_alignment={second_alignment:.6g}"
        ),
        "dominant_spectral_tail_signature": (
            f"low_mode_norm={low_mode:.6g}; high_mode_norm={high_mode:.6g}; "
            f"rho_fraction={rho_fraction:.6g}"
        ),
        "classification": classification,
        "diagnosis": f"{mechanism}; {diagnosis_hint}",
    }


def _strict_known_neighbor_acceptance(row: dict[str, Any], target: CorrectedDROFamilyMember) -> tuple[bool, str]:
    amplitude_error = abs(float(row["max_abs_z_km"]) - target.max_abs_z_km)
    rho_error = abs(float(row["rho"]) - target.rotation_angle_rad)
    jacobi_error = abs(float(row["mean_jacobi"]) - target.mean_jacobi)
    gates_ok = (
        bool(row["accepted"])
        and amplitude_error <= TARGET_AMPLITUDE_TOL_KM
        and rho_error <= TARGET_RHO_TOL
        and jacobi_error <= TARGET_MEAN_JACOBI_TOL
    )
    if gates_ok:
        return True, ""
    failed: list[str] = []
    if not bool(row["accepted"]):
        failed.append(str(row.get("failure_reason") or "failed residual/Jacobi/phase/tail gates"))
    if amplitude_error > TARGET_AMPLITUDE_TOL_KM:
        failed.append(f"amplitude_error>{TARGET_AMPLITUDE_TOL_KM:g} km")
    if rho_error > TARGET_RHO_TOL:
        failed.append(f"rho_error>{TARGET_RHO_TOL:g}")
    if jacobi_error > TARGET_MEAN_JACOBI_TOL:
        failed.append(f"mean_jacobi_error>{TARGET_MEAN_JACOBI_TOL:g}")
    return False, "; ".join(failed)


def _known_neighbor_case(
    *,
    case_id: str,
    previous: CorrectedDROFamilyMember,
    current: CorrectedDROFamilyMember,
    target: CorrectedDROFamilyMember,
    endpoint_condition: float,
    fraction: float,
    n_strategy: str,
    substep_index: int,
    substep_count: int,
    diagnosis: str,
) -> tuple[dict[str, Any], bvp.BVPAssembly]:
    source_members = f"{previous.member},{current.member}"
    row, _, assembly = bvp._palc_case(
        case_id=case_id,
        case_type="known_neighbor_reproduction",
        previous=previous,
        current=current,
        target=target,
        endpoint_condition=endpoint_condition,
        fraction=fraction,
    )
    accepted, strict_failure = _strict_known_neighbor_acceptance(row, target)
    failure_reason = strict_failure or row.get("failure_reason") or ""
    condition, classification = _condition_and_classification(assembly)
    return (
        {
            "case_id": case_id,
            "source_members": source_members,
            "target_member": target.member,
            "N_strategy": n_strategy,
            "solve_variant": "two_phase_rank_audit_plus_scaled_PALC",
            "substep_index": substep_index,
            "substep_count": substep_count,
            "step_size": row["step_size"],
            "palc_constraint_residual": row["palc_constraint_residual"],
            "converged": row["converged"],
            "accepted": accepted,
            "max_abs_z_km": row["max_abs_z_km"],
            "target_max_abs_z_km": target.max_abs_z_km,
            "amplitude_error_km": float(row["max_abs_z_km"]) - target.max_abs_z_km,
            "rho": row["rho"],
            "target_rho": target.rotation_angle_rad,
            "rho_error": float(row["rho"]) - target.rotation_angle_rad,
            "mean_jacobi": row["mean_jacobi"],
            "target_mean_jacobi": target.mean_jacobi,
            "mean_jacobi_error": float(row["mean_jacobi"]) - target.mean_jacobi,
            "map_residual_max_norm": row["map_residual_max_norm"],
            "map_residual_rms_norm": row["map_residual_rms_norm"],
            "curve_jacobi_span": row["curve_jacobi_span"],
            "phase_residual": row["phase_residual"],
            "one_map_phase_return_error": row["one_map_phase_return_error"],
            "ten_return_jacobi_span": row["ten_return_jacobi_span"],
            "fourier_tail_energy_state": row["fourier_tail_energy_state"],
            "fourier_tail_energy_z": row["fourier_tail_energy_z"],
            "condition_estimate": condition,
            "rank_estimate": assembly.rank_estimate,
            "failure_reason": failure_reason,
            "classification": classification,
            "diagnosis": diagnosis,
        },
        assembly,
    )


def _known_neighbor_rows(
    by_id: dict[int, CorrectedDROFamilyMember],
    lifted: dict[int, CorrectedDROFamilyMember],
    endpoint_condition: float,
) -> tuple[list[dict[str, Any]], dict[str, bvp.BVPAssembly]]:
    rows: list[dict[str, Any]] = []
    assemblies: dict[str, bvp.BVPAssembly] = {}
    native_row, native_assembly = _known_neighbor_case(
        case_id="8_to_9_native_retry",
        previous=by_id[7],
        current=by_id[8],
        target=by_id[9],
        endpoint_condition=endpoint_condition,
        fraction=1.0,
        n_strategy="native_N41_full_7_to_8_secant",
        substep_index=1,
        substep_count=1,
        diagnosis="full native 7_to_8 secant overshoots the small 8_to_9 neighbor gap",
    )
    rows.append(native_row)
    assemblies["8_to_9_native_retry"] = native_assembly

    lifted_row, lifted_assembly = _known_neighbor_case(
        case_id="8_to_9_N61_retry",
        previous=lifted[7],
        current=lifted[8],
        target=lifted[9],
        endpoint_condition=endpoint_condition,
        fraction=1.0,
        n_strategy="lifted_to_N61_full_7_to_8_secant",
        substep_index=1,
        substep_count=1,
        diagnosis="N61 lift alone does not fix the oversized predictor",
    )
    rows.append(lifted_row)
    assemblies["8_to_9_N61_retry"] = lifted_assembly

    rho_fraction = (
        (by_id[9].rotation_angle_rad - by_id[8].rotation_angle_rad)
        / (by_id[8].rotation_angle_rad - by_id[7].rotation_angle_rad)
    )
    substep_count = int(np.ceil(1.0 / max(rho_fraction, 1.0e-14)))
    substep_row, substep_assembly = _known_neighbor_case(
        case_id="8_to_9_substepped_retry",
        previous=lifted[7],
        current=lifted[8],
        target=lifted[9],
        endpoint_condition=endpoint_condition,
        fraction=float(rho_fraction),
        n_strategy="lifted_to_N61_rho_matched_substep",
        substep_index=1,
        substep_count=substep_count,
        diagnosis=(
            "bounded rho-matched substep mitigates the 8_to_9 predictor overshoot; "
            "this is local stabilization, not high-amplitude continuation"
        ),
    )
    rows.append(substep_row)
    assemblies["8_to_9_substepped_retry"] = substep_assembly

    confirm_row, confirm_assembly = _known_neighbor_case(
        case_id="9_to_10_N61_confirmation",
        previous=lifted[8],
        current=lifted[9],
        target=lifted[10],
        endpoint_condition=endpoint_condition,
        fraction=1.0,
        n_strategy="unified_N61_full_9_to_10_secant",
        substep_index=1,
        substep_count=1,
        diagnosis="9_to_10 remains accepted under unified N61 and strict local target gates",
    )
    rows.append(confirm_row)
    assemblies["9_to_10_N61_confirmation"] = confirm_assembly
    return rows, assemblies


def _rank_diagnostic_rows(
    n_assemblies: dict[str, bvp.BVPAssembly],
    retry_assemblies: dict[str, bvp.BVPAssembly],
) -> list[dict[str, Any]]:
    return [
        _rank_diagnostic_row(
            case_id="member_8_native_N",
            member_id=8,
            variant="native_N_one_phase_baseline",
            assembly=n_assemblies["member_8_native_N_one_phase"],
            diagnosis_hint="original rank-deficient classification is reproduced",
        ),
        _rank_diagnostic_row(
            case_id="member_9_native_N",
            member_id=9,
            variant="native_N_one_phase_baseline",
            assembly=n_assemblies["member_9_native_N_one_phase"],
            diagnosis_hint="original rank-deficient classification is reproduced",
        ),
        _rank_diagnostic_row(
            case_id="member_8_lifted_to_N61",
            member_id=8,
            variant="lifted_to_N61_one_phase_baseline",
            assembly=n_assemblies["member_8_lifted_to_N61_one_phase"],
            diagnosis_hint="N61 lift preserves residual but one-phase null direction remains",
        ),
        _rank_diagnostic_row(
            case_id="member_9_lifted_to_N61",
            member_id=9,
            variant="lifted_to_N61_one_phase_baseline",
            assembly=n_assemblies["member_9_lifted_to_N61_one_phase"],
            diagnosis_hint="N61 lift preserves residual but one-phase null direction remains",
        ),
        _rank_diagnostic_row(
            case_id="member_10_N61",
            member_id=10,
            variant="N61_two_phase_overdetermined",
            assembly=n_assemblies["member_10_native_N"],
            diagnosis_hint="best convention stays full rank at the endpoint",
        ),
        _rank_diagnostic_row(
            case_id="failed_8_to_9_PALC_candidate",
            member_id=None,
            variant="palc_failed_full_secant_N61",
            assembly=retry_assemblies["8_to_9_N61_retry"],
            diagnosis_hint="failure is consistent with an oversized full 7_to_8 predictor",
        ),
        _rank_diagnostic_row(
            case_id="accepted_9_to_10_PALC_candidate",
            member_id=None,
            variant="palc_accepted_unified_N61",
            assembly=retry_assemblies["9_to_10_N61_confirmation"],
            diagnosis_hint="local N61 PALC confirmation remains full-rank and accepted",
        ),
    ]


def _load_small_vertical_members() -> tuple[list[CorrectedDROFamilyMember], list[bvp.BVPAssembly]]:
    if not SMALL_VERTICAL_PATH.exists():
        return [], []
    with SMALL_VERTICAL_PATH.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    members: list[CorrectedDROFamilyMember] = []
    assemblies: list[bvp.BVPAssembly] = []
    for member_id in (0, 1, 2):
        selected = [
            row
            for row in rows
            if int(row["member"]) == member_id and int(row["time_index"]) == 0
        ]
        if not selected:
            return [], []
        selected.sort(key=lambda row: int(row["curve_index"]))
        phases = np.asarray([float(row["phase_rad"]) for row in selected], dtype=float)
        states = np.asarray(
            [
                [float(row[key]) for key in ("x", "y", "z", "xdot", "ydot", "zdot")]
                for row in selected
            ],
            dtype=float,
        )
        rho = float(selected[0]["rotation_angle_rad"])
        mapping_time_days = float(selected[0]["mapping_time_days"])
        assembly = bvp._assemble_bvp(
            case_id=f"small_quasi_vertical_member_{member_id}",
            member_id=member_id,
            states=states,
            phases=phases,
            rho=rho,
            mapping_time_days=mapping_time_days,
            target_jacobi=_mean_jacobi(states),
            reference_states=states,
            include_second_phase=True,
        )
        members.append(_member_from_assembly(member_id, assembly))
        assemblies.append(assembly)
    return members, assemblies


def _small_family_rows(endpoint_condition: float) -> list[dict[str, Any]]:
    checked_files = ";".join(
        str(path.relative_to(PROJECT_ROOT))
        for path in (SMALL_VERTICAL_PATH, SMALL_HALO_PATH)
        if path.exists()
    )
    members, assemblies = _load_small_vertical_members()
    if len(members) < 3:
        return [
            {
                "case_id": "small_family_not_available",
                "family": "not_available",
                "source_file": "N/A",
                "checked_files": checked_files or "no candidate files found",
                "operation": "not_available",
                "converged": False,
                "accepted": False,
                "failure_reason": "no compatible state-level smaller family with at least three members",
                "classification": "not_available",
                "diagnosis": "smaller-family sanity check could not be executed without fabricating data",
            }
        ]
    rows: list[dict[str, Any]] = []
    endpoint = assemblies[0]
    endpoint_condition_estimate, endpoint_classification = _condition_and_classification(endpoint)
    endpoint_accepted = bool(
        float(np.max(endpoint.map_residual_norms)) < AUDIT_TOLERANCE
        and float(np.ptp(endpoint.jacobi_values)) < AUDIT_TOLERANCE
        and _row_rank_deficiency(endpoint) == 0
    )
    rows.append(
        {
            "case_id": "small_quasi_vertical_endpoint_reproduction",
            "family": "chapter3_corrected_vertical_stroboscopic_torus_family",
            "source_file": str(SMALL_VERTICAL_PATH.relative_to(PROJECT_ROOT)),
            "checked_files": checked_files,
            "operation": "endpoint_style_BVP_residual_reproduction",
            "source_members": "0",
            "target_member": 0,
            "N": endpoint.states.shape[0],
            "mapping_time_days": endpoint.mapping_time_days,
            "rho": endpoint.rho,
            "converged": True,
            "accepted": endpoint_accepted,
            "max_abs_z_km": endpoint.max_abs_z_km,
            "target_max_abs_z_km": endpoint.max_abs_z_km,
            "amplitude_error_km": 0.0,
            "mean_jacobi": _mean_jacobi(endpoint.states),
            "map_residual_max_norm": float(np.max(endpoint.map_residual_norms)),
            "map_residual_rms_norm": float(np.sqrt(np.mean(endpoint.map_residual_norms**2))),
            "curve_jacobi_span": float(np.ptp(endpoint.jacobi_values)),
            "phase_residual": endpoint.phase_residual,
            "fourier_tail_energy_state": endpoint.fourier_tail_state,
            "condition_estimate": endpoint_condition_estimate,
            "rank_estimate": endpoint.rank_estimate,
            "failure_reason": "" if endpoint_accepted else "failed endpoint residual/rank audit",
            "classification": endpoint_classification,
            "diagnosis": "smaller quasi-vertical endpoint residual is reproducible but ill-conditioned",
        }
    )

    palc_row, _, palc_assembly = bvp._palc_case(
        case_id="small_quasi_vertical_known_neighbor",
        case_type="known_neighbor_reproduction",
        previous=members[0],
        current=members[1],
        target=members[2],
        endpoint_condition=endpoint_condition,
        fraction=1.0,
    )
    condition, classification = _condition_and_classification(palc_assembly)
    target = members[2]
    rows.append(
        {
            "case_id": "small_quasi_vertical_known_neighbor",
            "family": "chapter3_corrected_vertical_stroboscopic_torus_family",
            "source_file": str(SMALL_VERTICAL_PATH.relative_to(PROJECT_ROOT)),
            "checked_files": checked_files,
            "operation": "known_neighbor_PALC_reproduction",
            "source_members": "0,1",
            "target_member": 2,
            "N": palc_assembly.states.shape[0],
            "mapping_time_days": palc_assembly.mapping_time_days,
            "rho": palc_assembly.rho,
            "converged": palc_row["converged"],
            "accepted": False,
            "max_abs_z_km": palc_row["max_abs_z_km"],
            "target_max_abs_z_km": target.max_abs_z_km,
            "amplitude_error_km": float(palc_row["max_abs_z_km"]) - target.max_abs_z_km,
            "mean_jacobi": palc_row["mean_jacobi"],
            "map_residual_max_norm": palc_row["map_residual_max_norm"],
            "map_residual_rms_norm": palc_row["map_residual_rms_norm"],
            "curve_jacobi_span": palc_row["curve_jacobi_span"],
            "phase_residual": palc_row["phase_residual"],
            "fourier_tail_energy_state": palc_row["fourier_tail_energy_state"],
            "condition_estimate": condition,
            "rank_estimate": palc_assembly.rank_estimate,
            "failure_reason": palc_row["failure_reason"] or "failed strict smaller-family PALC gates",
            "classification": classification,
            "diagnosis": (
                "current PALC correction does not reproduce the smaller quasi-vertical neighbor; "
                "this points to solver/scaling fragility beyond quasi-DRO geometry alone"
            ),
        }
    )

    tiny_row, _, tiny_assembly = bvp._palc_case(
        case_id="small_quasi_vertical_tiny_forward",
        case_type="tiny_forward_diagnostic",
        previous=members[1],
        current=members[2],
        target=None,
        endpoint_condition=endpoint_condition,
        fraction=bvp.TINY_FORWARD_FRACTION,
    )
    condition, classification = _condition_and_classification(tiny_assembly)
    rows.append(
        {
            "case_id": "small_quasi_vertical_tiny_forward",
            "family": "chapter3_corrected_vertical_stroboscopic_torus_family",
            "source_file": str(SMALL_VERTICAL_PATH.relative_to(PROJECT_ROOT)),
            "checked_files": checked_files,
            "operation": "tiny_forward_diagnostic_step",
            "source_members": "1,2",
            "target_member": "predicted_forward",
            "N": tiny_assembly.states.shape[0],
            "mapping_time_days": tiny_assembly.mapping_time_days,
            "rho": tiny_assembly.rho,
            "converged": tiny_row["converged"],
            "accepted": bool(tiny_row["accepted"]),
            "max_abs_z_km": tiny_row["max_abs_z_km"],
            "target_max_abs_z_km": None,
            "amplitude_error_km": None,
            "mean_jacobi": tiny_row["mean_jacobi"],
            "map_residual_max_norm": tiny_row["map_residual_max_norm"],
            "map_residual_rms_norm": tiny_row["map_residual_rms_norm"],
            "curve_jacobi_span": tiny_row["curve_jacobi_span"],
            "phase_residual": tiny_row["phase_residual"],
            "fourier_tail_energy_state": tiny_row["fourier_tail_energy_state"],
            "condition_estimate": condition,
            "rank_estimate": tiny_assembly.rank_estimate,
            "failure_reason": tiny_row["failure_reason"],
            "classification": classification,
            "diagnosis": (
                "smaller-family tiny forward is not accepted with the present bounded PALC settings"
            ),
        }
    )
    return rows


def _stabilized_tiny_forward_rows(
    by_id: dict[int, CorrectedDROFamilyMember],
    endpoint_condition: float,
    prerequisites_ok: bool,
) -> list[dict[str, Any]]:
    if not prerequisites_ok:
        return [
            {
                "case_id": "stabilized_tiny_forward_skipped",
                "step_index": 0,
                "source_members": "9,10",
                "N_strategy": "N61",
                "solve_variant": "two_phase_rank_audit_plus_scaled_PALC",
                "converged": False,
                "accepted": False,
                "stop_trigger": "prerequisite gate failed",
                "classification": "skipped",
                "diagnosis": "N consistency, 8_to_9 mitigation, member 10 rank, or 9_to_10 confirmation failed",
            }
        ]
    rows: list[dict[str, Any]] = []
    previous = by_id[9]
    current = by_id[10]
    baseline_tail: float | None = None
    for step_index in range(1, 4):
        fraction = bvp.TINY_FORWARD_FRACTION if step_index == 1 else 1.0
        row, _, assembly = bvp._palc_case(
            case_id=f"stabilized_tiny_forward_step_{step_index}",
            case_type="tiny_forward_diagnostic",
            previous=previous,
            current=current,
            target=None,
            endpoint_condition=endpoint_condition,
            fraction=fraction,
        )
        condition, classification = _condition_and_classification(assembly)
        if baseline_tail is None:
            baseline_tail = max(float(row["fourier_tail_energy_state"]), 1.0e-30)
        stop_reasons: list[str] = []
        if condition > 100.0 * endpoint_condition:
            stop_reasons.append("condition estimate exceeded 100x endpoint")
        if float(row["fourier_tail_energy_state"]) > 100.0 * baseline_tail:
            stop_reasons.append("Fourier tail increased beyond 100x baseline")
        if not bool(row["accepted"]):
            stop_reasons.append(row["failure_reason"] or "residual/Jacobi/phase gate failed")
        if abs(float(row["delta_max_abs_z_km"])) > BRANCH_JUMP_TINY_KM:
            stop_reasons.append("possible branch jump from oversized tiny step")
        if float(row["max_abs_z_km"]) >= 10500.0:
            stop_reasons.append("hard stop before 10500 km target regime")
        accepted = bool(row["accepted"]) and not stop_reasons
        rows.append(
            {
                "case_id": f"stabilized_tiny_forward_step_{step_index}",
                "step_index": step_index,
                "source_members": f"{previous.member},{current.member}",
                "N_strategy": "N61",
                "solve_variant": "two_phase_rank_audit_plus_scaled_PALC",
                "step_size": row["step_size"],
                "converged": row["converged"],
                "accepted": accepted,
                "max_abs_z_km": row["max_abs_z_km"],
                "delta_max_abs_z_km": row["delta_max_abs_z_km"],
                "rho": row["rho"],
                "mean_jacobi": row["mean_jacobi"],
                "map_residual_max_norm": row["map_residual_max_norm"],
                "map_residual_rms_norm": row["map_residual_rms_norm"],
                "curve_jacobi_span": row["curve_jacobi_span"],
                "phase_residual": row["phase_residual"],
                "one_map_phase_return_error": row["one_map_phase_return_error"],
                "ten_return_jacobi_span": row["ten_return_jacobi_span"],
                "fourier_tail_energy_state": row["fourier_tail_energy_state"],
                "fourier_tail_energy_z": row["fourier_tail_energy_z"],
                "condition_estimate": condition,
                "rank_estimate": assembly.rank_estimate,
                "stop_trigger": "; ".join(stop_reasons),
                "classification": classification,
                "diagnosis": (
                    "accepted tiny local fixed-time diagnostic; not an accepted continuation branch breakthrough"
                    if accepted
                    else "stopped by bounded tiny-forward gate"
                ),
            }
        )
        if not accepted:
            break
        new_member = _member_from_assembly(10 + step_index, assembly)
        previous = current
        current = new_member
    return rows


def _bool_from_row(row: dict[str, Any], field: str) -> bool:
    value = row.get(field)
    return value is True or str(value) == "True"


def _document_text(
    *,
    n_rows: list[dict[str, Any]],
    rank_rows: list[dict[str, Any]],
    retry_rows: list[dict[str, Any]],
    small_rows: list[dict[str, Any]],
    tiny_rows: list[dict[str, Any]],
) -> str:
    n8_lift = next(row for row in n_rows if row["member_id"] == 8 and row["variant"] == "lifted_to_N61")
    n9_lift = next(row for row in n_rows if row["member_id"] == 9 and row["variant"] == "lifted_to_N61")
    retry_8_full = next(row for row in retry_rows if row["case_id"] == "8_to_9_N61_retry")
    retry_8_sub = next(row for row in retry_rows if row["case_id"] == "8_to_9_substepped_retry")
    retry_9_10 = next(row for row in retry_rows if row["case_id"] == "9_to_10_N61_confirmation")
    small_endpoint = next(row for row in small_rows if row["case_id"] == "small_quasi_vertical_endpoint_reproduction")
    small_palc = next(row for row in small_rows if row["case_id"] == "small_quasi_vertical_known_neighbor")
    accepted_tiny = [row for row in tiny_rows if _bool_from_row(row, "accepted")]
    total_tiny_gain = sum(float(row["delta_max_abs_z_km"]) for row in accepted_tiny)
    max_tiny = max(float(row["max_abs_z_km"]) for row in accepted_tiny) if accepted_tiny else None
    rank8 = next(row for row in rank_rows if row["case_id"] == "member_8_native_N")
    rank9 = next(row for row in rank_rows if row["case_id"] == "member_9_native_N")
    continuation_answer = (
        "not yet as a broad fixed-time continuation campaign; yes only as another bounded local diagnostic "
        "after PALC scaling is improved on the smaller-family sanity case"
    )
    return f"""# Chapter 3 Route B BVP/PALC Stabilization

## Purpose

This round tests whether the current fixed-time Route B BVP/PALC formulation is
stable, reproducible, and interpretable in the accepted quasi-DRO endpoint
neighborhood. It does not target 10,500 km or 11,000 km, does not update Figure
3.16 or Figure 3.17, and does not write any diagnostic candidate into the
accepted branch.

## Input Files

- `docs/route_b_formulation_note.md`
- `docs/chapter3_route_b_free_time_experiment.md`
- `docs/chapter3_route_b_refinement.md`
- `docs/chapter3_route_b_branch_consistency.md`
- `docs/chapter3_route_b_bvp_residual_prototype.md`
- `docs/chapter3_route_b_bvp_palc_neighborhood.md`
- `docs/reproduction_report/future_work_plan.md`
- `docs/project_index.md`
- `docs/artifact_manifest.md`
- `data/computed/chapter3_quasi_dro_palc_family.csv`
- `data/computed/chapter3_quasi_dro_palc_validation.csv`
- `data/computed/chapter3_route_b_bvp_scaling_experiments.csv`
- `data/computed/chapter3_route_b_bvp_neighbor_reproduction.csv`
- `data/computed/chapter3_route_b_bvp_palc_neighborhood.csv`
- `data/computed/chapter3_route_b_bvp_singular_values.csv`

## Implementation Decisions

- Reuse the existing local BVP/PALC assembly in
  `scripts/prototype_chapter3_route_b_bvp_palc_neighborhood.py`.
- Use trigonometric interpolation for the N=41 to N=61 lift.
- Use `two_phase_overdetermined` as the stabilized rank/conditioning convention,
  while retaining one-phase assemblies to diagnose the previous rank-deficient
  classification.
- Skip optional N=81 because N=61 is enough to test the stated neighborhood
  question and avoids expanding the search.
- Treat known-neighbor acceptance as stricter than Newton convergence: residual,
  Jacobi, phase, tail, condition, amplitude, rho, and mean-Jacobi closeness must
  all pass.
- Use `chapter3_corrected_vertical_stroboscopic_torus_family.csv` as the
  smaller-family sanity case because it contains state-level quasi-vertical
  invariant-curve samples.
- Allow at most three tiny forward steps from member 10, with hard stops on
  residual/Jacobi/phase failure, condition growth, Fourier-tail growth, branch
  jump, or entry into the 10,500 km target regime.

## N-Consistency Conclusion

Member 8 lifted to N=61 has map residual max
`{float(n8_lift["map_residual_max_norm"]):.6e}` and member 9 lifted to N=61 has
map residual max `{float(n9_lift["map_residual_max_norm"]):.6e}`. Both remain
within the local audit scale. Their Fourier tail drops after interpolation, but
the one-phase rank deficiency remains in the diagnostic one-phase system.

Therefore N=41/N=61 mixing does not explain the rank deficiency by itself. The
N=61 lift is still useful for uniform local diagnostics and tail control, so
subsequent BVP/PALC diagnostics should use N=61 when comparing members 7-10.

## Rank Deficiency Diagnosis

The one-phase member 8 diagnostic is `{rank8["classification"]}` with diagnosis
`{rank8["diagnosis"]}`. The one-phase member 9 diagnostic is
`{rank9["classification"]}` with diagnosis `{rank9["diagnosis"]}`.

Under the active second phase row, members 8, 9, and 10 are full column rank in
the local N-consistency audit. The dominant evidence is a phase-gauge/second
phase weakness in the one-phase convention, not a high-Fourier-tail failure or
an N=41 sampling artifact.

## 8_to_9 Failure Diagnosis

The full N=61 retry remains accepted=`{retry_8_full["accepted"]}` with failure
reason `{retry_8_full["failure_reason"]}`. The rho-matched substep retry is
accepted=`{retry_8_sub["accepted"]}`, amplitude error
`{float(retry_8_sub["amplitude_error_km"]):.6g}` km, rho error
`{float(retry_8_sub["rho_error"]):.6g}`, and map residual max
`{float(retry_8_sub["map_residual_max_norm"]):.6e}`.

This explains the previous 8_to_9 failure as an oversized 7_to_8 secant near a
small 8_to_9 neighbor gap. N=61 alone does not fix it; bounded substepping does.

## 9_to_10 Confirmation

The unified N=61 9_to_10 confirmation is accepted=`{retry_9_10["accepted"]}`.
It has amplitude error `{float(retry_9_10["amplitude_error_km"]):.6g}` km, rho
error `{float(retry_9_10["rho_error"]):.6g}`, and condition estimate
`{float(retry_9_10["condition_estimate"]):.6e}`. This remains a local
diagnostic candidate, not an accepted continuation-branch member.

## Smaller-Family Sanity Check

The smaller quasi-vertical endpoint reproduction is accepted=
`{small_endpoint["accepted"]}` with map residual max
`{float(small_endpoint["map_residual_max_norm"]):.6e}`. However, the
known-neighbor PALC sanity case is accepted=`{small_palc["accepted"]}` with
failure reason `{small_palc["failure_reason"]}`.

Thus the residual assembly is usable on a simpler family, but the present PALC
correction/scaling is not yet uniformly robust. This prevents a strong claim
that quasi-DRO 8_to_9 was the only problem.

## Stabilized Tiny Forward Result

Accepted tiny forward steps from member 10: `{len(accepted_tiny)}`. The total
accepted amplitude increase is `{total_tiny_gain:.6g}` km and the largest local
diagnostic amplitude is `{max_tiny if max_tiny is not None else 'N/A'}` km.
These steps remain tiny local diagnostics. They do not constitute a branch
breakthrough and do not approach the 10,500 km gate.

## Limited Fixed-Time BVP Continuation Decision

Decision: `{continuation_answer}`.

The quasi-DRO local layer is more interpretable than before: N-mixing is not the
main rank issue, the second phase row stabilizes rank, 8_to_9 is mitigated by a
bounded substep, 9_to_10 remains locally accepted, and tiny forward diagnostics
still work. The smaller-family PALC failure means the machinery should be
improved before any wider continuation campaign.

## Figure 3.16 / Figure 3.17 Freeze

Figure 3.16 and Figure 3.17 must remain frozen as partial physical-consistency
baselines. No diagnostic BVP/PALC row generated here is a McCarthy
constant-mapping-time reproduction source.

## Next Steps

1. Keep using N=61 and `two_phase_overdetermined` for local BVP/PALC diagnostics.
2. Replace full-secant 8_to_9 prediction with bounded rho/Jacobi-aware substeps.
3. Improve PALC scaling or correction safeguards on the smaller quasi-vertical
   family before extending quasi-DRO continuation.
4. Stop Route B high-amplitude attempts unless a multi-member fixed-time branch
   passes residual, Jacobi, phase, tail, conditioning, and target-closeness gates.
5. Continue reporting Figure 3.16 / Figure 3.17 as partial baselines until a
   confirmed fixed-time accepted continuation branch exists.
"""


def main() -> None:
    family = bvp.load_corrected_dro_family_csv(bvp.FAMILY_PATH)
    by_id = {member.member: member for member in family}
    required = {7, 8, 9, 10}
    missing = sorted(required.difference(by_id))
    if missing:
        raise RuntimeError(f"missing required quasi-DRO members: {missing}")
    endpoint_condition = bvp._read_endpoint_condition()
    target_phases = by_id[10].phases_rad

    n_rows, n_assemblies = _n_consistency_rows(by_id, target_phases)
    lifted = _build_lifted_members(by_id, target_phases)
    retry_rows, retry_assemblies = _known_neighbor_rows(by_id, lifted, endpoint_condition)
    rank_rows = _rank_diagnostic_rows(n_assemblies, retry_assemblies)
    small_rows = _small_family_rows(endpoint_condition)

    member10_rank_ok = any(
        row["member_id"] == 10
        and row["variant"] == "native_N"
        and int(row["rank_deficiency"]) == 0
        and row["classification"] == "full_column_rank_moderate"
        for row in n_rows
    )
    substep_ok = any(
        row["case_id"] == "8_to_9_substepped_retry" and _bool_from_row(row, "accepted")
        for row in retry_rows
    )
    confirmation_ok = any(
        row["case_id"] == "9_to_10_N61_confirmation" and _bool_from_row(row, "accepted")
        for row in retry_rows
    )
    tiny_rows = _stabilized_tiny_forward_rows(
        by_id,
        endpoint_condition,
        prerequisites_ok=member10_rank_ok and substep_ok and confirmation_ok,
    )

    _write_rows(N_CONSISTENCY_OUTPUT, N_CONSISTENCY_FIELDS, n_rows)
    _write_rows(RANK_DIAGNOSTICS_OUTPUT, RANK_DIAGNOSTIC_FIELDS, rank_rows)
    _write_rows(KNOWN_NEIGHBOR_OUTPUT, KNOWN_NEIGHBOR_FIELDS, retry_rows)
    _write_rows(SMALL_FAMILY_OUTPUT, SMALL_FAMILY_FIELDS, small_rows)
    _write_rows(TINY_FORWARD_OUTPUT, TINY_FORWARD_FIELDS, tiny_rows)
    DOC_OUTPUT.write_text(
        _document_text(
            n_rows=n_rows,
            rank_rows=rank_rows,
            retry_rows=retry_rows,
            small_rows=small_rows,
            tiny_rows=tiny_rows,
        ),
        encoding="utf-8",
    )

    print(f"wrote {N_CONSISTENCY_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {RANK_DIAGNOSTICS_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {KNOWN_NEIGHBOR_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {SMALL_FAMILY_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {TINY_FORWARD_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}")
    accepted_tiny = [row for row in tiny_rows if _bool_from_row(row, "accepted")]
    print(
        "stabilization summary: "
        f"substep_8_to_9={substep_ok}, "
        f"confirm_9_to_10={confirmation_ok}, "
        f"tiny_steps={len(accepted_tiny)}"
    )


if __name__ == "__main__":
    main()
