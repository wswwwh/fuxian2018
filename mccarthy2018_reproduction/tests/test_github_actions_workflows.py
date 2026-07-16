"""Contract tests for the fast and manually dispatched research CI workflows."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_ci_full_research_validation as full_ci  # noqa: E402


CONFIG = (
    ROOT / "research" / "invariant_bundles" / "configs" / "ci_validation.json"
)
FAST = ROOT / ".github" / "workflows" / "ci.yml"
FULL = ROOT / ".github" / "workflows" / "full_research_validation.yml"
HOLDOUT = (
    ROOT
    / "data"
    / "computed"
    / "chapter4_fig43_fig46_projection_holdout_audit.csv"
)
METHOD = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "csv"
    / "method_comparison.csv"
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

    def test_actions_and_authoritative_hash_guard_are_pinned(self) -> None:
        combined = FAST.read_text(encoding="utf-8") + FULL.read_text(encoding="utf-8")
        for action in (
            "actions/checkout@v6",
            "actions/setup-python@v6",
            "actions/upload-artifact@v7",
        ):
            self.assertIn(action, combined)
        self.assertEqual(
            combined.count("verify_ci_authoritative_immutability.py"),
            4,
        )

    def test_protected_authoritative_paths_exist(self) -> None:
        protected = self.config["authoritative_files_protected"]
        self.assertGreaterEqual(len(protected), 10)
        for relative in protected:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_full_controller_rejects_checkout_output(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "outside the repository"):
            full_ci.external_output_root(
                ROOT / "research" / "invariant_bundles" / "ci_forbidden",
                require_existing=False,
            )

    def test_frozen_chapter4_and_route_h_boundaries_remain_visible(self) -> None:
        holdout = read_csv(HOLDOUT)
        self.assertEqual(len(holdout), 4)
        self.assertTrue(all(row["holdout_gate"] == "fail" for row in holdout))
        self.assertTrue(
            all(row["paper_projection_acceptance"] == "fail" for row in holdout)
        )
        self.assertTrue(
            all(row["paper_3d_equivalence"] == "false" for row in holdout)
        )
        method = {
            (row["case_id"], row["method"]): row for row in read_csv(METHOD)
        }
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
