"""Behavior tests for conservative staged-goal gate evaluation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_mccarthy2018_staged_goal_gate_audit as staged_audit


class StagedGoalGateAuditTests(unittest.TestCase):
    def test_complex_manifold_eigenvalues_block_chapter4_and_goal_completion(self) -> None:
        rows = staged_audit.build_rows()
        by_gate = {row["gate_id"]: row for row in rows}

        chapter4 = by_gate["C4-ROUTE-H-DG-MANIFOLD"]
        cold_start = by_gate["C3-ROUTE-H-COLD-START"]
        goal = by_gate["STAGED-GOAL-STATUS"]
        self.assertEqual(cold_start["status"], "fail")
        self.assertEqual(chapter4["status"], "not_run_or_fail")
        self.assertGreater(float(chapter4["value"]), 0.3)
        self.assertIn("1/31", chapter4["notes"])
        self.assertEqual(
            goal["status"],
            "chapter3_route_h_artifact_pass_cold_start_failed",
        )


if __name__ == "__main__":
    unittest.main()
