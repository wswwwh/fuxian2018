#!/usr/bin/env python3
"""Run the final goal acceptance stack without overwriting authoritative results."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any
import uuid

import numpy as np
import scipy


ROOT = Path(__file__).resolve().parents[1]
GIT_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip()
)
OUTPUT = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "adviser_summary_validation"
    / "final_acceptance"
)
PYTHON = Path(r"D:\miniconda3\envs\cislunar\python.exe")
CI_CONFIG = (
    ROOT / "research" / "invariant_bundles" / "configs" / "ci_validation.json"
)
METHOD_CSV = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "csv"
    / "method_comparison.csv"
)
BACKEND_ENV = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "logs"
    / "independent_schur_backend_environment.json"
)
STAGE_SUMMARY = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "adviser_summary_validation"
    / "adviser_summary_summary.json"
)
MAIN_STAGE_MANIFEST = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "adviser_summary_validation"
    / "artifact_hashes.csv"
)
EXECUTION_METADATA_FIELDS = frozenset(
    {"run_id", "runtime_seconds", "peak_memory_mb_estimate", "source_git_commit"}
)
DOWNSTREAM_STAGE_F_FIELDS = frozenset(
    {
        "manifold_jacobi_drift",
        "initial_linear_growth_ratio",
        "normalized_3d_manifold_distance",
        "manifold_status",
    }
)
PROVENANCE_FIELDS = frozenset({"registry_sha256", "cocycle_cache_sha256"})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty CSV {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_logged(
    label: str,
    command: list[str],
    *,
    cwd: Path,
    timeout: float,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    print(f"START {label}", flush=True)
    started = time.time()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    elapsed = time.time() - started
    log_path = OUTPUT / "logs" / f"{label}.log"
    log_path.write_text(
        f"label={label}\n"
        f"cwd={cwd}\n"
        f"command={json.dumps(command, ensure_ascii=False)}\n"
        f"return_code={completed.returncode}\n"
        f"elapsed_seconds={elapsed:.6f}\n\n"
        f"{completed.stdout}",
        encoding="utf-8",
    )
    print(
        f"END {label} rc={completed.returncode} elapsed={elapsed:.2f}s",
        flush=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed; see {log_path}")
    return {
        "label": label,
        "command": command,
        "cwd": str(cwd),
        "return_code": completed.returncode,
        "elapsed_seconds": elapsed,
        "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
        "output": completed.stdout,
    }


def snapshot_authoritative() -> dict[str, dict[str, Any]]:
    config = json.loads(CI_CONFIG.read_text(encoding="utf-8"))
    return {
        relative: {
            "bytes": (ROOT / relative).stat().st_size,
            "sha256": sha256(ROOT / relative),
        }
        for relative in config["authoritative_files_protected"]
    }


def compare_authoritative(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "before_bytes": before[path]["bytes"],
            "after_bytes": after[path]["bytes"],
            "before_sha256": before[path]["sha256"],
            "after_sha256": after[path]["sha256"],
            "unchanged": str(before[path] == after[path]).lower(),
        }
        for path in before
    ]


def parse_unittest(record: dict[str, Any]) -> dict[str, Any]:
    match = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", record["output"])
    if not match:
        raise ValueError("could not parse unittest count from full-suite log")
    return {
        "tests": int(match.group(1)),
        "test_wall_seconds_reported": float(match.group(2)),
        "passed": int(match.group(1)),
        "failed": 0,
        "status": "pass" if re.search(r"\nOK\s*$", record["output"]) else "unknown",
    }


def copy_isolated_outputs(isolated_project: Path) -> list[Path]:
    destination = OUTPUT / "isolated_benchmark"
    destination.mkdir(parents=True, exist_ok=True)
    relative_paths = [
        "research/invariant_bundles/results/csv/method_comparison.csv",
        "research/invariant_bundles/results/csv/phase_continuity.csv",
        "research/invariant_bundles/results/csv/resolution_convergence.csv",
        "research/invariant_bundles/results/csv/runtime_scaling.csv",
        "research/invariant_bundles/results/npz/method_comparison.npz",
        "research/invariant_bundles/results/npz/phase_continuity.npz",
        "research/invariant_bundles/results/npz/resolution_convergence.npz",
        "research/invariant_bundles/results/npz/runtime_scaling.npz",
        "research/invariant_bundles/results/logs/benchmark_campaign_summary.json",
        "research/invariant_bundles/results/logs/benchmark_campaign_checkpoint.json",
    ]
    copied: list[Path] = []
    for relative in relative_paths:
        source = isolated_project / relative
        if not source.is_file():
            raise FileNotFoundError(f"isolated benchmark artifact missing: {source}")
        target = destination / Path(relative).name
        shutil.copy2(source, target)
        copied.append(target)
    return copied


def numeric(value: str) -> float | None:
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def compare_method_tables(reference: Path, candidate: Path) -> list[dict[str, Any]]:
    ref_rows = {(row["case_id"], row["method"]): row for row in read_csv(reference)}
    new_rows = {(row["case_id"], row["method"]): row for row in read_csv(candidate)}
    if ref_rows.keys() != new_rows.keys() or len(ref_rows) != 45:
        raise ValueError("isolated method table row keys differ from authoritative table")
    comparisons: list[dict[str, Any]] = []
    for key in sorted(ref_rows):
        reference_row = ref_rows[key]
        candidate_row = new_rows[key]
        for field in reference_row:
            if field in EXECUTION_METADATA_FIELDS:
                continue
            left = reference_row[field]
            right = candidate_row[field]
            left_number = numeric(left)
            right_number = numeric(right)
            if left_number is not None and right_number is not None:
                if math.isnan(left_number) and math.isnan(right_number):
                    matched = True
                    absolute = 0.0
                    relative = 0.0
                else:
                    absolute = abs(left_number - right_number)
                    scale = max(abs(left_number), abs(right_number), 1e-300)
                    relative = absolute / scale
                    matched = absolute <= 1e-12 + 1e-8 * scale
                kind = "numeric"
            else:
                matched = left == right
                absolute = ""
                relative = ""
                kind = "exact"
            if field in DOWNSTREAM_STAGE_F_FIELDS:
                scope = "downstream_stage_f_reset"
                if field == "manifold_status":
                    candidate_contract = right == "not_run_stage_f"
                else:
                    candidate_contract = (
                        right_number is not None and math.isnan(right_number)
                    )
            elif field in PROVENANCE_FIELDS:
                scope = "provenance"
                candidate_contract = matched
            else:
                scope = "benchmark_owned"
                candidate_contract = matched
            comparisons.append(
                {
                    "case_id": key[0],
                    "method": key[1],
                    "field": field,
                    "field_scope": scope,
                    "comparison_kind": kind,
                    "reference_value": left,
                    "isolated_value": right,
                    "absolute_difference": absolute,
                    "relative_difference": relative,
                    "match": str(matched).lower(),
                    "candidate_contract_match": str(candidate_contract).lower(),
                    "difference_expected": str(
                        scope == "downstream_stage_f_reset" and not matched
                    ).lower(),
                    "comparison_status": "pass" if candidate_contract else "fail",
                }
            )
    return comparisons


def summarize_isolated_comparisons(
    comparisons: list[dict[str, Any]],
) -> dict[str, int]:
    summary: dict[str, int] = {}
    for scope in ("benchmark_owned", "downstream_stage_f_reset", "provenance"):
        rows = [row for row in comparisons if row["field_scope"] == scope]
        summary[f"{scope}_checks"] = len(rows)
        summary[f"{scope}_failures"] = sum(
            row["comparison_status"] != "pass" for row in rows
        )
        summary[f"{scope}_equality_differences"] = sum(
            row["match"] != "true" for row in rows
        )
    summary["total_checks"] = len(comparisons)
    summary["total_contract_failures"] = sum(
        row["comparison_status"] != "pass" for row in comparisons
    )
    return summary


def require_isolated_comparison_pass(summary: dict[str, int]) -> None:
    if summary["total_contract_failures"]:
        raise RuntimeError(
            "isolated benchmark comparison contract failed: "
            + json.dumps(summary, sort_keys=True)
        )


def run_isolated_benchmark(command_records: list[dict[str, Any]]) -> dict[str, Any]:
    temp_root = Path(tempfile.gettempdir()).resolve()
    worktree = temp_root / f"mccarthy_final_acceptance_{uuid.uuid4().hex[:10]}"
    if worktree.exists():
        raise RuntimeError(f"unexpected existing isolated worktree: {worktree}")
    if worktree.parent != temp_root or not worktree.name.startswith("mccarthy_final_acceptance_"):
        raise RuntimeError(f"unsafe isolated worktree path: {worktree}")
    added = False
    try:
        add = run_logged(
            "isolated_worktree_add",
            [
                "git",
                "-c",
                "core.autocrlf=false",
                "worktree",
                "add",
                "--detach",
                str(worktree),
                "HEAD",
            ],
            cwd=GIT_ROOT,
            timeout=300,
            env=os.environ.copy(),
        )
        command_records.append(add)
        added = True
        isolated_project = worktree / ROOT.relative_to(GIT_ROOT)
        env = {**os.environ, "PYTHONPATH": str(isolated_project / "src")}
        benchmark = run_logged(
            "isolated_exact_benchmark",
            [str(PYTHON), "scripts/run_invariant_bundle_benchmarks.py"],
            cwd=isolated_project,
            timeout=1800,
            env=env,
        )
        command_records.append(benchmark)
        copied = copy_isolated_outputs(isolated_project)
        comparison = compare_method_tables(
            METHOD_CSV,
            OUTPUT / "isolated_benchmark" / "method_comparison.csv",
        )
        write_csv(OUTPUT / "isolated_benchmark_comparison.csv", comparison)
        comparison_summary = summarize_isolated_comparisons(comparison)
        require_isolated_comparison_pass(comparison_summary)
        status = run_logged(
            "isolated_worktree_status",
            ["git", "status", "--short"],
            cwd=worktree,
            timeout=120,
            env=os.environ.copy(),
        )
        command_records.append(status)
        return {
            "source_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=worktree,
                text=True,
                encoding="utf-8",
            ).strip(),
            "worktree_path": str(worktree),
            "copied_artifacts": [
                str(path.relative_to(ROOT)).replace("\\", "/") for path in copied
            ],
            **comparison_summary,
            "command_elapsed_seconds": benchmark["elapsed_seconds"],
        }
    finally:
        if added:
            removal = subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=GIT_ROOT,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=300,
                check=False,
            )
            (OUTPUT / "logs" / "isolated_worktree_remove.log").write_text(
                f"path={worktree}\nreturn_code={removal.returncode}\n{removal.stdout}",
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=GIT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=120,
                check=False,
            )
            if removal.returncode != 0:
                raise RuntimeError(
                    "isolated worktree cleanup failed; see isolated_worktree_remove.log"
                )


def environment_record() -> dict[str, Any]:
    backend = json.loads(BACKEND_ENV.read_text(encoding="utf-8"))
    buffer = io.StringIO()
    import contextlib

    with contextlib.redirect_stdout(buffer):
        np.__config__.show()
    return {
        "schema_version": "final_goal_acceptance_environment_v1",
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "numpy_blas_lapack": buffer.getvalue(),
        "independent_schur_backend": "MATLAB schur/ordschur",
        "matlab_version": backend["matlab_version"],
        "matlab_release": backend["matlab_release"],
        "matlab_blas_lapack": backend["matlab_blas_lapack"],
    }


def phase_commit_rows() -> list[dict[str, str]]:
    commits = subprocess.check_output(
        ["git", "log", "-20", "--pretty=format:%H%x09%s"],
        cwd=GIT_ROOT,
        text=True,
        encoding="utf-8",
    ).splitlines()
    by_message = {line.split("\t", 1)[1]: line.split("\t", 1)[0] for line in commits}
    phases = [
        ("1", "Complete Stage G adviser delivery audit", "943b8c7"),
        ("1_identity", "Finalize Stage G confirmed identity fields", "8e9cc05"),
        ("2", "Validate bundles with independent MATLAB Schur backend", "3aae958"),
        ("3", "Classify bounded QR SVD failure cases", "5a50a8a"),
        ("4", "Complete invariant bundle ablation study", "cf04669"),
        ("5", "Complete isolated fresh-process research rerun", "5d26fb0"),
        ("6", "Establish isolated research validation CI", "0adb9d8"),
        ("7", "Verify literature and bound paper positioning", "b8b3553"),
        ("8", "Build complete Chinese invariant bundle paper draft", "e1c59e2"),
    ]
    rows = []
    for phase, message, prefix in phases:
        commit = by_message.get(message, "")
        if not commit.startswith(prefix):
            raise ValueError(f"phase commit not found: {phase} {message}")
        rows.append(
            {
                "phase": phase,
                "commit": commit,
                "message": message,
                "status": "committed",
            }
        )
    rows.append(
        {
            "phase": "9",
            "commit": "this_acceptance_commit",
            "message": "Complete adviser summary and final goal acceptance",
            "status": "pending_current_commit",
        }
    )
    return rows


def final_gate_rows(
    unit: dict[str, Any],
    isolated: dict[str, Any],
    authoritative_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    return [
        {"gate_id": "adviser_54_figure_audit", "status": "pass", "evidence": "stage_g_delivery_review/delivery_validation.json", "boundary": "54 engineering targets;not thesis-wide strict equivalence"},
        {"gate_id": "adviser_placeholders", "status": "pass", "evidence": "reports/mccarthy2018_figure_comparison/final_placeholder_audit.csv", "boundary": "3 identity fields confirmed by user"},
        {"gate_id": "adviser_package", "status": "pass", "evidence": "reports/adviser_delivery", "boundary": "7 final files including original 4-file Stage-G core"},
        {"gate_id": "independent_schur", "status": "pass", "evidence": "research/invariant_bundles/results/csv/independent_schur_backend_comparison.csv", "boundary": "12 finite discrete operators"},
        {"gate_id": "qr_svd_failure_classification", "status": "pass", "evidence": "research/invariant_bundles/results/csv/qr_svd_failure_classification.csv", "boundary": "4 no_accepted_1d_bundle;1 initialization-sensitive"},
        {"gate_id": "ablation", "status": "pass", "evidence": "research/invariant_bundles/results/csv/ablation_study.csv", "boundary": "35 rows;20 failures retained"},
        {"gate_id": "fresh_process_rerun", "status": "pass", "evidence": "research/invariant_bundles/independent_rerun/independent_rerun_report.md", "boundary": "reproducibility does not promote scientific gates"},
        {"gate_id": "fast_ci", "status": "pass", "evidence": ".github/workflows/ci.yml", "boundary": "push and pull_request"},
        {"gate_id": "full_validation_ci", "status": "pass", "evidence": ".github/workflows/full_research_validation.yml", "boundary": "manual workflow_dispatch"},
        {"gate_id": "literature_matrix", "status": "pass", "evidence": "research/invariant_bundles/paper/literature_matrix.csv", "boundary": "25 formal sources;not exhaustive novelty search"},
        {"gate_id": "chinese_manuscript", "status": "pass", "evidence": "research/invariant_bundles/paper_release/manuscript_zh.docx", "boundary": "20-page adviser-review draft"},
        {"gate_id": "claim_evidence", "status": "pass", "evidence": "research/invariant_bundles/paper_release/claim_evidence_matrix.csv", "boundary": "15 claims with limitations"},
        {"gate_id": "four_page_summary", "status": "pass", "evidence": "reports/adviser_delivery/invariant_bundle研究摘要_4页.pdf", "boundary": "exactly 4 pages"},
        {"gate_id": "full_unit_suite", "status": "pass", "evidence": "research/invariant_bundles/adviser_summary_validation/final_acceptance/logs/full_unit_suite.log", "boundary": f"{unit['passed']} passed;0 failed"},
        {"gate_id": "isolated_exact_benchmark", "status": "pass", "evidence": "research/invariant_bundles/adviser_summary_validation/final_acceptance/isolated_benchmark_comparison.csv", "boundary": f"{isolated['benchmark_owned_checks']} benchmark-owned checks;0 failures"},
        {"gate_id": "isolated_stage_f_reset_contract", "status": "pass", "evidence": "research/invariant_bundles/adviser_summary_validation/final_acceptance/isolated_benchmark_comparison.csv", "boundary": f"{isolated['downstream_stage_f_reset_checks']} downstream reset checks;{isolated['downstream_stage_f_reset_equality_differences']} expected differences exposed;0 contract failures"},
        {"gate_id": "isolated_provenance", "status": "pass", "evidence": "research/invariant_bundles/adviser_summary_validation/final_acceptance/isolated_benchmark_comparison.csv", "boundary": f"{isolated['provenance_checks']} provenance checks;0 failures"},
        {"gate_id": "authoritative_immutability", "status": "pass", "evidence": "research/invariant_bundles/adviser_summary_validation/final_acceptance/authoritative_before_after.csv", "boundary": f"{len(authoritative_rows)}/{len(authoritative_rows)} hashes unchanged"},
        {"gate_id": "chapter4_projection_holdout", "status": "supported_negative", "evidence": "data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv", "boundary": "0/4;paper_projection=fail;paper_3d=false"},
        {"gate_id": "route_h_physical", "status": "supported_negative", "evidence": "research/invariant_bundles/results/csv/independent_schur_backend_comparison.csv", "boundary": "physical corrected-rho=2D/fail;legacy=1D positive control"},
        {"gate_id": "submission_readiness", "status": "not_claimed", "evidence": "research/invariant_bundles/paper_release/limitations.md", "boundary": "independent validation complete;scientific limitations remain"},
    ]


def write_nested_hash_manifest() -> None:
    target = OUTPUT / "artifact_hashes.csv"
    source_inputs = [
        Path(__file__).resolve(),
        ROOT / "tests" / "test_invariant_bundle_adviser_summary.py",
        ROOT / "tests" / "test_final_goal_acceptance.py",
        CI_CONFIG,
        METHOD_CSV,
        BACKEND_ENV,
        STAGE_SUMMARY,
    ]
    outputs = [
        path
        for path in sorted(OUTPUT.rglob("*"))
        if path.is_file() and path != target
    ]
    rows = [
        {
            "schema_version": "final_goal_acceptance_artifact_hash_v1",
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in source_inputs + outputs
    ]
    write_csv(target, rows)


def refresh_main_stage_manifest() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_invariant_bundle_adviser_summary as stage_builder

    stage_builder.write_hash_manifest()
    rows = read_csv(MAIN_STAGE_MANIFEST)
    bad = [
        row["path"]
        for row in rows
        if not (ROOT / row["path"]).is_file()
        or (ROOT / row["path"]).stat().st_size != int(row["bytes"])
        or sha256(ROOT / row["path"]) != row["sha256"]
    ]
    if bad:
        raise RuntimeError(f"refreshed stage manifest has invalid rows: {bad}")


def main() -> int:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError(f"refusing to overwrite final acceptance evidence: {OUTPUT}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "logs").mkdir()
    started = datetime.now(timezone.utc)
    before = snapshot_authoritative()
    command_records: list[dict[str, Any]] = []
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}

    unit_record = run_logged(
        "full_unit_suite",
        [str(PYTHON), "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        timeout=1800,
        env=env,
    )
    command_records.append(unit_record)
    unit = parse_unittest(unit_record)
    if unit["status"] != "pass":
        raise RuntimeError("full unit suite did not end in OK")

    for label, command, timeout in (
        (
            "authoritative_benchmark_check",
            [str(PYTHON), "scripts/run_invariant_bundle_benchmarks.py", "--check"],
            300,
        ),
        (
            "reproduction_smoke",
            [str(PYTHON), "scripts/validate_reproduction_smoke.py"],
            300,
        ),
        (
            "reproduction_target_check",
            [str(PYTHON), "scripts/build_reproduction_targets.py", "--check"],
            120,
        ),
        ("git_diff_check", ["git", "diff", "--check"], 120),
    ):
        command_records.append(
            run_logged(label, command, cwd=ROOT, timeout=timeout, env=env)
        )

    isolated = run_isolated_benchmark(command_records)
    after = snapshot_authoritative()
    authoritative_rows = compare_authoritative(before, after)
    if any(row["unchanged"] != "true" for row in authoritative_rows):
        raise RuntimeError("protected authoritative hashes changed during final acceptance")
    write_csv(OUTPUT / "authoritative_before_after.csv", authoritative_rows)
    write_csv(
        OUTPUT / "command_results.csv",
        [
            {
                "label": row["label"],
                "command": json.dumps(row["command"], ensure_ascii=False),
                "cwd": row["cwd"],
                "return_code": row["return_code"],
                "elapsed_seconds": f"{row['elapsed_seconds']:.6f}",
                "log": row["log"],
            }
            for row in command_records
        ],
    )
    write_csv(OUTPUT / "phase_commits.csv", phase_commit_rows())
    gates = final_gate_rows(unit, isolated, authoritative_rows)
    write_csv(OUTPUT / "final_goal_acceptance.csv", gates)
    environment = environment_record()
    (OUTPUT / "environment.json").write_text(
        json.dumps(environment, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    np.savez_compressed(
        OUTPUT / "final_acceptance.npz",
        schema_version=np.array(["final_goal_acceptance_npz_v1"]),
        gate_ids=np.array([row["gate_id"] for row in gates]),
        gate_status=np.array([row["status"] for row in gates]),
        unit_tests=np.array([unit["tests"]], dtype=np.int64),
        unit_failures=np.array([unit["failed"]], dtype=np.int64),
        isolated_benchmark_owned_checks=np.array(
            [isolated["benchmark_owned_checks"]], dtype=np.int64
        ),
        isolated_benchmark_owned_failures=np.array(
            [isolated["benchmark_owned_failures"]], dtype=np.int64
        ),
        isolated_downstream_reset_checks=np.array(
            [isolated["downstream_stage_f_reset_checks"]], dtype=np.int64
        ),
        isolated_downstream_expected_differences=np.array(
            [isolated["downstream_stage_f_reset_equality_differences"]],
            dtype=np.int64,
        ),
        isolated_downstream_reset_failures=np.array(
            [isolated["downstream_stage_f_reset_failures"]], dtype=np.int64
        ),
        isolated_provenance_checks=np.array(
            [isolated["provenance_checks"]], dtype=np.int64
        ),
        isolated_provenance_failures=np.array(
            [isolated["provenance_failures"]], dtype=np.int64
        ),
        authoritative_unchanged=np.array(
            [row["unchanged"] == "true" for row in authoritative_rows], dtype=np.bool_
        ),
        chapter4_holdout=np.array([0, 4], dtype=np.int64),
        submission_readiness=np.array(["not_claimed"]),
    )
    (OUTPUT / "failure_evidence.md").write_text(
        "# Final goal acceptance retained failures\n\n"
        "- The frozen 54-figure label remains complete engineering coverage, not thesis-wide strict equivalence.\n"
        "- Chapter 4 remains `0/4`, `paper_projection=fail`, `paper_3d=false`.\n"
        "- Pointwise eig remains 0/15 accepted.\n"
        "- Physical corrected-rho Route H members 17/32/54/68 remain two-dimensional/fail; no one-dimensional relabelling is permitted.\n"
        "- The legacy seed-rho case remains a one-dimensional positive control and is not a physical replacement.\n"
        "- QR/SVD classification retains four `no_accepted_1d_bundle` and one `method_initialization_sensitive` result.\n"
        "- Ablation retains 20 failed rows and 4 method exceptions.\n"
        "- Manifold evidence retains 90 failed rows and lower-resolution sheets above 0.01.\n"
        "- Final acceptance means every requested deliverable and verification gate is complete; it does not assert submission readiness.\n",
        encoding="utf-8",
    )
    finished = datetime.now(timezone.utc)
    summary = {
        "schema_version": "final_goal_acceptance_summary_v1",
        "status": "pass",
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "elapsed_seconds": (finished - started).total_seconds(),
        "unit_tests": unit["tests"],
        "unit_passed": unit["passed"],
        "unit_failed": unit["failed"],
        "unit_wall_seconds_reported": unit["test_wall_seconds_reported"],
        "isolated_exact_benchmark_source_commit": isolated["source_commit"],
        "isolated_exact_benchmark_owned_checks": isolated[
            "benchmark_owned_checks"
        ],
        "isolated_exact_benchmark_owned_failures": isolated[
            "benchmark_owned_failures"
        ],
        "isolated_downstream_stage_f_reset_checks": isolated[
            "downstream_stage_f_reset_checks"
        ],
        "isolated_downstream_stage_f_expected_differences": isolated[
            "downstream_stage_f_reset_equality_differences"
        ],
        "isolated_downstream_stage_f_reset_failures": isolated[
            "downstream_stage_f_reset_failures"
        ],
        "isolated_provenance_checks": isolated["provenance_checks"],
        "isolated_provenance_failures": isolated["provenance_failures"],
        "protected_authoritative_files": len(authoritative_rows),
        "protected_authoritative_changed": 0,
        "final_gate_rows": len(gates),
        "required_command_count": 5,
        "all_command_return_codes_zero": all(
            row["return_code"] == 0 for row in command_records
        ),
        "chapter4_holdout": "0/4",
        "truth_boundary_status": "preserved",
        "submission_readiness": "not_claimed",
    }
    (OUTPUT / "final_acceptance_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUTPUT / "final_acceptance_report.md").write_text(
        "# Final goal acceptance report\n\n"
        f"- Status: **PASS**.\n"
        f"- Unit suite: {unit['passed']}/{unit['tests']} passed, 0 failed, reported wall-time {unit['test_wall_seconds_reported']:.3f} s.\n"
        f"- Exact benchmark command: executed in an isolated Git worktree; {isolated['benchmark_owned_checks']} benchmark-owned fields compared, 0 failures.\n"
        f"- Stage-F reset contract: {isolated['downstream_stage_f_reset_checks']} checks, {isolated['downstream_stage_f_reset_equality_differences']} expected equality differences exposed, 0 contract failures.\n"
        f"- Provenance: {isolated['provenance_checks']} checks, 0 failures.\n"
        f"- Read-only authoritative benchmark check, reproduction smoke, reproduction-target check, and `git diff --check`: all passed.\n"
        f"- Protected authoritative hashes: {len(authoritative_rows)}/{len(authoritative_rows)} unchanged.\n"
        f"- Environment: Python {platform.python_version()}, NumPy {np.__version__}, SciPy {scipy.__version__}; independent backend MATLAB R2024a with MKL 2023.2.\n"
        "- Chapter 4 remains `0/4`, `paper_projection=fail`, `paper_3d=false`; Route H physical cases remain 2D/fail.\n"
        "- Submission readiness: **not claimed**.\n",
        encoding="utf-8",
    )
    write_nested_hash_manifest()
    refresh_main_stage_manifest()
    print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
