"""Regression gates for the frozen McCarthy 2018 reproduction baseline."""

from __future__ import annotations

import csv
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_reproduction_baseline_freeze.py"
SUMMARY = ROOT / "data" / "computed" / "reproduction_baseline_v1_summary.csv"
MANIFEST = ROOT / "data" / "computed" / "reproduction_baseline_v1_manifest.csv"
DOCUMENT = ROOT / "docs" / "reproduction_baseline_v1.md"


class ReproductionBaselineFreezeTests(unittest.TestCase):
    def test_generated_baseline_is_current_and_read_only_check_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("BASELINE FREEZE CHECK PASS", result.stdout)
        self.assertIn("holdout=0/4", result.stdout)

    def test_summary_preserves_counts_and_scientific_boundaries(self) -> None:
        with SUMMARY.open(newline="", encoding="utf-8") as stream:
            rows = {row["metric_id"]: row for row in csv.DictReader(stream)}
        self.assertEqual(rows["target_rows"]["value"], "54")
        self.assertEqual(rows["v0_targets"]["value"], "13")
        self.assertEqual(rows["v2_targets"]["value"], "41")
        self.assertEqual(rows["evidence_accepted"]["value"], "7")
        self.assertEqual(rows["evidence_boundary"]["value"], "30")
        self.assertEqual(rows["evidence_diagnostic"]["value"], "5")
        self.assertEqual(rows["evidence_proxy"]["value"], "12")
        self.assertEqual(rows["chapter4_frozen_holdout_pass"]["value"], "0")
        self.assertEqual(rows["chapter4_frozen_holdout_total"]["value"], "4")
        self.assertEqual(rows["route_h_real_hyperbolic_pass"]["value"], "1")
        self.assertEqual(rows["route_h_real_hyperbolic_total"]["value"], "31")
        self.assertEqual(rows["chapter5_bcr4bp_paper_equivalence_pass"]["value"], "0")

    def test_manifest_binds_goal_primary_source_and_protection_locks(self) -> None:
        with MANIFEST.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        by_path = {row["path"]: row for row in rows}
        required_suffixes = (
            "计划与目标/codex_goal_invariant_bundles.md",
            "目标论文/2018_McCarthy_拟周期轨道.pdf",
            "data/computed/chapter4_fig43_fig46_projection_fit_lock.json",
            "data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv",
            "src/qp_orbits/chapter4_reproduction_lock.py",
        )
        for suffix in required_suffixes:
            matches = [row for path, row in by_path.items() if path.endswith(suffix)]
            self.assertEqual(len(matches), 1, suffix)
            self.assertEqual(len(matches[0]["sha256"]), 64)
        self.assertEqual(
            by_path[
                "data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv"
            ]["freeze_policy"],
            "immutable_failed_boundary",
        )

    def test_document_states_non_equivalence_and_stage_b_block(self) -> None:
        text = DOCUMENT.read_text(encoding="utf-8")
        self.assertIn(
            "本基线用于支持后续原创方法研究，不代表 McCarthy 2018 全文严格数值等价复现",
            text,
        )
        self.assertIn("阶段 B 的 N33/N45 重建尚未完成", text)
        self.assertIn("paper_projection=fail", text)


if __name__ == "__main__":
    unittest.main()
