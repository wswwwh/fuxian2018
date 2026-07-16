"""Regression tests for the stored Stage-F manifold campaign."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "csv"
    / "manifold_convergence.csv"
)
METHODS = {
    "traditional_pointwise_eigendecomposition",
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
}


class InvariantBundleManifoldArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with OUTPUT.open(newline="", encoding="utf-8") as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_campaign_has_seven_cases_three_methods_three_epsilons_two_signs(self) -> None:
        self.assertEqual(len(self.rows), 7 * 3 * 3 * 2)
        self.assertEqual(len({row["case_id"] for row in self.rows}), 7)
        self.assertEqual({row["method"] for row in self.rows}, METHODS)
        self.assertEqual(
            {float(row["perturbation_norm"]) for row in self.rows},
            {5.0e-8, 1.0e-7, 2.0e-7},
        )
        self.assertEqual(
            {int(row["perturbation_sign"]) for row in self.rows}, {-1, 1}
        )

    def test_conditions_are_identical_across_methods_within_each_case(self) -> None:
        condition_fields = (
            "spectral_samples",
            "propagation_time_nd",
            "propagation_time_days",
            "time_samples",
            "coordinate_system",
            "integrator",
            "event_condition",
        )
        for case_id in {row["case_id"] for row in self.rows}:
            selected = [row for row in self.rows if row["case_id"] == case_id]
            for field in condition_fields:
                with self.subTest(case=case_id, field=field):
                    self.assertEqual(len({row[field] for row in selected}), 1)

    def test_jacobi_and_initial_linear_metrics_remain_strict(self) -> None:
        drifts = np.asarray(
            [float(row["manifold_jacobi_drift"]) for row in self.rows]
        )
        initial_ratios = np.asarray(
            [float(row["initial_linear_growth_ratio"]) for row in self.rows]
        )
        self.assertTrue(np.all(np.isfinite(drifts)))
        self.assertLess(float(np.max(drifts)), 1.0e-10)
        self.assertLess(float(np.max(np.abs(initial_ratios - 1.0))), 0.05)

    def test_high_resolution_improved_methods_pass_and_low_resolution_boundary_is_visible(self) -> None:
        nominal_positive = [
            row
            for row in self.rows
            if float(row["perturbation_norm"]) == 1.0e-7
            and int(row["perturbation_sign"]) == 1
        ]
        by_key = {(row["case_id"], row["method"]): row for row in nominal_positive}
        for case_id in (
            "em_halo_12p40_n45",
            "em_vertical_12p66_n57",
            "se_active_geometry_member_468",
        ):
            for method in (
                "ordered_partial_real_schur_tracking",
                "qr_svd_shifted_cocycle_iteration",
            ):
                self.assertEqual(by_key[(case_id, method)]["status"], "accepted")
        self.assertEqual(
            by_key[
                (
                    "em_halo_12p40_n21",
                    "qr_svd_shifted_cocycle_iteration",
                )
            ]["status"],
            "fail",
        )
        self.assertIn(
            "cross_resolution_manifold_distance_gt_0p01",
            by_key[
                (
                    "em_halo_12p40_n21",
                    "qr_svd_shifted_cocycle_iteration",
                )
            ]["failure_reason"],
        )


if __name__ == "__main__":
    unittest.main()
