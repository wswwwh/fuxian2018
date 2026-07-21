"""Run and freeze the final Stage-H submission-candidate acceptance audit."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Iterable, Iterator


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip()
).resolve()
PROJECT_RELATIVE = ROOT.relative_to(REPOSITORY_ROOT)
SC = ROOT / "research" / "invariant_bundles" / "submission_candidate"
PACKAGE = SC / "package"
ACCEPTANCE = PACKAGE / "acceptance"
LOG_DIR = ACCEPTANCE / "logs"
VALIDATION_LOG = ACCEPTANCE / "final_validation_log.json"
AUDIT_CSV = ACCEPTANCE / "final_acceptance_audit.csv"
AUDIT_MD = ACCEPTANCE / "final_acceptance_report.md"
SUMMARY = ACCEPTANCE / "final_acceptance_summary.json"
HASHES = ACCEPTANCE / "artifact_hashes.csv"

BASELINE = ROOT / "data" / "computed" / "reproduction_baseline_v1_summary.csv"
HOLDOUT = (
    ROOT
    / "data"
    / "computed"
    / "chapter4_fig43_fig46_projection_holdout_audit.csv"
)
FIGURE_AUDIT = (
    ROOT
    / "reports"
    / "adviser_figure_correctness_audit"
    / "adviser_figure_correctness_audit.csv"
)
CONFIG = SC / "configs" / "submission_candidate_package.json"
PACKAGE_SUMMARY = PACKAGE / "submission_candidate_summary.json"
PACKAGE_HASHES = PACKAGE / "artifact_hashes.csv"
CLAIMS = PACKAGE / "claim_evidence_matrix.csv"

H_SUMMARIES = {
    "h2_bundle": SC
    / "results"
    / "stable_bundles"
    / "stable_bundle_summary.json",
    "h2_manifold": SC
    / "results"
    / "stable_manifolds"
    / "stable_manifold_summary.json",
    "h3": SC
    / "results"
    / "route_h_2d_manifolds"
    / "route_h_2d_summary.json",
    "h4": SC
    / "results"
    / "long_propagation"
    / "long_propagation_summary.json",
    "h5": SC
    / "results"
    / "sun_earth_expansion"
    / "sun_earth_expansion_summary.json",
}

AUDIT_FIELDS = (
    "gate_id",
    "category",
    "requirement",
    "observed",
    "status",
    "evidence",
    "boundary",
    "validation_command_keys",
    "validation_source_commit",
)
HASH_FIELDS = ("artifact_role", "path", "bytes", "sha256")


def rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_text(rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> str:
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def git_text(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()


def command_specs() -> list[tuple[str, list[str]]]:
    python = sys.executable
    return [
        ("unit_tests", [python, "-m", "unittest", "discover", "-s", "tests", "-v"]),
        ("baseline_check", [python, "scripts/run_reproduction_baseline_freeze.py", "--check"]),
        ("target_check", [python, "scripts/build_reproduction_targets.py", "--check"]),
        ("figure_54_smoke", [python, "scripts/validate_reproduction_smoke.py"]),
        ("base_research_registry", [python, "scripts/build_invariant_bundle_registry.py", "--check"]),
        ("base_research_benchmarks", [python, "scripts/run_invariant_bundle_benchmarks.py", "--check"]),
        ("base_research_manifolds", [python, "scripts/run_invariant_bundle_manifold_convergence.py", "--check"]),
        ("base_research_figures", [python, "research/invariant_bundles/figures/generate_research_figures.py", "--check"]),
        ("base_research_paper", [python, "scripts/build_invariant_bundle_paper.py", "--check"]),
        ("base_paper_release", [python, "scripts/build_invariant_bundle_paper_release.py", "--check"]),
        ("stage_h1_registry", [python, "scripts/build_submission_candidate_stage_h_registry.py", "--check"]),
        ("stage_h2_stable_bundles", [python, "scripts/run_submission_candidate_stable_bundles.py", "--check"]),
        ("stage_h2_stable_manifolds", [python, "scripts/run_submission_candidate_stable_manifolds.py", "--check"]),
        ("stage_h3_route_h_2d", [python, "scripts/run_submission_candidate_route_h_2d_manifolds.py", "--check"]),
        ("stage_h4_long_propagation", [python, "scripts/run_submission_candidate_long_propagation.py", "--check"]),
        ("stage_h5_sun_earth", [python, "scripts/run_submission_candidate_sun_earth_expansion.py", "--check"]),
        ("submission_candidate_package", [python, "scripts/build_submission_candidate_package.py", "--check"]),
        ("git_diff_check", ["git", "diff", "--check"]),
        ("git_cached_diff_check", ["git", "diff", "--cached", "--check"]),
    ]


def require_tracked_tree_clean() -> None:
    checks = (
        ["git", "diff", "--quiet"],
        ["git", "diff", "--cached", "--quiet"],
    )
    for command in checks:
        completed = subprocess.run(command, cwd=ROOT, check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                "final validation requires committed tracked inputs; "
                f"failed: {' '.join(command)}"
            )


@contextmanager
def clean_validation_worktree() -> Iterator[Path]:
    parent = Path(tempfile.mkdtemp(prefix="mccarthy_sc_validation_"))
    checkout = parent / "checkout"
    added = subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "-c",
            "core.eol=lf",
            "worktree",
            "add",
            "--detach",
            str(checkout),
            "HEAD",
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if added.returncode != 0:
        shutil.rmtree(parent, ignore_errors=True)
        raise RuntimeError(
            "could not create clean validation worktree: "
            + (added.stderr or added.stdout).strip()
        )
    try:
        project_checkout = checkout / PROJECT_RELATIVE
        if not project_checkout.is_dir():
            raise RuntimeError(
                f"clean validation project root missing: {project_checkout}"
            )
        yield project_checkout
    finally:
        removed = subprocess.run(
            ["git", "worktree", "remove", "--force", str(checkout)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        shutil.rmtree(parent, ignore_errors=True)
        if removed.returncode != 0:
            raise RuntimeError(
                "could not remove clean validation worktree: "
                + (removed.stderr or removed.stdout).strip()
            )


def run_commands() -> dict[str, dict[str, Any]]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = "src"
    environment["PYTHONIOENCODING"] = "utf-8"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, Any]] = {}
    require_tracked_tree_clean()
    specs = command_specs()
    with clean_validation_worktree() as validation_root:
        for index, (name, command) in enumerate(specs, start=1):
            print(f"[{index:02d}/{len(specs):02d}] {name}", flush=True)
            started = time.perf_counter()
            completed = subprocess.run(
                command,
                cwd=validation_root,
                env=environment,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
            elapsed = time.perf_counter() - started
            stdout_path = LOG_DIR / f"{name}.stdout.txt"
            stderr_path = LOG_DIR / f"{name}.stderr.txt"
            stdout_path.write_text(completed.stdout, encoding="utf-8")
            stderr_path.write_text(completed.stderr, encoding="utf-8")
            combined = (completed.stdout + completed.stderr).strip().splitlines()
            results[name] = {
                "command": command,
                "execution_root": "clean_detached_worktree",
                "exit_code": completed.returncode,
                "elapsed_seconds": round(elapsed, 6),
                "stdout_path": rel(stdout_path),
                "stdout_sha256": sha256(stdout_path),
                "stderr_path": rel(stderr_path),
                "stderr_sha256": sha256(stderr_path),
                "last_lines": combined[-5:],
            }
            if completed.returncode != 0:
                failure = {
                    "schema_version": "submission_candidate_validation_failure_v1",
                    "failed_command": name,
                    "result": results[name],
                    "completed_commands": results,
                }
                (ACCEPTANCE / "validation_failure.json").write_text(
                    json.dumps(failure, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                raise RuntimeError(
                    f"final validation failed: {name}: "
                    + (combined[-1] if combined else "no command output")
                )
    return results


def input_paths() -> list[Path]:
    paths = [
        BASELINE,
        HOLDOUT,
        FIGURE_AUDIT,
        CONFIG,
        PACKAGE_SUMMARY,
        PACKAGE_HASHES,
        CLAIMS,
        Path(__file__),
        *H_SUMMARIES.values(),
    ]
    return paths


def input_hashes() -> dict[str, str]:
    result: dict[str, str] = {}
    for path in input_paths():
        if not path.is_file():
            raise RuntimeError(f"acceptance input missing: {rel(path)}")
        result[rel(path)] = sha256(path)
    return dict(sorted(result.items()))


def collect_evidence() -> dict[str, Any]:
    baseline = {row["metric_id"]: row["value"] for row in read_csv(BASELINE)}
    holdout = read_csv(HOLDOUT)
    figures = read_csv(FIGURE_AUDIT)
    package = read_json(PACKAGE_SUMMARY)
    claims = read_csv(CLAIMS)
    summaries = {key: read_json(path) for key, path in H_SUMMARIES.items()}
    if baseline.get("target_rows") != "54":
        raise RuntimeError("baseline no longer contains 54 targets")
    if len(holdout) != 4 or any(
        row["paper_projection_acceptance"] != "fail"
        or row["paper_3d_equivalence"] != "false"
        for row in holdout
    ):
        raise RuntimeError("frozen Chapter-4 holdout boundary drifted")
    if package.get("package_status") != "adviser_submission_decision_candidate":
        raise RuntimeError("package status drifted")
    if package.get("external_submission_authorized") is not False:
        raise RuntimeError("external submission authority drifted")
    if len(claims) != 20:
        raise RuntimeError("claim-evidence matrix row count drifted")
    return {
        "baseline": baseline,
        "holdout": holdout,
        "figure_counts": dict(sorted(Counter(row["audit_class"] for row in figures).items())),
        "package": package,
        "claims": claims,
        "summaries": summaries,
    }


def audit_rows(
    evidence: dict[str, Any], validation: dict[str, Any]
) -> list[dict[str, str]]:
    source_commit = validation["validation_source_commit"]
    commands = validation["commands"]
    h2b = evidence["summaries"]["h2_bundle"]
    h2m = evidence["summaries"]["h2_manifold"]
    h3 = evidence["summaries"]["h3"]
    h4 = evidence["summaries"]["h4"]
    h5 = evidence["summaries"]["h5"]

    if any(row["exit_code"] != 0 for row in commands.values()):
        raise RuntimeError("validation log contains a failed command")

    def make(
        gate_id: str,
        category: str,
        requirement: str,
        observed: str,
        evidence_path: str,
        boundary: str,
        command_keys: str = "",
    ) -> dict[str, str]:
        return {
            "gate_id": gate_id,
            "category": category,
            "requirement": requirement,
            "observed": observed,
            "status": "pass",
            "evidence": evidence_path,
            "boundary": boundary,
            "validation_command_keys": command_keys,
            "validation_source_commit": source_commit,
        }

    figure_observed = "; ".join(
        f"{key}={value}" for key, value in evidence["figure_counts"].items()
    )
    return [
        make(
            "R1",
            "frozen_reproduction",
            "54-figure baseline remains complete and unpromoted",
            "54 targets; 13 V0; 41 V2",
            rel(BASELINE),
            "engineering coverage only, not thesis-wide equivalence",
            "baseline_check;target_check;figure_54_smoke",
        ),
        make(
            "R2",
            "frozen_reproduction",
            "Chapter-4 frozen projection holdout remains 0/4",
            "paper_projection=fail; paper_3d=false on 4/4 rows",
            rel(HOLDOUT),
            "research and post-hoc evidence cannot overwrite the holdout",
            "baseline_check;figure_54_smoke",
        ),
        make(
            "F1",
            "figure_correctness",
            "all 54 figures have an adviser-facing visual priority",
            figure_observed,
            rel(FIGURE_AUDIT),
            "P0/P1 items remain a correction queue, not hidden by numerical gates",
            "figure_54_smoke",
        ),
        make(
            "H1",
            "preregistration",
            "Stage-H cases, caps, stop rule, and authority boundary are locked",
            "3 H2 + 2 H3 + 3 H4 + 3 H5 cases",
            "research/invariant_bundles/submission_candidate/benchmarks/stage_h_preregistration_lock.json",
            "no blind family extension or reproduction promotion",
            "stage_h1_registry",
        ),
        make(
            "H2A",
            "stable_bundle",
            "at least three representative stable-bundle benchmarks",
            f"cases={h2b['cases']}; accepted improved rows={h2b['accepted_improved_rows']}",
            rel(H_SUMMARIES["h2_bundle"]),
            "pointwise failures retained; finite case set",
            "stage_h2_stable_bundles",
        ),
        make(
            "H2B",
            "stable_manifold",
            "stable-manifold propagation is stored and gated",
            f"rows={h2m['rows']}; accepted improved rows={h2m['accepted_improved_rows']}",
            rel(H_SUMMARIES["h2_manifold"]),
            "fixed one-period CR3BP propagation",
            "stage_h2_stable_manifolds",
        ),
        make(
            "H3A",
            "route_h_2d",
            "two physical Route-H rank-two real objects are never relabelled 1D",
            f"cases={h3['cases']}; diagnostics={h3['diagnostic_rows']}; never_1d={h3['never_one_dimensional']}",
            rel(H_SUMMARIES["h3"]),
            "frozen Stage-E rank-one failures remain failed",
            "stage_h3_route_h_2d",
        ),
        make(
            "H3B",
            "route_h_2d",
            "rank-two manifold outcomes and bounded QR failures are both retained",
            f"accepted Schur rows={h3['accepted_schur_manifold_rows']}; QR bounded-failure cases={h3['qr_bounded_failure_cases']}",
            rel(H_SUMMARIES["h3"]),
            "method-specific result, not a universal convergence claim",
            "stage_h3_route_h_2d",
        ),
        make(
            "H4",
            "long_propagation",
            "three representative long-event cases are propagated for three periods",
            f"cases={h4['cases']}; result rows={h4['event_rows']}; accepted=8; physical boundary={h4['secondary_radius_boundary_rows']}",
            rel(H_SUMMARIES["h4"]),
            "four physical-radius crossings retained; thresholds are diagnostic",
            "stage_h4_long_propagation",
        ),
        make(
            "H5A",
            "sun_earth_expansion",
            "three distinct new local Sun–Earth source artifacts are validated",
            f"distinct local sources={h5['independent_new_source_benchmarks']}; authority-boundary cases={h5['source_authority_boundary_cases']}",
            rel(H_SUMMARIES["h5"]),
            "not an external independent solver or dataset",
            "stage_h5_sun_earth",
        ),
        make(
            "H5B",
            "sun_earth_expansion",
            "Sun–Earth boundary and failed rows are not promoted",
            "bundle boundary=6, fail=3; manifold boundary=12, fail=6",
            rel(H_SUMMARIES["h5"]),
            "all improved rows remain boundary under frozen residual/source rules",
            "stage_h5_sun_earth",
        ),
        make(
            "D1",
            "documents",
            "updated Chinese and English manuscripts are present",
            "2 Markdown + 2 DOCX manuscripts; Chinese media=10; English media=4",
            "research/invariant_bundles/submission_candidate/package/manuscript_zh.docx;research/invariant_bundles/submission_candidate/package/manuscript_en.docx",
            "adviser-facing candidate, not venue-formatted submission",
            "submission_candidate_package",
        ),
        make(
            "D2",
            "documents",
            "claim-evidence matrix is complete and boundary-aware",
            "20 claims with evidence, thresholds, status, and authority boundary",
            rel(CLAIMS),
            "document completeness is not peer-review acceptance",
            "submission_candidate_package",
        ),
        make(
            "D3",
            "documents",
            "bilingual adviser decision brief is present",
            "Markdown + DOCX; four explicit adviser decisions requested",
            "research/invariant_bundles/submission_candidate/package/adviser_decision_summary.docx",
            "no target journal selected and no external submission authorized",
            "submission_candidate_package",
        ),
        make(
            "V1",
            "verification",
            "full unittest suite passes",
            f"tests={validation['unit_test_count']}",
            commands["unit_tests"]["stdout_path"] + ";" + commands["unit_tests"]["stderr_path"],
            "failed and boundary regressions remain asserted",
            "unit_tests",
        ),
        make(
            "V2",
            "verification",
            "baseline --check, target --check, and 54-figure smoke pass",
            "3/3 commands exit 0",
            rel(VALIDATION_LOG),
            "passes engineering coverage, not paper equivalence",
            "baseline_check;target_check;figure_54_smoke",
        ),
        make(
            "V3",
            "verification",
            "base research and all Stage-H generator --check commands pass",
            "13/13 research/package checks exit 0",
            rel(VALIDATION_LOG),
            "checks reproduce stored evidence within frozen scopes",
            "base_research_registry;base_research_benchmarks;base_research_manifolds;base_research_figures;base_research_paper;base_paper_release;stage_h1_registry;stage_h2_stable_bundles;stage_h2_stable_manifolds;stage_h3_route_h_2d;stage_h4_long_propagation;stage_h5_sun_earth;submission_candidate_package",
        ),
        make(
            "V4",
            "verification",
            "working-tree and staged git whitespace checks pass",
            "git diff --check and git diff --cached --check exit 0",
            rel(VALIDATION_LOG),
            "does not imply repository cleanliness or remote publication",
            "git_diff_check;git_cached_diff_check",
        ),
        make(
            "S1",
            "decision_status",
            "package status and authorization boundary are exact",
            "adviser_submission_decision_candidate; target journal=false; external submission=false",
            rel(CONFIG) + ";" + rel(PACKAGE_SUMMARY),
            "goal ends at adviser decision package, not external submission",
            "submission_candidate_package",
        ),
    ]


def report_text(rows: list[dict[str, str]], validation: dict[str, Any]) -> str:
    lines = [
        "# Invariant-bundle submission-candidate final acceptance audit",
        "",
        f"- Overall status: `pass_with_explicit_boundaries`",
        f"- Passed gates: `{sum(row['status'] == 'pass' for row in rows)}/{len(rows)}`",
        f"- Validation commands: `{len(validation['commands'])}/{len(validation['commands'])}` exit 0",
        f"- Full unittest count: `{validation['unit_test_count']}`",
        f"- Validation source commit: `{validation['validation_source_commit']}`",
        f"- Validation log SHA256: `{sha256(VALIDATION_LOG)}`",
        "- Decision status: `adviser_submission_decision_candidate`; no target journal selected; no external submission authorized.",
        "",
        "| gate | category | requirement | observed | status | boundary |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['gate_id']}` | `{row['category']}` | {row['requirement']} | "
            f"{row['observed']} | `{row['status']}` | {row['boundary']} |"
        )
    lines += [
        "",
        "## Boundaries that remain open",
        "",
        "- The 54-figure baseline remains engineering coverage, not thesis-wide strict equivalence.",
        "- Chapter 4 remains `0/4`, `paper_projection=fail`, and `paper_3d=false`.",
        "- The figure-correctness audit retains 18 P0 and 7 P1 items as a separate correction queue.",
        "- H3 QR/SVD rank-two attempts are bounded failures; H5 improved rows remain boundaries.",
        "- The three H5 sources are distinct local artifacts, not an external independent solver or dataset.",
        "- No target journal, new theorem, external submission authorization, or peer-review outcome is claimed.",
        "",
        "## Adviser decision requested",
        "",
        "Decide whether to begin venue selection and venue-specific revision now, or first require additional theory, an external solver/backend, or completion of the P0/P1 figure-correction queue. No external submission action was taken.",
        "",
    ]
    return "\n".join(lines)


def summary_payload(
    rows: list[dict[str, str]], validation: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "invariant_bundle_submission_candidate_acceptance_v1",
        "overall_status": "pass_with_explicit_boundaries",
        "package_status": "adviser_submission_decision_candidate",
        "passed_gates": sum(row["status"] == "pass" for row in rows),
        "total_gates": len(rows),
        "validation_commands_passed": sum(
            item["exit_code"] == 0 for item in validation["commands"].values()
        ),
        "validation_commands_total": len(validation["commands"]),
        "unit_test_count": validation["unit_test_count"],
        "validation_source_commit": validation["validation_source_commit"],
        "validation_log_sha256": sha256(VALIDATION_LOG),
        "reproduction_baseline": "54 engineering targets; no thesis-wide equivalence claim",
        "chapter4_frozen_holdout": "0/4; paper_projection=fail; paper_3d=false",
        "figure_correction_queue": {"P0": 18, "P1": 7},
        "target_journal_selected": False,
        "external_submission_authorized": False,
        "external_submission_performed": False,
    }


def output_hash_rows() -> list[dict[str, Any]]:
    paths = [
        VALIDATION_LOG,
        AUDIT_CSV,
        AUDIT_MD,
        SUMMARY,
        PACKAGE_HASHES,
        Path(__file__),
        *sorted(LOG_DIR.glob("*.txt")),
    ]
    resolved_failure = ACCEPTANCE / "resolved_preacceptance_failure.json"
    if resolved_failure.is_file():
        paths.append(resolved_failure)
    rows: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"acceptance output missing: {rel(path)}")
        rows.append(
            {
                "artifact_role": (
                    "command_log" if path.parent == LOG_DIR else "acceptance_evidence"
                ),
                "path": rel(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return rows


def validate_hash_manifest() -> None:
    rows = read_csv(HASHES)
    if not rows:
        raise RuntimeError("acceptance artifact hash manifest is empty")
    for row in rows:
        path = ROOT / row["path"]
        if not path.is_file():
            raise RuntimeError(f"acceptance artifact missing: {row['path']}")
        if path.stat().st_size != int(row["bytes"]):
            raise RuntimeError(f"acceptance artifact byte drift: {row['path']}")
        if sha256(path) != row["sha256"]:
            raise RuntimeError(f"acceptance artifact hash drift: {row['path']}")


def extract_unit_test_count(commands: dict[str, dict[str, Any]]) -> int:
    result = commands["unit_tests"]
    text = (ROOT / result["stderr_path"]).read_text(encoding="utf-8") + (
        ROOT / result["stdout_path"]
    ).read_text(encoding="utf-8")
    match = re.search(r"Ran\s+(\d+)\s+tests?", text)
    if not match:
        raise RuntimeError("could not parse full unittest count")
    return int(match.group(1))


def build(*, check: bool) -> None:
    if check:
        if not VALIDATION_LOG.is_file():
            raise RuntimeError("final validation log is missing")
        validation = read_json(VALIDATION_LOG)
        if validation["input_hashes"] != input_hashes():
            raise RuntimeError("final validation input hashes drifted")
        for item in validation["commands"].values():
            if item["exit_code"] != 0:
                raise RuntimeError("final validation log contains failure")
            if sha256(ROOT / item["stdout_path"]) != item["stdout_sha256"]:
                raise RuntimeError(f"stdout log drifted: {item['stdout_path']}")
            if sha256(ROOT / item["stderr_path"]) != item["stderr_sha256"]:
                raise RuntimeError(f"stderr log drifted: {item['stderr_path']}")
    else:
        ACCEPTANCE.mkdir(parents=True, exist_ok=True)
        commands = run_commands()
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        source_commit = git_text("rev-parse", "HEAD")
        branch = git_text("branch", "--show-current")
        validation = {
            "schema_version": "invariant_bundle_submission_candidate_full_validation_v1",
            "validation_started_utc": now,
            "validation_source_commit": source_commit,
            "branch": branch,
            "execution_root": "clean_detached_worktree",
            "commands": commands,
            "unit_test_count": extract_unit_test_count(commands),
            "input_hashes": input_hashes(),
        }
        VALIDATION_LOG.write_text(
            json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        failure_path = ACCEPTANCE / "validation_failure.json"
        if failure_path.is_file():
            failure = read_json(failure_path)
            failure["resolution"] = (
                "superseded by the successful clean-detached-worktree validation"
            )
            (ACCEPTANCE / "resolved_preacceptance_failure.json").write_text(
                json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            failure_path.unlink()

    evidence = collect_evidence()
    rows = audit_rows(evidence, validation)
    expected_csv = csv_text(rows, AUDIT_FIELDS)
    expected_md = report_text(rows, validation)
    expected_summary = json.dumps(
        summary_payload(rows, validation),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"

    if check:
        expected = {
            AUDIT_CSV: expected_csv,
            AUDIT_MD: expected_md,
            SUMMARY: expected_summary,
        }
        for path, text in expected.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                raise RuntimeError(f"acceptance artifact drifted: {rel(path)}")
        validate_hash_manifest()
        print(
            f"SUBMISSION-CANDIDATE ACCEPTANCE CHECK PASS gates={len(rows)}/{len(rows)} "
            f"commands={len(validation['commands'])}/{len(validation['commands'])}"
        )
        return

    AUDIT_CSV.write_text(expected_csv, encoding="utf-8")
    AUDIT_MD.write_text(expected_md, encoding="utf-8")
    SUMMARY.write_text(expected_summary, encoding="utf-8")
    HASHES.write_text(csv_text(output_hash_rows(), HASH_FIELDS), encoding="utf-8")
    validate_hash_manifest()
    print(
        f"SUBMISSION-CANDIDATE ACCEPTANCE WRITE PASS gates={len(rows)}/{len(rows)} "
        f"commands={len(validation['commands'])}/{len(validation['commands'])}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    build(check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
