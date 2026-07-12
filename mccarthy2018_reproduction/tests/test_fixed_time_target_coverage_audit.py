"""Regression tests for the four-anchor fixed-time coverage audit."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter3_route_h_fixed_time_target_coverage_audit as coverage_audit


class FixedTimeTargetCoverageAuditTests(unittest.TestCase):
    def test_only_exact_fixed_time_rows_count_as_strict(self) -> None:
        rows = coverage_audit.build_rows()

        self.assertEqual(len(rows), 4)
        self.assertEqual(
            sum(row["strict_fixed_time_status"] == "pass" for row in rows),
            1,
        )
        self.assertEqual(
            sum(row["paper_rounding_boundary_status"] == "pass" for row in rows),
            1,
        )
        strict = next(row for row in rows if row["strict_fixed_time_status"] == "pass")
        self.assertAlmostEqual(float(strict["target_jacobi"]), 2.9221)


if __name__ == "__main__":
    unittest.main()
