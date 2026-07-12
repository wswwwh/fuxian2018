"""Regression tests for the hybrid Route H reconstruction chain."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter3_route_h_hybrid_cold_start_audit as hybrid_audit


class HybridColdStartAuditTests(unittest.TestCase):
    def test_zero_start_checkpoint_and_four_target_chain_pass(self) -> None:
        row = hybrid_audit.build_row()

        self.assertEqual(row["status"], "pass")
        self.assertTrue(row["zero_start_attempt_present"])
        self.assertTrue(row["checkpoint_hash_matches_attempt"])
        self.assertEqual(int(row["paper_precision_target_count"]), 4)
        self.assertGreaterEqual(int(row["strict_fixed_time_target_count"]), 3)
        self.assertEqual(int(row["state_target_count"]), 4)
        self.assertEqual(int(row["independently_revalidated_target_count"]), 4)


if __name__ == "__main__":
    unittest.main()
