"""Regression tests for the Stage-H3 Route-H two-dimensional campaign."""

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
    / "route_h_2d_manifolds"
)
ATTEMPTS = OUTPUT / "route_h_2d_method_attempts.csv"
DIAGNOSTICS = OUTPUT / "route_h_2d_subspace_diagnostics.csv"
MANIFOLDS = OUTPUT / "route_h_2d_manifold_convergence.csv"
RESULTS = OUTPUT / "route_h_2d_manifold_results.npz"
SUMMARY = OUTPUT / "route_h_2d_summary.json"
HASHES = OUTPUT / "artifact_hashes.csv"
AUDIT = OUTPUT / "route_h_2d_audit.md"
FAILURES = OUTPUT / "failure_evidence.md"
SCRIPT = ROOT / "scripts" / "run_submission_candidate_route_h_2d_manifolds.py"

CASES = {
    "h3_route_h_member_68_2d",
    "h3_route_h_member_32_2d",
}
SCHUR = "ordered_partial_real_schur_tracking"
QR = "qr_svd_shifted_cocycle_iteration"
PERTURBATIONS = {5.0e-8, 1.0e-7}
INITIALIZATIONS = {"local_svd", "schur_seed", "deterministic_random"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _sanitize(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


def _manifold_key(case_id: str, epsilon: float) -> str:
    key = f"{_sanitize(case_id)}__{_sanitize(SCHUR)}__eps_{epsilon:.0e}"
    return key.replace("-", "m").replace("+", "p")


class SubmissionCandidateRouteHTwoDimensionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.attempts = _read_csv(ATTEMPTS)
        cls.diagnostics = _read_csv(DIAGNOSTICS)
        cls.manifolds = _read_csv(MANIFOLDS)
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    def test_exact_case_method_retry_and_manifold_grids(self) -> None:
        self.assertEqual(len(self.attempts), 2 * 4)
        self.assertEqual(len(self.diagnostics), 2 * 45)
        self.assertEqual(len(self.manifolds), 2 * 2 * 2)
        self.assertEqual({row["case_id"] for row in self.attempts}, CASES)
        self.assertEqual(
            {row["method"] for row in self.attempts}, {SCHUR, QR}
        )
        self.assertEqual(
            {float(row["perturbation_norm"]) for row in self.manifolds},
            PERTURBATIONS,
        )
        self.assertTrue(
            all(int(row["bundle_dimension"]) == 2 for row in self.attempts)
        )
        self.assertTrue(
            all(int(row["bundle_dimension"]) == 2 for row in self.manifolds)
        )

    def test_latent_complex_pairs_pass_without_rewriting_stage_e(self) -> None:
        rows = [row for row in self.attempts if row["method"] == SCHUR]
        self.assertEqual(len(rows), 2)
        for row in rows:
            with self.subTest(case=row["case_id"]):
                self.assertEqual(row["classification"], "real_2d_complex_pair_invariant_subspace")
                self.assertEqual(row["h3_status"], "accepted")
                self.assertEqual(row["stage_e_research_status"], "fail")
                self.assertEqual(row["independent_dimension_agreement"], "true")
                self.assertEqual(row["independent_validation_verdict"], "accepted")
                self.assertGreater(float(row["target_eigenvalue_abs"]), 1.001)
                self.assertLess(float(row["global_selection_residual"]), 1.0e-8)
                self.assertLess(float(row["raw_equation_residual_max"]), 1.0e-6)
                self.assertLess(
                    float(row["gauge_consistent_subspace_residual_max"]),
                    1.0e-6,
                )
                self.assertGreater(
                    float(row["legacy_normalized_frame_residual_max"]),
                    1.0e-3,
                )

    def test_qr_initial_plus_two_retries_are_bounded_failures(self) -> None:
        rows = [row for row in self.attempts if row["method"] == QR]
        self.assertEqual(len(rows), 2 * 3)
        for case_id in CASES:
            selected = [row for row in rows if row["case_id"] == case_id]
            self.assertEqual(
                {row["initialization"] for row in selected}, INITIALIZATIONS
            )
            self.assertEqual(
                {int(row["attempt_index"]) for row in selected}, {1, 2, 3}
            )
            for row in selected:
                self.assertEqual(int(row["iterations_executed"]), 500)
                self.assertEqual(int(row["bundle_dimension"]), 2)
                self.assertEqual(row["converged"], "false")
                self.assertEqual(row["h3_status"], "bounded_fail")
                self.assertIn("qr_iteration_not_converged_at_500", row["failure_reason"])

    def test_only_valid_schur_frames_generate_accepted_sheets(self) -> None:
        self.assertEqual(
            Counter(row["status"] for row in self.manifolds),
            {"accepted": 4, "bounded_fail": 4},
        )
        for row in self.manifolds:
            with self.subTest(
                case=row["case_id"],
                method=row["method"],
                epsilon=row["perturbation_norm"],
            ):
                self.assertEqual(row["branch"], "unstable")
                self.assertEqual(row["propagation_direction"], "forward")
                self.assertEqual(int(row["angular_samples"]), 8)
                self.assertEqual(int(row["time_samples"]), 41)
                if row["method"] == SCHUR:
                    self.assertEqual(row["manifold_generated"], "true")
                    self.assertEqual(row["status"], "accepted")
                    self.assertEqual(int(row["initial_sheet_rank_min"]), 2)
                    self.assertLess(float(row["manifold_jacobi_drift"]), 1.0e-10)
                    self.assertLess(
                        abs(float(row["initial_linear_growth_ratio_mean"]) - 1.0),
                        0.05,
                    )
                    self.assertGreater(
                        float(row["final_growth_factor_geometric_mean"]), 1.0
                    )
                else:
                    self.assertEqual(row["manifold_generated"], "false")
                    self.assertEqual(row["status"], "bounded_fail")
                    self.assertIn("manifold_not_generated", row["failure_reason"])

    def test_npz_preserves_raw_frames_retries_and_full_sheets(self) -> None:
        with np.load(RESULTS, allow_pickle=False) as archive:
            self.assertEqual(set(archive["case_ids"].tolist()), CASES)
            for case_id in CASES:
                prefix = _sanitize(case_id)
                self.assertEqual(
                    archive[prefix + "__raw_frames"].shape, (45, 6, 2)
                )
                self.assertEqual(
                    archive[prefix + "__orthonormal_bases"].shape,
                    (45, 6, 2),
                )
                self.assertEqual(
                    archive[prefix + "__base_states"].shape, (41, 45, 6)
                )
                self.assertLess(
                    float(
                        np.max(archive[prefix + "__raw_equation_residuals"])
                    ),
                    1.0e-6,
                )
                for attempt, initialization in enumerate(
                    ("local_svd", "schur_seed", "deterministic_random"),
                    start=1,
                ):
                    key = f"{prefix}__qr_attempt_{attempt}_{initialization}"
                    self.assertEqual(archive[key + "__bases"].shape, (45, 6, 2))
                    self.assertEqual(
                        archive[key + "__convergence_history"].shape, (500,)
                    )
                for epsilon in PERTURBATIONS:
                    key = _manifold_key(case_id, epsilon)
                    self.assertEqual(
                        archive[key + "__manifold_states"].shape,
                        (41, 45, 8, 6),
                    )
                    self.assertEqual(
                        archive[key + "__linear_separation"].shape,
                        (41, 45, 8),
                    )

    def test_summary_boundaries_hashes_and_check_mode(self) -> None:
        self.assertEqual(self.summary["h3_gate_status"], "pass")
        self.assertEqual(
            self.summary["cases_with_accepted_2d_schur_object"], 2
        )
        self.assertEqual(self.summary["qr_bounded_failure_cases"], 2)
        self.assertTrue(self.summary["never_one_dimensional"])
        self.assertTrue(self.summary["stage_e_schur_failures_preserved"])
        audit = AUDIT.read_text(encoding="utf-8")
        self.assertIn("Stage-E method_comparison.csv remains unchanged", audit)
        self.assertIn("does not relabel the object", audit)
        failures = FAILURES.read_text(encoding="utf-8")
        self.assertEqual(failures.count("qr_svd_shifted_cocycle_iteration"), 6)
        self.assertIn("No one-dimensional", failures)
        self.assertEqual(len(_read_csv(HASHES)), 9)
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(
            "STAGE-H3 ROUTE-H 2D MANIFOLD CHECK PASS", completed.stdout
        )


if __name__ == "__main__":
    unittest.main()
