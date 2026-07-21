"""Regression tests for the Stage-H2 stable-bundle campaign."""

from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "submission_candidate"
    / "results"
    / "stable_bundles"
)
COMPARISON = OUTPUT / "stable_bundle_comparison.csv"
RESULTS = OUTPUT / "stable_bundle_results.npz"
SUMMARY = OUTPUT / "stable_bundle_summary.json"
HASHES = OUTPUT / "artifact_hashes.csv"
AUDIT = OUTPUT / "stable_bundle_audit.md"
FAILURES = OUTPUT / "failure_evidence.md"
SCRIPT = ROOT / "scripts" / "run_submission_candidate_stable_bundles.py"
UNSTABLE = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "csv"
    / "method_comparison.csv"
)

CASES = {
    "h2_stable_em_halo_12p40_n45": "em_halo_12p40_n45",
    "h2_stable_em_vertical_12p66_n57": "em_vertical_12p66_n57",
    "h2_stable_se_active_geometry_member_468": "se_active_geometry_member_468",
}
METHODS = {
    "traditional_pointwise_eigendecomposition",
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
}
IMPROVED = METHODS - {"traditional_pointwise_eigendecomposition"}


class SubmissionCandidateStableBundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with COMPARISON.open(newline="", encoding="utf-8") as stream:
            cls.rows = list(csv.DictReader(stream))
        with UNSTABLE.open(newline="", encoding="utf-8") as stream:
            cls.unstable_rows = list(csv.DictReader(stream))
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    def test_exact_case_method_grid_and_outcomes(self) -> None:
        self.assertEqual(len(self.rows), 3 * 3)
        self.assertEqual({row["case_id"] for row in self.rows}, set(CASES))
        self.assertEqual({row["method"] for row in self.rows}, METHODS)
        self.assertEqual({row["branch"] for row in self.rows}, {"stable"})
        self.assertEqual(
            Counter(row["research_status"] for row in self.rows),
            {"accepted": 6, "fail": 3},
        )
        for row in self.rows:
            if row["method"] in IMPROVED:
                self.assertEqual(row["research_status"], "accepted")
            else:
                self.assertEqual(row["research_status"], "fail")

    def test_improved_methods_are_real_one_dimensional_stable_bundles(self) -> None:
        for row in self.rows:
            if row["method"] not in IMPROVED:
                continue
            with self.subTest(case=row["case_id"], method=row["method"]):
                self.assertEqual(int(row["bundle_dimension"]), 1)
                self.assertEqual(row["classification"], "real_1d_hyperbolic_bundle")
                self.assertLess(float(row["max_invariance_residual"]), 1.0e-6)
                self.assertLess(float(row["bundle_multiplier_estimate"]), 1.0)
                self.assertLess(float(row["lyapunov_estimate_per_day"]), 0.0)
                self.assertEqual(row["stable_multiplier_lt_one"], "true")

    def test_stable_and_unstable_multiplier_pairs_are_reciprocal(self) -> None:
        stable_index = {
            (row["case_id"], row["method"]): row for row in self.rows
        }
        unstable_index = {
            (row["case_id"], row["method"]): row
            for row in self.unstable_rows
        }
        for stable_case, source_case in CASES.items():
            for method in IMPROVED:
                stable = float(
                    stable_index[(stable_case, method)][
                        "bundle_multiplier_estimate"
                    ]
                )
                unstable = float(
                    unstable_index[(source_case, method)][
                        "bundle_multiplier_estimate"
                    ]
                )
                with self.subTest(case=stable_case, method=method):
                    self.assertAlmostEqual(stable * unstable, 1.0, places=8)

    def test_npz_preserves_each_basis_and_metrics(self) -> None:
        with np.load(RESULTS, allow_pickle=False) as archive:
            self.assertEqual(set(archive["case_ids"].tolist()), set(CASES))
            for row in self.rows:
                prefix = (
                    row["case_id"].replace("-", "_")
                    + "__"
                    + row["method"].replace("-", "_")
                )
                bases = np.asarray(archive[prefix + "__bases"], dtype=float)
                residuals = np.asarray(
                    archive[prefix + "__invariance_residuals"], dtype=float
                )
                self.assertEqual(bases.shape[0], residuals.size)
                self.assertEqual(bases.shape[1:], (6, 1))
                self.assertTrue(np.all(np.isfinite(bases)))
                self.assertTrue(np.all(np.isfinite(residuals)))

    def test_summary_and_failure_evidence_retain_pointwise_failures(self) -> None:
        self.assertEqual(self.summary["h2_gate_status"], "pass")
        self.assertEqual(
            self.summary["cases_with_both_improved_methods_accepted"], 3
        )
        self.assertEqual(self.summary["accepted_improved_rows"], 6)
        failures = FAILURES.read_text(encoding="utf-8")
        self.assertEqual(
            failures.count("traditional_pointwise_eigendecomposition"), 3
        )
        audit = AUDIT.read_text(encoding="utf-8")
        self.assertIn("frozen 54-figure registry", audit)
        self.assertIn("Pointwise failures remain", audit)

    def test_artifact_hash_manifest_and_check_mode(self) -> None:
        with HASHES.open(newline="", encoding="utf-8") as stream:
            hashes = list(csv.DictReader(stream))
        self.assertEqual(len(hashes), 7)
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("STAGE-H2 STABLE BUNDLE CHECK PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
