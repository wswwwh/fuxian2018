#!/usr/bin/env python3
"""Run and audit an independent MATLAB real-Schur backend campaign."""

from __future__ import annotations

import argparse
import base64
import contextlib
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from itertools import permutations
from typing import Any, Iterable

import numpy as np
import scipy
from scipy.io import loadmat, savemat

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.invariant_bundles import (  # noqa: E402
    align_bundle_phase,
    assemble_discrete_cocycle_operator,
    bundle_invariance_metrics,
    phase_principal_angles_deg,
)

RESEARCH = ROOT / "research" / "invariant_bundles"
CONFIG = RESEARCH / "configs" / "independent_schur_backend_validation.json"
REGISTRY = RESEARCH / "benchmarks" / "benchmark_registry.csv"
METHOD_CSV = RESEARCH / "results" / "csv" / "method_comparison.csv"
METHOD_NPZ = RESEARCH / "results" / "npz" / "method_comparison.npz"
COCYCLE_DIR = RESEARCH / "results" / "npz" / "cocycles"
CSV_OUTPUT = RESEARCH / "results" / "csv" / "independent_schur_backend_comparison.csv"
NPZ_OUTPUT = RESEARCH / "results" / "npz" / "independent_schur_backend_bases.npz"
DOC_OUTPUT = RESEARCH / "docs" / "independent_schur_backend_validation.md"
BACKEND_DIR = RESEARCH / "results" / "independent_backend"
INPUT_MAT = BACKEND_DIR / "independent_schur_input.mat"
OUTPUT_MAT = BACKEND_DIR / "independent_schur_output.mat"
INPUT_MANIFEST = BACKEND_DIR / "independent_schur_input_manifest.json"
MATLAB_SCRIPT = RESEARCH / "independent_backend" / "independent_real_schur_backend.m"
LOG_DIR = RESEARCH / "results" / "logs"
RUN_LOG = LOG_DIR / "independent_schur_backend_validation.log"
MATLAB_LOG = LOG_DIR / "independent_schur_backend_matlab.log"
MATLAB_STDOUT = LOG_DIR / "independent_schur_backend_matlab_stdout.log"
ENVIRONMENT = LOG_DIR / "independent_schur_backend_environment.json"
FAILURE_EVIDENCE = LOG_DIR / "independent_schur_backend_failure_evidence.md"
PARSER_FAILURE_LOG = LOG_DIR / "independent_schur_backend_parser_failure.log"
HASHES = LOG_DIR / "independent_schur_backend_artifact_hashes.csv"
MATLAB_EXE = Path(r"C:\Program Files (x86)\MATLAB\bin\matlab.exe")
SCHEMA = "independent_schur_backend_comparison_v1"
METHOD = "ordered_partial_real_schur_tracking"

CSV_FIELDS = [
    "schema_version",
    "run_id",
    "case_id",
    "family",
    "member_id",
    "system",
    "backend",
    "backend_version",
    "spectral_samples",
    "internal_selected_block_dimension",
    "independent_selected_block_dimension",
    "dimension_agreement",
    "internal_selected_spectrum",
    "independent_selected_spectrum",
    "spectrum_relative_error",
    "internal_relative_imaginary_part",
    "independent_relative_imaginary_part",
    "invariant_subspace_principal_angle_max_deg",
    "invariant_subspace_principal_angle_mean_deg",
    "principal_angle_tolerance_deg",
    "internal_partial_schur_residual",
    "independent_partial_schur_residual",
    "independent_schur_orthogonality_residual",
    "internal_bundle_invariance_residual_max",
    "independent_bundle_invariance_residual_max",
    "independent_bundle_invariance_residual_mean",
    "bundle_residual_order_difference",
    "internal_multiplier_estimate",
    "independent_multiplier_estimate",
    "multiplier_relative_error",
    "internal_classification",
    "independent_classification",
    "classification_agreement",
    "internal_research_status",
    "independent_research_status",
    "status_agreement",
    "internal_runtime_seconds",
    "independent_runtime_seconds",
    "validation_verdict",
    "validation_notes",
    "registry_sha256",
    "input_operator_sha256",
    "source_cocycle_sha256",
    "source_git_commit",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def find_cocycle(case_id: str, expected_hash: str) -> Path:
    candidates = sorted(COCYCLE_DIR.glob(f"{case_id}_*.npz"))
    matched = [path for path in candidates if sha256(path) == expected_hash.upper()]
    if len(matched) != 1:
        raise RuntimeError(
            f"expected one hashed cocycle for {case_id}, found {len(matched)}"
        )
    return matched[0]


def prepare_input(config: dict[str, Any], log: list[str]) -> dict[str, dict[str, Any]]:
    registry_rows = {row["case_id"]: row for row in read_csv(REGISTRY)}
    method_rows = {
        row["case_id"]: row
        for row in read_csv(METHOD_CSV)
        if row["method"] == METHOD and row["case_id"] in config["cases"]
    }
    missing = set(config["cases"]) - registry_rows.keys() | set(config["cases"]) - method_rows.keys()
    if missing:
        raise RuntimeError(f"validation cases missing from frozen inputs: {sorted(missing)}")

    operators = np.empty((1, len(config["cases"])), dtype=object)
    case_ids = np.empty((1, len(config["cases"])), dtype=object)
    metadata: dict[str, dict[str, Any]] = {}
    for index, case_id in enumerate(config["cases"]):
        source_row = method_rows[case_id]
        cocycle_path = find_cocycle(case_id, source_row["cocycle_cache_sha256"])
        with np.load(cocycle_path, allow_pickle=False) as archive:
            stms = np.asarray(archive["stms"], dtype=float)
            phases = np.asarray(archive["phases"], dtype=float)
            rho = float(archive["rho"][0])
        operator = assemble_discrete_cocycle_operator(stms, phases, rho)
        operators[0, index] = operator
        case_ids[0, index] = case_id
        operator_hash = hashlib.sha256(operator.tobytes(order="C")).hexdigest().upper()
        metadata[case_id] = {
            "cocycle_path": str(cocycle_path.relative_to(ROOT)).replace("\\", "/"),
            "cocycle_sha256": sha256(cocycle_path),
            "operator_sha256": operator_hash,
            "operator_shape": list(operator.shape),
            "spectral_samples": int(stms.shape[0]),
            "state_dimension": int(stms.shape[1]),
            "rho": rho,
        }
        log.append(
            f"prepared case={case_id} shape={operator.shape} "
            f"operator_sha256={operator_hash}"
        )

    BACKEND_DIR.mkdir(parents=True, exist_ok=True)
    savemat(
        INPUT_MAT,
        {
            "schema_version": np.asarray(["independent_schur_input_v1"], dtype=object),
            "case_ids": case_ids,
            "operators": operators,
            "hyperbolic_tolerance": np.asarray([config["hyperbolic_tolerance"]]),
            "near_axis_tie_tolerance": np.asarray([config["near_axis_tie_tolerance"]]),
        },
        do_compression=True,
    )
    manifest = {
        "schema_version": "independent_schur_input_manifest_v1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "registry_sha256": sha256(REGISTRY),
        "config_sha256": sha256(CONFIG),
        "input_mat_sha256": sha256(INPUT_MAT),
        "source_git_commit": git_commit(),
        "cases": metadata,
    }
    INPUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def matlab_quote(path: Path) -> str:
    return str(path.resolve()).replace("'", "''").replace("\\", "/")


def run_matlab(config: dict[str, Any], log: list[str]) -> None:
    if not MATLAB_EXE.is_file():
        raise RuntimeError(f"MATLAB executable not found: {MATLAB_EXE}")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    expression = (
        f"addpath('{matlab_quote(MATLAB_SCRIPT.parent)}'); "
        f"independent_real_schur_backend('{matlab_quote(INPUT_MAT)}',"
        f"'{matlab_quote(OUTPUT_MAT)}','{matlab_quote(MATLAB_LOG)}');"
    )
    command = [str(MATLAB_EXE), "-batch", expression]
    log.append("matlab command=" + subprocess.list2cmdline(command))
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        timeout=float(config["wall_time_cap_seconds"]),
        check=False,
    )
    elapsed = time.perf_counter() - started
    stdout_decoded = completed.stdout.decode("utf-8", errors="replace")
    stderr_decoded = completed.stderr.decode("utf-8", errors="replace")
    MATLAB_STDOUT.write_text(
        "schema=independent_schur_matlab_console_capture_v1\n"
        "storage=base64_exact_bytes_plus_utf8_escaped_preview\n"
        "STDOUT_BASE64\n"
        + base64.b64encode(completed.stdout).decode("ascii")
        + "\nSTDERR_BASE64\n"
        + base64.b64encode(completed.stderr).decode("ascii")
        + "\nSTDOUT_UTF8_ESCAPED_PREVIEW\n"
        + stdout_decoded.encode("unicode_escape").decode("ascii")
        + "\nSTDERR_UTF8_ESCAPED_PREVIEW\n"
        + stderr_decoded.encode("unicode_escape").decode("ascii")
        + "\nEND_CONSOLE_CAPTURE\n",
        encoding="utf-8",
    )
    log.append(f"matlab returncode={completed.returncode} elapsed_seconds={elapsed:.6f}")
    if completed.returncode != 0 or not OUTPUT_MAT.is_file():
        raise RuntimeError(
            f"MATLAB backend failed returncode={completed.returncode}; "
            f"see {MATLAB_STDOUT.relative_to(ROOT)}"
        )


def cells(value: Any, expected: int) -> list[Any]:
    array = np.asarray(value, dtype=object)
    items = list(array.reshape(-1))
    if len(items) != expected:
        raise RuntimeError(f"MATLAB cell count {len(items)} != {expected}")
    return items


def string_cells(value: Any, expected: int) -> list[str]:
    output: list[str] = []
    for item in cells(value, expected):
        array = np.asarray(item)
        if array.size == 0:
            output.append("")
        else:
            output.append(str(item).strip())
    return output


def normalize_local_bases(global_basis: np.ndarray, samples: int, dimension: int) -> np.ndarray:
    values = np.asarray(global_basis, dtype=float).reshape(samples, 6, dimension)
    result = np.empty_like(values)
    for index, basis in enumerate(values):
        q, r = np.linalg.qr(basis, mode="reduced")
        signs = np.sign(np.diag(r))
        signs[signs == 0.0] = 1.0
        result[index] = q * signs
    return result


def multiplier(reduced_maps: np.ndarray) -> float:
    determinants = np.abs(np.linalg.det(np.asarray(reduced_maps, dtype=float)))
    determinants = np.maximum(determinants, np.finfo(float).tiny)
    return float(np.exp(np.mean(np.log(determinants)) / reduced_maps.shape[1]))


def cross_angles(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    output = np.empty(left.shape[0], dtype=float)
    for index in range(left.shape[0]):
        singular = np.linalg.svd(left[index].T @ right[index], compute_uv=False)
        output[index] = float(np.max(np.degrees(np.arccos(np.clip(singular, -1.0, 1.0)))))
    return output


def spectrum_error(left: np.ndarray, right: np.ndarray) -> float:
    expected = np.asarray(left, dtype=complex).reshape(-1)
    actual = np.asarray(right, dtype=complex).reshape(-1)
    if expected.size != actual.size:
        return float("inf")
    errors = []
    for order in permutations(range(actual.size)):
        candidate = actual[list(order)]
        errors.append(
            float(
                np.max(
                    np.abs(candidate - expected)
                    / np.maximum(np.abs(expected), np.finfo(float).tiny)
                )
            )
        )
    return min(errors)


def spectrum_text(values: np.ndarray) -> str:
    return ";".join(f"{value.real:.17g}{value.imag:+.17g}j" for value in np.asarray(values).reshape(-1))


def research_status(max_residual: float, selection_residual: float, config: dict[str, Any]) -> str:
    if selection_residual > float(config["pass_partial_schur_residual"]):
        return "fail"
    if max_residual <= float(config["pass_max_invariance_residual"]):
        return "accepted"
    if max_residual <= float(config["boundary_max_invariance_residual"]):
        return "boundary"
    return "fail"


def scalar_text(value: Any) -> str:
    if isinstance(value, np.ndarray):
        value = value.reshape(-1)[0]
    return str(value).strip()


def compare_outputs(config: dict[str, Any], metadata: dict[str, dict[str, Any]], log: list[str]) -> list[dict[str, Any]]:
    backend = loadmat(OUTPUT_MAT, simplify_cells=True)
    count = len(config["cases"])
    case_ids = [str(item) for item in np.asarray(backend["case_ids"], dtype=object).reshape(-1)]
    if case_ids != config["cases"]:
        raise RuntimeError(f"MATLAB case ordering drifted: {case_ids}")
    backend_bases = cells(backend["bases"], count)
    backend_blocks = cells(backend["selected_blocks"], count)
    backend_spectra = cells(backend["selected_spectra"], count)
    dimensions = np.asarray(backend["dimensions"], dtype=int).reshape(-1)
    relative_imaginary = np.asarray(backend["relative_imaginary"], dtype=float).reshape(-1)
    schur_residuals = np.asarray(backend["partial_schur_residual"], dtype=float).reshape(-1)
    orthogonality = np.asarray(backend["orthogonality_residual"], dtype=float).reshape(-1)
    runtimes = np.asarray(backend["runtime_seconds"], dtype=float).reshape(-1)
    errors = string_cells(backend["errors"], count)
    failures = {case: error for case, error in zip(case_ids, errors) if error}
    if failures:
        raise RuntimeError(f"MATLAB per-case failures: {failures}")

    source_rows = {
        row["case_id"]: row
        for row in read_csv(METHOD_CSV)
        if row["method"] == METHOD and row["case_id"] in config["cases"]
    }
    registry_rows = {row["case_id"]: row for row in read_csv(REGISTRY)}
    registry_hash = sha256(REGISTRY)
    backend_version = f"MATLAB {scalar_text(backend['matlab_version'])}"
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA]),
        "run_id": np.asarray([time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())]),
        "case_ids": np.asarray(config["cases"]),
        "registry_sha256": np.asarray([registry_hash]),
        "config_sha256": np.asarray([sha256(CONFIG)]),
        "input_mat_sha256": np.asarray([sha256(INPUT_MAT)]),
        "output_mat_sha256": np.asarray([sha256(OUTPUT_MAT)]),
        "backend_version": np.asarray([backend_version]),
    }
    run_id = arrays["run_id"][0]
    rows: list[dict[str, Any]] = []
    with np.load(METHOD_NPZ, allow_pickle=False) as internal:
        for index, case_id in enumerate(config["cases"]):
            source = source_rows[case_id]
            registry = registry_rows[case_id]
            samples = int(source["spectral_samples"])
            dimension = int(dimensions[index])
            cocycle_path = ROOT / metadata[case_id]["cocycle_path"]
            with np.load(cocycle_path, allow_pickle=False) as archive:
                stms = np.asarray(archive["stms"], dtype=float)
                phases = np.asarray(archive["phases"], dtype=float)
                rho = float(archive["rho"][0])

            independent_basis = normalize_local_bases(backend_bases[index], samples, dimension)
            independent_basis, independent_flips = align_bundle_phase(independent_basis, phases)
            independent_maps, independent_residuals = bundle_invariance_metrics(
                stms, phases, rho, independent_basis
            )
            independent_phase_angles = phase_principal_angles_deg(independent_basis, phases)
            internal_key = f"{case_id}__{METHOD}__bases"
            internal_spectrum_key = f"{case_id}__{METHOD}__selected_spectrum"
            internal_basis = np.asarray(internal[internal_key], dtype=float)
            internal_spectrum = np.asarray(internal[internal_spectrum_key], dtype=complex)
            angles = cross_angles(internal_basis, independent_basis)
            independent_spectrum = np.asarray(backend_spectra[index], dtype=complex).reshape(-1)
            spectrum_relative_error = spectrum_error(internal_spectrum, independent_spectrum)
            independent_multiplier = multiplier(independent_maps)
            internal_multiplier = float(source["bundle_multiplier_estimate"])
            multiplier_relative_error = abs(independent_multiplier - internal_multiplier) / max(
                abs(internal_multiplier), np.finfo(float).tiny
            )
            independent_max = float(np.max(independent_residuals))
            internal_max = float(source["max_invariance_residual"])
            residual_order_difference = abs(
                math.log10(max(independent_max, np.finfo(float).tiny))
                - math.log10(max(internal_max, np.finfo(float).tiny))
            )
            independent_classification = (
                "real_1d_hyperbolic_bundle"
                if dimension == 1
                else "real_2d_complex_pair_invariant_subspace"
            )
            independent_status = research_status(
                independent_max, float(schur_residuals[index]), config
            )
            dimension_agreement = dimension == int(source["bundle_dimension"])
            classification_agreement = independent_classification == source["classification"]
            status_agreement = independent_status == source["research_status"]
            hard_checks = {
                "dimension": dimension_agreement,
                "classification": classification_agreement,
                "principal_angle": float(np.max(angles)) <= float(config["principal_angle_tolerance_deg"]),
                "spectrum": spectrum_relative_error <= float(config["spectrum_relative_tolerance"]),
                "multiplier": multiplier_relative_error <= float(config["multiplier_relative_tolerance"]),
                "residual_order": residual_order_difference <= float(config["residual_order_tolerance"]),
                "status": status_agreement,
                "partial_schur": float(schur_residuals[index]) <= float(config["pass_partial_schur_residual"]),
            }
            failed_checks = [name for name, passed in hard_checks.items() if not passed]
            verdict = "accepted" if not failed_checks else (
                "boundary" if dimension_agreement and classification_agreement else "fail"
            )
            notes = "all preset checks passed" if not failed_checks else "failed preset checks: " + ",".join(failed_checks)
            row = {
                "schema_version": SCHEMA,
                "run_id": run_id,
                "case_id": case_id,
                "family": registry["family"],
                "member_id": registry["member_id"],
                "system": registry["system"],
                "backend": "matlab_schur_ordschur",
                "backend_version": backend_version,
                "spectral_samples": samples,
                "internal_selected_block_dimension": source["bundle_dimension"],
                "independent_selected_block_dimension": dimension,
                "dimension_agreement": str(dimension_agreement).lower(),
                "internal_selected_spectrum": spectrum_text(internal_spectrum),
                "independent_selected_spectrum": spectrum_text(independent_spectrum),
                "spectrum_relative_error": spectrum_relative_error,
                "internal_relative_imaginary_part": source["relative_imaginary_part"],
                "independent_relative_imaginary_part": relative_imaginary[index],
                "invariant_subspace_principal_angle_max_deg": float(np.max(angles)),
                "invariant_subspace_principal_angle_mean_deg": float(np.mean(angles)),
                "principal_angle_tolerance_deg": config["principal_angle_tolerance_deg"],
                "internal_partial_schur_residual": source["selection_residual"],
                "independent_partial_schur_residual": schur_residuals[index],
                "independent_schur_orthogonality_residual": orthogonality[index],
                "internal_bundle_invariance_residual_max": internal_max,
                "independent_bundle_invariance_residual_max": independent_max,
                "independent_bundle_invariance_residual_mean": float(np.mean(independent_residuals)),
                "bundle_residual_order_difference": residual_order_difference,
                "internal_multiplier_estimate": internal_multiplier,
                "independent_multiplier_estimate": independent_multiplier,
                "multiplier_relative_error": multiplier_relative_error,
                "internal_classification": source["classification"],
                "independent_classification": independent_classification,
                "classification_agreement": str(classification_agreement).lower(),
                "internal_research_status": source["research_status"],
                "independent_research_status": independent_status,
                "status_agreement": str(status_agreement).lower(),
                "internal_runtime_seconds": source["runtime_seconds"],
                "independent_runtime_seconds": runtimes[index],
                "validation_verdict": verdict,
                "validation_notes": notes,
                "registry_sha256": registry_hash,
                "input_operator_sha256": metadata[case_id]["operator_sha256"],
                "source_cocycle_sha256": metadata[case_id]["cocycle_sha256"],
                "source_git_commit": git_commit(),
            }
            rows.append(row)
            prefix = case_id.replace("-", "_")
            arrays[f"{prefix}__basis"] = independent_basis
            arrays[f"{prefix}__global_schur_basis"] = np.asarray(backend_bases[index], dtype=float)
            arrays[f"{prefix}__selected_real_schur_block"] = np.asarray(backend_blocks[index], dtype=float)
            arrays[f"{prefix}__selected_spectrum"] = independent_spectrum
            arrays[f"{prefix}__local_reduced_maps"] = independent_maps
            arrays[f"{prefix}__invariance_residuals"] = independent_residuals
            arrays[f"{prefix}__phase_principal_angles_deg"] = independent_phase_angles
            arrays[f"{prefix}__cross_backend_principal_angles_deg"] = angles
            arrays[f"{prefix}__sign_or_subspace_flips"] = np.asarray([independent_flips])
            log.append(
                f"compared case={case_id} dim={dimension} internal_status={source['research_status']} "
                f"independent_status={independent_status} angle_max_deg={np.max(angles):.9g} "
                f"verdict={verdict}"
            )
    write_csv(CSV_OUTPUT, rows, CSV_FIELDS)
    NPZ_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ_OUTPUT, **arrays)
    return rows


def write_documents(config: dict[str, Any], rows: list[dict[str, Any]], backend: dict[str, Any]) -> None:
    verdict_counts = {status: sum(row["validation_verdict"] == status for row in rows) for status in ("accepted", "boundary", "fail")}
    dimension_consistent = sum(row["dimension_agreement"] == "true" for row in rows)
    status_consistent = sum(row["status_agreement"] == "true" for row in rows)
    route_h_physical = [row for row in rows if row["case_id"].startswith("route_h_member_") and "legacy" not in row["case_id"]]
    legacy = next(row for row in rows if row["case_id"] == "route_h_member_68_legacy_dg_positive")
    lines = [
        "# Independent real-Schur backend validation",
        "",
        "## Scope and backend",
        "",
        f"This audit used **MATLAB {scalar_text(backend['matlab_version'])}** "
        "with native `schur` and `ordschur`. Python supplied only frozen real collocation operators; "
        "it did not supply NumPy eigenpairs or a selected basis to MATLAB.",
        "",
        f"Preset tolerances were fixed before the comparison: principal angle <= {config['principal_angle_tolerance_deg']} deg, "
        f"spectrum relative error <= {config['spectrum_relative_tolerance']}, multiplier relative error <= "
        f"{config['multiplier_relative_tolerance']}, and residual-order difference <= {config['residual_order_tolerance']}.",
        "",
        "## Results",
        "",
        f"- Cases: {len(rows)}; dimension agreement: {dimension_consistent}/{len(rows)}; status agreement: {status_consistent}/{len(rows)}.",
        f"- Validation verdicts: accepted={verdict_counts['accepted']}, boundary={verdict_counts['boundary']}, fail={verdict_counts['fail']}.",
        f"- Route H physical corrected-rho rows: {len(route_h_physical)} rows, all retained as 2D/fail = "
        f"{all(row['independent_selected_block_dimension'] == 2 and row['independent_research_status'] == 'fail' for row in route_h_physical)}.",
        f"- Route H member 68 legacy seed-rho control: dimension={legacy['independent_selected_block_dimension']}, "
        f"status={legacy['independent_research_status']}; this remains an algorithmic control only.",
        "",
        "| case | dim internal/backend | angle max (deg) | bundle residual internal/backend | multiplier internal/backend | status internal/backend | verdict |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['internal_selected_block_dimension']}/{row['independent_selected_block_dimension']} | "
            f"{float(row['invariant_subspace_principal_angle_max_deg']):.3e} | "
            f"{float(row['internal_bundle_invariance_residual_max']):.3e}/{float(row['independent_bundle_invariance_residual_max']):.3e} | "
            f"{float(row['internal_multiplier_estimate']):.9g}/{float(row['independent_multiplier_estimate']):.9g} | "
            f"{row['internal_research_status']}/{row['independent_research_status']} | {row['validation_verdict']} |"
        )
    lines.extend(
        [
            "",
            "## Truth boundary",
            "",
            "This independent check validates the research-layer spectral classification; it does not promote the McCarthy "
            "reproduction level. The frozen Chapter 4 projection holdout remains `0/4`, `paper_projection=fail`, "
            "and `paper_3d=false`. Boundary and failed rows are retained without threshold relaxation.",
            "",
            "## Reproducibility artifacts",
            "",
            "The configuration, MATLAB source, input/output MAT files, comparison CSV, basis NPZ, environment record, "
            "raw logs, failure evidence, and SHA256 manifest are committed together. The failed higher-priority Conda "
            "attempt is documented separately rather than omitted.",
        ]
    )
    DOC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    failed = config["failed_backend_attempt"]
    FAILURE_EVIDENCE.write_text(
        "# Independent backend failure and recovery evidence\n\n"
        "## Higher-priority Conda attempt\n\n"
        f"- Date: {failed['date']}\n"
        f"- Backend: `{failed['backend']}`\n"
        f"- Command: `{failed['command']}`\n"
        f"- Observed result: `{failed['status']}`. {failed['observation']}\n"
        "- Recovery: proceeded to the next declared backend priority, MATLAB `schur`/`ordschur`; no result row was "
        "deleted and no tolerance was changed.\n\n"
        "## MATLAB startup-path noise\n\n"
        "The machine-wide MATLAB startup script emits missing-directory warnings for an unrelated toolbox. The raw "
        "stdout is preserved in `independent_schur_backend_matlab_stdout.log`. MATLAB returned zero, resolved both "
        "`schur` and `ordschur`, and the backend diary records all per-case results. The unrelated startup warnings "
        "were not treated as numerical evidence.\n"
        "\n## First comparison-parser pass\n\n"
        "The first post-processing pass treated MATLAB empty character arrays as the literal string `[]` and "
        "therefore raised a conservative per-case failure before writing the comparison CSV. The parser was "
        "corrected to recognize zero-length arrays as empty error fields, then the entire campaign was rerun from "
        "input preparation. The original MATLAB diary and raw stdout remain in the logged evidence chain.\n",
        encoding="utf-8",
    )


def write_environment(backend: dict[str, Any]) -> None:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        np.show_config()
    record = {
        "schema_version": "independent_schur_backend_environment_v1",
        "platform": platform.platform(),
        "python": sys.version,
        "python_executable": sys.executable,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "numpy_build_configuration": buffer.getvalue(),
        "matlab_version": scalar_text(backend["matlab_version"]),
        "matlab_release": scalar_text(backend["matlab_release"]),
        "matlab_computer": scalar_text(backend["computer_architecture"]),
        "matlab_blas_lapack": scalar_text(backend["blas_lapack_info"]),
        "matlab_executable": str(MATLAB_EXE),
        "source_git_commit": git_commit(),
    }
    ENVIRONMENT.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_hashes() -> None:
    paths = [
        CONFIG,
        MATLAB_SCRIPT,
        Path(__file__),
        REGISTRY,
        METHOD_CSV,
        METHOD_NPZ,
        INPUT_MAT,
        OUTPUT_MAT,
        INPUT_MANIFEST,
        CSV_OUTPUT,
        NPZ_OUTPUT,
        DOC_OUTPUT,
        RUN_LOG,
        MATLAB_LOG,
        MATLAB_STDOUT,
        PARSER_FAILURE_LOG,
        ENVIRONMENT,
        FAILURE_EVIDENCE,
    ]
    rows = [
        {
            "artifact": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in paths
    ]
    write_csv(HASHES, rows, ["artifact", "bytes", "sha256"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--compare-only", action="store_true")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    log = [
        f"start_utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"python={sys.executable}",
        f"config_sha256={sha256(CONFIG)}",
        f"registry_sha256={sha256(REGISTRY)}",
    ]
    metadata = prepare_input(config, log)
    if args.prepare_only:
        RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
        RUN_LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
        return
    if not args.compare_only:
        run_matlab(config, log)
    rows = compare_outputs(config, metadata, log)
    backend = loadmat(OUTPUT_MAT, simplify_cells=True)
    write_documents(config, rows, backend)
    write_environment(backend)
    log.append(f"complete_utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    log.append(
        "verdict_counts="
        + json.dumps(
            {status: sum(row["validation_verdict"] == status for row in rows) for status in ("accepted", "boundary", "fail")},
            sort_keys=True,
        )
    )
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG.write_text("\n".join(log) + "\n", encoding="utf-8")
    write_hashes()
    print(
        f"independent Schur validation PASS cases={len(rows)} "
        f"accepted={sum(row['validation_verdict'] == 'accepted' for row in rows)} "
        f"boundary={sum(row['validation_verdict'] == 'boundary' for row in rows)} "
        f"fail={sum(row['validation_verdict'] == 'fail' for row in rows)}"
    )


if __name__ == "__main__":
    main()
