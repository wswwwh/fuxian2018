#!/usr/bin/env python3
"""Validate the repository-root GitHub Actions workflow contracts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import subprocess
import tomllib
from typing import Any, Iterable

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG = (
    PROJECT_ROOT
    / "research"
    / "invariant_bundles"
    / "configs"
    / "ci_validation.json"
)
FULL_CONTROLLER = PROJECT_ROOT / "scripts" / "run_ci_full_research_validation.py"
ENVIRONMENT_LOCK = PROJECT_ROOT / "environment-lock.yml"
CAMERA_PARAMETERS = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter4_fig43_fig46_camera_parameters.csv"
)


def discover_repository_root(project_root: Path = PROJECT_ROOT) -> Path:
    """Resolve the Git worktree root independently of the process cwd."""
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=project_root,
        text=True,
        encoding="utf-8",
        errors="strict",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "cannot resolve Git repository root from "
            f"{project_root}: {completed.stderr.strip()}"
        )
    repository_root = Path(completed.stdout.strip()).resolve()
    if not (repository_root / ".git").exists():
        raise RuntimeError(f"resolved repository root has no .git marker: {repository_root}")
    try:
        project_root.resolve().relative_to(repository_root)
    except ValueError as error:
        raise RuntimeError(
            f"project root is outside resolved repository root: {project_root}"
        ) from error
    return repository_root


REPOSITORY_ROOT = discover_repository_root()


def repository_relative(path: Path) -> str:
    return path.resolve().relative_to(REPOSITORY_ROOT).as_posix()


def frozen_renderer_dependency_valid(
    pyproject_path: Path, camera_parameters_path: Path = CAMERA_PARAMETERS
) -> tuple[bool, str]:
    """Bind the installed Matplotlib release to the frozen camera evidence."""

    with pyproject_path.open("rb") as stream:
        pyproject = tomllib.load(stream)
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list) or not all(
        isinstance(dependency, str) for dependency in dependencies
    ):
        return False, "pyproject project.dependencies is invalid"
    with camera_parameters_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    versions = {row.get("matplotlib_version", "") for row in rows}
    if len(versions) != 1 or not next(iter(versions), ""):
        return False, "camera evidence does not declare one Matplotlib version"
    requirement = f"matplotlib=={next(iter(versions))}"
    return requirement in dependencies, requirement


def frozen_direct_dependency_lock_valid(
    pyproject_path: Path, environment_lock_path: Path = ENVIRONMENT_LOCK
) -> tuple[bool, str]:
    """Require pip installs to reproduce the tested direct-dependency lock."""

    with pyproject_path.open("rb") as stream:
        pyproject = tomllib.load(stream)
    dependencies = pyproject.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list) or not all(
        isinstance(dependency, str) for dependency in dependencies
    ):
        return False, "pyproject project.dependencies is invalid"

    lock = yaml.safe_load(environment_lock_path.read_text(encoding="utf-8"))
    lock_dependencies = lock.get("dependencies", []) if isinstance(lock, dict) else []
    if not isinstance(lock_dependencies, list):
        return False, "environment-lock dependencies is invalid"

    expected: list[str] = []
    for entry in lock_dependencies:
        if isinstance(entry, str):
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)=([^=].*)", entry)
            if match is None:
                return False, f"invalid conda lock entry: {entry}"
            name, version = match.groups()
            if name.lower() not in {"python", "pip"}:
                expected.append(f"{name}=={version}")
            continue
        if not isinstance(entry, dict) or set(entry) != {"pip"}:
            return False, "environment-lock contains an unsupported dependency entry"
        pip_dependencies = entry["pip"]
        if not isinstance(pip_dependencies, list) or not all(
            isinstance(dependency, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]+==[^=].*", dependency)
            for dependency in pip_dependencies
        ):
            return False, "environment-lock pip dependencies are not exact pins"
        expected.extend(pip_dependencies)

    detail = ", ".join(expected)
    return dependencies == expected, detail


def load_workflow(path: Path) -> dict[str, Any]:
    parsed = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"workflow is not a YAML mapping: {path}")
    return parsed


def scalar_commands(workflow: dict[str, Any]) -> str:
    return json.dumps(workflow, ensure_ascii=False, sort_keys=True)


def workflow_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    jobs = workflow.get("jobs", {})
    if not isinstance(jobs, dict):
        return steps
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        candidates = job.get("steps", [])
        if not isinstance(candidates, list):
            continue
        steps.extend(step for step in candidates if isinstance(step, dict))
    return steps


def action_steps(workflow: dict[str, Any], action: str) -> list[dict[str, Any]]:
    return [step for step in workflow_steps(workflow) if step.get("uses") == action]


def artifact_paths(step: dict[str, Any]) -> list[str]:
    settings = step.get("with", {})
    if not isinstance(settings, dict):
        return []
    value = settings.get("path", "")
    if not isinstance(value, str):
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]


def artifact_upload_valid(step: dict[str, Any]) -> bool:
    settings = step.get("with", {})
    if not isinstance(settings, dict):
        return False
    paths = artifact_paths(step)
    try:
        retention_days = int(settings.get("retention-days", "0"))
    except (TypeError, ValueError):
        return False
    return (
        step.get("if") == "always()"
        and bool(paths)
        and all(path.startswith("${{ runner.temp }}/") for path in paths)
        and "${{ github.run_id }}" in str(settings.get("name", ""))
        and settings.get("if-no-files-found") in {"warn", "error"}
        and 1 <= retention_days <= 90
    )


def defaults_are_project_scoped(
    workflow: dict[str, Any], expected_directory: str
) -> bool:
    defaults = workflow.get("defaults", {})
    run_defaults = defaults.get("run", {}) if isinstance(defaults, dict) else {}
    if not isinstance(run_defaults, dict):
        return False
    if run_defaults.get("shell") != "bash":
        return False
    if run_defaults.get("working-directory") != expected_directory:
        return False
    jobs = workflow.get("jobs", {})
    if not isinstance(jobs, dict):
        return False
    for job in jobs.values():
        if not isinstance(job, dict):
            return False
        job_defaults = job.get("defaults")
        if job_defaults is not None:
            job_run = job_defaults.get("run", {}) if isinstance(job_defaults, dict) else {}
            if not isinstance(job_run, dict):
                return False
            if job_run.get("working-directory", expected_directory) != expected_directory:
                return False
        for step in job.get("steps", []):
            if not isinstance(step, dict) or "run" not in step:
                continue
            if step.get("working-directory", expected_directory) != expected_directory:
                return False
    return True


def uses_steps_have_no_working_directory(workflow: dict[str, Any]) -> bool:
    for step in workflow_steps(workflow):
        if "uses" not in step:
            continue
        settings = step.get("with", {})
        if "working-directory" in step:
            return False
        if isinstance(settings, dict) and "working-directory" in settings:
            return False
    return True


def jobs_preserve_environment(
    workflow: dict[str, Any], expected: dict[str, str]
) -> bool:
    jobs = workflow.get("jobs", {})
    if not isinstance(jobs, dict) or not jobs:
        return False
    for job in jobs.values():
        if not isinstance(job, dict):
            return False
        environment = job.get("env", {})
        if not isinstance(environment, dict):
            return False
        if any(environment.get(key) != value for key, value in expected.items()):
            return False
    return True


def setup_python_cache_valid(
    workflow: dict[str, Any], action: str, dependency_path: str
) -> bool:
    matches = action_steps(workflow, action)
    if len(matches) != 1:
        return False
    settings = matches[0].get("with", {})
    return (
        isinstance(settings, dict)
        and settings.get("cache") == "pip"
        and settings.get("cache-dependency-path") == dependency_path
    )


def official_action_evidence_valid(
    evidence: dict[str, Any], expected_actions: Iterable[str]
) -> bool:
    releases = evidence.get("releases", [])
    if not isinstance(releases, list):
        return False
    rows = {
        row.get("uses"): row
        for row in releases
        if isinstance(row, dict) and isinstance(row.get("uses"), str)
    }
    if set(rows) != set(expected_actions):
        return False
    for action in expected_actions:
        row = rows[action]
        major = action.rsplit("@", 1)[-1]
        release = str(row.get("release", ""))
        url = str(row.get("url", ""))
        repository = action.split("@", 1)[0]
        if not release.startswith(f"{major}."):
            return False
        if url != f"https://github.com/{repository}/releases/tag/{release}":
            return False
    return (
        evidence.get("verified_on") == "2026-07-16"
        and evidence.get("runner") == "github-hosted ubuntu-latest"
        and evidence.get("minimum_node24_runner_version") == "2.327.1"
    )


def record(rows: list[dict[str, str]], check_id: str, passed: bool, detail: str) -> None:
    rows.append(
        {
            "schema_version": "github_actions_contract_check_v2",
            "check_id": check_id,
            "status": "pass" if passed else "fail",
            "detail": detail,
        }
    )


def validate(output: Path) -> list[dict[str, str]]:
    output.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    contract = config["workflow_contract"]
    fast_path = REPOSITORY_ROOT / contract["fast_workflow"]
    full_path = REPOSITORY_ROOT / contract["full_workflow"]
    repository_workflow_dir = (REPOSITORY_ROOT / ".github" / "workflows").resolve()
    legacy_workflow_dir = PROJECT_ROOT / ".github" / "workflows"
    legacy_workflows = (
        sorted(legacy_workflow_dir.glob("*.yml"))
        + sorted(legacy_workflow_dir.glob("*.yaml"))
        if legacy_workflow_dir.is_dir()
        else []
    )
    if not fast_path.is_file() or not full_path.is_file():
        missing = [
            repository_relative(path)
            for path in (fast_path, full_path)
            if not path.is_file()
        ]
        raise FileNotFoundError(f"repository-root workflows missing: {missing}")

    fast_text = fast_path.read_text(encoding="utf-8")
    full_text = full_path.read_text(encoding="utf-8")
    full_controller_text = FULL_CONTROLLER.read_text(encoding="utf-8")
    fast = load_workflow(fast_path)
    full = load_workflow(full_path)
    fast_blob = scalar_commands(fast)
    full_blob = scalar_commands(full)
    fast_steps = workflow_steps(fast)
    full_steps = workflow_steps(full)
    rows: list[dict[str, str]] = []

    actual_project_directory = PROJECT_ROOT.relative_to(REPOSITORY_ROOT).as_posix()
    expected_directory = contract["working_directory"]
    record(
        rows,
        "workflow_paths_are_repository_relative",
        contract.get("path_root") == "repository",
        "workflow_contract.path_root=repository",
    )
    record(
        rows,
        "project_directory_case_sensitive",
        actual_project_directory == expected_directory
        and (REPOSITORY_ROOT / expected_directory / "pyproject.toml").is_file(),
        f"repository project directory={expected_directory}",
    )
    record(
        rows,
        "fast_repository_root_location",
        fast_path.resolve().parent == repository_workflow_dir
        and repository_relative(fast_path) == ".github/workflows/ci.yml",
        repository_relative(fast_path),
    )
    record(
        rows,
        "full_repository_root_location",
        full_path.resolve().parent == repository_workflow_dir
        and repository_relative(full_path)
        == ".github/workflows/full_research_validation.yml",
        repository_relative(full_path),
    )
    record(
        rows,
        "legacy_workflow_directory_has_no_duplicates",
        not legacy_workflows,
        "legacy project .github/workflows contains no yml/yaml files",
    )
    record(rows, "fast_yaml_parse", True, repository_relative(fast_path))
    record(rows, "full_yaml_parse", True, repository_relative(full_path))

    fast_on = fast.get("on", {})
    full_on = full.get("on", {})
    record(
        rows,
        "fast_push_pull_request",
        isinstance(fast_on, dict) and {"push", "pull_request"}.issubset(fast_on),
        "fast workflow runs on push and pull_request",
    )
    record(
        rows,
        "full_workflow_dispatch",
        isinstance(full_on, dict) and "workflow_dispatch" in full_on,
        "full workflow is manually dispatchable",
    )
    record(
        rows,
        "fast_project_working_directory",
        defaults_are_project_scoped(fast, expected_directory),
        f"defaults.run shell=bash working-directory={expected_directory}",
    )
    record(
        rows,
        "full_project_working_directory",
        defaults_are_project_scoped(full, expected_directory),
        f"defaults.run shell=bash working-directory={expected_directory}",
    )
    record(
        rows,
        "uses_steps_have_no_working_directory",
        uses_steps_have_no_working_directory(fast)
        and uses_steps_have_no_working_directory(full),
        "working-directory applies only through defaults.run",
    )

    for action_key in ("checkout_action", "setup_python_action"):
        expected = contract[action_key]
        record(rows, f"fast_{action_key}", expected in fast_text, expected)
        record(rows, f"full_{action_key}", expected in full_text, expected)
    expected_upload = contract["upload_artifact_action"]
    record(rows, "fast_artifact_action", expected_upload in fast_text, expected_upload)
    record(rows, "full_artifact_action", expected_upload in full_text, expected_upload)

    dependency_path = contract["cache_dependency_path"]
    record(
        rows,
        "cache_dependency_path_exists",
        (REPOSITORY_ROOT / dependency_path).is_file(),
        dependency_path,
    )
    renderer_dependency_valid, renderer_requirement = (
        frozen_renderer_dependency_valid(REPOSITORY_ROOT / dependency_path)
    )
    record(
        rows,
        "frozen_camera_renderer_dependency_pin",
        renderer_dependency_valid,
        renderer_requirement,
    )
    dependency_lock_valid, dependency_lock_detail = (
        frozen_direct_dependency_lock_valid(REPOSITORY_ROOT / dependency_path)
    )
    record(
        rows,
        "frozen_direct_dependency_lock",
        dependency_lock_valid,
        dependency_lock_detail,
    )
    record(
        rows,
        "fast_setup_python_pip_cache",
        setup_python_cache_valid(fast, contract["setup_python_action"], dependency_path),
        f"cache=pip cache-dependency-path={dependency_path}",
    )
    record(
        rows,
        "full_setup_python_pip_cache",
        setup_python_cache_valid(full, contract["setup_python_action"], dependency_path),
        f"cache=pip cache-dependency-path={dependency_path}",
    )

    required_environment = contract["required_job_environment"]
    record(
        rows,
        "fast_ubuntu_environment",
        jobs_preserve_environment(fast, required_environment),
        json.dumps(required_environment, sort_keys=True),
    )
    record(
        rows,
        "full_ubuntu_environment",
        jobs_preserve_environment(full, required_environment),
        json.dumps(required_environment, sort_keys=True),
    )
    windows_only = re.compile(r"\b(?:powershell|pwsh)\b|[A-Za-z]:\\|\\\\", re.I)
    record(
        rows,
        "ubuntu_shell_portability",
        windows_only.search(fast_text + "\n" + full_text) is None,
        "no PowerShell command, drive-qualified path, or UNC path",
    )

    fast_requirements = {
        "install_command": "python -m pip install -e . PyYAML",
        "import_checks": "import qp_orbits",
        "unit_tests": "unittest discover",
        "benchmark_registry_integrity": "test_invariant_bundle_benchmark_registry",
        "small_synthetic_bundle_tests": "test_bundle_phase_alignment",
        "one_small_physical_benchmark": "run_ci_small_physical_benchmark.py",
        "document_registry_consistency": "test_stage_g_delivery_artifacts",
        "git_diff_check": "git diff --check",
        "git_clean_check": "git status --porcelain",
    }
    for check_id, needle in fast_requirements.items():
        record(rows, f"fast_{check_id}", needle in fast_blob, needle)
    full_requirements = {
        "install_command": "python -m pip install -e . PyYAML",
        "isolated_controller": "run_ci_full_research_validation.py",
        "fifteen_case_bundle": "--max-bundle-wall-seconds",
        "selected_manifold": "--max-manifold-wall-seconds",
        "schema_check": "--check-only",
        "git_diff_check": "git diff --check",
        "git_clean_check": "git status --porcelain",
    }
    for check_id, needle in full_requirements.items():
        record(rows, f"full_{check_id}", needle in full_blob, needle)

    record(
        rows,
        "fast_read_only_permissions",
        fast.get("permissions", {}).get("contents") == "read",
        "permissions.contents=read",
    )
    record(
        rows,
        "full_read_only_permissions",
        full.get("permissions", {}).get("contents") == "read",
        "permissions.contents=read",
    )
    record(
        rows,
        "fast_runner_temp_output",
        "RUNNER_TEMP" in fast_text and "runner.temp" in fast_text,
        "generated evidence uses runner temporary storage",
    )
    record(
        rows,
        "full_runner_temp_output",
        "RUNNER_TEMP" in full_text and "runner.temp" in full_text,
        "full numerical outputs use runner temporary storage",
    )
    forbidden_writers = contract["forbidden_direct_writers"]
    record(
        rows,
        "workflows_do_not_invoke_authoritative_writers",
        all(writer not in fast_text and writer not in full_text for writer in forbidden_writers),
        "authoritative writers are absent from workflow run commands",
    )
    record(
        rows,
        "both_authoritative_hash_guards",
        all(
            text.count("verify_ci_authoritative_immutability.py") == 2
            and " snapshot" in text
            and " compare" in text
            for text in (fast_text, full_text)
        ),
        "snapshot and compare guards are present in both workflows",
    )

    fast_uploads = action_steps(fast, expected_upload)
    full_uploads = action_steps(full, expected_upload)
    fast_expected_paths = {
        "${{ runner.temp }}/fast_ci_physical",
        "${{ runner.temp }}/workflow_contracts",
        "${{ runner.temp }}/authoritative_before.json",
        "${{ runner.temp }}/authoritative_before_after.csv",
    }
    full_expected_paths = {
        "${{ runner.temp }}/full_research_validation",
        "${{ runner.temp }}/authoritative_before.json",
    }
    record(
        rows,
        "fast_artifact_upload_config",
        len(fast_uploads) == 1 and artifact_upload_valid(fast_uploads[0]),
        "always upload uniquely named runner.temp evidence for 14 days",
    )
    record(
        rows,
        "full_artifact_upload_config",
        len(full_uploads) == 1 and artifact_upload_valid(full_uploads[0]),
        "always upload uniquely named runner.temp evidence for 14 days",
    )
    record(
        rows,
        "fast_artifact_paths_complete",
        len(fast_uploads) == 1 and set(artifact_paths(fast_uploads[0])) == fast_expected_paths,
        "fast evidence, workflow contracts, and immutability reports are uploaded",
    )
    record(
        rows,
        "full_artifact_paths_complete",
        len(full_uploads) == 1 and set(artifact_paths(full_uploads[0])) == full_expected_paths,
        "the complete full-validation directory and before snapshot are uploaded",
    )
    record(
        rows,
        "failed_and_boundary_results_not_filtered",
        len(full_uploads) == 1
        and "${{ runner.temp }}/full_research_validation" in artifact_paths(full_uploads[0])
        and "failed_bundle_cases_visible" in full_controller_text
        and "failed_manifold_cases_visible" in full_controller_text
        and "Numerical failures and boundary cases remain present" in full_controller_text,
        "full generated CSV/log/hash tree retains failed and boundary rows",
    )

    expected_actions = (
        contract["checkout_action"],
        contract["setup_python_action"],
        contract["upload_artifact_action"],
    )
    action_evidence = config["official_action_version_evidence"]
    record(
        rows,
        "official_action_release_evidence",
        official_action_evidence_valid(action_evidence, expected_actions),
        "official releases verified 2026-07-16 for github-hosted ubuntu-latest",
    )

    csv_path = output / "workflow_contract_checks.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["status"] != "pass"]
    summary = {
        "schema_version": "github_actions_contract_summary_v2",
        "status": "PASS" if not failures else "FAIL",
        "checks": len(rows),
        "passed": len(rows) - len(failures),
        "failed": len(failures),
        "failed_check_ids": [row["check_id"] for row in failures],
        "path_root": "repository",
        "project_directory": expected_directory,
        "fast_workflow": repository_relative(fast_path),
        "full_workflow": repository_relative(full_path),
        "official_action_version_evidence": action_evidence,
        "truth_boundary": config["truth_boundaries"],
    }
    with (output / "workflow_contract_summary.json").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        stream.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if failures:
        raise RuntimeError(f"workflow contract failures: {summary['failed_check_ids']}")
    print(f"workflow contract PASS checks={len(rows)}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    validate(args.output_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
