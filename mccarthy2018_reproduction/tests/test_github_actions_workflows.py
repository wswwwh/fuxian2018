"""Contract tests for repository-root GitHub Actions workflows."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_ci_full_research_validation as full_ci  # noqa: E402
import validate_github_actions_workflows as workflow_contracts  # noqa: E402


REPOSITORY_ROOT = workflow_contracts.REPOSITORY_ROOT
CONFIG = (
    PROJECT_ROOT
    / "research"
    / "invariant_bundles"
    / "configs"
    / "ci_validation.json"
)
FAST = REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml"
FULL = REPOSITORY_ROOT / ".github" / "workflows" / "full_research_validation.yml"
HOLDOUT = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter4_fig43_fig46_projection_holdout_audit.csv"
)
METHOD = (
    PROJECT_ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "csv"
    / "method_comparison.csv"
)
CI_ARTIFACTS = (
    PROJECT_ROOT
    / "research"
    / "invariant_bundles"
    / "ci_validation"
    / "artifact_hashes.csv"
)


def load_yaml(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class GithubActionsWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.fast = load_yaml(FAST)
        cls.full = load_yaml(FULL)

    def test_workflows_are_only_at_repository_root(self) -> None:
        self.assertEqual(PROJECT_ROOT.name, "mccarthy2018_reproduction")
        self.assertTrue(FAST.is_file())
        self.assertTrue(FULL.is_file())
        self.assertEqual(
            FAST.relative_to(REPOSITORY_ROOT).as_posix(),
            ".github/workflows/ci.yml",
        )
        self.assertEqual(
            FULL.relative_to(REPOSITORY_ROOT).as_posix(),
            ".github/workflows/full_research_validation.yml",
        )
        legacy = PROJECT_ROOT / ".github" / "workflows"
        duplicates = (
            list(legacy.glob("*.yml")) + list(legacy.glob("*.yaml"))
            if legacy.is_dir()
            else []
        )
        self.assertEqual(duplicates, [])

    def test_fast_workflow_has_every_required_gate(self) -> None:
        self.assertEqual(set(self.fast["on"]), {"push", "pull_request"})
        text = FAST.read_text(encoding="utf-8")
        for needle in (
            "Import checks",
            "Benchmark registry integrity",
            "Small synthetic bundle tests",
            "One small physical benchmark",
            "Document registry consistency",
            "Unit tests",
            "git diff --check",
            "git status --porcelain",
        ):
            self.assertIn(needle, text)

    def test_full_workflow_is_manual_isolated_and_uploads_artifacts(self) -> None:
        self.assertEqual(set(self.full["on"]), {"workflow_dispatch"})
        text = FULL.read_text(encoding="utf-8")
        self.assertIn("run_ci_full_research_validation.py", text)
        self.assertIn("--check-only", text)
        self.assertIn("actions/upload-artifact@v7", text)
        self.assertIn("RUNNER_TEMP}/full_research_validation", text)
        self.assertEqual(self.full["permissions"]["contents"], "read")

    def test_run_defaults_and_job_environment_are_ubuntu_safe(self) -> None:
        expected_directory = "mccarthy2018_reproduction"
        expected_environment = {"MPLBACKEND": "Agg", "PYTHONHASHSEED": "0", "PYTHONPATH": "src"}
        for workflow in (self.fast, self.full):
            self.assertEqual(
                workflow["defaults"]["run"],
                {"shell": "bash", "working-directory": expected_directory},
            )
            self.assertTrue(
                workflow_contracts.defaults_are_project_scoped(
                    workflow, expected_directory
                )
            )
            self.assertTrue(
                workflow_contracts.uses_steps_have_no_working_directory(workflow)
            )
            self.assertTrue(
                workflow_contracts.jobs_preserve_environment(
                    workflow, expected_environment
                )
            )
        combined = FAST.read_text(encoding="utf-8") + FULL.read_text(encoding="utf-8")
        self.assertNotIn("pwsh", combined.lower())
        self.assertNotIn("powershell", combined.lower())
        self.assertNotIn("\\", combined)

    def test_setup_python_cache_uses_repository_root_dependency_path(self) -> None:
        dependency = "mccarthy2018_reproduction/pyproject.toml"
        action = "actions/setup-python@v6"
        self.assertTrue((REPOSITORY_ROOT / dependency).is_file())
        for workflow in (self.fast, self.full):
            self.assertTrue(
                workflow_contracts.setup_python_cache_valid(
                    workflow, action, dependency
                )
            )

    def test_actions_and_authoritative_hash_guard_are_pinned(self) -> None:
        combined = FAST.read_text(encoding="utf-8") + FULL.read_text(encoding="utf-8")
        expected_actions = (
            "actions/checkout@v6",
            "actions/setup-python@v6",
            "actions/upload-artifact@v7",
        )
        for action in expected_actions:
            self.assertIn(action, combined)
        self.assertEqual(combined.count("verify_ci_authoritative_immutability.py"), 4)
        self.assertTrue(
            workflow_contracts.official_action_evidence_valid(
                self.config["official_action_version_evidence"], expected_actions
            )
        )

    def test_artifact_upload_contracts_are_complete(self) -> None:
        action = "actions/upload-artifact@v7"
        fast_upload = workflow_contracts.action_steps(self.fast, action)
        full_upload = workflow_contracts.action_steps(self.full, action)
        self.assertEqual(len(fast_upload), 1)
        self.assertEqual(len(full_upload), 1)
        self.assertTrue(workflow_contracts.artifact_upload_valid(fast_upload[0]))
        self.assertTrue(workflow_contracts.artifact_upload_valid(full_upload[0]))
        self.assertIn(
            "${{ runner.temp }}/full_research_validation",
            workflow_contracts.artifact_paths(full_upload[0]),
        )

    def test_ci_artifact_hash_manifest_is_repository_rooted_and_current(self) -> None:
        rows = read_csv(CI_ARTIFACTS)
        self.assertTrue(rows)
        self.assertTrue(all(row["path_root"] == "repository" for row in rows))
        for row in rows:
            path = REPOSITORY_ROOT / row["path"]
            self.assertTrue(path.is_file(), row["path"])
            self.assertEqual(path.stat().st_size, int(row["bytes"]), row["path"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest().upper(),
                row["sha256"],
                row["path"],
            )

    def test_local_validator_passes_all_contracts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow_contract_test_") as tmp:
            rows = workflow_contracts.validate(Path(tmp))
            self.assertTrue(rows)
            self.assertTrue(all(row["status"] == "pass" for row in rows))
            summary = json.loads(
                (Path(tmp) / "workflow_contract_summary.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["path_root"], "repository")
        self.assertEqual(summary["project_directory"], "mccarthy2018_reproduction")

    def test_protected_authoritative_paths_exist(self) -> None:
        protected = self.config["authoritative_files_protected"]
        self.assertEqual(len(protected), 11)
        for relative in protected:
            self.assertTrue((PROJECT_ROOT / relative).is_file(), relative)

    def test_full_controller_rejects_any_checkout_output(self) -> None:
        for forbidden in (
            PROJECT_ROOT / "research" / "invariant_bundles" / "ci_forbidden",
            REPOSITORY_ROOT / "repository_sibling_forbidden",
        ):
            with self.assertRaisesRegex(RuntimeError, "outside the repository"):
                full_ci.external_output_root(forbidden, require_existing=False)
        with tempfile.TemporaryDirectory(prefix="full_ci_external_test_") as tmp:
            accepted = full_ci.external_output_root(
                Path(tmp) / "evidence", require_existing=False
            )
            self.assertNotIn(REPOSITORY_ROOT, accepted.parents)

    def test_failed_and_boundary_rows_remain_visible(self) -> None:
        controller = (
            PROJECT_ROOT / "scripts" / "run_ci_full_research_validation.py"
        ).read_text(encoding="utf-8")
        self.assertIn("failed_bundle_cases_visible", controller)
        self.assertIn("failed_manifold_cases_visible", controller)
        self.assertIn("Numerical failures and boundary cases remain present", controller)

    def test_frozen_chapter4_and_route_h_boundaries_remain_visible(self) -> None:
        holdout = read_csv(HOLDOUT)
        self.assertEqual(len(holdout), 4)
        self.assertTrue(all(row["holdout_gate"] == "fail" for row in holdout))
        self.assertTrue(
            all(row["paper_projection_acceptance"] == "fail" for row in holdout)
        )
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in holdout))
        method = {(row["case_id"], row["method"]): row for row in read_csv(METHOD)}
        schur = "ordered_partial_real_schur_tracking"
        physical = method[("route_h_member_68", schur)]
        legacy = method[("route_h_member_68_legacy_dg_positive", schur)]
        self.assertEqual(
            (physical["bundle_dimension"], physical["research_status"]),
            ("2", "fail"),
        )
        self.assertEqual(
            (legacy["bundle_dimension"], legacy["research_status"]),
            ("1", "accepted"),
        )


if __name__ == "__main__":
    unittest.main()
