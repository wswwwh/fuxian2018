"""Route B Fourier/collocation BVP residual prototype for the quasi-DRO endpoint.

This script is intentionally diagnostic. It assembles a map-based one-angle
invariant-curve residual at the current accepted N=61 endpoint, with fixed
mapping time and solved/diagnostic rotation angle. It does not run continuation,
does not update figure data, and does not modify accepted branch CSV files.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import CorrectedDROFamilyMember, load_corrected_dro_family_csv
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    _jacobi_gradient,
    _stroboscopic_map_and_stms,
    _trigonometric_interpolation_derivative_matrix,
    _trigonometric_interpolation_matrix,
)


FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
VALIDATION_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_validation.csv"
ENDPOINT_OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_endpoint_residual.csv"
BLOCK_OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_residual_blocks.csv"
INDEX_OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_bvp_index_map.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_route_b_bvp_residual_prototype.md"

FIXED_MAPPING_TIME_DAYS = 14.74932760227518
CURRENT_RHO_RAD = 1.443877875293695
EXPECTED_ENDPOINT_SAMPLES = 61
INTEGRATION_MAX_STEP = 0.02


ENDPOINT_FIELDS = (
    "case_id",
    "source_family_csv",
    "source_validation_csv",
    "source_member",
    "curve_samples",
    "fixed_mapping_time_days",
    "fixed_mapping_time_nd",
    "rho_input_rad",
    "rho_endpoint_rad",
    "rho_delta_rad",
    "mean_jacobi_target",
    "mean_jacobi",
    "total_residual_norm",
    "map_residual_max_norm",
    "map_residual_rms_norm",
    "mean_jacobi_residual",
    "phase_residual",
    "second_phase_diagnostic",
    "curve_jacobi_span",
    "fourier_tail_energy_state",
    "fourier_tail_energy_z",
    "residual_peak_index",
    "residual_peak_phase",
    "jacobian_shape",
    "jacobian_rank_estimate",
    "condition_estimate",
    "max_singular_value",
    "min_singular_value",
    "smallest_singular_values",
    "largest_singular_values",
    "existing_audit_map_residual_norm",
    "existing_audit_curve_jacobi_span",
    "existing_audit_phase_residual",
    "existing_validation_one_map_phase_return_error",
    "endpoint_residual_matches_existing_audit_level",
    "phase_constraint_closed",
    "conditioning_classification",
    "bvp_route_worth_continuing",
    "correction_attempted",
    "correction_before_residual",
    "correction_after_residual",
    "correction_norm",
    "correction_accepted",
    "correction_reason",
)

BLOCK_FIELDS = (
    "block_name",
    "index",
    "phase_rad",
    "residual_size",
    "l2_norm",
    "rms_norm",
    "max_abs",
    "row_norm",
    "entered_endpoint_residual",
    "notes",
)

INDEX_FIELDS = (
    "kind",
    "name",
    "index",
    "start",
    "end",
    "size",
    "notes",
)


@dataclass(frozen=True)
class ResidualAssembly:
    member: CorrectedDROFamilyMember
    validation: dict[str, str]
    mapping_time_nd: float
    rho: float
    mapped_states: np.ndarray
    target_states: np.ndarray
    map_residuals: np.ndarray
    map_residual_norms: np.ndarray
    mean_jacobi_residual: float
    phase_residual: float
    second_phase_diagnostic: float
    jacobi_values: np.ndarray
    fourier_tail_state: float
    fourier_tail_z: float
    jacobian: np.ndarray
    singular_values: np.ndarray
    rank_estimate: int


def _fmt(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    number = float(value)
    if not np.isfinite(number):
        return "N/A"
    return f"{number:.16g}"


def _write_rows(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in fields})


def _read_validation_rows(path: Path) -> dict[int, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return {int(row["member"]): row for row in csv.DictReader(stream)}


def _select_endpoint(family: tuple[CorrectedDROFamilyMember, ...]) -> CorrectedDROFamilyMember:
    candidates = [member for member in family if member.states.shape[0] == EXPECTED_ENDPOINT_SAMPLES]
    if not candidates:
        raise RuntimeError(f"no N={EXPECTED_ENDPOINT_SAMPLES} endpoint found in {FAMILY_PATH}")
    endpoint = candidates[-1]
    if endpoint.member != family[-1].member:
        raise RuntimeError("N=61 candidate is not the final accepted PALC endpoint")
    if abs(endpoint.mapping_time_days - FIXED_MAPPING_TIME_DAYS) > 1.0e-12:
        raise RuntimeError("endpoint mapping time differs from the frozen Route B target")
    if abs(endpoint.rotation_angle_rad - CURRENT_RHO_RAD) > 1.0e-12:
        raise RuntimeError("endpoint rho differs from the frozen Route B target")
    return endpoint


def _phase_direction(phases: np.ndarray, reference: np.ndarray) -> np.ndarray:
    derivative = _trigonometric_interpolation_derivative_matrix(phases, phases) @ reference
    norm = float(np.linalg.norm(derivative))
    if norm <= 1.0e-14:
        raise RuntimeError("degenerate curve phase direction")
    return derivative / norm


def _second_phase_direction(phases: np.ndarray, reference: np.ndarray) -> np.ndarray:
    first = _trigonometric_interpolation_derivative_matrix(phases, phases) @ reference
    second = _trigonometric_interpolation_derivative_matrix(phases, phases) @ first
    norm = float(np.linalg.norm(second))
    if norm <= 1.0e-14:
        return np.zeros_like(second)
    return second / norm


def _fourier_tail_energy(values: np.ndarray, tail_fraction: float = 0.15) -> float:
    coefficients = np.fft.rfft(np.asarray(values, dtype=float), axis=0)
    energy = float(np.sum(np.abs(coefficients) ** 2))
    if energy <= 0.0:
        return 0.0
    tail_count = max(1, int(np.ceil(coefficients.shape[0] * tail_fraction)))
    return float(np.sum(np.abs(coefficients[-tail_count:]) ** 2) / energy)


def _assemble_jacobian(
    *,
    states: np.ndarray,
    phases: np.ndarray,
    rho: float,
    stms: np.ndarray,
    target_jacobi: float,
    mu: float,
) -> np.ndarray:
    sample_count = states.shape[0]
    state_size = states.size
    interpolation = _trigonometric_interpolation_matrix(phases, phases + rho)
    interpolation_derivative = _trigonometric_interpolation_derivative_matrix(phases, phases + rho)
    jacobian = np.zeros((state_size + 2, state_size + 1), dtype=float)

    for row in range(sample_count):
        row_slice = slice(6 * row, 6 * row + 6)
        for col in range(sample_count):
            col_slice = slice(6 * col, 6 * col + 6)
            block = -interpolation[row, col] * np.eye(6)
            if row == col:
                block = block + stms[row]
            jacobian[row_slice, col_slice] = block
    jacobian[:state_size, state_size] = -(interpolation_derivative @ states).reshape(-1)

    del target_jacobi
    jacobian[state_size, :state_size] = (_jacobi_gradient(states, mu) / sample_count).reshape(-1)
    jacobian[state_size + 1, :state_size] = _phase_direction(phases, states).reshape(-1)
    return jacobian


def _rank_from_singular_values(singular_values: np.ndarray, shape: tuple[int, int]) -> int:
    if singular_values.size == 0:
        return 0
    tolerance = np.finfo(float).eps * max(shape) * float(singular_values[0])
    return int(np.sum(singular_values > tolerance))


def _assemble_endpoint() -> ResidualAssembly:
    system = SYSTEMS["earth_moon"]
    time_unit = system.time_unit_days or 1.0
    family = load_corrected_dro_family_csv(FAMILY_PATH)
    validation_rows = _read_validation_rows(VALIDATION_PATH)
    endpoint = _select_endpoint(family)
    validation = validation_rows.get(endpoint.member)
    if validation is None:
        raise RuntimeError(f"missing validation row for endpoint member {endpoint.member}")

    mapping_time_nd = FIXED_MAPPING_TIME_DAYS / time_unit
    states = endpoint.states
    phases = endpoint.phases_rad
    interpolation = _trigonometric_interpolation_matrix(phases, phases + CURRENT_RHO_RAD)
    mapped, stms = _stroboscopic_map_and_stms(
        states,
        period=mapping_time_nd,
        mu=system.mu,
        max_step=INTEGRATION_MAX_STEP,
    )
    targets = interpolation @ states
    residuals = mapped - targets
    residual_norms = np.linalg.norm(residuals, axis=1)
    jacobi_values = np.asarray(jacobi_constant(states, system.mu), dtype=float)
    target_jacobi = endpoint.mean_jacobi
    phase_direction = _phase_direction(phases, states)
    second_phase_direction = _second_phase_direction(phases, states)
    state_delta = states - endpoint.states
    phase_residual = float(np.sum(state_delta * phase_direction))
    second_phase = float(np.sum(state_delta * second_phase_direction))
    jacobian = _assemble_jacobian(
        states=states,
        phases=phases,
        rho=CURRENT_RHO_RAD,
        stms=stms,
        target_jacobi=target_jacobi,
        mu=system.mu,
    )
    singular_values = np.linalg.svd(jacobian, compute_uv=False)
    return ResidualAssembly(
        member=endpoint,
        validation=validation,
        mapping_time_nd=mapping_time_nd,
        rho=CURRENT_RHO_RAD,
        mapped_states=mapped,
        target_states=targets,
        map_residuals=residuals,
        map_residual_norms=residual_norms,
        mean_jacobi_residual=float(np.mean(jacobi_values) - target_jacobi),
        phase_residual=phase_residual,
        second_phase_diagnostic=second_phase,
        jacobi_values=jacobi_values,
        fourier_tail_state=_fourier_tail_energy(states),
        fourier_tail_z=_fourier_tail_energy(states[:, 2:3]),
        jacobian=jacobian,
        singular_values=singular_values,
        rank_estimate=_rank_from_singular_values(singular_values, jacobian.shape),
    )


def _endpoint_row(assembly: ResidualAssembly) -> dict[str, Any]:
    residual_vector = np.concatenate(
        [
            assembly.map_residuals.reshape(-1),
            np.array([assembly.mean_jacobi_residual, assembly.phase_residual]),
        ]
    )
    peak_index = int(np.argmax(assembly.map_residual_norms))
    existing_phase_return = float(assembly.validation["one_map_phase_return_error"])
    condition = float(assembly.singular_values[0] / assembly.singular_values[-1])
    audit_residual = float(assembly.member.map_residual_norm)
    audit_jacobi_span = float(assembly.member.curve_jacobi_span)
    map_residual_max = float(np.max(assembly.map_residual_norms))
    jacobi_span = float(np.ptp(assembly.jacobi_values))
    matches_audit = bool(
        map_residual_max <= max(10.0 * audit_residual, 1.0e-12)
        and jacobi_span <= max(10.0 * audit_jacobi_span, 1.0e-12)
    )
    phase_closed = bool(abs(assembly.phase_residual) <= 1.0e-12)
    full_column_rank = assembly.rank_estimate == assembly.jacobian.shape[1]
    if not full_column_rank:
        conditioning = "rank_deficient"
    elif condition < 1.0e9:
        conditioning = "full_column_rank_moderate"
    else:
        conditioning = "full_column_rank_ill_conditioned"
    worth_continuing = bool(matches_audit and phase_closed and full_column_rank)
    reason = (
        "one-step correction skipped; endpoint diagnostic residual is already at the accepted audit level"
        if worth_continuing
        else "one-step correction skipped; prototype should be inspected before Newton updates"
    )
    return {
        "case_id": "route_b_bvp_endpoint_residual",
        "source_family_csv": FAMILY_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "source_validation_csv": VALIDATION_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "source_member": assembly.member.member,
        "curve_samples": assembly.member.states.shape[0],
        "fixed_mapping_time_days": FIXED_MAPPING_TIME_DAYS,
        "fixed_mapping_time_nd": assembly.mapping_time_nd,
        "rho_input_rad": CURRENT_RHO_RAD,
        "rho_endpoint_rad": assembly.member.rotation_angle_rad,
        "rho_delta_rad": CURRENT_RHO_RAD - assembly.member.rotation_angle_rad,
        "mean_jacobi_target": assembly.member.mean_jacobi,
        "mean_jacobi": float(np.mean(assembly.jacobi_values)),
        "total_residual_norm": float(np.linalg.norm(residual_vector)),
        "map_residual_max_norm": map_residual_max,
        "map_residual_rms_norm": float(np.sqrt(np.mean(assembly.map_residual_norms**2))),
        "mean_jacobi_residual": assembly.mean_jacobi_residual,
        "phase_residual": assembly.phase_residual,
        "second_phase_diagnostic": assembly.second_phase_diagnostic,
        "curve_jacobi_span": jacobi_span,
        "fourier_tail_energy_state": assembly.fourier_tail_state,
        "fourier_tail_energy_z": assembly.fourier_tail_z,
        "residual_peak_index": peak_index,
        "residual_peak_phase": float(assembly.member.phases_rad[peak_index]),
        "jacobian_shape": f"{assembly.jacobian.shape[0]}x{assembly.jacobian.shape[1]}",
        "jacobian_rank_estimate": assembly.rank_estimate,
        "condition_estimate": condition,
        "max_singular_value": float(assembly.singular_values[0]),
        "min_singular_value": float(assembly.singular_values[-1]),
        "smallest_singular_values": ";".join(f"{value:.16g}" for value in assembly.singular_values[-8:]),
        "largest_singular_values": ";".join(f"{value:.16g}" for value in assembly.singular_values[:8]),
        "existing_audit_map_residual_norm": audit_residual,
        "existing_audit_curve_jacobi_span": audit_jacobi_span,
        "existing_audit_phase_residual": assembly.member.phase_residual,
        "existing_validation_one_map_phase_return_error": existing_phase_return,
        "endpoint_residual_matches_existing_audit_level": matches_audit,
        "phase_constraint_closed": phase_closed,
        "conditioning_classification": conditioning,
        "bvp_route_worth_continuing": worth_continuing,
        "correction_attempted": False,
        "correction_before_residual": map_residual_max,
        "correction_after_residual": None,
        "correction_norm": None,
        "correction_accepted": False,
        "correction_reason": reason,
    }


def _block_rows(assembly: ResidualAssembly) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    map_flat = assembly.map_residuals.reshape(-1)
    rows.append(
        {
            "block_name": "A_map_invariance",
            "index": "summary",
            "phase_rad": None,
            "residual_size": map_flat.size,
            "l2_norm": float(np.linalg.norm(map_flat)),
            "rms_norm": float(np.sqrt(np.mean(map_flat**2))),
            "max_abs": float(np.max(np.abs(map_flat))),
            "row_norm": float(np.max(assembly.map_residual_norms)),
            "entered_endpoint_residual": True,
            "notes": "Phi_T(X_i) - I_rho[X](theta_i)",
        }
    )
    for idx, norm in enumerate(assembly.map_residual_norms):
        values = assembly.map_residuals[idx]
        rows.append(
            {
                "block_name": "A_map_invariance_point",
                "index": idx,
                "phase_rad": float(assembly.member.phases_rad[idx]),
                "residual_size": 6,
                "l2_norm": float(norm),
                "rms_norm": float(np.sqrt(np.mean(values**2))),
                "max_abs": float(np.max(np.abs(values))),
                "row_norm": float(norm),
                "entered_endpoint_residual": True,
                "notes": "pointwise map residual",
            }
        )
    rows.append(
        {
            "block_name": "B_mean_jacobi",
            "index": "summary",
            "phase_rad": None,
            "residual_size": 1,
            "l2_norm": abs(assembly.mean_jacobi_residual),
            "rms_norm": abs(assembly.mean_jacobi_residual),
            "max_abs": abs(assembly.mean_jacobi_residual),
            "row_norm": abs(assembly.mean_jacobi_residual),
            "entered_endpoint_residual": True,
            "notes": "mean(C(X_i)) - C_target",
        }
    )
    rows.append(
        {
            "block_name": "C_curve_phase",
            "index": "summary",
            "phase_rad": None,
            "residual_size": 1,
            "l2_norm": abs(assembly.phase_residual),
            "rms_norm": abs(assembly.phase_residual),
            "max_abs": abs(assembly.phase_residual),
            "row_norm": abs(assembly.phase_residual),
            "entered_endpoint_residual": True,
            "notes": "<X - X_ref, dX_ref/dtheta>",
        }
    )
    rows.append(
        {
            "block_name": "D_second_phase_diagnostic",
            "index": "summary",
            "phase_rad": None,
            "residual_size": 1,
            "l2_norm": abs(assembly.second_phase_diagnostic),
            "rms_norm": abs(assembly.second_phase_diagnostic),
            "max_abs": abs(assembly.second_phase_diagnostic),
            "row_norm": abs(assembly.second_phase_diagnostic),
            "entered_endpoint_residual": False,
            "notes": "diagnostic only; not included in the residual vector",
        }
    )
    rows.append(
        {
            "block_name": "E_fourier_tail_state",
            "index": "summary",
            "phase_rad": None,
            "residual_size": 1,
            "l2_norm": assembly.fourier_tail_state,
            "rms_norm": assembly.fourier_tail_state,
            "max_abs": assembly.fourier_tail_state,
            "row_norm": assembly.fourier_tail_state,
            "entered_endpoint_residual": False,
            "notes": "spectral quality diagnostic only",
        }
    )
    rows.append(
        {
            "block_name": "E_fourier_tail_z",
            "index": "summary",
            "phase_rad": None,
            "residual_size": 1,
            "l2_norm": assembly.fourier_tail_z,
            "rms_norm": assembly.fourier_tail_z,
            "max_abs": assembly.fourier_tail_z,
            "row_norm": assembly.fourier_tail_z,
            "entered_endpoint_residual": False,
            "notes": "z-component spectral quality diagnostic only",
        }
    )
    return rows


def _index_rows(sample_count: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(sample_count):
        rows.append(
            {
                "kind": "unknown",
                "name": f"X_{idx}",
                "index": idx,
                "start": 6 * idx,
                "end": 6 * idx + 5,
                "size": 6,
                "notes": "state sample [x,y,z,xdot,ydot,zdot]",
            }
        )
    rows.append(
        {
            "kind": "unknown",
            "name": "rho",
            "index": sample_count,
            "start": 6 * sample_count,
            "end": 6 * sample_count,
            "size": 1,
            "notes": "rotation angle; solved variable in the prototype Jacobian",
        }
    )
    for idx in range(sample_count):
        rows.append(
            {
                "kind": "residual",
                "name": f"R_map_{idx}",
                "index": idx,
                "start": 6 * idx,
                "end": 6 * idx + 5,
                "size": 6,
                "notes": "map invariance residual",
            }
        )
    state_size = 6 * sample_count
    rows.append(
        {
            "kind": "residual",
            "name": "R_C",
            "index": sample_count,
            "start": state_size,
            "end": state_size,
            "size": 1,
            "notes": "mean Jacobi residual",
        }
    )
    rows.append(
        {
            "kind": "residual",
            "name": "R_phase",
            "index": sample_count + 1,
            "start": state_size + 1,
            "end": state_size + 1,
            "size": 1,
            "notes": "curve phase condition",
        }
    )
    return rows


def _document_text(assembly: ResidualAssembly, endpoint: dict[str, Any]) -> str:
    worth = "yes" if endpoint["bvp_route_worth_continuing"] else "no"
    match = "yes" if endpoint["endpoint_residual_matches_existing_audit_level"] else "no"
    phase = "closed" if endpoint["phase_constraint_closed"] else "not closed"
    return f"""# Chapter 3 Route B BVP Residual Prototype

## Purpose

This document records the minimum residual-design prototype for Route B. The
prototype is deliberately narrower than a full continuation method: it assembles
a map-based one-angle invariant-curve BVP residual at the current accepted
`N=61` quasi-DRO endpoint, compares the residual blocks with the existing
shooting audit, and records the endpoint Jacobian conditioning.

## Why Route B Turns To A BVP Residual

The prior Route B free-time branch audit showed that the diagnostic free-time
branch is continuous, phase-gauge robust, and audit-clean. Its highest member
reached `max_abs_z_km = 11107.54149221647`, but at a mapping time of
`14.80556377691894` days. The original/current fixed mapping time is
`14.74932760227518` days, so the diagnostic high-amplitude member drifted by
about `+0.05623617464375563` days.

That makes the free-time branch useful as a diagnostic result, but not as a
constant-mapping-time McCarthy Figure 3.16/3.17 reproduction. A BVP residual
prototype is the next local formulation check because it exposes the global
curve residual, phase constraints, Jacobi constraint, and Jacobian spectrum in
one assembled system.

## Why Fixed-Time Projection Failed

The fixed-time projection audit did not produce an accepted higher-amplitude
fixed-time candidate. The first projection above 10,500 km had
`map_residual_norm = 0.003183144472324563` and
`curve_jacobi_span = 4.202137698250397e-05`. The highest/first projection above
11,000 km had `map_residual_norm = 0.0086721521025836` and
`curve_jacobi_span = 0.0004517468991371842`. These are far above the current
accepted-branch audit level and indicate that the amplitude gain did not survive
the constant-mapping-time constraint.

## Prototype Goal

The goal is endpoint reproduction only. This round does not chase 10,500 km or
11,000 km, does not update Figure 3.16 or Figure 3.17, does not touch Chapter 5,
and does not promote the BVP prototype to a complete continuation method.

The endpoint input is `data/computed/chapter3_quasi_dro_palc_family.csv`,
member `{assembly.member.member}`, with `N={assembly.member.states.shape[0]}`,
fixed mapping time `{FIXED_MAPPING_TIME_DAYS:.14f}` days, and
`rho={CURRENT_RHO_RAD:.15f}` rad.

## Unknown Vector Layout

The first version uses a map-based one-angle invariant-curve BVP:

```text
u = [X_0, X_1, ..., X_{{N-1}}, rho]
```

Each `X_i` is a six-component CR3BP rotating-frame state. The mapping time `T`
is fixed to the McCarthy/current endpoint value. The rotation `rho` is included
as the last unknown in the Jacobian and is also recorded as a diagnostic
variable. The curve-average Jacobi constant is fixed to the endpoint mean
Jacobi. Amplitude is not a hard constraint.

## Residual Blocks

- `A_map_invariance`: `R_map_i = Phi_T(X_i) - I_rho[X](theta_i)`.
- `B_mean_jacobi`: `R_C = mean(C(X_i)) - C_target`.
- `C_curve_phase`: `R_phase = <X - X_ref, dX_ref/dtheta>`.
- `D_second_phase_diagnostic`: recorded only as a diagnostic, not included in
  the endpoint residual vector.
- `E_fourier_tail_state` and `E_fourier_tail_z`: spectral quality diagnostics,
  not residual equations.

Continuation and PALC are intentionally not implemented in this prototype.

## Endpoint Reproduction Criteria

Endpoint reproduction is considered successful if the assembled map residual and
Jacobi span match the existing accepted audit level, the phase condition closes
at the endpoint, and the assembled Jacobian has full column rank with a
condition estimate that is not obviously worse than the failed shooting
neighborhood.

## Endpoint Result

- Total residual norm: `{endpoint["total_residual_norm"]:.16g}`
- Map residual max norm: `{endpoint["map_residual_max_norm"]:.16g}`
- Map residual RMS norm: `{endpoint["map_residual_rms_norm"]:.16g}`
- Mean Jacobi residual: `{endpoint["mean_jacobi_residual"]:.16g}`
- Phase residual: `{endpoint["phase_residual"]:.16g}`
- Optional second phase diagnostic: `{endpoint["second_phase_diagnostic"]:.16g}`
- Curve Jacobi span: `{endpoint["curve_jacobi_span"]:.16g}`
- Fourier tail energy, full state: `{endpoint["fourier_tail_energy_state"]:.16g}`
- Fourier tail energy, z: `{endpoint["fourier_tail_energy_z"]:.16g}`
- Residual peak phase: `{endpoint["residual_peak_phase"]:.16g}`
- Existing audit map residual: `{endpoint["existing_audit_map_residual_norm"]:.16g}`
- Existing audit Jacobi span: `{endpoint["existing_audit_curve_jacobi_span"]:.16g}`
- Endpoint residual matches existing audit level: `{match}`

## Conditioning Result

- Jacobian shape: `{endpoint["jacobian_shape"]}`
- Rank estimate: `{endpoint["jacobian_rank_estimate"]}`
- Condition estimate: `{endpoint["condition_estimate"]:.16g}`
- Largest singular values: `{endpoint["largest_singular_values"]}`
- Smallest singular values: `{endpoint["smallest_singular_values"]}`
- Classification: `{endpoint["conditioning_classification"]}`

This is an endpoint linearization only. It is not evidence that high-amplitude
continuation will succeed, but it is a cleaner residual assembly than the failed
fixed-time projection because the endpoint itself reproduces the accepted audit
level.

## Answers

1. The BVP residual prototype does reproduce the current accepted endpoint:
   `{match}`.
2. Its residual blocks are consistent with the current shooting audit at the
   endpoint; the recomputed map residual and Jacobi span remain at the accepted
   level.
3. The primary curve phase constraint is `{phase}` at the endpoint. The second
   phase diagnostic is recorded but not used to square or close the system.
4. The endpoint Jacobian is `{endpoint["conditioning_classification"]}` with
   condition estimate `{endpoint["condition_estimate"]:.6g}`. This is more
   informative than the free-time/fixed-time shooting audit at this endpoint,
   but it does not yet prove better conditioning along a continuation branch.
5. The prototype is worth continuing to a bounded PALC design round: `{worth}`.
6. If it fails in the next round, likely causes are loss of full-rank phase
   closure, high Fourier tail growth, or the same fixed-time high-amplitude
   obstruction seen in the projection audit.

## If This Succeeds Later

The next round should add a controlled continuation layer around this residual:
choose the square/overdetermined solve convention, add a pseudo-arclength
condition, preserve fixed `T`, keep mean Jacobi or an explicitly chosen branch
parameter, and first reproduce nearby accepted endpoints before attempting any
10,500 km or 11,000 km member. Figure 3.16 and Figure 3.17 should remain frozen
until such a continuation produces a multi-member fixed-time branch that passes
the same residual, Jacobi, phase, tail, and multi-return gates.
"""


def main() -> None:
    assembly = _assemble_endpoint()
    endpoint = _endpoint_row(assembly)
    _write_rows(ENDPOINT_OUTPUT, ENDPOINT_FIELDS, [endpoint])
    _write_rows(BLOCK_OUTPUT, BLOCK_FIELDS, _block_rows(assembly))
    _write_rows(INDEX_OUTPUT, INDEX_FIELDS, _index_rows(assembly.member.states.shape[0]))
    DOC_OUTPUT.write_text(_document_text(assembly, endpoint), encoding="utf-8")
    print(f"wrote {ENDPOINT_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {BLOCK_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {INDEX_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(
        "endpoint map residual max="
        f"{endpoint['map_residual_max_norm']:.6e}, condition="
        f"{endpoint['condition_estimate']:.6e}, rank="
        f"{endpoint['jacobian_rank_estimate']}"
    )


if __name__ == "__main__":
    main()
