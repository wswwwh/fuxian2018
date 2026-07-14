"""Regression tests for the native-image Fig. 4.2 comparison audit."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter4_fig42_digitized_comparison_audit as fig42_audit


class Chapter4Figure42DigitizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = fig42_audit.analyze()

    def test_native_curve_extraction_and_axis_calibration_are_stable(self) -> None:
        summary = self.result.summary

        self.assertEqual(int(summary["source_image_width"]), 1517)
        self.assertEqual(int(summary["source_image_height"]), 682)
        self.assertGreaterEqual(int(summary["blue_curve_columns"]), 1000)
        self.assertLess(float(summary["axis_calibration_max_abs_residual_px"]), 1.0e-6)

    def test_overlap_passes_without_hiding_the_uncovered_tail(self) -> None:
        summary = self.result.summary

        self.assertEqual(summary["pointwise_overlap_acceptance"], "true")
        self.assertEqual(summary["full_curve_coverage"], "false")
        self.assertEqual(
            summary["overall_status"],
            "pointwise_overlap_pass_full_curve_coverage_boundary",
        )
        self.assertGreaterEqual(int(summary["overlap_comparison_rows"]), 10)
        self.assertGreater(float(summary["reference_time_coverage_fraction"]), 0.85)
        self.assertLess(float(summary["pointwise_rmse_nu"]), 0.6)
        self.assertLess(float(summary["pointwise_max_abs_error_nu"]), 0.7)
        self.assertGreater(float(summary["computed_tail_time_gap_days"]), 0.04)


if __name__ == "__main__":
    unittest.main()
