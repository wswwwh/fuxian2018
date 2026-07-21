"""Propagate the preregistered Stage-H2 stable bundles backward in time."""

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

import run_invariant_bundle_benchmarks as stage_e  # noqa: E402
import run_invariant_bundle_manifold_convergence as stage_f  # noqa: E402
import run_submission_candidate_stable_bundles as stable  # noqa: E402
from qp_orbits.artifact_fingerprints import (  # noqa: E402
    artifact_fingerprint,
    fingerprint_matches,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_states_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.variational import integrate_states_and_stms  # noqa: E402


STAGE_H = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "submission_candidate"
)
H1_REGISTRY = STAGE_H / "benchmarks" / "stage_h_case_registry.csv"
STAGE_C_REGISTRY = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "benchmarks"
    / "benchmark_registry.csv"
)
STABLE_CSV = (
    STAGE_H
    / "results"
    / "stable_bundles"
    / "stable_bundle_comparison.csv"
)
STABLE_NPZ = (
    STAGE_H
    / "results"
    / "stable_bundles"
    / "stable_bundle_results.npz"
)
OUTPUT_DIR = STAGE_H / "results" / "stable_manifolds"
OUTPUT_CSV = OUTPUT_DIR / "stable_manifold_convergence.csv"
OUTPUT_NPZ = OUTPUT_DIR / "stable_manifold_convergence.npz"
SUMMARY = OUTPUT_DIR / "stable_manifold_summary.json"
CHECKPOINT = OUTPUT_DIR / "stable_manifold_checkpoint.json"
ENVIRONMENT = OUTPUT_DIR / "environment.json"
AUDIT = OUTPUT_DIR / "stable_manifold_audit.md"
FAILURE_EVIDENCE = OUTPUT_DIR / "failure_evidence.md"
ARTIFACT_HASHES = OUTPUT_DIR / "artifact_hashes.csv"

SCHEMA_VERSION = "submission_candidate_stable_manifold_v1"
CASES = stable.EXPECTED_CASES
METHODS = stable.METHODS
PERTURBATIONS = (5.0e-8, 1.0e-7, 2.0e-7)
SIGNS = (-1, 1)
NOMINAL_PERTURBATION = 1.0e-7
JACOBI_DRIFT_LIMIT = 1.0e-10
INITIAL_LINEAR_RATIO_TOLERANCE = 0.05

FIELDS = (
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
    "bundle_dimension",
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
    "manifold_jacobi_drift",
    "initial_linear_growth_ratio",
    "final_linear_growth_ratio",
    "backward_growth_factor_mean",
    "backward_growth_factor_max",
    "normalized_3d_manifold_distance_to_qr",
    "normalized_displacement_distance_to_qr",
    "normalized_displacement_perturbation_sensitivity",
    "runtime_seconds",
    "status",
    "failure_reason",
    "h1_registry_sha256",
    "stable_bundle_npz_sha256",
    "state_artifact_sha256",
    "source_git_commit",
)

HASH_FIELDS = (
    "artifact",
    "hash_mode",
    "bytes",
    "sha256",
)


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
        writer = csv.DictWriter(
            stream,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row[field]) for field in fields})


def _sanitize(value: str) -> str:
    return "".join(
        character if character.isalnum() else "_" for character in value
    )


def _key(case_id: str, method: str) -> str:
    return f"{_sanitize(case_id)}__{_sanitize(method)}"


def _run_id() -> str:
    digest = hashlib.sha256()
    for path in (
        H1_REGISTRY,
        STABLE_CSV,
        STABLE_NPZ,
        Path(__file__),
    ):
        digest.update(artifact_fingerprint(path).sha256.encode("ascii"))
    return digest.hexdigest().upper()[:20]


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _load_bundle_bases(
    archive: np.lib.npyio.NpzFile,
    case_id: str,
    method: str,
) -> np.ndarray:
    key = _key(case_id, method) + "__bases"
    if key not in archive.files:
        raise RuntimeError(f"missing stable-bundle bases: {key}")
    bases = np.asarray(archive[key], dtype=float)
    if bases.ndim != 3 or bases.shape[1:] != (6, 1):
        raise RuntimeError(f"stable-bundle basis shape drifted: {key}")
    return bases


def _classify(row: Mapping[str, Any]) -> tuple[str, str]:
    reasons: list[str] = []
    if row["bundle_research_status"] == "fail":
        reasons.append("bundle_method_failed_before_manifold")
    if float(row["manifold_jacobi_drift"]) > JACOBI_DRIFT_LIMIT:
        reasons.append("jacobi_drift_gt_1e-10")
    if (
        abs(float(row["initial_linear_growth_ratio"]) - 1.0)
        > INITIAL_LINEAR_RATIO_TOLERANCE
    ):
        reasons.append("initial_linear_growth_ratio_outside_5pct")
    if not bool(row["branch_sign_consistent"]):
        reasons.append("stable_branch_sign_inconsistent")
    if reasons:
        return "fail", ";".join(reasons)
    if row["bundle_research_status"] == "boundary":
        return "boundary", "bundle_method_boundary"
    return "accepted", ""


def _write_checkpoint(payload: Mapping[str, Any]) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_environment(commit: str, run_id: str) -> None:
    payload = {
        "schema_version": "submission_candidate_stable_manifold_environment_v1",
        "run_id": run_id,
        "source_git_commit": commit,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }
    ENVIRONMENT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_audit(
    rows: list[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    nominal = [
        row
        for row in rows
        if math.isclose(
            float(row["perturbation_norm"]),
            NOMINAL_PERTURBATION,
            rel_tol=0.0,
            abs_tol=1.0e-20,
        )
    ]
    lines = [
        "# Stage H2 stable-manifold audit",
        "",
        f"- Run ID: {summary['run_id']}",
        f"- Stable-bundle run ID: {summary['stable_bundle_run_id']}",
        f"- Cases: {summary['cases']}",
        f"- Stored rows: {summary['rows']}",
        f"- Accepted improved-method rows: {summary['accepted_improved_rows']}",
        f"- Cases with both improved methods accepted: {summary['cases_with_both_improved_methods_accepted']}",
        f"- H2 stable-manifold gate: {summary['h2_stable_manifold_gate_status']}",
        "",
        "## Nominal perturbation results",
        "",
        "| case | method | Jacobi drift | initial ratio | backward growth | displacement distance to QR | status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for case_id in CASES:
        for method in METHODS:
            selected = [
                row
                for row in nominal
                if row["case_id"] == case_id and row["method"] == method
            ]
            worst = (
                "fail"
                if any(row["status"] == "fail" for row in selected)
                else "boundary"
                if any(row["status"] == "boundary" for row in selected)
                else "accepted"
            )
            lines.append(
                f"| {case_id} | {method} | "
                f"{max(float(row['manifold_jacobi_drift']) for row in selected):.3e} | "
                f"{np.mean([float(row['initial_linear_growth_ratio']) for row in selected]):.6f} | "
                f"{np.mean([float(row['backward_growth_factor_mean']) for row in selected]):.3e} | "
                f"{max(float(row['normalized_displacement_distance_to_qr']) for row in selected):.3e} | "
                f"{worst} |"
            )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "Stable directions are propagated backward for exactly one mapping period.",
        "This validates the local stable-manifold branch under frozen conditions;",
        "it is not the H4 long-propagation result and does not alter reproduction",
        "or paper-equivalence gates.",
        "",
    ]
    AUDIT.write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n",
    )


def _write_failure_evidence(rows: list[Mapping[str, Any]]) -> None:
    failed = [
        row for row in rows if str(row["status"]) != "accepted"
    ]
    lines = [
        "# Stage H2 stable-manifold failure evidence",
        "",
        f"- Non-accepted rows retained: {len(failed)}",
        "",
    ]
    for row in failed:
        lines.append(
            f"- {row['case_id']} / {row['method']} / "
            f"epsilon={row['perturbation_norm']} / sign={row['perturbation_sign']}: "
            f"{row['status']} - {row['failure_reason']}"
        )
    lines += [
        "",
        "The pointwise baseline failures remain in all perturbation and sign cells.",
        "",
    ]
    FAILURE_EVIDENCE.write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n",
    )


def _write_artifact_hashes() -> None:
    artifacts = (
        OUTPUT_CSV,
        OUTPUT_NPZ,
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
    stable.check_outputs()
    h1_rows = {
        row["case_id"]: row
        for row in _read_csv(H1_REGISTRY)
        if row["campaign"] == "H2_stable_bundle"
    }
    if tuple(h1_rows) != CASES:
        raise RuntimeError("the H2 stable-manifold case order drifted")
    cap = min(float(row["max_wall_seconds"]) for row in h1_rows.values())
    if max_wall_seconds <= 0.0 or max_wall_seconds > cap:
        raise ValueError(f"max-wall-seconds must be in (0, {cap}]")
    stage_c_rows = _read_csv(STAGE_C_REGISTRY)
    stage_c_index = {row["case_id"]: row for row in stage_c_rows}
    bundle_rows = _read_csv(STABLE_CSV)
    bundle_index = {
        (row["case_id"], row["method"]): row for row in bundle_rows
    }
    bundle_run_ids = {row["run_id"] for row in bundle_rows}
    if len(bundle_run_ids) != 1:
        raise RuntimeError("stable-bundle results contain mixed run IDs")
    stable_bundle_run_id = next(iter(bundle_run_ids))
    h1_hash = artifact_fingerprint(H1_REGISTRY).sha256
    stable_npz_hash = artifact_fingerprint(STABLE_NPZ).sha256
    run_id = _run_id()
    commit = _git_commit()
    started_campaign = time.perf_counter()
    records: list[dict[str, Any]] = []
    surfaces: dict[tuple[str, str, float, int], np.ndarray] = {}
    displacements: dict[tuple[str, str, float, int], np.ndarray] = {}
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "run_id": np.asarray([run_id]),
        "stable_bundle_run_id": np.asarray([stable_bundle_run_id]),
        "h1_registry_sha256": np.asarray([h1_hash]),
        "stable_bundle_npz_sha256": np.asarray([stable_npz_hash]),
        "source_git_commit": np.asarray([commit]),
        "perturbations": np.asarray(PERTURBATIONS),
        "signs": np.asarray(SIGNS),
    }
    completed_cases: list[str] = []
    with np.load(STABLE_NPZ, allow_pickle=False) as bundle_archive:
        for case_index, case_id in enumerate(CASES, start=1):
            if time.perf_counter() - started_campaign > max_wall_seconds:
                _write_checkpoint(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": run_id,
                        "status": "wall_time_cap_reached",
                        "completed_cases": completed_cases,
                        "max_wall_seconds": max_wall_seconds,
                    }
                )
                raise RuntimeError(
                    "stable-manifold campaign reached the preregistered wall-time cap"
                )
            preregistered = h1_rows[case_id]
            source_case_id = preregistered["source_case_id"]
            source = stage_c_index[source_case_id]
            states, _ = stage_e._load_states(source)
            system = SYSTEMS[source["system"]]
            duration_days = float(source["mapping_time"])
            duration = duration_days / system.time_unit_days
            evaluation_times = np.linspace(
                0.0,
                -duration,
                int(preregistered["time_samples"]),
            )
            max_step = 0.005 if source["system"] == "sun_earth" else 0.01
            base_solution = integrate_states_and_stms(
                states,
                (0.0, -duration),
                system.mu,
                t_eval=evaluation_times,
                max_step=max_step,
            )
            if not base_solution.success:
                raise RuntimeError(base_solution.message)
            time_samples = evaluation_times.size
            base_values = base_solution.y.T.reshape(
                time_samples,
                states.shape[0],
                42,
            )
            base_history = base_values[:, :, :6]
            stms = base_values[:, :, 6:].reshape(
                time_samples,
                states.shape[0],
                6,
                6,
            )
            arrays[f"{_sanitize(case_id)}__times_nd"] = evaluation_times
            arrays[f"{_sanitize(case_id)}__base_states"] = base_history
            qr_bases = _load_bundle_bases(
                bundle_archive,
                case_id,
                "qr_svd_shifted_cocycle_iteration",
            )
            qr_direction = qr_bases[:, :, 0]
            print(
                f"H2 stable manifold {case_index}/{len(CASES)} "
                f"{case_id} duration={duration_days:.9f}d backward",
                flush=True,
            )
            for method in METHODS:
                method_meta = bundle_index[(case_id, method)]
                bases = _load_bundle_bases(bundle_archive, case_id, method)
                direction = bases[:, :, 0].copy()
                dot = np.sum(direction * qr_direction, axis=1)
                if float(np.mean(dot)) < 0.0:
                    direction *= -1.0
                    dot *= -1.0
                cosines = np.clip(np.abs(dot), 0.0, 1.0)
                direction_angle = float(
                    np.max(np.degrees(np.arccos(cosines)))
                )
                branch_consistent = bool(np.all(dot > 0.0))
                arrays[f"{_key(case_id, method)}__directions"] = direction
                for epsilon in PERTURBATIONS:
                    for sign in SIGNS:
                        run_started = time.perf_counter()
                        initial = (
                            states
                            + float(sign) * epsilon * direction
                        )
                        solution = integrate_states_cr3bp(
                            initial,
                            (0.0, -duration),
                            system.mu,
                            t_eval=evaluation_times,
                            max_step=max_step,
                        )
                        if not solution.success:
                            raise RuntimeError(solution.message)
                        history = solution.y.T.reshape(
                            time_samples,
                            states.shape[0],
                            6,
                        )
                        separation = np.linalg.norm(
                            history - base_history,
                            axis=2,
                        )
                        linear = np.einsum(
                            "tnij,nj->tni",
                            stms,
                            float(sign) * epsilon * direction,
                        )
                        linear_separation = np.linalg.norm(linear, axis=2)
                        ratios = separation[1:] / np.maximum(
                            linear_separation[1:],
                            np.finfo(float).tiny,
                        )
                        jacobi = jacobi_constant(
                            history.reshape(-1, 6),
                            system.mu,
                        ).reshape(time_samples, states.shape[0])
                        jacobi_drift = float(
                            np.max(np.abs(jacobi - jacobi[0][None, :]))
                        )
                        final_growth = separation[-1] / epsilon
                        geometry_key = (case_id, method, epsilon, sign)
                        surfaces[geometry_key] = history[:, :, :3]
                        displacements[geometry_key] = (
                            history[:, :, :3] - base_history[:, :, :3]
                        ) / epsilon
                        prefix = (
                            f"{_key(case_id, method)}__eps_{epsilon:.0e}"
                            f"__sign_{sign:+d}"
                        ).replace("+", "p").replace("-", "m")
                        arrays[prefix + "__manifold_states"] = history
                        arrays[prefix + "__linear_separation"] = (
                            linear_separation
                        )
                        row: dict[str, Any] = {
                            "schema_version": SCHEMA_VERSION,
                            "run_id": run_id,
                            "stable_bundle_run_id": stable_bundle_run_id,
                            "case_id": case_id,
                            "source_case_id": source_case_id,
                            "family": source["family"],
                            "system": source["system"],
                            "method": method,
                            "branch": "stable",
                            "propagation_direction": "backward",
                            "bundle_dimension": 1,
                            "spectral_samples": states.shape[0],
                            "perturbation_sign": sign,
                            "perturbation_norm": epsilon,
                            "propagation_time_nd": -duration,
                            "propagation_time_days": -duration_days,
                            "time_samples": time_samples,
                            "coordinate_system": "cr3bp_synodic_rotating_nondimensional",
                            "integrator": "DOP853_rtol1e-11_atol1e-13",
                            "event_condition": preregistered[
                                "event_condition"
                            ],
                            "bundle_research_status": method_meta[
                                "research_status"
                            ],
                            "bundle_invariance_residual_max": float(
                                method_meta["max_invariance_residual"]
                            ),
                            "direction_principal_angle_max_deg_to_qr": direction_angle,
                            "branch_sign_consistent": branch_consistent,
                            "manifold_jacobi_drift": jacobi_drift,
                            "initial_linear_growth_ratio": float(
                                np.mean(ratios[0])
                            ),
                            "final_linear_growth_ratio": float(
                                np.mean(ratios[-1])
                            ),
                            "backward_growth_factor_mean": float(
                                np.mean(final_growth)
                            ),
                            "backward_growth_factor_max": float(
                                np.max(final_growth)
                            ),
                            "normalized_3d_manifold_distance_to_qr": float(
                                "nan"
                            ),
                            "normalized_displacement_distance_to_qr": float(
                                "nan"
                            ),
                            "normalized_displacement_perturbation_sensitivity": float(
                                "nan"
                            ),
                            "runtime_seconds": time.perf_counter()
                            - run_started,
                            "status": "pending_geometry_comparison",
                            "failure_reason": "",
                            "h1_registry_sha256": h1_hash,
                            "stable_bundle_npz_sha256": stable_npz_hash,
                            "state_artifact_sha256": preregistered[
                                "state_artifact_sha256"
                            ],
                            "source_git_commit": commit,
                        }
                        records.append(row)
            completed_cases.append(case_id)
            _write_checkpoint(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "status": "running",
                    "completed_cases": completed_cases,
                    "total_cases": len(CASES),
                    "elapsed_seconds": time.perf_counter()
                    - started_campaign,
                    "max_wall_seconds": max_wall_seconds,
                }
            )
    record_index = {
        (
            row["case_id"],
            row["method"],
            float(row["perturbation_norm"]),
            int(row["perturbation_sign"]),
        ): row
        for row in records
    }
    for key, row in record_index.items():
        case_id, method, epsilon, sign = key
        qr_key = (
            case_id,
            "qr_svd_shifted_cocycle_iteration",
            epsilon,
            sign,
        )
        _, row["normalized_3d_manifold_distance_to_qr"] = (
            stage_f._symmetric_hd95(
                surfaces[qr_key],
                surfaces[key],
            )
        )
        _, row["normalized_displacement_distance_to_qr"] = (
            stage_f._symmetric_hd95(
                displacements[qr_key],
                displacements[key],
            )
        )
        nominal_key = (
            case_id,
            method,
            NOMINAL_PERTURBATION,
            sign,
        )
        _, row["normalized_displacement_perturbation_sensitivity"] = (
            stage_f._symmetric_hd95(
                displacements[nominal_key],
                displacements[key],
            )
        )
        row["status"], row["failure_reason"] = _classify(row)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(OUTPUT_CSV, FIELDS, records)
    np.savez_compressed(OUTPUT_NPZ, **arrays)
    improved_methods = {
        "ordered_partial_real_schur_tracking",
        "qr_svd_shifted_cocycle_iteration",
    }
    improved = [
        row for row in records if row["method"] in improved_methods
    ]
    cases_with_both = sum(
        all(
            row["status"] == "accepted"
            for row in improved
            if row["case_id"] == case_id
        )
        for case_id in CASES
    )
    counts = Counter(str(row["status"]) for row in records)
    elapsed = time.perf_counter() - started_campaign
    summary = {
        "schema_version": "submission_candidate_stable_manifold_summary_v1",
        "run_id": run_id,
        "stable_bundle_run_id": stable_bundle_run_id,
        "status": "complete",
        "cases": len(CASES),
        "methods": len(METHODS),
        "perturbations": len(PERTURBATIONS),
        "signs": len(SIGNS),
        "rows": len(records),
        "status_counts": dict(counts),
        "accepted_improved_rows": sum(
            row["status"] == "accepted" for row in improved
        ),
        "cases_with_both_improved_methods_accepted": cases_with_both,
        "h2_stable_manifold_gate_status": (
            "pass" if cases_with_both >= 2 else "fail"
        ),
        "elapsed_seconds": elapsed,
        "max_wall_seconds": max_wall_seconds,
        "jacobi_drift_limit": JACOBI_DRIFT_LIMIT,
        "initial_linear_ratio_tolerance": INITIAL_LINEAR_RATIO_TOLERANCE,
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
    _write_audit(records, summary)
    _write_failure_evidence(records)
    _write_artifact_hashes()
    print(
        "STAGE-H2 STABLE MANIFOLD WRITE PASS "
        f"cases={len(CASES)} rows={len(records)} "
        f"gate={summary['h2_stable_manifold_gate_status']} "
        f"elapsed={elapsed:.3f}s",
        flush=True,
    )


def check_outputs() -> None:
    stable.check_outputs()
    rows = _read_csv(OUTPUT_CSV)
    expected_rows = (
        len(CASES) * len(METHODS) * len(PERTURBATIONS) * len(SIGNS)
    )
    if len(rows) != expected_rows:
        raise RuntimeError(
            f"stable-manifold row count {len(rows)} != {expected_rows}"
        )
    if {row["case_id"] for row in rows} != set(CASES):
        raise RuntimeError("stable-manifold case coverage drifted")
    if {row["method"] for row in rows} != set(METHODS):
        raise RuntimeError("stable-manifold method coverage drifted")
    if {row["branch"] for row in rows} != {"stable"}:
        raise RuntimeError("stable-manifold branch semantics drifted")
    if {row["propagation_direction"] for row in rows} != {"backward"}:
        raise RuntimeError("stable-manifold propagation direction drifted")
    h1_hash = artifact_fingerprint(H1_REGISTRY).sha256
    stable_npz_hash = artifact_fingerprint(STABLE_NPZ).sha256
    if any(row["h1_registry_sha256"] != h1_hash for row in rows):
        raise RuntimeError("stable-manifold H1 registry hash drifted")
    if any(
        row["stable_bundle_npz_sha256"] != stable_npz_hash for row in rows
    ):
        raise RuntimeError("stable-manifold bundle input hash drifted")
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary["h2_stable_manifold_gate_status"] != "pass":
        raise RuntimeError("stored H2 stable-manifold gate is not passing")
    if summary["cases_with_both_improved_methods_accepted"] < 2:
        raise RuntimeError("H2 stable-manifold accepted-case count regressed")
    with np.load(OUTPUT_NPZ, allow_pickle=False) as archive:
        if str(archive["h1_registry_sha256"][0]) != h1_hash:
            raise RuntimeError("stable-manifold NPZ H1 hash drifted")
        if str(archive["stable_bundle_npz_sha256"][0]) != stable_npz_hash:
            raise RuntimeError("stable-manifold NPZ bundle hash drifted")
    hash_rows = _read_csv(ARTIFACT_HASHES)
    if len(hash_rows) != 7:
        raise RuntimeError("stable-manifold artifact manifest count drifted")
    for row in hash_rows:
        path = ROOT / row["artifact"]
        if not fingerprint_matches(
            path,
            expected_bytes=int(row["bytes"]),
            expected_sha256=row["sha256"],
            hash_mode=row["hash_mode"],
        ):
            raise RuntimeError(
                f"stable-manifold artifact hash drifted: {_rel(path)}"
            )
    print(
        "STAGE-H2 STABLE MANIFOLD CHECK PASS "
        f"cases={len(CASES)} rows={expected_rows} "
        f"gate={summary['h2_stable_manifold_gate_status']}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-wall-seconds", type=float, default=1800.0)
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
