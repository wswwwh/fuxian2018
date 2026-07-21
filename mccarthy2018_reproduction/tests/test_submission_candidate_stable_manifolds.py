"""Regression tests for the Stage-H2 stable-manifold campaign."""

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
    / "stable_manifolds"
)
COMPARISON = OUTPUT / "stable_manifold_convergence.csv"
RESULTS = OUTPUT / "stable_manifold_convergence.npz"
SUMMARY = OUTPUT / "stable_manifold_summary.json"
HASHES = OUTPUT / "artifact_hashes.csv"
AUDIT = OUTPUT / "stable_manifold_audit.md"
FAILURES = OUTPUT / "failure_evidence.md"
SCRIPT = ROOT / "scripts" / "run_submission_candidate_stable_manifolds.py"

CASES = {
    "h2_stable_em_halo_12p40_n45": 45,
    "h2_stable_em_vertical_12p66_n57": 57,
    "h2_stable_se_active_geometry_member_468": 21,
}
METHODS = {
    "traditional_pointwise_eigendecomposition",
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
}
IMPROVED = METHODS - {"traditional_pointwise_eigendecomposition"}
PERTURBATIONS = (5.0e-8, 1.0e-7, 2.0e-7)
SIGNS = (-1, 1)


def _sanitize(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


def _array_prefix(case_id: str, method: str, epsilon: float, sign: int) -> str:
    prefix = (
        f"{_sanitize(case_id)}__{_sanitize(method)}"
        f"__eps_{epsilon:.0e}__sign_{sign:+d}"
    )
    return prefix.replace("+", "p").replace("-", "m")


class SubmissionCandidateStableManifoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with COMPARISON.open(newline="", encoding="utf-8") as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    def test_exact_case_method_perturbation_sign_grid(self) -> None:
        self.assertEqual(len(self.rows), 3 * 3 * 3 * 2)
        self.assertEqual({row["case_id"] for row in self.rows}, set(CASES))
        self.assertEqual({row["method"] for row in self.rows}, METHODS)
        self.assertEqual(
            {float(row["perturbation_norm"]) for row in self.rows},
            set(PERTURBATIONS),
        )
        self.assertEqual(
            {int(row["perturbation_sign"]) for row in self.rows}, set(SIGNS)
        )
        self.assertEqual({row["branch"] for row in self.rows}, {"stable"})
        self.assertEqual(
            {row["propagation_direction"] for row in self.rows}, {"backward"}
        )
        self.assertEqual(
            Counter(row["status"] for row in self.rows),
            {"accepted": 36, "fail": 18},
        )

    def test_improved_methods_pass_frozen_local_manifold_gates(self) -> None:
        for row in self.rows:
            with self.subTest(
                case=row["case_id"],
                method=row["method"],
                epsilon=row["perturbation_norm"],
                sign=row["perturbation_sign"],
            ):
                self.assertEqual(int(row["bundle_dimension"]), 1)
                self.assertEqual(int(row["time_samples"]), 41)
                self.assertEqual(
                    row["coordinate_system"],
                    "cr3bp_synodic_rotating_nondimensional",
                )
                if row["method"] in IMPROVED:
                    self.assertEqual(row["bundle_research_status"], "accepted")
                    self.assertEqual(row["status"], "accepted")
                    self.assertLess(float(row["manifold_jacobi_drift"]), 1.0e-10)
                    self.assertLess(
                        abs(float(row["initial_linear_growth_ratio"]) - 1.0),
                        0.05,
                    )
                    self.assertEqual(row["branch_sign_consistent"], "true")
                else:
                    self.assertEqual(row["bundle_research_status"], "fail")
                    self.assertEqual(row["status"], "fail")

    def test_npz_preserves_base_and_perturbed_histories(self) -> None:
        with np.load(RESULTS, allow_pickle=False) as archive:
            np.testing.assert_allclose(
                np.sort(archive["perturbations"]),
                np.asarray(PERTURBATIONS),
                rtol=0.0,
                atol=0.0,
            )
            np.testing.assert_array_equal(
                np.sort(archive["signs"]), np.asarray(SIGNS)
            )
            for case_id, samples in CASES.items():
                times = archive[f"{_sanitize(case_id)}__times_nd"]
                base = archive[f"{_sanitize(case_id)}__base_states"]
                self.assertEqual(times.shape, (41,))
                self.assertEqual(base.shape, (41, samples, 6))
                self.assertTrue(np.all(np.isfinite(base)))
                for method in METHODS:
                    for epsilon in PERTURBATIONS:
                        for sign in SIGNS:
                            prefix = _array_prefix(
                                case_id, method, epsilon, sign
                            )
                            history = archive[prefix + "__manifold_states"]
                            linear = archive[prefix + "__linear_separation"]
                            self.assertEqual(history.shape, (41, samples, 6))
                            self.assertEqual(linear.shape, (41, samples))
                            self.assertTrue(np.all(np.isfinite(history)))
                            self.assertTrue(np.all(np.isfinite(linear)))

    def test_summary_audit_and_failures_preserve_boundaries(self) -> None:
        self.assertEqual(self.summary["h2_stable_manifold_gate_status"], "pass")
        self.assertEqual(
            self.summary["cases_with_both_improved_methods_accepted"], 3
        )
        self.assertEqual(self.summary["accepted_improved_rows"], 36)
        self.assertEqual(
            self.summary["status_counts"], {"accepted": 36, "fail": 18}
        )
        audit = AUDIT.read_text(encoding="utf-8")
        self.assertIn("not the H4 long-propagation result", audit)
        failures = FAILURES.read_text(encoding="utf-8")
        self.assertEqual(
            failures.count("traditional_pointwise_eigendecomposition"), 18
        )

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
        self.assertIn("STAGE-H2 STABLE MANIFOLD CHECK PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
