"""Run the bounded Stage-F manifold convergence campaign on seven cases."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping

import numpy as np
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(SCRIPTS))

import run_invariant_bundle_benchmarks as benchmark  # noqa: E402
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_states_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.variational import integrate_states_and_stms  # noqa: E402


RESEARCH = ROOT / "research" / "invariant_bundles"
REGISTRY = RESEARCH / "benchmarks" / "benchmark_registry.csv"
METHOD_CSV = RESEARCH / "results" / "csv" / "method_comparison.csv"
METHOD_NPZ = RESEARCH / "results" / "npz" / "method_comparison.npz"
OUTPUT_CSV = RESEARCH / "results" / "csv" / "manifold_convergence.csv"
OUTPUT_NPZ = RESEARCH / "results" / "npz" / "manifold_convergence.npz"
CHECKPOINT = RESEARCH / "results" / "logs" / "manifold_campaign_checkpoint.json"
SUMMARY = RESEARCH / "results" / "logs" / "manifold_campaign_summary.json"
AUDIT = (
    RESEARCH
    / "experiments"
    / "manifold_convergence"
    / "stage_f_audit.md"
)

SCHEMA_VERSION = "invariant_bundle_manifold_convergence_v2"
CASES = (
    "em_halo_12p40_n21",
    "em_halo_12p40_n33",
    "em_halo_12p40_n45",
    "em_vertical_12p66_n33",
    "em_vertical_12p66_n45",
    "em_vertical_12p66_n57",
    "se_active_geometry_member_468",
)
METHODS = benchmark.METHODS
PERTURBATIONS = (5.0e-8, 1.0e-7, 2.0e-7)
SIGNS = (-1, 1)
NOMINAL_PERTURBATION = 1.0e-7
TIME_SAMPLES = 41
MAX_CASES = 7
MAX_WALL_SECONDS = 1800.0
JACOBI_DRIFT_LIMIT = 1.0e-10
INITIAL_LINEAR_RATIO_TOLERANCE = 0.05
CROSS_RESOLUTION_DISTANCE_LIMIT = 0.01

GROUPS = {
    "halo_12p40": (
        "em_halo_12p40_n21",
        "em_halo_12p40_n33",
        "em_halo_12p40_n45",
    ),
    "vertical_12p66": (
        "em_vertical_12p66_n33",
        "em_vertical_12p66_n45",
        "em_vertical_12p66_n57",
    ),
}

FIELDS = (
    "schema_version",
    "run_id",
    "bundle_run_id",
    "case_id",
    "family",
    "method",
    "spectral_samples",
    "bundle_dimension",
    "branch",
    "perturbation_sign",
    "perturbation_norm",
    "propagation_time_nd",
    "propagation_time_days",
    "time_samples",
    "coordinate_system",
    "integrator",
    "event_condition",
    "source_map_status",
    "bundle_research_status",
    "bundle_invariance_residual_max",
    "direction_principal_angle_max_deg_to_qr",
    "branch_sign_consistent",
    "manifold_jacobi_drift",
    "initial_linear_growth_ratio",
    "final_linear_growth_ratio",
    "normalized_3d_manifold_distance_to_qr",
    "normalized_displacement_distance_to_qr",
    "normalized_displacement_perturbation_sensitivity",
    "cross_resolution_normalized_3d_distance",
    "cross_resolution_reference_case",
    "runtime_seconds",
    "status",
    "failure_reason",
    "registry_sha256",
    "method_npz_sha256",
    "source_git_commit",
)


def _rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _run_id() -> str:
    digest = hashlib.sha256()
    for path in (REGISTRY, METHOD_NPZ, Path(__file__)):
        digest.update(path.read_bytes())
    return digest.hexdigest().upper()[:20]


def _sanitize(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


def _key(case_id: str, method: str) -> str:
    return f"{_sanitize(case_id)}__{_sanitize(method)}"


def _symmetric_hd95(
    reference: np.ndarray,
    candidate: np.ndarray,
) -> tuple[float, float]:
    ref = np.asarray(reference, dtype=float).reshape(-1, 3)
    cand = np.asarray(candidate, dtype=float).reshape(-1, 3)
    ref_tree = cKDTree(ref)
    cand_tree = cKDTree(cand)
    cand_to_ref = ref_tree.query(cand, k=1, workers=1)[0]
    ref_to_cand = cand_tree.query(ref, k=1, workers=1)[0]
    raw = max(
        float(np.quantile(cand_to_ref, 0.95)),
        float(np.quantile(ref_to_cand, 0.95)),
    )
    diagonal = float(np.linalg.norm(np.ptp(ref, axis=0)))
    if diagonal <= np.finfo(float).tiny:
        diagonal = float(np.linalg.norm(ref, axis=1).max(initial=0.0))
    if diagonal <= np.finfo(float).tiny:
        raise RuntimeError("reference point cloud has zero normalization scale")
    return raw, raw / diagonal


def _duration_days(
    case_id: str,
    registry: Mapping[str, Mapping[str, str]],
) -> float:
    for cases in GROUPS.values():
        if case_id in cases:
            return float(registry[cases[-1]]["mapping_time"])
    return float(registry[case_id]["mapping_time"])


def _load_bundle_bases(
    archive: np.lib.npyio.NpzFile,
    case_id: str,
    method: str,
) -> np.ndarray:
    key = _key(case_id, method) + "__bases"
    if key not in archive.files:
        raise RuntimeError(f"missing stored bundle bases: {key}")
    return np.asarray(archive[key], dtype=float)


def _write_checkpoint(payload: Mapping[str, Any]) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
        reasons.append("branch_sign_inconsistent")
    cross_resolution = float(row["cross_resolution_normalized_3d_distance"])
    if np.isfinite(cross_resolution) and cross_resolution > CROSS_RESOLUTION_DISTANCE_LIMIT:
        reasons.append("cross_resolution_manifold_distance_gt_0p01")
    if reasons:
        return "fail", ";".join(reasons)
    if row["bundle_research_status"] == "boundary":
        return "boundary", "bundle_method_boundary"
    return "accepted", ""


def run_campaign(*, max_wall_seconds: float) -> None:
    if max_wall_seconds <= 0.0 or max_wall_seconds > MAX_WALL_SECONDS:
        raise ValueError(f"max-wall-seconds must be in (0, {MAX_WALL_SECONDS}]")
    registry_rows = _read_csv(REGISTRY)
    registry = {row["case_id"]: row for row in registry_rows}
    if len(CASES) != MAX_CASES or any(case not in registry for case in CASES):
        raise RuntimeError("the frozen Stage-F case set drifted")
    method_rows = _read_csv(METHOD_CSV)
    method_index = {
        (row["case_id"], row["method"]): row for row in method_rows
    }
    if any((case, method) not in method_index for case in CASES for method in METHODS):
        raise RuntimeError("stored bundle results do not cover the Stage-F case set")
    bundle_run_ids = {row["run_id"] for row in method_rows}
    if len(bundle_run_ids) != 1:
        raise RuntimeError("method comparison contains mixed bundle run IDs")
    bundle_run_id = next(iter(bundle_run_ids))
    run_id = _run_id()
    registry_hash = _sha256(REGISTRY)
    method_npz_hash = _sha256(METHOD_NPZ)
    commit = method_rows[0]["source_git_commit"]
    started_campaign = time.perf_counter()
    records: list[dict[str, Any]] = []
    surfaces: dict[tuple[str, str, float, int], np.ndarray] = {}
    displacements: dict[tuple[str, str, float, int], np.ndarray] = {}
    base_surfaces: dict[str, np.ndarray] = {}
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "run_id": np.asarray([run_id]),
        "bundle_run_id": np.asarray([bundle_run_id]),
        "registry_sha256": np.asarray([registry_hash]),
        "method_npz_sha256": np.asarray([method_npz_hash]),
        "source_git_commit": np.asarray([commit]),
        "perturbations": np.asarray(PERTURBATIONS),
        "signs": np.asarray(SIGNS),
    }
    completed: list[str] = []
    with np.load(METHOD_NPZ, allow_pickle=False) as bundle_archive:
        for case_index, case_id in enumerate(CASES, start=1):
            if time.perf_counter() - started_campaign > max_wall_seconds:
                _write_checkpoint(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": run_id,
                        "status": "wall_time_cap_reached",
                        "completed_cases": completed,
                    }
                )
                raise RuntimeError("Stage-F campaign reached the frozen wall-time cap")
            source = registry[case_id]
            states, phases = benchmark._load_states(source)
            system = SYSTEMS[source["system"]]
            duration_days = _duration_days(case_id, registry)
            duration = duration_days / system.time_unit_days
            evaluation_times = np.linspace(0.0, duration, TIME_SAMPLES)
            max_step = 0.005 if source["system"] == "sun_earth" else 0.01
            base_solution = integrate_states_and_stms(
                states,
                (0.0, duration),
                system.mu,
                t_eval=evaluation_times,
                max_step=max_step,
            )
            if not base_solution.success:
                raise RuntimeError(base_solution.message)
            base_values = base_solution.y.T.reshape(TIME_SAMPLES, states.shape[0], 42)
            base_history = base_values[:, :, :6]
            stms = base_values[:, :, 6:].reshape(
                TIME_SAMPLES, states.shape[0], 6, 6
            )
            base_surfaces[case_id] = base_history[:, :, :3]
            arrays[f"{_sanitize(case_id)}__times_nd"] = evaluation_times
            arrays[f"{_sanitize(case_id)}__base_states"] = base_history
            qr_bases = _load_bundle_bases(
                bundle_archive, case_id, "qr_svd_shifted_cocycle_iteration"
            )
            if qr_bases.shape[2] != 1:
                raise RuntimeError(f"Stage-F reference is not 1-D for {case_id}")
            qr_direction = qr_bases[:, :, 0]
            print(
                f"manifold case {case_index}/{len(CASES)} {case_id} "
                f"N={states.shape[0]} duration={duration_days:.9f}d",
                flush=True,
            )
            for method in METHODS:
                method_meta = method_index[(case_id, method)]
                bases = _load_bundle_bases(bundle_archive, case_id, method)
                if bases.shape[2] != 1:
                    raise RuntimeError(
                        f"Stage-F selected case {case_id}/{method} is not a 1-D bundle"
                    )
                direction = bases[:, :, 0].copy()
                dot = np.sum(direction * qr_direction, axis=1)
                if float(np.mean(dot)) < 0.0:
                    direction *= -1.0
                    dot *= -1.0
                cosines = np.clip(np.abs(dot), 0.0, 1.0)
                direction_angle = float(np.max(np.degrees(np.arccos(cosines))))
                branch_consistent = bool(np.all(dot > 0.0))
                arrays[f"{_key(case_id, method)}__directions"] = direction
                for epsilon in PERTURBATIONS:
                    for sign in SIGNS:
                        run_started = time.perf_counter()
                        initial = states + float(sign) * epsilon * direction
                        solution = integrate_states_cr3bp(
                            initial,
                            (0.0, duration),
                            system.mu,
                            t_eval=evaluation_times,
                            max_step=max_step,
                        )
                        if not solution.success:
                            raise RuntimeError(solution.message)
                        history = solution.y.T.reshape(
                            TIME_SAMPLES, states.shape[0], 6
                        )
                        separation = np.linalg.norm(history - base_history, axis=2)
                        linear = np.einsum(
                            "tnij,nj->tni",
                            stms,
                            float(sign) * epsilon * direction,
                        )
                        linear_separation = np.linalg.norm(linear, axis=2)
                        ratios = separation[1:] / np.maximum(
                            linear_separation[1:], np.finfo(float).tiny
                        )
                        initial_ratio = float(np.mean(ratios[0]))
                        final_ratio = float(np.mean(ratios[-1]))
                        jacobi = jacobi_constant(
                            history.reshape(-1, 6), system.mu
                        ).reshape(TIME_SAMPLES, states.shape[0])
                        jacobi_drift = float(
                            np.max(np.abs(jacobi - jacobi[0][None, :]))
                        )
                        geometry_key = (case_id, method, epsilon, sign)
                        surface = history[:, :, :3]
                        displacement = (history[:, :, :3] - base_history[:, :, :3]) / epsilon
                        surfaces[geometry_key] = surface
                        displacements[geometry_key] = displacement
                        array_prefix = (
                            f"{_key(case_id, method)}__eps_{epsilon:.0e}__sign_{sign:+d}"
                            .replace("+", "p")
                            .replace("-", "m")
                        )
                        arrays[array_prefix + "__manifold_states"] = history
                        arrays[array_prefix + "__linear_separation"] = linear_separation
                        records.append(
                            {
                                "schema_version": SCHEMA_VERSION,
                                "run_id": run_id,
                                "bundle_run_id": bundle_run_id,
                                "case_id": case_id,
                                "family": source["family"],
                                "method": method,
                                "spectral_samples": int(source["spectral_samples"]),
                                "bundle_dimension": 1,
                                "branch": "unstable",
                                "perturbation_sign": sign,
                                "perturbation_norm": epsilon,
                                "propagation_time_nd": duration,
                                "propagation_time_days": duration_days,
                                "time_samples": TIME_SAMPLES,
                                "coordinate_system": "cr3bp_synodic_rotating_nondimensional",
                                "integrator": "DOP853_rtol1e-11_atol1e-13",
                                "event_condition": "none_fixed_duration",
                                "source_map_status": method_meta["source_map_status"],
                                "bundle_research_status": method_meta["research_status"],
                                "bundle_invariance_residual_max": float(
                                    method_meta["max_invariance_residual"]
                                ),
                                "direction_principal_angle_max_deg_to_qr": direction_angle,
                                "branch_sign_consistent": branch_consistent,
                                "manifold_jacobi_drift": jacobi_drift,
                                "initial_linear_growth_ratio": initial_ratio,
                                "final_linear_growth_ratio": final_ratio,
                                "normalized_3d_manifold_distance_to_qr": float("nan"),
                                "normalized_displacement_distance_to_qr": float("nan"),
                                "normalized_displacement_perturbation_sensitivity": float("nan"),
                                "cross_resolution_normalized_3d_distance": float("nan"),
                                "cross_resolution_reference_case": "",
                                "runtime_seconds": time.perf_counter() - run_started,
                                "status": "pending_geometry_comparison",
                                "failure_reason": "",
                                "registry_sha256": registry_hash,
                                "method_npz_sha256": method_npz_hash,
                                "source_git_commit": commit,
                            }
                        )
            completed.append(case_id)
            _write_checkpoint(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "status": "running",
                    "completed_cases": completed,
                    "total_cases": len(CASES),
                    "elapsed_seconds": time.perf_counter() - started_campaign,
                    "max_wall_seconds": max_wall_seconds,
                    "perturbations": PERTURBATIONS,
                    "signs": SIGNS,
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
        qr_key = (case_id, "qr_svd_shifted_cocycle_iteration", epsilon, sign)
        _, row["normalized_3d_manifold_distance_to_qr"] = _symmetric_hd95(
            surfaces[qr_key], surfaces[key]
        )
        _, row["normalized_displacement_distance_to_qr"] = _symmetric_hd95(
            displacements[qr_key], displacements[key]
        )
        nominal_key = (case_id, method, NOMINAL_PERTURBATION, sign)
        _, row["normalized_displacement_perturbation_sensitivity"] = _symmetric_hd95(
            displacements[nominal_key], displacements[key]
        )
        for cases in GROUPS.values():
            if case_id not in cases:
                continue
            reference_case = cases[-1]
            reference_key = (reference_case, method, epsilon, sign)
            _, row["cross_resolution_normalized_3d_distance"] = _symmetric_hd95(
                surfaces[reference_key], surfaces[key]
            )
            row["cross_resolution_reference_case"] = reference_case
            break
        row["status"], row["failure_reason"] = _classify(row)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_NPZ.parent.mkdir(parents=True, exist_ok=True)
    benchmark._write_csv(OUTPUT_CSV, FIELDS, records)
    np.savez_compressed(OUTPUT_NPZ, **arrays)

    status_order = {"accepted": 0, "boundary": 1, "fail": 2}
    for row in method_rows:
        key = (row["case_id"], row["method"])
        if row["case_id"] not in CASES:
            row["manifold_status"] = "not_selected_stage_f"
            continue
        selected = [
            item
            for item_key, item in record_index.items()
            if item_key[:2] == key
            and math.isclose(item_key[2], NOMINAL_PERTURBATION, rel_tol=0.0, abs_tol=1.0e-20)
        ]
        row["manifold_jacobi_drift"] = max(
            float(item["manifold_jacobi_drift"]) for item in selected
        )
        row["initial_linear_growth_ratio"] = float(
            np.mean([float(item["initial_linear_growth_ratio"]) for item in selected])
        )
        row["normalized_3d_manifold_distance"] = max(
            float(item["normalized_3d_manifold_distance_to_qr"])
            for item in selected
        )
        row["manifold_status"] = max(
            (item["status"] for item in selected), key=status_order.__getitem__
        )
    benchmark._write_csv(METHOD_CSV, benchmark.METHOD_FIELDS, method_rows)

    counts: dict[str, int] = {}
    for row in records:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    elapsed = time.perf_counter() - started_campaign
    nominal = [
        row
        for row in records
        if math.isclose(
            float(row["perturbation_norm"]),
            NOMINAL_PERTURBATION,
            rel_tol=0.0,
            abs_tol=1.0e-20,
        )
    ]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "bundle_run_id": bundle_run_id,
        "status": "complete",
        "cases": len(CASES),
        "families": len({registry[case]["family"] for case in CASES}),
        "methods": len(METHODS),
        "perturbations": len(PERTURBATIONS),
        "signs": len(SIGNS),
        "rows": len(records),
        "status_counts": counts,
        "elapsed_seconds": elapsed,
        "jacobi_drift_limit": JACOBI_DRIFT_LIMIT,
        "initial_linear_ratio_tolerance": INITIAL_LINEAR_RATIO_TOLERANCE,
        "cross_resolution_distance_limit": CROSS_RESOLUTION_DISTANCE_LIMIT,
        "registry_sha256": registry_hash,
        "method_npz_sha256": method_npz_hash,
        "source_git_commit": commit,
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_checkpoint({**summary, "completed_cases": completed})
    _write_audit(
        records=records,
        nominal=nominal,
        summary=summary,
        registry=registry,
    )
    benchmark_summary_path = benchmark.RUN_SUMMARY
    if benchmark_summary_path.is_file():
        benchmark_summary = json.loads(benchmark_summary_path.read_text(encoding="utf-8"))
        benchmark_summary["stage_f_status"] = "complete"
        benchmark_summary["stage_f_run_id"] = run_id
        benchmark_summary["stage_f_rows"] = len(records)
        benchmark_summary_path.write_text(
            json.dumps(benchmark_summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        f"invariant-bundle manifold WRITE PASS cases={len(CASES)} rows={len(records)} "
        f"statuses={counts} elapsed={elapsed:.3f}s",
        flush=True,
    )


def _write_audit(
    *,
    records: list[dict[str, Any]],
    nominal: list[dict[str, Any]],
    summary: Mapping[str, Any],
    registry: Mapping[str, Mapping[str, str]],
) -> None:
    aggregate: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in nominal:
        aggregate.setdefault((row["case_id"], row["method"]), []).append(row)
    lines = [
        "# Stage F invariant-bundle manifold audit",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Bundle run ID: `{summary['bundle_run_id']}`",
        f"- Cases: `{summary['cases']}` across `{summary['families']}` families",
        f"- Methods: `{summary['methods']}`",
        f"- Perturbations: `{PERTURBATIONS}`",
        f"- Signs: `{SIGNS}`",
        f"- Stored rows: `{summary['rows']}`",
        f"- Status counts: `{summary['status_counts']}`",
        "",
        "## Frozen conditions",
        "",
        "All methods within a case use the same source states, phase samples, full-state perturbation norm,",
        "fixed propagation duration, DOP853 tolerances, synodic rotating nondimensional coordinates, and",
        "no event termination. Halo and vertical resolution groups use the highest-resolution member's",
        "propagation duration. The Jacobi drift limit remains `1e-10`, and cross-resolution full-sheet",
        "distance retains the Stage-B `0.01` normalized boundary.",
        "",
        "## Nominal perturbation summary",
        "",
        "| case | method | bundle status | manifold status | max Jacobi drift | mean initial linear ratio | max distance to QR | max cross-resolution distance |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for case_id in CASES:
        for method in METHODS:
            selected = aggregate[(case_id, method)]
            worst = "fail" if any(row["status"] == "fail" for row in selected) else (
                "boundary" if any(row["status"] == "boundary" for row in selected) else "accepted"
            )
            cross = [
                float(row["cross_resolution_normalized_3d_distance"])
                for row in selected
                if np.isfinite(float(row["cross_resolution_normalized_3d_distance"]))
            ]
            lines.append(
                f"| `{case_id}` | `{method}` | `{selected[0]['bundle_research_status']}` | `{worst}` | "
                f"{max(float(row['manifold_jacobi_drift']) for row in selected):.3e} | "
                f"{np.mean([float(row['initial_linear_growth_ratio']) for row in selected]):.6f} | "
                f"{max(float(row['normalized_3d_manifold_distance_to_qr']) for row in selected):.3e} | "
                f"{max(cross) if cross else float('nan'):.3e} |"
            )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "The Route-H physical corrected-rho cases are not used for Stage-F manifolds because Stage D did",
        "not produce an accepted one-dimensional real bundle for them. Sun-Earth member 468 is used as the",
        "third family instead. These results compare numerical methods; they do not alter the frozen thesis",
        "projection holdout or establish McCarthy 2018 paper-equivalence.",
        "",
    ]
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text("\n".join(lines), encoding="utf-8")


def check_outputs() -> None:
    rows = _read_csv(OUTPUT_CSV)
    expected = len(CASES) * len(METHODS) * len(PERTURBATIONS) * len(SIGNS)
    if len(rows) != expected:
        raise RuntimeError(f"manifold row count {len(rows)} != {expected}")
    registry_hash = _sha256(REGISTRY)
    if any(row["registry_sha256"] != registry_hash for row in rows):
        raise RuntimeError("manifold registry hash drifted")
    if {row["case_id"] for row in rows} != set(CASES):
        raise RuntimeError("manifold case coverage drifted")
    if {row["method"] for row in rows} != set(METHODS):
        raise RuntimeError("manifold method coverage drifted")
    if any(not np.isfinite(float(row["manifold_jacobi_drift"])) for row in rows):
        raise RuntimeError("manifold metrics contain non-finite Jacobi drift")
    with np.load(OUTPUT_NPZ, allow_pickle=False) as archive:
        if str(archive["registry_sha256"][0]) != registry_hash:
            raise RuntimeError("manifold NPZ registry hash drifted")
        if str(archive["method_npz_sha256"][0]) != _sha256(METHOD_NPZ):
            raise RuntimeError("manifold NPZ method hash drifted")
    if not AUDIT.is_file() or not SUMMARY.is_file():
        raise RuntimeError("manifold report or summary is missing")
    print(
        f"invariant-bundle manifold CHECK PASS cases={len(CASES)} rows={expected}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--max-wall-seconds", type=float, default=MAX_WALL_SECONDS
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        check_outputs()
        return 0
    run_campaign(max_wall_seconds=args.max_wall_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
