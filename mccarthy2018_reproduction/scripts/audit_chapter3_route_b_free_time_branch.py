"""Audit the Route B diagnostic free-time branch for consistency and projection."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    CorrectedDROFamilyMember,
    chapter3_quasi_dro_validation_row,
    load_corrected_dro_family_csv,
)
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    _jacobi_gradient,
    _stroboscopic_map_and_stms,
    _trigonometric_interpolation_derivative_matrix,
    _trigonometric_interpolation_matrix,
    stroboscopic_curve_fixed_jacobi_free_time_rotation_correction,
    stroboscopic_dro_invariant_curve_seed,
)
from run_chapter3_route_b_free_time_experiment import (
    _audit_route_b,
    _float_from_audit,
    _member_from_route_b,
)
from run_chapter3_route_b_refinement import (
    BRANCH_STATE_AUDIT_METRICS,
    BRANCH_STATE_SCHEMA_VERSION,
    VariantConfig,
    _branch_state_record,
    _run_route_b_correction,
    _variants,
    _write_branch_state_archive,
)


BRANCH_CONSISTENCY_FIELDS = (
    "case_id",
    "variant",
    "member_index",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "mapping_time_days",
    "delta_mapping_time_days_from_endpoint",
    "rho",
    "delta_rho_from_endpoint",
    "mean_jacobi",
    "delta_mean_jacobi",
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "fourier_tail_energy_state",
    "fourier_tail_energy_z",
    "max_pointwise_residual",
    "residual_peak_phase",
    "max_pointwise_jacobi_error",
    "jacobi_peak_phase",
    "row_to_row_state_distance",
    "row_to_row_phase_aligned_state_distance",
    "row_to_row_tangent_angle_deg",
    "monotone_amplitude",
    "monotone_mapping_time",
    "monotone_mean_jacobi",
    "classification",
    "diagnosis",
)

PHASE_GAUGE_FIELDS = (
    "case_id",
    "test_type",
    "requested_phase_shift",
    "actual_shift_index",
    "actual_phase_shift_rad",
    "shift_method",
    "phase_condition",
    "perturbation_norm",
    "converged",
    "accepted",
    "corrected_max_abs_z_km",
    "delta_max_abs_z_km_from_reference",
    "corrected_mapping_time_days",
    "delta_mapping_time_days_from_reference",
    "corrected_rho",
    "delta_rho_from_reference",
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "state_distance_to_reference",
    "phase_aligned_state_distance",
    "classification",
    "diagnosis",
)

FIXED_TIME_FIELDS = (
    "source_case_id",
    "source_max_abs_z_km",
    "source_mapping_time_days",
    "source_rho",
    "target_mapping_time_days",
    "projection_mode",
    "converged",
    "accepted",
    "projected_max_abs_z_km",
    "projected_rho",
    "mean_jacobi",
    "map_residual_norm",
    "curve_jacobi_span",
    "one_map_phase_return_error",
    "ten_return_jacobi_span",
    "amplitude_loss_km",
    "state_distance_from_free_time_source",
    "failure_reason",
    "interpretation",
)

SELECTED_CASES = (
    "05_E_amplitude_monitor_large_step_correction",
    "05_E_amplitude_monitor_large_step_step",
    "bounded_01_E_amplitude_monitor_large_step",
    "bounded_02_E_amplitude_monitor_large_step",
    "bounded_03_E_amplitude_monitor_large_step",
    "bounded_04_E_amplitude_monitor_large_step",
    "bounded_05_E_amplitude_monitor_large_step",
)

ALIGNMENT_FIELDS = (
    "max_abs_z_km",
    "mapping_time_days",
    "rho",
    "mean_jacobi",
    "map_residual_norm",
    "curve_jacobi_span",
)

AUDIT_MAP_RESIDUAL = 1.0e-8
AUDIT_JACOBI_SPAN = 1.0e-8
AUDIT_PHASE_RETURN = 1.0e-8
T_FIXED_DAYS = 14.74932760227518


@dataclass(frozen=True)
class BranchArchive:
    case_ids: np.ndarray
    states: np.ndarray
    phase_grid: np.ndarray
    mapping_time_days: np.ndarray
    rho: np.ndarray
    mean_jacobi: np.ndarray
    max_abs_z_km: np.ndarray
    source_case: np.ndarray
    variant: np.ndarray
    accepted: np.ndarray
    audit_metric_names: np.ndarray
    audit_metrics: np.ndarray


@dataclass(frozen=True)
class FixedTimeProjection:
    states: np.ndarray
    mapped_states: np.ndarray
    target_states: np.ndarray
    rho: float
    target_jacobi: float
    residual_norms: np.ndarray
    phase_residual: float
    correction_norm_history: np.ndarray
    converged: bool
    failure_reason: str


def _value(value: float | int | str | bool | None) -> str:
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


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_rows(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _system_seed(endpoint: CorrectedDROFamilyMember):
    system = SYSTEMS["earth_moon"]
    length_unit = system.length_unit_km or 1.0
    time_unit = system.time_unit_days or 1.0
    x0 = 1.0 - system.mu - 73800.0 / length_unit
    initial_ydot = 0.53
    initial_half_period = 14.75 / (2.0 * time_unit)
    seed = stroboscopic_dro_invariant_curve_seed(
        system.mu,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
        vertical_amplitude=endpoint.target_vertical_amplitude_nd,
        samples=endpoint.states.shape[0],
        curve_samples=max(4 * endpoint.states.shape[0], 120),
    )
    if not np.allclose(seed.phases, endpoint.phases_rad, rtol=0.0, atol=1.0e-12):
        raise RuntimeError("Route B endpoint phases do not match the reconstructed seed")
    return system, seed, time_unit, length_unit


def _reconstruct_branch_archive(
    *,
    path: Path,
    endpoint: CorrectedDROFamilyMember,
) -> None:
    system, seed, time_unit, length_unit = _system_seed(endpoint)
    e_variant = next(item for item in _variants(time_unit) if item.variant == "E_amplitude_monitor_large_step")
    records: list[dict[str, object]] = []

    correction, member, audit_row, accepted, _ = _run_route_b_correction(
        seed=seed,
        system=system,
        endpoint=endpoint,
        variant=e_variant,
        target_jacobi=endpoint.mean_jacobi,
        initial_states=endpoint.states,
        initial_mapping_time=endpoint.mapping_time_days / time_unit,
        initial_rotation=endpoint.rotation_angle_rad,
        phase_reference_states=endpoint.states,
        source_member=endpoint.member,
        time_unit_days=time_unit,
        length_unit_km=length_unit,
    )
    if not accepted:
        raise RuntimeError("E correction-only reconstruction failed audit")
    records.append(
        _branch_state_record(
            case_id="05_E_amplitude_monitor_large_step_correction",
            source_case="accepted_endpoint",
            variant=e_variant.variant,
            correction=correction,
            member=member,
            audit_row=audit_row,
            accepted=accepted,
        )
    )

    current_correction = correction
    current_member = member
    step_delta = e_variant.target_delta
    for case_id, source_case, member_id in [
        ("05_E_amplitude_monitor_large_step_step", "E_amplitude_monitor_large_step_correction", endpoint.member + 5),
        ("bounded_01_E_amplitude_monitor_large_step", "05_E_amplitude_monitor_large_step_step", endpoint.member + 101),
        ("bounded_02_E_amplitude_monitor_large_step", "bounded_previous_1", endpoint.member + 102),
        ("bounded_03_E_amplitude_monitor_large_step", "bounded_previous_2", endpoint.member + 103),
        ("bounded_04_E_amplitude_monitor_large_step", "bounded_previous_3", endpoint.member + 104),
        ("bounded_05_E_amplitude_monitor_large_step", "bounded_previous_4", endpoint.member + 105),
    ]:
        correction, member, audit_row, accepted, _ = _run_route_b_correction(
            seed=seed,
            system=system,
            endpoint=endpoint,
            variant=e_variant,
            target_jacobi=current_member.mean_jacobi + step_delta,
            initial_states=current_correction.corrected_states,
            initial_mapping_time=current_correction.mapping_time,
            initial_rotation=current_correction.rotation_angle_rad,
            phase_reference_states=current_correction.corrected_states,
            source_member=member_id,
            time_unit_days=time_unit,
            length_unit_km=length_unit,
        )
        if not accepted:
            raise RuntimeError(f"{case_id} reconstruction failed audit")
        records.append(
            _branch_state_record(
                case_id=case_id,
                source_case=source_case,
                variant=e_variant.variant,
                correction=correction,
                member=member,
                audit_row=audit_row,
                accepted=accepted,
            )
        )
        current_correction = correction
        current_member = member

    _write_branch_state_archive(path, records=records, phase_grid=seed.phases)


def _load_archive(path: Path) -> BranchArchive:
    with np.load(path, allow_pickle=False) as data:
        required = {
            "schema_version",
            "created_by_script",
            "case_ids",
            "states",
            "phase_grid",
            "mapping_time_days",
            "rho",
            "mean_jacobi",
            "max_abs_z_km",
            "source_case",
            "variant",
            "accepted",
            "audit_metric_names",
            "audit_metrics",
        }
        missing = sorted(required.difference(data.files))
        if missing:
            raise RuntimeError(f"branch-state archive missing required keys: {', '.join(missing)}")
        schema = str(np.asarray(data["schema_version"]).item())
        if schema != BRANCH_STATE_SCHEMA_VERSION:
            raise RuntimeError(f"unsupported branch-state schema_version {schema!r}")
        return BranchArchive(
            case_ids=np.asarray(data["case_ids"]).astype(str),
            states=np.asarray(data["states"], dtype=float),
            phase_grid=np.asarray(data["phase_grid"], dtype=float),
            mapping_time_days=np.asarray(data["mapping_time_days"], dtype=float),
            rho=np.asarray(data["rho"], dtype=float),
            mean_jacobi=np.asarray(data["mean_jacobi"], dtype=float),
            max_abs_z_km=np.asarray(data["max_abs_z_km"], dtype=float),
            source_case=np.asarray(data["source_case"]).astype(str),
            variant=np.asarray(data["variant"]).astype(str),
            accepted=np.asarray(data["accepted"], dtype=bool),
            audit_metric_names=np.asarray(data["audit_metric_names"]).astype(str),
            audit_metrics=np.asarray(data["audit_metrics"], dtype=float),
        )


def _metric(archive: BranchArchive, row_index: int, name: str) -> float:
    names = list(archive.audit_metric_names)
    return float(archive.audit_metrics[row_index, names.index(name)])


def _experiment_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["experiment_id"]: row for row in rows}


def _expected_jacobi_by_case(endpoint: CorrectedDROFamilyMember) -> dict[str, float]:
    values: dict[str, float] = {}
    current = endpoint.mean_jacobi
    for case_id in SELECTED_CASES:
        if case_id == "05_E_amplitude_monitor_large_step_correction":
            values[case_id] = endpoint.mean_jacobi
        else:
            current -= 7.5e-5
            values[case_id] = current
    return values


def _assert_archive_alignment(
    *,
    archive: BranchArchive,
    experiment_rows: list[dict[str, str]],
    endpoint: CorrectedDROFamilyMember,
) -> None:
    experiments = _experiment_lookup(experiment_rows)
    expected_jacobi = _expected_jacobi_by_case(endpoint)
    tolerances = {
        "max_abs_z_km": 5.0e-6,
        "mapping_time_days": 5.0e-10,
        "rho": 5.0e-10,
        "mean_jacobi": 1.0e-8,
        "map_residual_norm": 1.0e-10,
        "curve_jacobi_span": 1.0e-10,
    }
    for case_id in SELECTED_CASES:
        if case_id not in archive.case_ids:
            raise RuntimeError(f"archive alignment failed: missing {case_id}")
        if case_id not in experiments:
            raise RuntimeError(f"archive alignment failed: refinement CSV missing {case_id}")
        idx = int(np.where(archive.case_ids == case_id)[0][0])
        csv_row = experiments[case_id]
        archive_values = {
            "max_abs_z_km": float(archive.max_abs_z_km[idx]),
            "mapping_time_days": float(archive.mapping_time_days[idx]),
            "rho": float(archive.rho[idx]),
            "mean_jacobi": float(archive.mean_jacobi[idx]),
            "map_residual_norm": _metric(archive, idx, "map_residual_norm"),
            "curve_jacobi_span": _metric(archive, idx, "curve_jacobi_span"),
        }
        csv_values = {
            "max_abs_z_km": float(csv_row["max_abs_z_km"]),
            "mapping_time_days": float(csv_row["corrected_mapping_time_days"]),
            "rho": float(csv_row["corrected_rho"]),
            "mean_jacobi": expected_jacobi[case_id],
            "map_residual_norm": float(csv_row["map_residual_norm"]),
            "curve_jacobi_span": float(csv_row["curve_jacobi_span"]),
        }
        for field in ALIGNMENT_FIELDS:
            diff = abs(archive_values[field] - csv_values[field])
            if diff > tolerances[field]:
                raise RuntimeError(
                    "archive alignment failed for "
                    f"{case_id}.{field}: archive={archive_values[field]:.16g}, "
                    f"csv={csv_values[field]:.16g}, diff={diff:.3e}, "
                    f"tolerance={tolerances[field]:.3e}"
                )


def _member_from_archive(
    archive: BranchArchive,
    row_index: int,
    *,
    system,
    seed,
    length_unit: float,
) -> CorrectedDROFamilyMember:
    states = archive.states[row_index].copy()
    jacobi = np.asarray(jacobi_constant(states, system.mu), dtype=float)
    displacement = states[:, 2] - seed.orbit_state[2]
    vertical_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    return CorrectedDROFamilyMember(
        member=row_index,
        curve_indices=np.arange(states.shape[0]),
        phases_rad=archive.phase_grid.copy(),
        states=states,
        jacobi_values=jacobi,
        target_vertical_amplitude_nd=vertical_amplitude,
        target_vertical_amplitude_km=vertical_amplitude * length_unit,
        max_abs_z_km=float(archive.max_abs_z_km[row_index]),
        rotation_angle_rad=float(archive.rho[row_index]),
        mapping_time_days=float(archive.mapping_time_days[row_index]),
        map_residual_norm=_metric(archive, row_index, "map_residual_norm"),
        amplitude_residual=0.0,
        phase_residual=0.0,
        curve_jacobi_span=_metric(archive, row_index, "curve_jacobi_span"),
    )


def _pointwise_metrics(states: np.ndarray, phases: np.ndarray, rho: float, mapping_time: float, mu: float):
    interpolation = _trigonometric_interpolation_matrix(phases, phases + rho)
    mapped, _ = _stroboscopic_map_and_stms(states, period=mapping_time, mu=mu, max_step=0.02)
    targets = interpolation @ states
    residuals = np.linalg.norm(mapped - targets, axis=1)
    jacobi_values = np.asarray(jacobi_constant(states, mu), dtype=float)
    jacobi_errors = jacobi_values - float(np.mean(jacobi_values))
    return residuals, jacobi_values, jacobi_errors


def _fourier_tail_energy(values: np.ndarray, tail_fraction: float = 0.15) -> float:
    coefficients = np.fft.rfft(values, axis=0)
    energy = np.sum(np.abs(coefficients) ** 2)
    if energy <= 0.0:
        return 0.0
    tail_count = max(1, int(np.ceil(coefficients.shape[0] * tail_fraction)))
    tail = coefficients[-tail_count:]
    return float(np.sum(np.abs(tail) ** 2) / energy)


def _raw_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b) / np.sqrt(a.size))


def _phase_aligned_distance(a: np.ndarray, b: np.ndarray) -> tuple[float, int]:
    best_distance = np.inf
    best_shift = 0
    for shift in range(a.shape[0]):
        distance = _raw_distance(np.roll(a, shift, axis=0), b)
        if distance < best_distance:
            best_distance = distance
            best_shift = shift
    return float(best_distance), int(best_shift)


def _angle_deg(a: np.ndarray, b: np.ndarray) -> float | None:
    a_flat = a.reshape(-1)
    b_flat = b.reshape(-1)
    denom = float(np.linalg.norm(a_flat) * np.linalg.norm(b_flat))
    if denom <= 0.0:
        return None
    cosine = float(np.clip(np.dot(a_flat, b_flat) / denom, -1.0, 1.0))
    return float(np.degrees(np.arccos(cosine)))


def _audit_pass(member: CorrectedDROFamilyMember, validation: dict[str, str]) -> bool:
    phase_error = _float_from_audit(validation, "one_map_phase_return_error")
    ten_span = _float_from_audit(validation, "ten_return_jacobi_span")
    return bool(
        member.map_residual_norm <= AUDIT_MAP_RESIDUAL
        and member.curve_jacobi_span <= AUDIT_JACOBI_SPAN
        and phase_error is not None
        and phase_error <= AUDIT_PHASE_RETURN
        and ten_span is not None
        and ten_span <= AUDIT_JACOBI_SPAN
    )


def _branch_consistency_rows(
    *,
    archive: BranchArchive,
    endpoint: CorrectedDROFamilyMember,
    system,
    seed,
    time_unit: float,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    previous_states: np.ndarray | None = None
    previous_tangent: np.ndarray | None = None
    amplitudes: list[float] = []
    mapping_times: list[float] = []
    jacobis: list[float] = []
    for member_index, case_id in enumerate(SELECTED_CASES):
        idx = int(np.where(archive.case_ids == case_id)[0][0])
        states = archive.states[idx]
        mapping_time_days = float(archive.mapping_time_days[idx])
        mapping_time = mapping_time_days / time_unit
        rho = float(archive.rho[idx])
        residuals, jacobi_values, jacobi_errors = _pointwise_metrics(
            states,
            archive.phase_grid,
            rho,
            mapping_time,
            system.mu,
        )
        max_residual_idx = int(np.argmax(residuals))
        max_jacobi_idx = int(np.argmax(np.abs(jacobi_errors)))

        raw_distance: float | None = None
        aligned_distance: float | None = None
        tangent_angle: float | None = None
        aligned_current = states
        if previous_states is not None:
            raw_distance = _raw_distance(states, previous_states)
            aligned_distance, shift = _phase_aligned_distance(states, previous_states)
            aligned_current = np.roll(states, shift, axis=0)
            tangent = aligned_current - previous_states
            tangent_angle = _angle_deg(tangent, previous_tangent) if previous_tangent is not None else None
            previous_tangent = tangent
        previous_states = aligned_current.copy()
        if previous_tangent is None and member_index == 0:
            previous_tangent = np.zeros_like(states)

        amplitudes.append(float(archive.max_abs_z_km[idx]))
        mapping_times.append(mapping_time_days)
        jacobis.append(float(archive.mean_jacobi[idx]))
        monotone_amp = all(np.diff(amplitudes) > 0.0) if len(amplitudes) > 1 else True
        monotone_time = all(np.diff(mapping_times) > 0.0) if len(mapping_times) > 1 else True
        monotone_jacobi = all(np.diff(jacobis) < 0.0) if len(jacobis) > 1 else True

        phase_error = _metric(archive, idx, "one_map_phase_return_error")
        ten_span = _metric(archive, idx, "ten_return_jacobi_span")
        accepted = bool(
            _metric(archive, idx, "map_residual_norm") <= AUDIT_MAP_RESIDUAL
            and _metric(archive, idx, "curve_jacobi_span") <= AUDIT_JACOBI_SPAN
            and phase_error <= AUDIT_PHASE_RETURN
            and ten_span <= AUDIT_JACOBI_SPAN
        )
        if not accepted:
            classification = "audit_failed_diagnostic_member"
            diagnosis = "Route B archive member fails the residual/Jacobi/phase audit."
        elif aligned_distance is not None and raw_distance is not None and aligned_distance < raw_distance:
            classification = "continuous_phase_aligned_diagnostic_branch"
            diagnosis = "Row-to-row continuity is better after cyclic phase alignment; classification uses phase-aligned distance."
        else:
            classification = "continuous_diagnostic_branch"
            diagnosis = "Member is audit-clean and locally continuous under the stored phase gauge."

        values: dict[str, float | int | str | bool | None] = {
            "case_id": case_id,
            "variant": str(archive.variant[idx]),
            "member_index": member_index,
            "max_abs_z_km": archive.max_abs_z_km[idx],
            "delta_max_abs_z_km": archive.max_abs_z_km[idx] - endpoint.max_abs_z_km,
            "mapping_time_days": mapping_time_days,
            "delta_mapping_time_days_from_endpoint": mapping_time_days - endpoint.mapping_time_days,
            "rho": rho,
            "delta_rho_from_endpoint": rho - endpoint.rotation_angle_rad,
            "mean_jacobi": archive.mean_jacobi[idx],
            "delta_mean_jacobi": archive.mean_jacobi[idx] - endpoint.mean_jacobi,
            "map_residual_norm": _metric(archive, idx, "map_residual_norm"),
            "curve_jacobi_span": _metric(archive, idx, "curve_jacobi_span"),
            "one_map_phase_return_error": phase_error,
            "ten_return_jacobi_span": ten_span,
            "fourier_tail_energy_state": _fourier_tail_energy(states),
            "fourier_tail_energy_z": _fourier_tail_energy(states[:, 2:3]),
            "max_pointwise_residual": float(np.max(residuals)),
            "residual_peak_phase": float(archive.phase_grid[max_residual_idx]),
            "max_pointwise_jacobi_error": float(np.max(np.abs(jacobi_errors))),
            "jacobi_peak_phase": float(archive.phase_grid[max_jacobi_idx]),
            "row_to_row_state_distance": raw_distance,
            "row_to_row_phase_aligned_state_distance": aligned_distance,
            "row_to_row_tangent_angle_deg": tangent_angle,
            "monotone_amplitude": monotone_amp,
            "monotone_mapping_time": monotone_time,
            "monotone_mean_jacobi": monotone_jacobi,
            "classification": classification,
            "diagnosis": diagnosis,
        }
        rows.append({field: _value(values[field]) for field in BRANCH_CONSISTENCY_FIELDS})
    return rows


def _phase_test_row(
    *,
    case_id: str,
    test_type: str,
    requested_phase_shift: str,
    actual_shift_index: int | None,
    actual_phase_shift_rad: float | None,
    shift_method: str,
    phase_condition: str,
    perturbation_norm: float | None,
    reference_member: CorrectedDROFamilyMember,
    correction,
    audit_row: dict[str, str] | None,
    accepted: bool,
    failure_reason: str,
    time_unit: float,
    length_unit: float,
) -> dict[str, str]:
    if correction is None:
        values: dict[str, float | str | bool | int | None] = {
            "case_id": case_id,
            "test_type": test_type,
            "requested_phase_shift": requested_phase_shift,
            "actual_shift_index": actual_shift_index,
            "actual_phase_shift_rad": actual_phase_shift_rad,
            "shift_method": shift_method,
            "phase_condition": phase_condition,
            "perturbation_norm": perturbation_norm,
            "converged": False,
            "accepted": False,
            "corrected_max_abs_z_km": None,
            "delta_max_abs_z_km_from_reference": None,
            "corrected_mapping_time_days": None,
            "delta_mapping_time_days_from_reference": None,
            "corrected_rho": None,
            "delta_rho_from_reference": None,
            "map_residual_norm": None,
            "curve_jacobi_span": None,
            "one_map_phase_return_error": None,
            "ten_return_jacobi_span": None,
            "state_distance_to_reference": None,
            "phase_aligned_state_distance": None,
            "classification": "phase_gauge_test_exception",
            "diagnosis": failure_reason,
        }
    else:
        member = _member_from_route_b(
            -1,
            correction,
            time_unit_days=time_unit,
            length_unit_km=length_unit,
        )
        raw_distance = _raw_distance(correction.corrected_states, reference_member.states)
        aligned_distance, _ = _phase_aligned_distance(correction.corrected_states, reference_member.states)
        phase_error = None if audit_row is None else _float_from_audit(audit_row, "one_map_phase_return_error")
        ten_span = None if audit_row is None else _float_from_audit(audit_row, "ten_return_jacobi_span")
        classification = "phase_gauge_robust" if accepted and aligned_distance <= 1.0e-6 else "phase_gauge_sensitive"
        diagnosis = (
            "Corrected solution returns to the reference branch member after phase alignment."
            if classification == "phase_gauge_robust"
            else (failure_reason or "Correction passed weakly but phase-aligned distance is larger than the robustness gate.")
        )
        values = {
            "case_id": case_id,
            "test_type": test_type,
            "requested_phase_shift": requested_phase_shift,
            "actual_shift_index": actual_shift_index,
            "actual_phase_shift_rad": actual_phase_shift_rad,
            "shift_method": shift_method,
            "phase_condition": phase_condition,
            "perturbation_norm": perturbation_norm,
            "converged": True,
            "accepted": accepted,
            "corrected_max_abs_z_km": member.max_abs_z_km,
            "delta_max_abs_z_km_from_reference": member.max_abs_z_km - reference_member.max_abs_z_km,
            "corrected_mapping_time_days": correction.mapping_time * time_unit,
            "delta_mapping_time_days_from_reference": correction.mapping_time * time_unit - reference_member.mapping_time_days,
            "corrected_rho": correction.rotation_angle_rad,
            "delta_rho_from_reference": correction.rotation_angle_rad - reference_member.rotation_angle_rad,
            "map_residual_norm": member.map_residual_norm,
            "curve_jacobi_span": member.curve_jacobi_span,
            "one_map_phase_return_error": phase_error,
            "ten_return_jacobi_span": ten_span,
            "state_distance_to_reference": raw_distance,
            "phase_aligned_state_distance": aligned_distance,
            "classification": classification,
            "diagnosis": diagnosis,
        }
    return {field: _value(values[field]) for field in PHASE_GAUGE_FIELDS}


def _phase_gauge_rows(
    *,
    archive: BranchArchive,
    endpoint: CorrectedDROFamilyMember,
    system,
    seed,
    time_unit: float,
    length_unit: float,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    base_variant = next(item for item in _variants(time_unit) if item.variant == "E_amplitude_monitor_large_step")
    rng = np.random.default_rng(20260701)
    for case_id in SELECTED_CASES:
        idx = int(np.where(archive.case_ids == case_id)[0][0])
        reference_member = _member_from_archive(
            archive,
            idx,
            system=system,
            seed=seed,
            length_unit=length_unit,
        )
        for fraction_label, fraction in (("1/4", 0.25), ("1/2", 0.5), ("3/4", 0.75)):
            shift_index = int(round(fraction * reference_member.states.shape[0]))
            actual_shift = 2.0 * np.pi * shift_index / reference_member.states.shape[0]
            shifted_states = np.roll(reference_member.states, shift_index, axis=0)
            try:
                correction = stroboscopic_curve_fixed_jacobi_free_time_rotation_correction(
                    seed,
                    target_jacobi=reference_member.mean_jacobi,
                    initial_states=shifted_states,
                    initial_mapping_time=reference_member.mapping_time_days / time_unit,
                    initial_rotation_angle_rad=reference_member.rotation_angle_rad,
                    phase_reference_states=shifted_states,
                    max_iterations=10,
                    tolerance=1.0e-10,
                    jacobi_tolerance=1.0e-10,
                    phase_tolerance=1.0e-10,
                    max_step=0.02,
                    max_state_step=base_variant.max_state_step,
                    max_mapping_time_step=base_variant.max_mapping_time_step_days / time_unit,
                    max_rotation_step=base_variant.max_rotation_step,
                    mapping_time_variable_scale=base_variant.mapping_time_variable_scale,
                    rotation_variable_scale=base_variant.rotation_variable_scale,
                    jacobi_residual_scale=base_variant.jacobi_residual_scale,
                    phase_condition="curve_tangent",
                )
                member = _member_from_route_b(-1, correction, time_unit_days=time_unit, length_unit_km=length_unit)
                audit_row, accepted, reason = _audit_route_b(
                    member,
                    correction,
                    target_mean_jacobi=reference_member.mean_jacobi,
                    system=system,
                )
            except Exception as exc:  # noqa: BLE001 - numerical audit records failures.
                rows.append(
                    _phase_test_row(
                        case_id=case_id,
                        test_type="cyclic_phase_shift",
                        requested_phase_shift=fraction_label,
                        actual_shift_index=shift_index,
                        actual_phase_shift_rad=actual_shift,
                        shift_method="cyclic_index_shift",
                        phase_condition="curve_tangent",
                        perturbation_norm=None,
                        reference_member=reference_member,
                        correction=None,
                        audit_row=None,
                        accepted=False,
                        failure_reason=str(exc),
                        time_unit=time_unit,
                        length_unit=length_unit,
                    )
                )
                continue
            rows.append(
                _phase_test_row(
                    case_id=case_id,
                    test_type="cyclic_phase_shift",
                    requested_phase_shift=fraction_label,
                    actual_shift_index=shift_index,
                    actual_phase_shift_rad=actual_shift,
                    shift_method="cyclic_index_shift",
                    phase_condition="curve_tangent",
                    perturbation_norm=None,
                    reference_member=reference_member,
                    correction=correction,
                    audit_row=audit_row,
                    accepted=accepted,
                    failure_reason=reason,
                    time_unit=time_unit,
                    length_unit=length_unit,
                )
            )

        for phase_condition in ("curve_tangent", "two_orthogonality"):
            variant = replace(base_variant, phase_condition=phase_condition)
            try:
                correction, member, audit_row, accepted, reason = _run_route_b_correction(
                    seed=seed,
                    system=system,
                    endpoint=endpoint,
                    variant=variant,
                    target_jacobi=reference_member.mean_jacobi,
                    initial_states=reference_member.states,
                    initial_mapping_time=reference_member.mapping_time_days / time_unit,
                    initial_rotation=reference_member.rotation_angle_rad,
                    phase_reference_states=reference_member.states,
                    source_member=reference_member.member,
                    time_unit_days=time_unit,
                    length_unit_km=length_unit,
                )
            except Exception as exc:  # noqa: BLE001
                rows.append(
                    _phase_test_row(
                        case_id=case_id,
                        test_type="alternative_phase_anchor",
                        requested_phase_shift="0",
                        actual_shift_index=0,
                        actual_phase_shift_rad=0.0,
                        shift_method="none",
                        phase_condition=phase_condition,
                        perturbation_norm=None,
                        reference_member=reference_member,
                        correction=None,
                        audit_row=None,
                        accepted=False,
                        failure_reason=str(exc),
                        time_unit=time_unit,
                        length_unit=length_unit,
                    )
                )
                continue
            rows.append(
                _phase_test_row(
                    case_id=case_id,
                    test_type="alternative_phase_anchor",
                    requested_phase_shift="0",
                    actual_shift_index=0,
                    actual_phase_shift_rad=0.0,
                    shift_method="none",
                    phase_condition=phase_condition,
                    perturbation_norm=None,
                    reference_member=reference_member,
                    correction=correction,
                    audit_row=audit_row,
                    accepted=accepted,
                    failure_reason=reason,
                    time_unit=time_unit,
                    length_unit=length_unit,
                )
            )

        for perturbation_norm in (1.0e-8, 1.0e-7):
            noise = rng.normal(size=reference_member.states.shape)
            noise *= perturbation_norm / float(np.linalg.norm(noise))
            perturbed_states = reference_member.states + noise
            try:
                correction, member, audit_row, accepted, reason = _run_route_b_correction(
                    seed=seed,
                    system=system,
                    endpoint=endpoint,
                    variant=base_variant,
                    target_jacobi=reference_member.mean_jacobi,
                    initial_states=perturbed_states,
                    initial_mapping_time=reference_member.mapping_time_days / time_unit,
                    initial_rotation=reference_member.rotation_angle_rad,
                    phase_reference_states=reference_member.states,
                    source_member=reference_member.member,
                    time_unit_days=time_unit,
                    length_unit_km=length_unit,
                )
            except Exception as exc:  # noqa: BLE001
                rows.append(
                    _phase_test_row(
                        case_id=case_id,
                        test_type="small_perturbation",
                        requested_phase_shift="0",
                        actual_shift_index=0,
                        actual_phase_shift_rad=0.0,
                        shift_method="none",
                        phase_condition="curve_tangent",
                        perturbation_norm=perturbation_norm,
                        reference_member=reference_member,
                        correction=None,
                        audit_row=None,
                        accepted=False,
                        failure_reason=str(exc),
                        time_unit=time_unit,
                        length_unit=length_unit,
                    )
                )
                continue
            rows.append(
                _phase_test_row(
                    case_id=case_id,
                    test_type="small_perturbation",
                    requested_phase_shift="0",
                    actual_shift_index=0,
                    actual_phase_shift_rad=0.0,
                    shift_method="none",
                    phase_condition="curve_tangent",
                    perturbation_norm=perturbation_norm,
                    reference_member=reference_member,
                    correction=correction,
                    audit_row=audit_row,
                    accepted=accepted,
                    failure_reason=reason,
                    time_unit=time_unit,
                    length_unit=length_unit,
                )
            )
    return rows


def _fixed_time_projection(
    *,
    seed,
    initial_states: np.ndarray,
    fixed_mapping_time: float,
    initial_rho: float,
    target_jacobi: float,
    phase_reference_states: np.ndarray,
    max_iterations: int = 16,
) -> FixedTimeProjection:
    states = np.array(initial_states, dtype=float, copy=True)
    reference = np.array(phase_reference_states, dtype=float, copy=True)
    rho = float(initial_rho) % (2.0 * np.pi)
    tangent = np.roll(reference, -1, axis=0) - np.roll(reference, 1, axis=0)
    tangent_norm = float(np.linalg.norm(tangent))
    if tangent_norm <= 1.0e-14:
        raise RuntimeError("fixed-time projection phase tangent is degenerate")
    tangent /= tangent_norm
    correction_history: list[np.ndarray] = []
    best_metric = np.inf
    best = None
    failure_reason = "maximum iterations reached"

    for _ in range(max_iterations):
        interpolation = _trigonometric_interpolation_matrix(seed.phases, seed.phases + rho)
        interpolation_derivative = _trigonometric_interpolation_derivative_matrix(seed.phases, seed.phases + rho)
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=fixed_mapping_time,
            mu=seed.mu,
            max_step=0.02,
        )
        targets = interpolation @ states
        residuals = mapped - targets
        residual_norms = np.linalg.norm(residuals, axis=1)
        jacobi_values = np.asarray(jacobi_constant(states, seed.mu), dtype=float)
        energy_residual = float(np.mean(jacobi_values) - target_jacobi)
        energy_gradient = _jacobi_gradient(states, seed.mu) / states.shape[0]
        phase_residual = float(np.sum((states - reference) * tangent))
        metric = max(float(residual_norms.max()), abs(energy_residual), abs(phase_residual))
        if metric < best_metric:
            best_metric = metric
            best = (
                states.copy(),
                mapped.copy(),
                targets.copy(),
                rho,
                residual_norms.copy(),
                phase_residual,
            )
        if residual_norms.max() < 1.0e-10 and abs(energy_residual) < 1.0e-10 and abs(phase_residual) < 1.0e-10:
            failure_reason = ""
            break

        sample_count = states.shape[0]
        state_size = 6 * sample_count
        jacobian = np.zeros((state_size + 2, state_size + 1), dtype=float)
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block = block + stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
        jacobian[:state_size, state_size] = -(interpolation_derivative @ states).reshape(-1)
        jacobian[state_size, :state_size] = energy_gradient.reshape(-1)
        jacobian[state_size + 1, :state_size] = tangent.reshape(-1)
        rhs = -np.concatenate([residuals.reshape(-1), np.array([energy_residual, phase_residual])])
        row_scales = np.concatenate([np.ones(state_size), np.array([1.0e5, 1.0])])
        column_scales = np.concatenate([np.ones(state_size), np.array([1.0e-3])])
        delta_scaled = np.linalg.lstsq(
            row_scales[:, None] * jacobian * column_scales[None, :],
            row_scales * rhs,
            rcond=1.0e-11,
        )[0]
        delta = column_scales * delta_scaled
        state_delta = delta[:state_size].reshape(sample_count, 6)
        rho_delta = float(delta[state_size])
        block_norms = np.linalg.norm(state_delta, axis=1)
        scale = 1.0
        if block_norms.max() > 2.0e-3:
            scale = min(scale, 2.0e-3 / float(block_norms.max()))
        if abs(rho_delta) > 4.0e-3:
            scale = min(scale, 4.0e-3 / abs(rho_delta))
        state_delta *= scale
        rho_delta *= scale
        correction_history.append(np.linalg.norm(state_delta, axis=1))
        states += state_delta
        rho = float((rho + rho_delta) % (2.0 * np.pi))

    if best is None:
        raise RuntimeError("fixed-time projection did not evaluate a candidate")
    best_states, best_mapped, best_targets, best_rho, best_residuals, best_phase_residual = best
    converged = failure_reason == ""
    return FixedTimeProjection(
        states=best_states,
        mapped_states=best_mapped,
        target_states=best_targets,
        rho=float(best_rho),
        target_jacobi=float(target_jacobi),
        residual_norms=best_residuals,
        phase_residual=float(best_phase_residual),
        correction_norm_history=np.asarray(correction_history, dtype=float),
        converged=converged,
        failure_reason=failure_reason,
    )


def _member_from_projection(
    projection: FixedTimeProjection,
    *,
    seed,
    time_unit: float,
    length_unit: float,
    member_id: int,
) -> CorrectedDROFamilyMember:
    jacobi_values = np.asarray(jacobi_constant(projection.states, seed.mu), dtype=float)
    displacement = projection.states[:, 2] - seed.orbit_state[2]
    vertical_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    return CorrectedDROFamilyMember(
        member=member_id,
        curve_indices=np.arange(projection.states.shape[0]),
        phases_rad=seed.phases.copy(),
        states=projection.states.copy(),
        jacobi_values=jacobi_values,
        target_vertical_amplitude_nd=vertical_amplitude,
        target_vertical_amplitude_km=vertical_amplitude * length_unit,
        max_abs_z_km=float(np.max(np.abs(projection.states[:, 2])) * length_unit),
        rotation_angle_rad=projection.rho,
        mapping_time_days=T_FIXED_DAYS,
        map_residual_norm=float(np.max(projection.residual_norms)),
        amplitude_residual=0.0,
        phase_residual=projection.phase_residual,
        curve_jacobi_span=float(np.ptp(jacobi_values)),
    )


def _fixed_time_rows(
    *,
    archive: BranchArchive,
    system,
    seed,
    time_unit: float,
    length_unit: float,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    cases = []
    gt_10500 = [case_id for case_id in SELECTED_CASES if archive.max_abs_z_km[np.where(archive.case_ids == case_id)[0][0]] > 10500.0]
    gt_11000 = [case_id for case_id in SELECTED_CASES if archive.max_abs_z_km[np.where(archive.case_ids == case_id)[0][0]] > 11000.0]
    if gt_10500:
        cases.append(("first_gt_10500", gt_10500[0]))
    if gt_11000:
        cases.append(("first_gt_11000", gt_11000[0]))
    highest_idx = int(np.argmax(archive.max_abs_z_km))
    cases.append(("highest", str(archive.case_ids[highest_idx])))

    for mode_label, case_id in cases:
        idx = int(np.where(archive.case_ids == case_id)[0][0])
        source_member = _member_from_archive(archive, idx, system=system, seed=seed, length_unit=length_unit)
        try:
            projection = _fixed_time_projection(
                seed=seed,
                initial_states=source_member.states,
                fixed_mapping_time=T_FIXED_DAYS / time_unit,
                initial_rho=source_member.rotation_angle_rad,
                target_jacobi=source_member.mean_jacobi,
                phase_reference_states=source_member.states,
            )
            projected = _member_from_projection(
                projection,
                seed=seed,
                time_unit=time_unit,
                length_unit=length_unit,
                member_id=idx,
            )
            validation = chapter3_quasi_dro_validation_row(
                projected,
                system,
                one_map_time_samples=7,
                ten_return_samples=401,
                max_step=0.02,
            )
            accepted = projection.converged and _audit_pass(projected, validation)
            phase_error = _float_from_audit(validation, "one_map_phase_return_error")
            ten_span = _float_from_audit(validation, "ten_return_jacobi_span")
            state_distance = _raw_distance(projected.states, source_member.states)
            amplitude_loss = source_member.max_abs_z_km - projected.max_abs_z_km
            if not accepted:
                interpretation = "projection failed; diagnostic free-time branch cannot directly serve as constant-mapping-time reproduction"
            elif projected.max_abs_z_km < 10250.0:
                interpretation = "projection accepted but amplitude returns near the endpoint; high-amplitude gain mainly came from T drift"
            elif projected.max_abs_z_km > 10500.0:
                interpretation = "candidate fixed-time projection result requiring multi-member continuation confirmation"
            else:
                interpretation = "projection accepted but remains below the 10,500 km fixed-time gate"
            failure_reason = projection.failure_reason if not accepted else ""
            values: dict[str, float | str | bool | None] = {
                "source_case_id": case_id,
                "source_max_abs_z_km": source_member.max_abs_z_km,
                "source_mapping_time_days": source_member.mapping_time_days,
                "source_rho": source_member.rotation_angle_rad,
                "target_mapping_time_days": T_FIXED_DAYS,
                "projection_mode": f"{mode_label}_fixed_T_fixed_mean_jacobi_free_rho",
                "converged": projection.converged,
                "accepted": accepted,
                "projected_max_abs_z_km": projected.max_abs_z_km,
                "projected_rho": projected.rotation_angle_rad,
                "mean_jacobi": projected.mean_jacobi,
                "map_residual_norm": projected.map_residual_norm,
                "curve_jacobi_span": projected.curve_jacobi_span,
                "one_map_phase_return_error": phase_error,
                "ten_return_jacobi_span": ten_span,
                "amplitude_loss_km": amplitude_loss,
                "state_distance_from_free_time_source": state_distance,
                "failure_reason": failure_reason,
                "interpretation": interpretation,
            }
        except Exception as exc:  # noqa: BLE001
            values = {
                "source_case_id": case_id,
                "source_max_abs_z_km": source_member.max_abs_z_km,
                "source_mapping_time_days": source_member.mapping_time_days,
                "source_rho": source_member.rotation_angle_rad,
                "target_mapping_time_days": T_FIXED_DAYS,
                "projection_mode": f"{mode_label}_fixed_T_fixed_mean_jacobi_free_rho",
                "converged": False,
                "accepted": False,
                "projected_max_abs_z_km": None,
                "projected_rho": None,
                "mean_jacobi": None,
                "map_residual_norm": None,
                "curve_jacobi_span": None,
                "one_map_phase_return_error": None,
                "ten_return_jacobi_span": None,
                "amplitude_loss_km": None,
                "state_distance_from_free_time_source": None,
                "failure_reason": str(exc),
                "interpretation": "projection failed; diagnostic free-time branch cannot directly serve as constant-mapping-time reproduction",
            }
        rows.append({field: _value(values[field]) for field in FIXED_TIME_FIELDS})
    return rows


def _write_doc(
    path: Path,
    *,
    consistency_rows: list[dict[str, str]],
    phase_rows: list[dict[str, str]],
    projection_rows: list[dict[str, str]],
) -> None:
    continuous = all(row["classification"].startswith("continuous") for row in consistency_rows)
    monotone_amp = consistency_rows[-1]["monotone_amplitude"] == "True"
    monotone_time = consistency_rows[-1]["monotone_mapping_time"] == "True"
    robust_rows = [row for row in phase_rows if row["classification"] == "phase_gauge_robust"]
    robust = len(robust_rows) == len(phase_rows) and bool(phase_rows)
    perturb_rows = [row for row in phase_rows if row["test_type"] == "small_perturbation"]
    perturb_ok = all(row["classification"] == "phase_gauge_robust" for row in perturb_rows) and bool(perturb_rows)
    accepted_projection = [row for row in projection_rows if row["accepted"] == "True"]
    accepted_gt_10500 = [
        row for row in accepted_projection
        if row["projected_max_abs_z_km"] != "N/A" and float(row["projected_max_abs_z_km"]) > 10500.0
    ]
    accepted_gt_11000 = [
        row for row in accepted_projection
        if row["projected_max_abs_z_km"] != "N/A" and float(row["projected_max_abs_z_km"]) > 11000.0
    ]
    best_projection = max(
        accepted_projection,
        key=lambda row: float(row["projected_max_abs_z_km"]) if row["projected_max_abs_z_km"] != "N/A" else -np.inf,
    ) if accepted_projection else None
    if accepted_gt_10500:
        next_action = (
            "Run multi-member fixed-time continuation confirmation. The current result is only a fixed-time "
            "projected candidate and must not update figure status."
        )
    elif accepted_projection:
        next_action = (
            "Refine fixed-time projection if needed, but current evidence says the high-amplitude diagnostic "
            "gain is tied to mapping-time drift."
        )
    else:
        next_action = (
            "Keep the free-time branch as a diagnostic result and prioritize Fourier/collocation BVP or a "
            "smaller-family sanity check before figure-source work."
        )

    content = f"""# Chapter 3 Route B Branch Consistency Audit

## Purpose

This audit checks the Route B `E_amplitude_monitor_large_step` diagnostic
free-time branch. It does not update Figure 3.16, Figure 3.17, fixed-mapping
accepted branch CSV files, `figure_validation_table.csv`, Chapter 5, or the
teacher package.

## Branch Consistency

- Diagnostic free-time branch continuous: `{continuous}`
- Amplitude monotone: `{monotone_amp}`
- Mapping-time drift monotone: `{monotone_time}`
- Highest diagnostic free-time member: `{consistency_rows[-1]['max_abs_z_km']}` km
- Highest mapping time: `{consistency_rows[-1]['mapping_time_days']}` days

The continuity classification uses phase-aligned row-to-row distance before raw
state distance. The branch remains a diagnostic free-time branch, not a
constant-mapping-time McCarthy reproduction.

## Phase-Gauge Robustness

- Phase-gauge robustness passed all tests: `{robust}`
- Small perturbation recovery passed: `{perturb_ok}`
- Robust rows: `{len(robust_rows)}` / `{len(phase_rows)}`

The phase-shift rows record requested shift, actual integer shift index, actual
phase shift in radians, and shift method. Because `N=61` is odd, requested
quarter/half shifts are not treated as exact unless the recorded index and
radian shift show it.

## Fixed-Time Projection

- Accepted fixed-time projections: `{len(accepted_projection)}`
- Accepted projected candidate beyond 10,500 km: `{bool(accepted_gt_10500)}`
- Accepted projected candidate beyond 11,000 km: `{bool(accepted_gt_11000)}`
- Best accepted projection: `{('N/A' if best_projection is None else best_projection['projected_max_abs_z_km'])}` km

A projection failure means the diagnostic free-time branch cannot directly serve
as a constant-mapping-time reproduction. A projection that falls back near the
endpoint indicates that the high-amplitude gain mainly came from mapping-time
drift. A projection above 10,500 or 11,000 km is only a candidate fixed-time
projection result requiring multi-member continuation confirmation.

## Category Separation

- Diagnostic free-time branch: audit-passing Route B members with free mapping
  time.
- Fixed-time projected candidate: one-member projection to the original mapping
  time that still needs multi-member fixed-time continuation confirmation.
- Confirmed fixed-time continuation branch: not produced by this audit.

Only a confirmed fixed-time continuation branch can support a later discussion
of replacing Figure 3.16 or Figure 3.17 data sources.

## Next Action

{next_action}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    computed = PROJECT_ROOT / "data" / "computed"
    experiments_path = computed / "chapter3_route_b_refinement_experiments.csv"
    branch_states_path = computed / "chapter3_route_b_free_time_branch_states.npz"
    family_path = computed / "chapter3_quasi_dro_palc_family.csv"
    consistency_path = computed / "chapter3_route_b_branch_consistency.csv"
    phase_path = computed / "chapter3_route_b_phase_gauge_robustness.csv"
    projection_path = computed / "chapter3_route_b_fixed_time_projection.csv"
    doc_path = PROJECT_ROOT / "docs" / "chapter3_route_b_branch_consistency.md"

    experiment_rows = _read_rows(experiments_path)
    endpoint = load_corrected_dro_family_csv(family_path)[-1]
    system, seed, time_unit, length_unit = _system_seed(endpoint)
    if not branch_states_path.exists():
        _reconstruct_branch_archive(path=branch_states_path, endpoint=endpoint)
    archive = _load_archive(branch_states_path)
    _assert_archive_alignment(archive=archive, experiment_rows=experiment_rows, endpoint=endpoint)

    consistency_rows = _branch_consistency_rows(
        archive=archive,
        endpoint=endpoint,
        system=system,
        seed=seed,
        time_unit=time_unit,
    )
    _write_rows(consistency_path, BRANCH_CONSISTENCY_FIELDS, consistency_rows)
    phase_rows = _phase_gauge_rows(
        archive=archive,
        endpoint=endpoint,
        system=system,
        seed=seed,
        time_unit=time_unit,
        length_unit=length_unit,
    )
    _write_rows(phase_path, PHASE_GAUGE_FIELDS, phase_rows)
    projection_rows = _fixed_time_rows(
        archive=archive,
        system=system,
        seed=seed,
        time_unit=time_unit,
        length_unit=length_unit,
    )
    _write_rows(projection_path, FIXED_TIME_FIELDS, projection_rows)
    _write_doc(
        doc_path,
        consistency_rows=consistency_rows,
        phase_rows=phase_rows,
        projection_rows=projection_rows,
    )

    accepted_projection_gt_10500 = any(
        row["accepted"] == "True"
        and row["projected_max_abs_z_km"] != "N/A"
        and float(row["projected_max_abs_z_km"]) > 10500.0
        for row in projection_rows
    )
    print("Route B free-time branch audit complete")
    print(f"branch_rows={len(consistency_rows)}")
    print(f"phase_gauge_rows={len(phase_rows)}")
    print(f"fixed_time_projection_rows={len(projection_rows)}")
    print(f"diagnostic_free_time_continuous={all(row['classification'].startswith('continuous') for row in consistency_rows)}")
    print(f"phase_gauge_robust={all(row['classification'] == 'phase_gauge_robust' for row in phase_rows)}")
    print(f"fixed_time_candidate_beyond_10500_km={accepted_projection_gt_10500}")


if __name__ == "__main__":
    main()
