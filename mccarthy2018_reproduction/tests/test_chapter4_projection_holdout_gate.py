"""Synthetic gate tests for the frozen Chapter 4 holdout evaluator."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_chapter4_fig43_fig46_projection_holdout_audit.py"
SPEC = importlib.util.spec_from_file_location("chapter4_holdout_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Chapter4ProjectionHoldoutGateTests(unittest.TestCase):
    def test_all_pre_registered_thresholds_are_required(self) -> None:
        passing = {
            "symmetric_chamfer_diagonal_fraction": 0.019,
            "f1_at_0p01_diagonal": 0.71,
            "hd95_diagonal_fraction": 0.049,
            "area_ratio_prediction_over_paper": 1.0,
        }
        self.assertEqual(
            MODULE._holdout_failures(passing, anchor_rmse=3.9, anchor_max=7.9),
            [],
        )
        failing = dict(passing, f1_at_0p01_diagonal=0.69)
        self.assertEqual(
            MODULE._holdout_failures(failing, anchor_rmse=3.9, anchor_max=7.9),
            ["f1_lt_0.70"],
        )

    def test_area_gate_has_both_bounds(self) -> None:
        baseline = {
            "symmetric_chamfer_diagonal_fraction": 0.0,
            "f1_at_0p01_diagonal": 1.0,
            "hd95_diagonal_fraction": 0.0,
            "area_ratio_prediction_over_paper": 0.66,
        }
        self.assertIn(
            "area_ratio_lt_0.67",
            MODULE._holdout_failures(baseline, anchor_rmse=0.0, anchor_max=0.0),
        )
        baseline["area_ratio_prediction_over_paper"] = 1.51
        self.assertIn(
            "area_ratio_gt_1.50",
            MODULE._holdout_failures(baseline, anchor_rmse=0.0, anchor_max=0.0),
        )


if __name__ == "__main__":
    unittest.main()
