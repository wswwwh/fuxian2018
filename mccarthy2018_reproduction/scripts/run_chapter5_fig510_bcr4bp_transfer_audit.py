"""Audit DE421-initialized planar BCR4BP extensions of Fig. 5.10.

The thesis flight times and impulse targets are preserved. Figure 5.10 is an
autonomous CR3BP calculation, so an epoch is not applicable to the published
case; the date below belongs only to this project-defined DE421/BCR4BP
extension. Numerical BCR4BP acceptance and paper-equivalence acceptance are
deliberately separate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize_scalar

from _paths import PROJECT_ROOT
from qp_orbits.application_scenarios import earth_moon_nrho_transfer_baseline
from qp_orbits.bcr4bp import (
    bcr4bp_rhs,
    bicircular_sun_position,
    correct_bcr4bp_velocity_to_position_target,
    earth_moon_bcr4bp_parameters,
    integrate_bcr4bp,
)
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.ephemeris import MOON_RADIUS_KM, de421_bcr4bp_initial_geometry


EPOCH_UTC = "2020-06-15T00:00:00Z"
EPOCH_SOURCE = "project_bcr4bp_extension_epoch_cr3bp_epoch_not_applicable"
KERNEL = PROJECT_ROOT / "data" / "raw" / "ephemeris" / "de421.bsp"
BASELINE_CSV = (
    PROJECT_ROOT / "data" / "computed" / "chapter5_earth_moon_nrho_transfer_baseline.csv"
)
TARGET_REGISTRY = PROJECT_ROOT / "data" / "reproduction_targets.csv"
REFERENCE_IMAGE = PROJECT_ROOT / "outputs" / "reference_pages" / "fig_5_10_reference.png"
PUBLIC_SOURCE_NOTE = PROJECT_ROOT / "docs" / "chapter5_fig510_public_source_anchors.md"

AUDIT_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter5_fig510_bcr4bp_transfer_audit.csv"
)
TRAJECTORY_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter5_fig510_bcr4bp_transfer_trajectories.csv"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_fig510_bcr4bp_transfer_audit.md"

ENDPOINT_THRESHOLD_KM = 1.0e-3
TOLERANCE_POSITION_SPREAD_THRESHOLD_KM = 1.0e-3
TOLERANCE_VELOCITY_SPREAD_THRESHOLD_M_S = 1.0e-3
SEGMENT_POSITION_THRESHOLD_KM = 1.0e-3
SEGMENT_VELOCITY_THRESHOLD_M_S = 1.0e-3
TOTAL_DELTA_V_SANITY_THRESHOLD_M_S = 250.0
PAPER_COMPONENT_DELTA_V_THRESHOLD_M_S = 1.0
PAPER_TOTAL_RELATIVE_ERROR_THRESHOLD = 0.01
TRAJECTORY_SAMPLES = 1201
SEGMENT_COUNT = 16

PRIMARY_RTOL = 1.0e-11
PRIMARY_ATOL = 1.0e-13
PRIMARY_MAX_STEP = 0.01
STRICT_RTOL = 1.0e-12
STRICT_ATOL = 1.0e-14
STRICT_MAX_STEP = 0.0025

PAPER_TARGETS = (
    {
        "case_id": 1,
        "time_of_flight_days": 23.0,
        "departure_delta_v_m_s": 48.3,
        "arrival_delta_v_m_s": 32.2,
        "total_delta_v_m_s": 80.5,
    },
    {
        "case_id": 2,
        "time_of_flight_days": 12.4,
        "departure_delta_v_m_s": 51.3,
        "arrival_delta_v_m_s": 35.3,
        "total_delta_v_m_s": 86.6,
    },
)

AUDIT_FIELDS = (
    "figure_id",
    "case_id",
    "source_model",
    "epoch_utc",
    "epoch_source",
    "kernel_sha256",
    "baseline_csv_sha256",
    "sun_phase_rad",
    "sun_phase_deg",
    "sun_distance_full_km",
    "sun_distance_planar_km",
    "sun_distance_planar_nd",
    "sun_elevation_deg",
    "sun_angular_rate_nd",
    "initial_sun_xy_closure_nd",
    "earth_moon_distance_km",
    "frame_orthogonality_error",
    "frame_determinant",
    "earth_moon_barycenter_spk_error_km",
    "departure_phase",
    "arrival_phase",
    "time_of_flight_nd",
    "time_of_flight_days",
    "paper_time_of_flight_days",
    "de421_end_sun_phase_deg",
    "bcr4bp_end_sun_phase_deg",
    "end_sun_phase_error_deg",
    "de421_end_sun_elevation_deg",
    "uncorrected_endpoint_error_km",
    "solver_endpoint_error_km",
    "independent_endpoint_error_km",
    "tolerance_position_spread_km",
    "tolerance_velocity_spread_m_s",
    "segment_count",
    "segment_time_origin",
    "segment_max_position_defect_km",
    "segment_max_velocity_defect_m_s",
    "reset_time_negative_control_position_defect_km",
    "reset_time_negative_control_velocity_defect_m_s",
    "rhs_all_finite",
    "minimum_moon_radius_method",
    "minimum_moon_radius_time_nd",
    "minimum_moon_radius_km",
    "cr3bp_jacobi_span_diagnostic_only",
    "cr3bp_seed_departure_delta_v_m_s",
    "cr3bp_seed_arrival_delta_v_m_s",
    "cr3bp_seed_total_delta_v_m_s",
    "departure_delta_v_m_s",
    "arrival_delta_v_m_s",
    "total_delta_v_m_s",
    "paper_departure_delta_v_m_s",
    "paper_arrival_delta_v_m_s",
    "paper_total_delta_v_m_s",
    "departure_delta_v_error_m_s",
    "arrival_delta_v_error_m_s",
    "total_delta_v_error_m_s",
    "total_delta_v_relative_error",
    "solver_success",
    "independent_propagation_success",
    "paper_tof_agreement",
    "paper_delta_v_agreement",
    "paper_model_geometry_match",
    "numerical_acceptance",
    "paper_equivalence",
    "numerical_threshold",
    "paper_equivalence_threshold",
    "evidence_artifact",
    "boundary",
)

TRAJECTORY_FIELDS = (
    "figure_id",
    "case_id",
    "model",
    "sample",
    "time_nd",
    "time_days",
    "x_nd",
    "y_nd",
    "z_nd",
    "xdot_nd",
    "ydot_nd",
    "zdot_nd",
    "moon_radius_km",
    "cr3bp_jacobi_diagnostic",
)


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return f"{number:.16g}" if np.isfinite(number) else str(number)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "pass", "1", "yes"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _wrap_angle(value: float) -> float:
    return float((value + np.pi) % (2.0 * np.pi) - np.pi)


def _parse_epoch(value: str) -> datetime:
    epoch = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if epoch.tzinfo is None:
        epoch = epoch.replace(tzinfo=timezone.utc)
    return epoch.astimezone(timezone.utc)


def _velocity_unit_m_s() -> float:
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Earth-Moon dimensional units are required")
    return system.length_unit_km / (system.time_unit_days * 86400.0) * 1000.0


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in fields})


def numerical_acceptance(row: dict[str, Any]) -> bool:
    """Evaluate only the BCR4BP numerical/physical extension gate."""

    return bool(
        _truthy(row.get("solver_success"))
        and _truthy(row.get("independent_propagation_success"))
        and _truthy(row.get("rhs_all_finite"))
        and float(row["solver_endpoint_error_km"]) <= ENDPOINT_THRESHOLD_KM
        and float(row["independent_endpoint_error_km"]) <= ENDPOINT_THRESHOLD_KM
        and float(row["tolerance_position_spread_km"])
        <= TOLERANCE_POSITION_SPREAD_THRESHOLD_KM
        and float(row["tolerance_velocity_spread_m_s"])
        <= TOLERANCE_VELOCITY_SPREAD_THRESHOLD_M_S
        and float(row["segment_max_position_defect_km"])
        <= SEGMENT_POSITION_THRESHOLD_KM
        and float(row["segment_max_velocity_defect_m_s"])
        <= SEGMENT_VELOCITY_THRESHOLD_M_S
        and float(row["reset_time_negative_control_position_defect_km"]) > 1.0
        and row.get("minimum_moon_radius_method")
        == "strict_DOP853_dense_output_all_sampled_local_minima"
        and 0.0
        <= float(row["minimum_moon_radius_time_nd"])
        <= float(row["time_of_flight_nd"])
        and float(row["minimum_moon_radius_km"]) > MOON_RADIUS_KM
        and float(row["total_delta_v_m_s"]) <= TOTAL_DELTA_V_SANITY_THRESHOLD_M_S
        and float(row["initial_sun_xy_closure_nd"]) <= 1.0e-12
        and float(row["frame_orthogonality_error"]) <= 1.0e-12
        and float(row["frame_determinant"]) > 0.0
        and float(row["earth_moon_barycenter_spk_error_km"]) <= 1.0e-3
        and row.get("segment_time_origin") == "absolute"
    )


def paper_equivalence(row: dict[str, Any]) -> bool:
    """Require thesis TOF, impulse, model/boundary, and geometry agreement."""

    return bool(
        _truthy(row.get("paper_tof_agreement"))
        and _truthy(row.get("paper_delta_v_agreement"))
        and _truthy(row.get("paper_model_geometry_match"))
    )


def _segment_defects(
    times: np.ndarray,
    states: np.ndarray,
    params: Any,
    *,
    reset_time: bool,
) -> tuple[float, float]:
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None:
        raise ValueError("Earth-Moon dimensional length unit is required")
    velocity_unit = _velocity_unit_m_s()
    indices = np.linspace(0, times.size - 1, SEGMENT_COUNT + 1, dtype=int)
    position_defects: list[float] = []
    velocity_defects: list[float] = []
    for start, stop in zip(indices[:-1], indices[1:]):
        if reset_time:
            span = (0.0, float(times[stop] - times[start]))
            evaluation_time = span[1]
        else:
            span = (float(times[start]), float(times[stop]))
            evaluation_time = span[1]
        solution = integrate_bcr4bp(
            states[start],
            span,
            params,
            t_eval=np.array([evaluation_time]),
            rtol=STRICT_RTOL,
            atol=STRICT_ATOL,
            max_step=STRICT_MAX_STEP,
        )
        if not solution.success or solution.y.shape[1] != 1:
            return float("inf"), float("inf")
        defect = solution.y[:, -1] - states[stop]
        position_defects.append(float(np.linalg.norm(defect[:3]) * system.length_unit_km))
        velocity_defects.append(float(np.linalg.norm(defect[3:]) * velocity_unit))
    return max(position_defects), max(velocity_defects)


def _continuous_minimum_moon_radius(
    times: np.ndarray,
    states: np.ndarray,
    solution: Any,
) -> tuple[float, float]:
    """Refine every sampled local lunar-radius minimum with dense output."""

    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None:
        raise ValueError("Earth-Moon dimensional length unit is required")
    if solution.sol is None:
        raise ValueError("dense BCR4BP output is required for lunar-clearance audit")
    moon = np.array([1.0 - system.mu, 0.0, 0.0], dtype=float)

    def radius_nd(time: float) -> float:
        state = np.asarray(solution.sol(float(time)), dtype=float)
        return float(np.linalg.norm(state[:3] - moon))

    sampled = np.linalg.norm(states[:, :3] - moon, axis=1)
    candidates = [0, times.size - 1]
    candidates.extend(
        index
        for index in range(1, times.size - 1)
        if sampled[index] <= sampled[index - 1]
        and sampled[index] <= sampled[index + 1]
    )
    best_time = float(times[int(np.argmin(sampled))])
    best_radius = radius_nd(best_time)
    for index in candidates:
        if index == 0 or index == times.size - 1:
            candidate_time = float(times[index])
            candidate_radius = radius_nd(candidate_time)
        else:
            refinement = minimize_scalar(
                radius_nd,
                bounds=(float(times[index - 1]), float(times[index + 1])),
                method="bounded",
                options={"xatol": 1.0e-13},
            )
            if not refinement.success or not np.isfinite(refinement.fun):
                raise RuntimeError("failed to refine BCR4BP lunar-clearance minimum")
            candidate_time = float(refinement.x)
            candidate_radius = float(refinement.fun)
        if candidate_radius < best_radius:
            best_time = candidate_time
            best_radius = candidate_radius
    return best_radius * system.length_unit_km, best_time


def _trajectory_rows(
    *,
    case_id: int,
    model: str,
    times_nd: np.ndarray,
    states: np.ndarray,
) -> list[dict[str, Any]]:
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Earth-Moon dimensional units are required")
    moon = np.array([1.0 - system.mu, 0.0, 0.0], dtype=float)
    moon_radius = np.linalg.norm(states[:, :3] - moon, axis=1) * system.length_unit_km
    jacobi = jacobi_constant(states, system.mu)
    rows: list[dict[str, Any]] = []
    for sample, (time, state) in enumerate(zip(times_nd, states)):
        rows.append(
            {
                "figure_id": "5.10",
                "case_id": case_id,
                "model": model,
                "sample": sample,
                "time_nd": time,
                "time_days": time * system.time_unit_days,
                "x_nd": state[0],
                "y_nd": state[1],
                "z_nd": state[2],
                "xdot_nd": state[3],
                "ydot_nd": state[4],
                "zdot_nd": state[5],
                "moon_radius_km": moon_radius[sample],
                "cr3bp_jacobi_diagnostic": jacobi[sample],
            }
        )
    return rows


def build_audit() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    system = SYSTEMS["earth_moon"]
    if system.length_unit_km is None or system.time_unit_days is None:
        raise ValueError("Earth-Moon dimensional units are required")
    if not KERNEL.is_file():
        raise FileNotFoundError(KERNEL)
    baseline = earth_moon_nrho_transfer_baseline()
    initial_geometry = de421_bcr4bp_initial_geometry(
        KERNEL,
        epoch_utc=EPOCH_UTC,
        system=system,
    )
    params = replace(
        earth_moon_bcr4bp_parameters(system),
        sun_phase=initial_geometry.sun_phase_rad,
        sun_distance=initial_geometry.sun_planar_distance_nd,
    )
    projected_sun = initial_geometry.sun_rotating_vector_km[:2] / system.length_unit_km
    sun_xy_closure = float(
        np.linalg.norm(bicircular_sun_position(0.0, params)[:2] - projected_sun)
    )
    kernel_hash = _sha256(KERNEL)
    baseline_hash = _sha256(BASELINE_CSV)
    velocity_unit = _velocity_unit_m_s()
    epoch = _parse_epoch(EPOCH_UTC)

    rows: list[dict[str, Any]] = []
    trajectory_rows: list[dict[str, Any]] = []
    for target, transfer in zip(PAPER_TARGETS, baseline.forward_transfers):
        case_id = int(target["case_id"])
        time_of_flight = transfer.time_of_flight_days / system.time_unit_days
        seed_initial = transfer.transfer_states[0].copy()
        target_position = transfer.arrival_state[:3].copy()

        uncorrected = integrate_bcr4bp(
            seed_initial,
            (0.0, time_of_flight),
            params,
            t_eval=np.array([time_of_flight]),
            rtol=PRIMARY_RTOL,
            atol=PRIMARY_ATOL,
            max_step=PRIMARY_MAX_STEP,
        )
        if not uncorrected.success or uncorrected.y.shape[1] != 1:
            raise RuntimeError(f"case {case_id} uncorrected BCR4BP propagation failed")
        uncorrected_error = float(
            np.linalg.norm(uncorrected.y[:3, -1] - target_position)
            * system.length_unit_km
        )

        correction = correct_bcr4bp_velocity_to_position_target(
            seed_initial,
            target_position,
            time_of_flight,
            params,
            residual_scale=1.0,
            rtol=PRIMARY_RTOL,
            atol=PRIMARY_ATOL,
            max_step=PRIMARY_MAX_STEP,
            max_nfev=35,
        )
        times = np.linspace(0.0, time_of_flight, TRAJECTORY_SAMPLES)
        primary = integrate_bcr4bp(
            correction.corrected_initial_state,
            (0.0, time_of_flight),
            params,
            t_eval=times,
            rtol=PRIMARY_RTOL,
            atol=PRIMARY_ATOL,
            max_step=PRIMARY_MAX_STEP,
        )
        strict = integrate_bcr4bp(
            correction.corrected_initial_state,
            (0.0, time_of_flight),
            params,
            t_eval=times,
            rtol=STRICT_RTOL,
            atol=STRICT_ATOL,
            max_step=STRICT_MAX_STEP,
            dense_output=True,
        )
        primary_success = bool(primary.success and primary.y.shape[1] == times.size)
        strict_success = bool(strict.success and strict.y.shape[1] == times.size)
        if not primary_success or not strict_success:
            raise RuntimeError(f"case {case_id} corrected BCR4BP propagation failed")
        primary_states = primary.y.T
        strict_states = strict.y.T
        solver_endpoint_error = correction.residual_norm * system.length_unit_km
        independent_endpoint_error = float(
            np.linalg.norm(strict_states[-1, :3] - target_position)
            * system.length_unit_km
        )
        tolerance_position_spread = float(
            np.linalg.norm(primary_states[-1, :3] - strict_states[-1, :3])
            * system.length_unit_km
        )
        tolerance_velocity_spread = float(
            np.linalg.norm(primary_states[-1, 3:] - strict_states[-1, 3:])
            * velocity_unit
        )
        segment_position, segment_velocity = _segment_defects(
            times,
            strict_states,
            params,
            reset_time=False,
        )
        reset_position, reset_velocity = _segment_defects(
            times,
            strict_states,
            params,
            reset_time=True,
        )
        rhs_finite = bool(
            all(
                np.all(np.isfinite(bcr4bp_rhs(float(times[index]), strict_states[index], params)))
                for index in np.linspace(0, times.size - 1, 61, dtype=int)
            )
        )
        minimum_moon_radius, minimum_moon_radius_time = (
            _continuous_minimum_moon_radius(times, strict_states, strict)
        )
        jacobi_span = float(np.ptp(jacobi_constant(strict_states, system.mu)))

        departure_delta_v = float(
            np.linalg.norm(
                correction.corrected_initial_state[3:] - transfer.departure_state[3:]
            )
            * velocity_unit
        )
        arrival_delta_v = float(
            np.linalg.norm(transfer.arrival_state[3:] - strict_states[-1, 3:])
            * velocity_unit
        )
        total_delta_v = departure_delta_v + arrival_delta_v
        departure_error = departure_delta_v - float(target["departure_delta_v_m_s"])
        arrival_error = arrival_delta_v - float(target["arrival_delta_v_m_s"])
        total_error = total_delta_v - float(target["total_delta_v_m_s"])
        total_relative_error = total_error / float(target["total_delta_v_m_s"])

        end_epoch = epoch + timedelta(days=transfer.time_of_flight_days)
        end_geometry = de421_bcr4bp_initial_geometry(
            KERNEL,
            epoch_utc=end_epoch,
            system=system,
        )
        bcr4bp_end_phase = _wrap_angle(
            params.sun_phase + params.sun_angular_rate * time_of_flight
        )
        end_phase_error = _wrap_angle(bcr4bp_end_phase - end_geometry.sun_phase_rad)

        paper_tof = bool(
            abs(transfer.time_of_flight_days - float(target["time_of_flight_days"]))
            <= 1.0e-9
        )
        paper_delta_v = bool(
            abs(departure_error) <= PAPER_COMPONENT_DELTA_V_THRESHOLD_M_S
            and abs(arrival_error) <= PAPER_COMPONENT_DELTA_V_THRESHOLD_M_S
            and abs(total_relative_error) <= PAPER_TOTAL_RELATIVE_ERROR_THRESHOLD
        )
        row: dict[str, Any] = {
            "figure_id": "5.10",
            "case_id": case_id,
            "source_model": "DE421-initialized planar Earth-Moon BCR4BP",
            "epoch_utc": EPOCH_UTC,
            "epoch_source": EPOCH_SOURCE,
            "kernel_sha256": kernel_hash,
            "baseline_csv_sha256": baseline_hash,
            "sun_phase_rad": initial_geometry.sun_phase_rad,
            "sun_phase_deg": np.degrees(initial_geometry.sun_phase_rad),
            "sun_distance_full_km": initial_geometry.sun_distance_km,
            "sun_distance_planar_km": initial_geometry.sun_planar_distance_km,
            "sun_distance_planar_nd": initial_geometry.sun_planar_distance_nd,
            "sun_elevation_deg": np.degrees(initial_geometry.sun_elevation_rad),
            "sun_angular_rate_nd": params.sun_angular_rate,
            "initial_sun_xy_closure_nd": sun_xy_closure,
            "earth_moon_distance_km": initial_geometry.earth_moon_distance_km,
            "frame_orthogonality_error": initial_geometry.frame_orthogonality_error,
            "frame_determinant": initial_geometry.frame_determinant,
            "earth_moon_barycenter_spk_error_km": (
                initial_geometry.earth_moon_barycenter_spk_error_km
            ),
            "departure_phase": transfer.departure_phase,
            "arrival_phase": transfer.arrival_phase,
            "time_of_flight_nd": time_of_flight,
            "time_of_flight_days": transfer.time_of_flight_days,
            "paper_time_of_flight_days": target["time_of_flight_days"],
            "de421_end_sun_phase_deg": np.degrees(end_geometry.sun_phase_rad),
            "bcr4bp_end_sun_phase_deg": np.degrees(bcr4bp_end_phase),
            "end_sun_phase_error_deg": np.degrees(end_phase_error),
            "de421_end_sun_elevation_deg": np.degrees(end_geometry.sun_elevation_rad),
            "uncorrected_endpoint_error_km": uncorrected_error,
            "solver_endpoint_error_km": solver_endpoint_error,
            "independent_endpoint_error_km": independent_endpoint_error,
            "tolerance_position_spread_km": tolerance_position_spread,
            "tolerance_velocity_spread_m_s": tolerance_velocity_spread,
            "segment_count": SEGMENT_COUNT,
            "segment_time_origin": "absolute",
            "segment_max_position_defect_km": segment_position,
            "segment_max_velocity_defect_m_s": segment_velocity,
            "reset_time_negative_control_position_defect_km": reset_position,
            "reset_time_negative_control_velocity_defect_m_s": reset_velocity,
            "rhs_all_finite": rhs_finite,
            "minimum_moon_radius_method": (
                "strict_DOP853_dense_output_all_sampled_local_minima"
            ),
            "minimum_moon_radius_time_nd": minimum_moon_radius_time,
            "minimum_moon_radius_km": minimum_moon_radius,
            "cr3bp_jacobi_span_diagnostic_only": jacobi_span,
            "cr3bp_seed_departure_delta_v_m_s": transfer.departure_delta_v_m_s,
            "cr3bp_seed_arrival_delta_v_m_s": transfer.arrival_delta_v_m_s,
            "cr3bp_seed_total_delta_v_m_s": transfer.total_delta_v_m_s,
            "departure_delta_v_m_s": departure_delta_v,
            "arrival_delta_v_m_s": arrival_delta_v,
            "total_delta_v_m_s": total_delta_v,
            "paper_departure_delta_v_m_s": target["departure_delta_v_m_s"],
            "paper_arrival_delta_v_m_s": target["arrival_delta_v_m_s"],
            "paper_total_delta_v_m_s": target["total_delta_v_m_s"],
            "departure_delta_v_error_m_s": departure_error,
            "arrival_delta_v_error_m_s": arrival_error,
            "total_delta_v_error_m_s": total_error,
            "total_delta_v_relative_error": total_relative_error,
            "solver_success": bool(correction.accepted and primary_success),
            "independent_propagation_success": strict_success,
            "paper_tof_agreement": paper_tof,
            "paper_delta_v_agreement": paper_delta_v,
            "paper_model_geometry_match": False,
            "numerical_acceptance": False,
            "paper_equivalence": False,
            "numerical_threshold": (
                "endpoint/spread/segment position <= 1e-3 km; velocity <= 1e-3 m/s; "
                "finite RHS; minimum Moon radius > 1737.4 km; absolute segment time"
            ),
            "paper_equivalence_threshold": (
                "TOF <= 1e-9 day; each impulse <= 1 m/s; total relative error <= 1%; "
                "paper torus member/intersection phases/boundaries/pointwise geometry required"
            ),
            "evidence_artifact": (
                f"{_rel(BASELINE_CSV)};{_rel(TARGET_REGISTRY)};{_rel(REFERENCE_IMAGE)};"
                f"{_rel(PUBLIC_SOURCE_NOTE)};src/qp_orbits/bcr4bp.py;"
                "src/qp_orbits/ephemeris.py"
            ),
            "boundary": (
                "Numerically accepted DE421-initialized planar BCR4BP extension. "
                "Departure/arrival states remain CR3BP NRHO boundaries; epoch is not "
                "applicable to the autonomous paper case and this date belongs only to "
                "the project BCR4BP extension. The paper torus member, intersection phases, "
                "impulse agreement, and pointwise thesis geometry remain open."
            ),
        }
        row["numerical_acceptance"] = numerical_acceptance(row)
        row["paper_equivalence"] = paper_equivalence(row)
        rows.append(row)

        strict_times = np.asarray(strict.t, dtype=float)
        trajectory_rows.extend(
            _trajectory_rows(
                case_id=case_id,
                model="bcr4bp_strict",
                times_nd=strict_times,
                states=strict_states,
            )
        )
        trajectory_rows.extend(
            _trajectory_rows(
                case_id=case_id,
                model="cr3bp_seed",
                times_nd=transfer.transfer_times_days / system.time_unit_days,
                states=transfer.transfer_states,
            )
        )
    return rows, trajectory_rows


def _render_doc(rows: list[dict[str, Any]]) -> None:
    numerical = sum(bool(row["numerical_acceptance"]) for row in rows)
    paper = sum(bool(row["paper_equivalence"]) for row in rows)
    table = [
        "| case | TOF day | uncorrected km | independent km | segment km | min Moon km | BCR4BP dV1+dV2=total m/s | paper total m/s | total error | numerical | paper equivalent |",
        "|---:|---:|---:|---:|---:|---:|---|---:|---:|---|---|",
    ]
    for row in rows:
        table.append(
            f"| {row['case_id']} | {_fmt(row['time_of_flight_days'])} | "
            f"{_fmt(row['uncorrected_endpoint_error_km'])} | "
            f"{_fmt(row['independent_endpoint_error_km'])} | "
            f"{_fmt(row['segment_max_position_defect_km'])} | "
            f"{_fmt(row['minimum_moon_radius_km'])} | "
            f"{_fmt(row['departure_delta_v_m_s'])} + "
            f"{_fmt(row['arrival_delta_v_m_s'])} = {_fmt(row['total_delta_v_m_s'])} | "
            f"{_fmt(row['paper_total_delta_v_m_s'])} | "
            f"{_fmt(row['total_delta_v_error_m_s'])} | "
            f"{_fmt(row['numerical_acceptance'])} | {_fmt(row['paper_equivalence'])} |"
        )
    first = rows[0]
    DOC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 Figure 5.10 BCR4BP transfer audit

Generated by `scripts/run_chapter5_fig510_bcr4bp_transfer_audit.py`.

## Scope

This is a robustness/high-fidelity extension of the accepted Fig. 5.10 CR3BP
direct transfers. It is not a claim that McCarthy published BCR4BP initial
states. The project-selected epoch `{EPOCH_UTC}` initializes the planar Sun
geometry from DE421; the two target NRHO states remain corrected CR3BP boundary
states.

The BCR4BP solar angular rate uses the required normalized radians conversion,
`2*pi*TU/year - 1`, not the older cycles-per-year expression that omitted
`2*pi`.

## Initial geometry

- Epoch source: `{EPOCH_SOURCE}`
- DE421 kernel SHA256: `{first['kernel_sha256']}`
- Sun phase: `{_fmt(first['sun_phase_rad'])}` rad
- Full / planar Sun distance: `{_fmt(first['sun_distance_full_km'])}` / `{_fmt(first['sun_distance_planar_km'])}` km
- Planar Sun distance: `{_fmt(first['sun_distance_planar_nd'])}` LU
- Ignored solar elevation: `{_fmt(first['sun_elevation_deg'])}` deg
- BCR4BP normalized solar angular rate: `{_fmt(first['sun_angular_rate_nd'])}`
- Initial DE421/BCR4BP planar closure: `{_fmt(first['initial_sun_xy_closure_nd'])}` LU
- Frame orthogonality error: `{_fmt(first['frame_orthogonality_error'])}`
- Model barycenter versus SPK EMB: `{_fmt(first['earth_moon_barycenter_spk_error_km'])}` km

## Results

- Numerical BCR4BP acceptance: `{numerical}` / `{len(rows)}`
- Paper-equivalence acceptance: `{paper}` / `{len(rows)}`
- Independent propagation: `rtol={STRICT_RTOL}`, `atol={STRICT_ATOL}`, `max_step={STRICT_MAX_STEP}`
- Segment validation: `{SEGMENT_COUNT}` segments with absolute BCR4BP time
- Lunar-clearance validation: strict DOP853 dense output with bounded refinement of every sampled local minimum

{chr(10).join(table)}

The `cr3bp_jacobi_span_diagnostic_only` field is intentionally excluded from
acceptance: the BCR4BP model is time dependent and does not conserve the CR3BP
Jacobi constant. The reset-time segment rows are a negative control; resetting
every segment to `t=0` incorrectly resets the Sun phase and produces large
defects.

## Decision

Both cases pass the numerical endpoint, tolerance, absolute-time segment,
finite-RHS, lunar-clearance, and delta-v sanity gates. Both remain
`paper_equivalence=false`: an epoch is not applicable to the autonomous CR3BP
paper case, and this project epoch applies only to the BCR4BP extension. The
paper-specific quasi-NRHO member, intersection phases, raw boundary states, and
optimization constraints are unavailable; the individual impulse targets do
not agree within 1 m/s, and no pointwise thesis-trajectory comparison is
claimed.

Artifacts:

- `{_rel(AUDIT_OUTPUT)}`
- `{_rel(TRAJECTORY_OUTPUT)}`
- `{_rel(BASELINE_CSV)}`
- `{_rel(REFERENCE_IMAGE)}`
- `{_rel(PUBLIC_SOURCE_NOTE)}`
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Recompute and validate without rewriting audit artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows, trajectories = build_audit()
    numerical = sum(bool(row["numerical_acceptance"]) for row in rows)
    paper = sum(bool(row["paper_equivalence"]) for row in rows)
    if len(rows) != 2 or numerical != 2 or paper != 0:
        raise SystemExit(
            f"Fig. 5.10 BCR4BP gate failed: rows={len(rows)}, numerical={numerical}, paper={paper}"
        )
    if not args.check:
        _write_csv(AUDIT_OUTPUT, rows, AUDIT_FIELDS)
        _write_csv(TRAJECTORY_OUTPUT, trajectories, TRAJECTORY_FIELDS)
        _render_doc(rows)
        print(f"wrote {_rel(AUDIT_OUTPUT)}")
        print(f"wrote {_rel(TRAJECTORY_OUTPUT)}")
        print(f"wrote {_rel(DOC_OUTPUT)}")
    print(
        "fig510_bcr4bp: "
        f"numerical={numerical}/2, paper_equivalence={paper}/2, "
        f"endpoint_km={max(float(row['independent_endpoint_error_km']) for row in rows):.6e}, "
        f"delta_v_m_s={[round(float(row['total_delta_v_m_s']), 6) for row in rows]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
