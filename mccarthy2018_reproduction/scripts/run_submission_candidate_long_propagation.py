"""Run the preregistered Stage-H4 three-map stable-manifold campaign."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Mapping

import numpy as np
import scipy


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(SCRIPTS))

import build_submission_candidate_stage_h_registry as preregistration  # noqa: E402
import run_invariant_bundle_benchmarks as stage_e  # noqa: E402
import run_submission_candidate_stable_bundles as stable  # noqa: E402
from qp_orbits.artifact_fingerprints import (  # noqa: E402
    artifact_fingerprint,
    fingerprint_matches,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_states_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.ephemeris import MOON_RADIUS_KM  # noqa: E402
from qp_orbits.variational import integrate_states_and_stms  # noqa: E402


STAGE_H = ROOT / "research" / "invariant_bundles" / "submission_candidate"
H1_REGISTRY = STAGE_H / "benchmarks" / "stage_h_case_registry.csv"
STAGE_C_REGISTRY = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "benchmarks"
    / "benchmark_registry.csv"
)
STABLE_CSV = STAGE_H / "results" / "stable_bundles" / "stable_bundle_comparison.csv"
STABLE_NPZ = STAGE_H / "results" / "stable_bundles" / "stable_bundle_results.npz"

OUTPUT_DIR = STAGE_H / "results" / "long_propagation"
ATTEMPTS_CSV = OUTPUT_DIR / "long_propagation_attempts.csv"
EVENTS_CSV = OUTPUT_DIR / "long_propagation_events.csv"
TRAJECTORIES_CSV = OUTPUT_DIR / "long_propagation_trajectory_events.csv"
RESULTS_NPZ = OUTPUT_DIR / "long_propagation_results.npz"
SUMMARY = OUTPUT_DIR / "long_propagation_summary.json"
CHECKPOINT = OUTPUT_DIR / "long_propagation_checkpoint.json"
ENVIRONMENT = OUTPUT_DIR / "environment.json"
AUDIT = OUTPUT_DIR / "long_propagation_audit.md"
FAILURE_EVIDENCE = OUTPUT_DIR / "failure_evidence.md"
ARTIFACT_HASHES = OUTPUT_DIR / "artifact_hashes.csv"

SCHEMA_VERSION = "submission_candidate_long_propagation_v1"
CASES = (
    "h4_long_stable_em_halo_12p40_n45",
    "h4_long_stable_em_vertical_12p66_n57",
    "h4_long_stable_se_active_geometry_member_468",
)
H2_CASE = {
    "h4_long_stable_em_halo_12p40_n45": "h2_stable_em_halo_12p40_n45",
    "h4_long_stable_em_vertical_12p66_n57": "h2_stable_em_vertical_12p66_n57",
    "h4_long_stable_se_active_geometry_member_468": (
        "h2_stable_se_active_geometry_member_468"
    ),
}
METHODS = (
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
)
SIGNS = (-1, 1)
PERTURBATION = 1.0e-7
MAPPING_PERIODS = 3
TIME_SAMPLES = 121
JACOBI_LIMIT = 1.0e-10
LOCAL_LINEAR_ERROR_LIMIT = 0.05
LOCAL_LINEAR_MULTIPLE = 100.0
LOCAL_EXIT_THRESHOLD = 1.0e-4
GLOBAL_EXIT_THRESHOLD = 1.0e-2
FAR_FIELD_THRESHOLD = 1.0e-1
EARTH_RADIUS_KM = 6378.1363
SECONDARY_RADIUS_KM = {
    "earth_moon": MOON_RADIUS_KM,
    "sun_earth": EARTH_RADIUS_KM,
}

ATTEMPT_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "source_case_id",
    "method",
    "perturbation_sign",
    "attempt_index",
    "rtol",
    "atol",
    "max_step",
    "success",
    "integrator_message",
    "jacobi_drift",
    "secondary_min_distance_km",
    "secondary_radius_crossing_trajectories",
    "runtime_seconds",
    "selected_for_final",
    "retry_trigger",
    "h1_registry_sha256",
    "stable_bundle_npz_sha256",
    "source_git_commit",
)

EVENT_FIELDS = (
    "schema_version",
    "run_id",
    "stable_bundle_run_id",
    "case_id",
    "source_case_id",
    "family",
    "system",
    "method",
    "branch",
    "propagation_direction",
    "duration_mapping_periods",
    "spectral_samples",
    "perturbation_sign",
    "perturbation_norm",
    "propagation_time_nd",
    "propagation_time_days",
    "time_samples",
    "coordinate_system",
    "integrator",
    "event_condition",
    "bundle_research_status",
    "bundle_invariance_residual_max",
    "direction_principal_angle_max_deg_to_qr",
    "branch_sign_consistent",
    "attempts_executed",
    "selected_attempt_index",
    "selected_rtol",
    "selected_atol",
    "selected_max_step",
    "manifold_jacobi_drift",
    "local_linear_sample_count",
    "local_linear_max_relative_error",
    "final_separation_median_nd",
    "final_separation_max_nd",
    "final_linear_ratio_median",
    "final_linear_ratio_max",
    "primary_min_distance_km",
    "secondary_min_distance_km",
    "secondary_min_distance_elapsed_days",
    "secondary_radius_km",
    "secondary_radius_crossing_trajectories",
    "secondary_radius_crossing_fraction",
    "barycentric_radius_max_nd",
    "local_exit_threshold_nd",
    "local_exit_trajectory_count",
    "local_exit_elapsed_days_min",
    "local_exit_elapsed_days_median",
    "local_exit_elapsed_days_max",
    "global_exit_threshold_nd",
    "global_exit_trajectory_count",
    "global_exit_elapsed_days_min",
    "global_exit_elapsed_days_median",
    "global_exit_elapsed_days_max",
    "far_field_threshold_nd",
    "far_field_trajectory_count",
    "far_field_elapsed_days_min",
    "far_field_elapsed_days_median",
    "far_field_elapsed_days_max",
    "runtime_seconds",
    "status",
    "failure_reason",
    "h1_registry_sha256",
    "stable_bundle_npz_sha256",
    "state_artifact_sha256",
    "source_git_commit",
)

TRAJECTORY_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "source_case_id",
    "method",
    "perturbation_sign",
    "phase_index",
    "phase_rad",
    "local_exit_crossed",
    "local_exit_elapsed_days",
    "global_exit_crossed",
    "global_exit_elapsed_days",
    "far_field_crossed",
    "far_field_elapsed_days",
    "primary_min_distance_km",
    "primary_min_distance_elapsed_days",
    "secondary_min_distance_km",
    "secondary_min_distance_elapsed_days",
    "secondary_radius_crossed",
    "final_separation_nd",
    "max_separation_nd",
    "source_git_commit",
)

HASH_FIELDS = ("artifact", "hash_mode", "bytes", "sha256")


def _rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (float, np.floating)):
        return format(float(value), ".16g")
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _write_csv(
    path: Path,
    fields: tuple[str, ...],
    rows: list[Mapping[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row[field]) for field in fields})


def _sanitize(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


def _key(case_id: str, method: str, sign: int) -> str:
    prefix = f"{_sanitize(case_id)}__{_sanitize(method)}__sign_{sign:+d}"
    return prefix.replace("+", "p").replace("-", "m")


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _run_id() -> str:
    digest = hashlib.sha256()
    for path in (H1_REGISTRY, STAGE_C_REGISTRY, STABLE_CSV, STABLE_NPZ, Path(__file__)):
        digest.update(artifact_fingerprint(path).sha256.encode("ascii"))
    return digest.hexdigest().upper()[:20]


def _load_basis(
    archive: np.lib.npyio.NpzFile,
    h2_case_id: str,
    method: str,
) -> np.ndarray:
    key = f"{_sanitize(h2_case_id)}__{_sanitize(method)}__bases"
    if key not in archive.files:
        raise RuntimeError(f"missing H2 stable basis: {key}")
    bases = np.asarray(archive[key], dtype=float)
    if bases.ndim != 3 or bases.shape[1:] != (6, 1):
        raise RuntimeError(f"H2 stable basis shape drifted: {key}")
    return bases[:, :, 0]


def _first_crossing_elapsed_days(
    values: np.ndarray,
    threshold: float,
    elapsed_days: np.ndarray,
) -> tuple[bool, float]:
    indices = np.flatnonzero(values >= threshold)
    if indices.size == 0:
        return False, float("nan")
    return True, float(elapsed_days[int(indices[0])])


def _event_time_summary(values: list[float]) -> tuple[int, float, float, float]:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=float)
    if finite.size == 0:
        return 0, float("nan"), float("nan"), float("nan")
    return (
        int(finite.size),
        float(np.min(finite)),
        float(np.median(finite)),
        float(np.max(finite)),
    )


def _attempt_metrics(
    history: np.ndarray,
    *,
    mu: float,
    length_unit_km: float,
    secondary_radius_km: float,
) -> dict[str, Any]:
    jacobi = jacobi_constant(history.reshape(-1, 6), mu).reshape(
        history.shape[0], history.shape[1]
    )
    jacobi_drift = float(np.max(np.abs(jacobi - jacobi[0][None, :])))
    secondary = np.array([1.0 - mu, 0.0, 0.0])
    secondary_distance = np.linalg.norm(
        history[:, :, :3] - secondary, axis=2
    )
    minimum_by_trajectory = np.min(secondary_distance, axis=0) * length_unit_km
    return {
        "jacobi_drift": jacobi_drift,
        "secondary_min_distance_km": float(np.min(minimum_by_trajectory)),
        "secondary_radius_crossing_trajectories": int(
            np.sum(minimum_by_trajectory <= secondary_radius_km)
        ),
    }


def _write_checkpoint(payload: Mapping[str, Any]) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_environment(commit: str, run_id: str) -> None:
    payload = {
        "schema_version": "submission_candidate_long_propagation_environment_v1",
        "run_id": run_id,
        "source_git_commit": commit,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "moon_radius_km": MOON_RADIUS_KM,
        "earth_radius_km": EARTH_RADIUS_KM,
        "secondary_radius_semantics": "sampled-history physical-radius diagnostic",
    }
    ENVIRONMENT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_audit(
    rows: list[Mapping[str, Any]],
    attempts: list[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    lines = [
        "# Stage H4 three-map long-propagation audit",
        "",
        f"- Run ID: {summary['run_id']}",
        f"- Cases: {summary['cases']}",
        f"- Stored method/sign rows: {summary['event_rows']}",
        f"- Attempt rows including retries: {summary['attempt_rows']}",
        f"- Status counts: {summary['status_counts']}",
        f"- Cases with a collision-free accepted row: {summary['cases_with_collision_free_accepted_row']}",
        f"- H4 gate: {summary['h4_gate_status']}",
        "",
        "## Three-map results",
        "",
        "| case | method | sign | Jacobi drift | local exit median days | global exit median days | secondary minimum km | collisions | status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['method']} | {row['perturbation_sign']} | "
            f"{float(row['manifold_jacobi_drift']):.3e} | "
            f"{float(row['local_exit_elapsed_days_median']):.3f} | "
            f"{float(row['global_exit_elapsed_days_median']):.3f} | "
            f"{float(row['secondary_min_distance_km']):.3f} | "
            f"{row['secondary_radius_crossing_trajectories']} | {row['status']} |"
        )
    retry_rows = [row for row in attempts if int(row["attempt_index"]) > 1]
    lines += [
        "",
        "## Numerical retries",
        "",
        f"The preregistered one-retry allowance was used in {len(retry_rows)} method/sign cells.",
        "Retries use rtol=3e-13, atol=3e-15, and max_step=0.001 after",
        "an initial Jacobi drift above 1e-10. Initial attempts remain in the CSV",
        "and both attempt histories remain in the NPZ archive.",
        "",
        "## Event semantics and interpretation boundary",
        "",
        "All trajectories are propagated for exactly three mapping periods; events",
        "are diagnostics and do not terminate integration. Local, global, and far",
        "exits are first sampled crossings of separation 1e-4, 1e-2, and 1e-1.",
        "Secondary-radius crossings use the 121 stored time samples, so a collision",
        "flag is a positive boundary finding but collision_free is not a continuous",
        "minimum-distance proof. Far-field nonlinear/STM ratios are diagnostic only.",
        "Rows entering the secondary physical radius are boundary, not accepted.",
        "",
        "This H4 research campaign does not alter the frozen 54-figure baseline,",
        "the Chapter 4 projection holdout, or any paper-equivalence label.",
        "",
    ]
    AUDIT.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _write_failure_evidence(
    rows: list[Mapping[str, Any]],
    attempts: list[Mapping[str, Any]],
) -> None:
    nonaccepted = [row for row in rows if row["status"] != "accepted"]
    retried_initial = [
        row
        for row in attempts
        if int(row["attempt_index"]) == 1 and row["selected_for_final"] is False
    ]
    lines = [
        "# Stage H4 boundary and retry evidence",
        "",
        f"- Non-accepted final rows retained: {len(nonaccepted)}",
        f"- Superseded initial attempts retained: {len(retried_initial)}",
        "",
    ]
    for row in nonaccepted:
        lines.append(
            f"- {row['case_id']} / {row['method']} / sign={row['perturbation_sign']}: "
            f"{row['status']} - {row['failure_reason']} "
            f"(secondary minimum {float(row['secondary_min_distance_km']):.3f} km)"
        )
    lines += [
        "",
        "Every initial high-drift close-approach attempt is retained in",
        "long_propagation_attempts.csv. A tighter retry improves numerical",
        "conservation but does not erase the physical-radius boundary.",
        "",
    ]
    FAILURE_EVIDENCE.write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def _write_artifact_hashes() -> None:
    artifacts = (
        ATTEMPTS_CSV,
        EVENTS_CSV,
        TRAJECTORIES_CSV,
        RESULTS_NPZ,
        SUMMARY,
        CHECKPOINT,
        ENVIRONMENT,
        AUDIT,
        FAILURE_EVIDENCE,
    )
    rows: list[dict[str, Any]] = []
    for path in artifacts:
        fingerprint = artifact_fingerprint(path)
        rows.append(
            {
                "artifact": _rel(path),
                "hash_mode": fingerprint.hash_mode,
                "bytes": fingerprint.bytes,
                "sha256": fingerprint.sha256,
            }
        )
    _write_csv(ARTIFACT_HASHES, HASH_FIELDS, rows)


def run_campaign(*, max_wall_seconds: float) -> None:
    preregistration.check_outputs()
    stable.check_outputs()
    h1_rows = {
        row["case_id"]: row
        for row in _read_csv(H1_REGISTRY)
        if row["campaign"] == "H4_long_propagation"
    }
    if tuple(h1_rows) != CASES:
        raise RuntimeError("the H4 case order drifted")
    cap = min(float(row["max_wall_seconds"]) for row in h1_rows.values())
    if max_wall_seconds <= 0.0 or max_wall_seconds > cap:
        raise ValueError(f"max-wall-seconds must be in (0, {cap}]")
    for row in h1_rows.values():
        if int(row["duration_mapping_periods"]) != MAPPING_PERIODS:
            raise RuntimeError("H4 mapping-period count drifted")
        if int(row["time_samples"]) != TIME_SAMPLES:
            raise RuntimeError("H4 time-sample count drifted")
        if int(row["max_retries"]) != 1:
            raise RuntimeError("H4 retry allowance drifted")

    stage_c_rows = _read_csv(STAGE_C_REGISTRY)
    stage_c_index = {row["case_id"]: row for row in stage_c_rows}
    stable_rows = _read_csv(STABLE_CSV)
    stable_index = {(row["case_id"], row["method"]): row for row in stable_rows}
    stable_run_ids = {row["run_id"] for row in stable_rows}
    if len(stable_run_ids) != 1:
        raise RuntimeError("H2 stable rows contain mixed run IDs")
    stable_bundle_run_id = next(iter(stable_run_ids))
    h1_hash = artifact_fingerprint(H1_REGISTRY).sha256
    stable_npz_hash = artifact_fingerprint(STABLE_NPZ).sha256
    run_id = _run_id()
    commit = _git_commit()
    campaign_started = time.perf_counter()
    attempts: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    trajectory_rows: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "run_id": np.asarray([run_id]),
        "stable_bundle_run_id": np.asarray([stable_bundle_run_id]),
        "case_ids": np.asarray(CASES),
        "methods": np.asarray(METHODS),
        "signs": np.asarray(SIGNS),
        "perturbation_norm": np.asarray([PERTURBATION]),
        "exit_thresholds": np.asarray(
            [LOCAL_EXIT_THRESHOLD, GLOBAL_EXIT_THRESHOLD, FAR_FIELD_THRESHOLD]
        ),
        "h1_registry_sha256": np.asarray([h1_hash]),
        "stable_bundle_npz_sha256": np.asarray([stable_npz_hash]),
        "source_git_commit": np.asarray([commit]),
    }
    completed_cases: list[str] = []

    with np.load(STABLE_NPZ, allow_pickle=False) as stable_archive:
        for case_index, case_id in enumerate(CASES, start=1):
            if time.perf_counter() - campaign_started > max_wall_seconds:
                _write_checkpoint(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": run_id,
                        "status": "wall_time_cap_reached",
                        "completed_cases": completed_cases,
                        "max_wall_seconds": max_wall_seconds,
                    }
                )
                raise RuntimeError("H4 campaign reached the preregistered cap")
            case = h1_rows[case_id]
            source = stage_c_index[case["source_case_id"]]
            states, phases = stage_e._load_states(source)
            system = SYSTEMS[source["system"]]
            if system.time_unit_days is None or system.length_unit_km is None:
                raise RuntimeError("H4 system lacks physical unit scales")
            duration_days = MAPPING_PERIODS * float(source["mapping_time"])
            duration = -duration_days / system.time_unit_days
            evaluation_times = np.linspace(0.0, duration, TIME_SAMPLES)
            elapsed_days = np.abs(evaluation_times) * system.time_unit_days
            default_max_step = 0.005 if source["system"] == "sun_earth" else 0.01
            base_solution = integrate_states_and_stms(
                states,
                (0.0, duration),
                system.mu,
                t_eval=evaluation_times,
                max_step=default_max_step,
            )
            if not base_solution.success:
                raise RuntimeError(base_solution.message)
            base_values = base_solution.y.T.reshape(TIME_SAMPLES, states.shape[0], 42)
            base_history = base_values[:, :, :6]
            state_transition_history = base_values[:, :, 6:].reshape(
                TIME_SAMPLES, states.shape[0], 6, 6
            )
            case_prefix = _sanitize(case_id)
            arrays[case_prefix + "__times_nd"] = evaluation_times
            arrays[case_prefix + "__elapsed_days"] = elapsed_days
            arrays[case_prefix + "__base_states"] = base_history
            h2_case_id = H2_CASE[case_id]
            qr_direction = _load_basis(stable_archive, h2_case_id, METHODS[1])
            secondary_radius_km = SECONDARY_RADIUS_KM[source["system"]]
            primary_position = np.array([-system.mu, 0.0, 0.0])
            secondary_position = np.array([1.0 - system.mu, 0.0, 0.0])

            for method in METHODS:
                bundle_meta = stable_index[(h2_case_id, method)]
                direction = _load_basis(stable_archive, h2_case_id, method)
                dots = np.sum(direction * qr_direction, axis=1)
                if float(np.mean(dots)) < 0.0:
                    direction *= -1.0
                    dots *= -1.0
                direction_angle = float(
                    np.max(
                        np.degrees(
                            np.arccos(np.clip(np.abs(dots), 0.0, 1.0))
                        )
                    )
                )
                branch_consistent = bool(np.all(dots > 0.0))
                arrays[f"{case_prefix}__{_sanitize(method)}__directions"] = direction

                for sign in SIGNS:
                    cell_started = time.perf_counter()
                    initial = states + float(sign) * PERTURBATION * direction
                    attempt_configs = (
                        (1, 1.0e-11, 1.0e-13, default_max_step),
                        (2, 3.0e-13, 3.0e-15, 0.001),
                    )
                    cell_attempts: list[tuple[dict[str, Any], np.ndarray | None]] = []
                    retry_trigger = ""
                    for attempt_index, rtol, atol, max_step in attempt_configs:
                        started = time.perf_counter()
                        solution = integrate_states_cr3bp(
                            initial,
                            (0.0, duration),
                            system.mu,
                            t_eval=evaluation_times,
                            rtol=rtol,
                            atol=atol,
                            max_step=max_step,
                        )
                        runtime = time.perf_counter() - started
                        complete = bool(
                            solution.success and solution.y.shape[1] == TIME_SAMPLES
                        )
                        history: np.ndarray | None = None
                        metrics = {
                            "jacobi_drift": float("nan"),
                            "secondary_min_distance_km": float("nan"),
                            "secondary_radius_crossing_trajectories": 0,
                        }
                        if complete:
                            history = solution.y.T.reshape(
                                TIME_SAMPLES, states.shape[0], 6
                            )
                            metrics = _attempt_metrics(
                                history,
                                mu=system.mu,
                                length_unit_km=system.length_unit_km,
                                secondary_radius_km=secondary_radius_km,
                            )
                        attempt_row: dict[str, Any] = {
                            "schema_version": SCHEMA_VERSION,
                            "run_id": run_id,
                            "case_id": case_id,
                            "source_case_id": source["case_id"],
                            "method": method,
                            "perturbation_sign": sign,
                            "attempt_index": attempt_index,
                            "rtol": rtol,
                            "atol": atol,
                            "max_step": max_step,
                            "success": complete,
                            "integrator_message": solution.message,
                            "jacobi_drift": metrics["jacobi_drift"],
                            "secondary_min_distance_km": metrics[
                                "secondary_min_distance_km"
                            ],
                            "secondary_radius_crossing_trajectories": metrics[
                                "secondary_radius_crossing_trajectories"
                            ],
                            "runtime_seconds": runtime,
                            "selected_for_final": False,
                            "retry_trigger": retry_trigger,
                            "h1_registry_sha256": h1_hash,
                            "stable_bundle_npz_sha256": stable_npz_hash,
                            "source_git_commit": commit,
                        }
                        attempts.append(attempt_row)
                        cell_attempts.append((attempt_row, history))
                        if history is not None:
                            attempt_key = (
                                _key(case_id, method, sign)
                                + f"__attempt_{attempt_index}__manifold_states"
                            )
                            arrays[attempt_key] = history
                        if complete and float(metrics["jacobi_drift"]) <= JACOBI_LIMIT:
                            break
                        retry_trigger = (
                            "integrator_incomplete"
                            if not complete
                            else "jacobi_drift_gt_1e-10"
                        )

                    successful = [item for item in cell_attempts if item[1] is not None]
                    if not successful:
                        selected_row, selected_history = cell_attempts[-1]
                    else:
                        selected_row, selected_history = min(
                            successful, key=lambda item: float(item[0]["jacobi_drift"])
                        )
                    selected_row["selected_for_final"] = True
                    common: dict[str, Any] = {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": run_id,
                        "stable_bundle_run_id": stable_bundle_run_id,
                        "case_id": case_id,
                        "source_case_id": source["case_id"],
                        "family": source["family"],
                        "system": source["system"],
                        "method": method,
                        "branch": "stable",
                        "propagation_direction": "backward",
                        "duration_mapping_periods": MAPPING_PERIODS,
                        "spectral_samples": states.shape[0],
                        "perturbation_sign": sign,
                        "perturbation_norm": PERTURBATION,
                        "propagation_time_nd": duration,
                        "propagation_time_days": -duration_days,
                        "time_samples": TIME_SAMPLES,
                        "coordinate_system": "cr3bp_synodic_rotating_nondimensional",
                        "integrator": "DOP853_adaptive_with_one_tight_retry",
                        "event_condition": case["event_condition"],
                        "bundle_research_status": bundle_meta["research_status"],
                        "bundle_invariance_residual_max": float(
                            bundle_meta["max_invariance_residual"]
                        ),
                        "direction_principal_angle_max_deg_to_qr": direction_angle,
                        "branch_sign_consistent": branch_consistent,
                        "attempts_executed": len(cell_attempts),
                        "selected_attempt_index": int(selected_row["attempt_index"]),
                        "selected_rtol": float(selected_row["rtol"]),
                        "selected_atol": float(selected_row["atol"]),
                        "selected_max_step": float(selected_row["max_step"]),
                        "local_exit_threshold_nd": LOCAL_EXIT_THRESHOLD,
                        "global_exit_threshold_nd": GLOBAL_EXIT_THRESHOLD,
                        "far_field_threshold_nd": FAR_FIELD_THRESHOLD,
                        "secondary_radius_km": secondary_radius_km,
                        "h1_registry_sha256": h1_hash,
                        "stable_bundle_npz_sha256": stable_npz_hash,
                        "state_artifact_sha256": case["state_artifact_sha256"],
                        "source_git_commit": commit,
                    }
                    if selected_history is None:
                        event_rows.append(
                            {
                                **common,
                                "manifold_jacobi_drift": float("nan"),
                                "local_linear_sample_count": 0,
                                "local_linear_max_relative_error": float("nan"),
                                "final_separation_median_nd": float("nan"),
                                "final_separation_max_nd": float("nan"),
                                "final_linear_ratio_median": float("nan"),
                                "final_linear_ratio_max": float("nan"),
                                "primary_min_distance_km": float("nan"),
                                "secondary_min_distance_km": float("nan"),
                                "secondary_min_distance_elapsed_days": float("nan"),
                                "secondary_radius_crossing_trajectories": 0,
                                "secondary_radius_crossing_fraction": float("nan"),
                                "barycentric_radius_max_nd": float("nan"),
                                "local_exit_trajectory_count": 0,
                                "local_exit_elapsed_days_min": float("nan"),
                                "local_exit_elapsed_days_median": float("nan"),
                                "local_exit_elapsed_days_max": float("nan"),
                                "global_exit_trajectory_count": 0,
                                "global_exit_elapsed_days_min": float("nan"),
                                "global_exit_elapsed_days_median": float("nan"),
                                "global_exit_elapsed_days_max": float("nan"),
                                "far_field_trajectory_count": 0,
                                "far_field_elapsed_days_min": float("nan"),
                                "far_field_elapsed_days_median": float("nan"),
                                "far_field_elapsed_days_max": float("nan"),
                                "runtime_seconds": time.perf_counter() - cell_started,
                                "status": "bounded_fail",
                                "failure_reason": "integrator_incomplete_after_one_retry",
                            }
                        )
                        continue

                    history = selected_history
                    separation = np.linalg.norm(history - base_history, axis=2)
                    linear = np.einsum(
                        "tnij,nj->tni",
                        state_transition_history,
                        float(sign) * PERTURBATION * direction,
                    )
                    linear_separation = np.linalg.norm(linear, axis=2)
                    ratios = separation[1:] / np.maximum(
                        linear_separation[1:], np.finfo(float).tiny
                    )
                    local_mask = (
                        linear_separation[1:]
                        <= LOCAL_LINEAR_MULTIPLE * PERTURBATION
                    )
                    local_error = float(
                        np.max(np.abs(ratios[local_mask] - 1.0))
                    ) if np.any(local_mask) else float("nan")
                    primary_distance = np.linalg.norm(
                        history[:, :, :3] - primary_position, axis=2
                    )
                    secondary_distance = np.linalg.norm(
                        history[:, :, :3] - secondary_position, axis=2
                    )
                    barycentric_radius = np.linalg.norm(history[:, :, :3], axis=2)
                    local_times: list[float] = []
                    global_times: list[float] = []
                    far_times: list[float] = []
                    collision_count = 0
                    for phase_index, phase in enumerate(phases):
                        local_crossed, local_time = _first_crossing_elapsed_days(
                            separation[:, phase_index],
                            LOCAL_EXIT_THRESHOLD,
                            elapsed_days,
                        )
                        global_crossed, global_time = _first_crossing_elapsed_days(
                            separation[:, phase_index],
                            GLOBAL_EXIT_THRESHOLD,
                            elapsed_days,
                        )
                        far_crossed, far_time = _first_crossing_elapsed_days(
                            separation[:, phase_index],
                            FAR_FIELD_THRESHOLD,
                            elapsed_days,
                        )
                        local_times.append(local_time)
                        global_times.append(global_time)
                        far_times.append(far_time)
                        primary_index = int(np.argmin(primary_distance[:, phase_index]))
                        secondary_index = int(
                            np.argmin(secondary_distance[:, phase_index])
                        )
                        secondary_min_km = float(
                            secondary_distance[secondary_index, phase_index]
                            * system.length_unit_km
                        )
                        collision = bool(secondary_min_km <= secondary_radius_km)
                        collision_count += int(collision)
                        trajectory_rows.append(
                            {
                                "schema_version": SCHEMA_VERSION,
                                "run_id": run_id,
                                "case_id": case_id,
                                "source_case_id": source["case_id"],
                                "method": method,
                                "perturbation_sign": sign,
                                "phase_index": phase_index,
                                "phase_rad": phase,
                                "local_exit_crossed": local_crossed,
                                "local_exit_elapsed_days": local_time,
                                "global_exit_crossed": global_crossed,
                                "global_exit_elapsed_days": global_time,
                                "far_field_crossed": far_crossed,
                                "far_field_elapsed_days": far_time,
                                "primary_min_distance_km": float(
                                    primary_distance[primary_index, phase_index]
                                    * system.length_unit_km
                                ),
                                "primary_min_distance_elapsed_days": float(
                                    elapsed_days[primary_index]
                                ),
                                "secondary_min_distance_km": secondary_min_km,
                                "secondary_min_distance_elapsed_days": float(
                                    elapsed_days[secondary_index]
                                ),
                                "secondary_radius_crossed": collision,
                                "final_separation_nd": float(
                                    separation[-1, phase_index]
                                ),
                                "max_separation_nd": float(
                                    np.max(separation[:, phase_index])
                                ),
                                "source_git_commit": commit,
                            }
                        )
                    local_count, local_min, local_median, local_max = (
                        _event_time_summary(local_times)
                    )
                    global_count, global_min, global_median, global_max = (
                        _event_time_summary(global_times)
                    )
                    far_count, far_min, far_median, far_max = _event_time_summary(
                        far_times
                    )
                    secondary_flat_index = int(np.argmin(secondary_distance))
                    secondary_time_index, _ = np.unravel_index(
                        secondary_flat_index, secondary_distance.shape
                    )
                    jacobi_drift = float(selected_row["jacobi_drift"])
                    reasons: list[str] = []
                    if bundle_meta["research_status"] != "accepted":
                        reasons.append("upstream_stable_bundle_not_accepted")
                    if not branch_consistent:
                        reasons.append("stable_branch_sign_inconsistent")
                    if jacobi_drift > JACOBI_LIMIT:
                        reasons.append("jacobi_drift_gt_1e-10_after_retry")
                    if not np.isfinite(local_error) or local_error > LOCAL_LINEAR_ERROR_LIMIT:
                        reasons.append("local_linear_error_gt_5pct")
                    if reasons:
                        status = "bounded_fail"
                    elif collision_count:
                        status = "boundary"
                        reasons.append("sampled_secondary_physical_radius_crossing")
                    else:
                        status = "accepted"
                    event_rows.append(
                        {
                            **common,
                            "manifold_jacobi_drift": jacobi_drift,
                            "local_linear_sample_count": int(np.sum(local_mask)),
                            "local_linear_max_relative_error": local_error,
                            "final_separation_median_nd": float(
                                np.median(separation[-1])
                            ),
                            "final_separation_max_nd": float(
                                np.max(separation[-1])
                            ),
                            "final_linear_ratio_median": float(
                                np.median(ratios[-1])
                            ),
                            "final_linear_ratio_max": float(np.max(ratios[-1])),
                            "primary_min_distance_km": float(
                                np.min(primary_distance) * system.length_unit_km
                            ),
                            "secondary_min_distance_km": float(
                                np.min(secondary_distance) * system.length_unit_km
                            ),
                            "secondary_min_distance_elapsed_days": float(
                                elapsed_days[secondary_time_index]
                            ),
                            "secondary_radius_crossing_trajectories": collision_count,
                            "secondary_radius_crossing_fraction": (
                                collision_count / states.shape[0]
                            ),
                            "barycentric_radius_max_nd": float(
                                np.max(barycentric_radius)
                            ),
                            "local_exit_trajectory_count": local_count,
                            "local_exit_elapsed_days_min": local_min,
                            "local_exit_elapsed_days_median": local_median,
                            "local_exit_elapsed_days_max": local_max,
                            "global_exit_trajectory_count": global_count,
                            "global_exit_elapsed_days_min": global_min,
                            "global_exit_elapsed_days_median": global_median,
                            "global_exit_elapsed_days_max": global_max,
                            "far_field_trajectory_count": far_count,
                            "far_field_elapsed_days_min": far_min,
                            "far_field_elapsed_days_median": far_median,
                            "far_field_elapsed_days_max": far_max,
                            "runtime_seconds": time.perf_counter() - cell_started,
                            "status": status,
                            "failure_reason": ";".join(reasons),
                        }
                    )
                    cell_key = _key(case_id, method, sign)
                    arrays[cell_key + "__selected_manifold_states"] = history
                    arrays[cell_key + "__separation"] = separation
                    arrays[cell_key + "__linear_separation"] = linear_separation
                    arrays[cell_key + "__primary_distance"] = primary_distance
                    arrays[cell_key + "__secondary_distance"] = secondary_distance

            completed_cases.append(case_id)
            _write_checkpoint(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "status": "running",
                    "completed_cases": completed_cases,
                    "total_cases": len(CASES),
                    "elapsed_seconds": time.perf_counter() - campaign_started,
                    "max_wall_seconds": max_wall_seconds,
                }
            )
            case_statuses = [
                row["status"] for row in event_rows if row["case_id"] == case_id
            ]
            print(
                f"H4 long propagation {case_index}/{len(CASES)} {case_id} "
                f"statuses={dict(Counter(case_statuses))}",
                flush=True,
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(ATTEMPTS_CSV, ATTEMPT_FIELDS, attempts)
    _write_csv(EVENTS_CSV, EVENT_FIELDS, event_rows)
    _write_csv(TRAJECTORIES_CSV, TRAJECTORY_FIELDS, trajectory_rows)
    np.savez_compressed(RESULTS_NPZ, **arrays)
    accepted_cases = {
        row["case_id"] for row in event_rows if row["status"] == "accepted"
    }
    statuses = Counter(str(row["status"]) for row in event_rows)
    gate = bool(
        len(accepted_cases) == len(CASES)
        and not any(row["status"] == "bounded_fail" for row in event_rows)
        and max(float(row["manifold_jacobi_drift"]) for row in event_rows)
        <= JACOBI_LIMIT
    )
    elapsed = time.perf_counter() - campaign_started
    summary = {
        "schema_version": "submission_candidate_long_propagation_summary_v1",
        "run_id": run_id,
        "stable_bundle_run_id": stable_bundle_run_id,
        "status": "complete",
        "cases": len(CASES),
        "methods": len(METHODS),
        "signs": len(SIGNS),
        "attempt_rows": len(attempts),
        "event_rows": len(event_rows),
        "trajectory_rows": len(trajectory_rows),
        "status_counts": dict(statuses),
        "cases_with_collision_free_accepted_row": len(accepted_cases),
        "secondary_radius_boundary_rows": sum(
            row["status"] == "boundary" for row in event_rows
        ),
        "retry_rows": sum(int(row["attempt_index"]) > 1 for row in attempts),
        "maximum_selected_jacobi_drift": max(
            float(row["manifold_jacobi_drift"]) for row in event_rows
        ),
        "h4_gate_status": "pass" if gate else "fail",
        "elapsed_seconds": elapsed,
        "max_wall_seconds": max_wall_seconds,
        "h1_registry_sha256": h1_hash,
        "stable_bundle_npz_sha256": stable_npz_hash,
        "source_git_commit": commit,
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_checkpoint({**summary, "completed_cases": completed_cases})
    _write_environment(commit, run_id)
    _write_audit(event_rows, attempts, summary)
    _write_failure_evidence(event_rows, attempts)
    _write_artifact_hashes()
    print(
        "STAGE-H4 LONG PROPAGATION WRITE PASS "
        f"cases={len(CASES)} rows={len(event_rows)} "
        f"gate={summary['h4_gate_status']} elapsed={elapsed:.3f}s",
        flush=True,
    )


def check_outputs() -> None:
    preregistration.check_outputs()
    stable.check_outputs()
    attempts = _read_csv(ATTEMPTS_CSV)
    rows = _read_csv(EVENTS_CSV)
    trajectories = _read_csv(TRAJECTORIES_CSV)
    expected_events = len(CASES) * len(METHODS) * len(SIGNS)
    expected_trajectories = len(METHODS) * len(SIGNS) * (45 + 57 + 21)
    if len(rows) != expected_events:
        raise RuntimeError("H4 event row count drifted")
    if len(trajectories) != expected_trajectories:
        raise RuntimeError("H4 trajectory-event row count drifted")
    if {row["case_id"] for row in rows} != set(CASES):
        raise RuntimeError("H4 case coverage drifted")
    if {row["method"] for row in rows} != set(METHODS):
        raise RuntimeError("H4 method coverage drifted")
    if {int(row["perturbation_sign"]) for row in rows} != set(SIGNS):
        raise RuntimeError("H4 sign coverage drifted")
    if any(int(row["duration_mapping_periods"]) != 3 for row in rows):
        raise RuntimeError("H4 duration semantics drifted")
    if any(int(row["time_samples"]) != 121 for row in rows):
        raise RuntimeError("H4 time-sample semantics drifted")
    if any(row["branch"] != "stable" for row in rows):
        raise RuntimeError("H4 branch semantics drifted")
    if any(row["propagation_direction"] != "backward" for row in rows):
        raise RuntimeError("H4 propagation direction drifted")
    if any(row["bundle_research_status"] != "accepted" for row in rows):
        raise RuntimeError("H4 used a non-accepted stable bundle")
    if any(row["branch_sign_consistent"] != "true" for row in rows):
        raise RuntimeError("H4 stable direction sign drifted")
    if max(float(row["manifold_jacobi_drift"]) for row in rows) > JACOBI_LIMIT:
        raise RuntimeError("H4 selected propagation violates Jacobi gate")
    if max(float(row["local_linear_max_relative_error"]) for row in rows) > LOCAL_LINEAR_ERROR_LIMIT:
        raise RuntimeError("H4 local linearity diagnostic regressed")
    counts = Counter(row["status"] for row in rows)
    if counts != {"accepted": 8, "boundary": 4}:
        raise RuntimeError(f"H4 accepted/boundary split drifted: {counts}")
    if any(
        int(row["secondary_radius_crossing_trajectories"]) != 0
        for row in rows
        if row["status"] == "accepted"
    ):
        raise RuntimeError("H4 accepted a sampled physical-radius crossing")
    if any(
        int(row["secondary_radius_crossing_trajectories"]) == 0
        for row in rows
        if row["status"] == "boundary"
    ):
        raise RuntimeError("H4 boundary lost its physical-radius evidence")
    if any(int(row["local_exit_trajectory_count"]) == 0 for row in rows):
        raise RuntimeError("H4 local-exit diagnostics are empty")
    if any(int(row["global_exit_trajectory_count"]) == 0 for row in rows):
        raise RuntimeError("H4 global-exit diagnostics are empty")

    if len(attempts) != 16:
        raise RuntimeError("H4 retry-attempt count drifted")
    retries = [row for row in attempts if int(row["attempt_index"]) == 2]
    if len(retries) != 4:
        raise RuntimeError("H4 tight-retry count drifted")
    if any(row["selected_for_final"] != "true" for row in retries):
        raise RuntimeError("H4 tight retry was not selected")
    if any(float(row["jacobi_drift"]) > JACOBI_LIMIT for row in retries):
        raise RuntimeError("H4 tight retry did not clear the Jacobi gate")
    superseded = [
        row
        for row in attempts
        if int(row["attempt_index"]) == 1
        and row["selected_for_final"] == "false"
    ]
    if len(superseded) != 4:
        raise RuntimeError("H4 superseded initial-attempt evidence drifted")

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary["h4_gate_status"] != "pass":
        raise RuntimeError("stored H4 gate is not passing")
    if summary["cases_with_collision_free_accepted_row"] != 3:
        raise RuntimeError("H4 accepted-case count drifted")
    if summary["secondary_radius_boundary_rows"] != 4:
        raise RuntimeError("H4 boundary-row count drifted")

    sample_counts = {
        "h4_long_stable_em_halo_12p40_n45": 45,
        "h4_long_stable_em_vertical_12p66_n57": 57,
        "h4_long_stable_se_active_geometry_member_468": 21,
    }
    with np.load(RESULTS_NPZ, allow_pickle=False) as archive:
        for case_id, samples in sample_counts.items():
            prefix = _sanitize(case_id)
            if archive[prefix + "__base_states"].shape != (121, samples, 6):
                raise RuntimeError("H4 base-state archive shape drifted")
            for method in METHODS:
                for sign in SIGNS:
                    cell = _key(case_id, method, sign)
                    if archive[cell + "__selected_manifold_states"].shape != (
                        121,
                        samples,
                        6,
                    ):
                        raise RuntimeError("H4 selected history shape drifted")
                    if archive[cell + "__separation"].shape != (121, samples):
                        raise RuntimeError("H4 separation shape drifted")
        for row in attempts:
            if row["success"] != "true":
                continue
            key = (
                _key(row["case_id"], row["method"], int(row["perturbation_sign"]))
                + f"__attempt_{int(row['attempt_index'])}__manifold_states"
            )
            if key not in archive.files:
                raise RuntimeError(f"H4 attempt history missing: {key}")

    hash_rows = _read_csv(ARTIFACT_HASHES)
    if len(hash_rows) != 9:
        raise RuntimeError("H4 artifact-hash manifest row count drifted")
    for row in hash_rows:
        path = ROOT / row["artifact"]
        if not fingerprint_matches(
            path,
            expected_bytes=int(row["bytes"]),
            expected_sha256=row["sha256"],
            hash_mode=row["hash_mode"],
        ):
            raise RuntimeError(f"H4 artifact fingerprint mismatch: {path}")
    audit = AUDIT.read_text(encoding="utf-8")
    for marker in (
        "are diagnostics and do not terminate integration",
        "Far-field nonlinear/STM ratios are diagnostic only",
        "does not alter the frozen 54-figure baseline",
    ):
        if marker not in audit:
            raise RuntimeError(f"H4 audit boundary marker missing: {marker}")
    print(
        "STAGE-H4 LONG PROPAGATION CHECK PASS "
        f"cases={len(CASES)} rows={len(rows)} gate=pass",
        flush=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-wall-seconds", type=float, default=3600.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        check_outputs()
    else:
        run_campaign(max_wall_seconds=args.max_wall_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
