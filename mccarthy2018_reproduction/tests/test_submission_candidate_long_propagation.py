"""Regression tests for the Stage-H4 three-map propagation campaign."""

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
    / "long_propagation"
)
ATTEMPTS = OUTPUT / "long_propagation_attempts.csv"
EVENTS = OUTPUT / "long_propagation_events.csv"
TRAJECTORIES = OUTPUT / "long_propagation_trajectory_events.csv"
RESULTS = OUTPUT / "long_propagation_results.npz"
SUMMARY = OUTPUT / "long_propagation_summary.json"
HASHES = OUTPUT / "artifact_hashes.csv"
AUDIT = OUTPUT / "long_propagation_audit.md"
FAILURES = OUTPUT / "failure_evidence.md"
SCRIPT = ROOT / "scripts" / "run_submission_candidate_long_propagation.py"

CASES = {
    "h4_long_stable_em_halo_12p40_n45": 45,
    "h4_long_stable_em_vertical_12p66_n57": 57,
    "h4_long_stable_se_active_geometry_member_468": 21,
}
METHODS = {
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
}
SIGNS = {-1, 1}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _sanitize(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


def _key(case_id: str, method: str, sign: int) -> str:
    prefix = f"{_sanitize(case_id)}__{_sanitize(method)}__sign_{sign:+d}"
    return prefix.replace("+", "p").replace("-", "m")


class SubmissionCandidateLongPropagationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.attempts = _read_csv(ATTEMPTS)
        cls.events = _read_csv(EVENTS)
        cls.trajectories = _read_csv(TRAJECTORIES)
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    def test_exact_case_method_sign_and_trajectory_grids(self) -> None:
        self.assertEqual(len(self.events), 3 * 2 * 2)
        self.assertEqual(len(self.trajectories), 4 * sum(CASES.values()))
        self.assertEqual({row["case_id"] for row in self.events}, set(CASES))
        self.assertEqual({row["method"] for row in self.events}, METHODS)
        self.assertEqual(
            {int(row["perturbation_sign"]) for row in self.events}, SIGNS
        )
        self.assertTrue(
            all(int(row["duration_mapping_periods"]) == 3 for row in self.events)
        )
        self.assertTrue(
            all(int(row["time_samples"]) == 121 for row in self.events)
        )
        self.assertEqual(
            {row["branch"] for row in self.events}, {"stable"}
        )
        self.assertEqual(
            {row["propagation_direction"] for row in self.events}, {"backward"}
        )

    def test_selected_histories_pass_numerical_and_local_linearity_gates(self) -> None:
        for row in self.events:
            with self.subTest(
                case=row["case_id"],
                method=row["method"],
                sign=row["perturbation_sign"],
            ):
                self.assertEqual(row["bundle_research_status"], "accepted")
                self.assertEqual(row["branch_sign_consistent"], "true")
                self.assertLess(float(row["manifold_jacobi_drift"]), 1.0e-10)
                self.assertLess(
                    float(row["local_linear_max_relative_error"]), 0.05
                )
                self.assertGreater(int(row["local_linear_sample_count"]), 0)
                self.assertGreater(int(row["local_exit_trajectory_count"]), 0)
                self.assertGreater(int(row["global_exit_trajectory_count"]), 0)
                self.assertLess(
                    float(row["local_exit_elapsed_days_median"]),
                    float(row["global_exit_elapsed_days_median"]),
                )

    def test_physical_radius_boundaries_are_retained(self) -> None:
        self.assertEqual(
            Counter(row["status"] for row in self.events),
            {"accepted": 8, "boundary": 4},
        )
        boundary = [row for row in self.events if row["status"] == "boundary"]
        accepted = [row for row in self.events if row["status"] == "accepted"]
        self.assertEqual(len(boundary), 4)
        for row in boundary:
            self.assertGreater(
                int(row["secondary_radius_crossing_trajectories"]), 0
            )
            self.assertLessEqual(
                float(row["secondary_min_distance_km"]),
                float(row["secondary_radius_km"]),
            )
            self.assertIn(
                "sampled_secondary_physical_radius_crossing",
                row["failure_reason"],
            )
        for row in accepted:
            self.assertEqual(
                int(row["secondary_radius_crossing_trajectories"]), 0
            )
            self.assertGreater(
                float(row["secondary_min_distance_km"]),
                float(row["secondary_radius_km"]),
            )

    def test_one_tight_retry_is_auditable_and_selected(self) -> None:
        self.assertEqual(len(self.attempts), 16)
        retries = [
            row for row in self.attempts if int(row["attempt_index"]) == 2
        ]
        superseded = [
            row
            for row in self.attempts
            if int(row["attempt_index"]) == 1
            and row["selected_for_final"] == "false"
        ]
        self.assertEqual(len(retries), 4)
        self.assertEqual(len(superseded), 4)
        for row in retries:
            self.assertEqual(row["selected_for_final"], "true")
            self.assertEqual(float(row["rtol"]), 3.0e-13)
            self.assertEqual(float(row["atol"]), 3.0e-15)
            self.assertEqual(float(row["max_step"]), 0.001)
            self.assertLess(float(row["jacobi_drift"]), 1.0e-10)
        for row in superseded:
            self.assertGreater(float(row["jacobi_drift"]), 1.0e-10)

    def test_npz_preserves_base_selected_and_every_successful_attempt(self) -> None:
        with np.load(RESULTS, allow_pickle=False) as archive:
            self.assertEqual(set(archive["case_ids"].tolist()), set(CASES))
            for case_id, samples in CASES.items():
                prefix = _sanitize(case_id)
                self.assertEqual(
                    archive[prefix + "__base_states"].shape, (121, samples, 6)
                )
                for method in METHODS:
                    for sign in SIGNS:
                        key = _key(case_id, method, sign)
                        self.assertEqual(
                            archive[key + "__selected_manifold_states"].shape,
                            (121, samples, 6),
                        )
                        self.assertEqual(
                            archive[key + "__separation"].shape, (121, samples)
                        )
            for row in self.attempts:
                if row["success"] != "true":
                    continue
                key = (
                    _key(
                        row["case_id"],
                        row["method"],
                        int(row["perturbation_sign"]),
                    )
                    + f"__attempt_{int(row['attempt_index'])}__manifold_states"
                )
                self.assertIn(key, archive.files)

    def test_summary_boundaries_hashes_and_check_mode(self) -> None:
        self.assertEqual(self.summary["h4_gate_status"], "pass")
        self.assertEqual(
            self.summary["cases_with_collision_free_accepted_row"], 3
        )
        self.assertEqual(self.summary["secondary_radius_boundary_rows"], 4)
        self.assertEqual(self.summary["retry_rows"], 4)
        self.assertLess(
            float(self.summary["maximum_selected_jacobi_drift"]), 1.0e-10
        )
        audit = AUDIT.read_text(encoding="utf-8")
        self.assertIn("are diagnostics and do not terminate integration", audit)
        self.assertIn("Far-field nonlinear/STM ratios are diagnostic only", audit)
        failures = FAILURES.read_text(encoding="utf-8")
        self.assertEqual(failures.count("sampled_secondary_physical_radius_crossing"), 4)
        self.assertEqual(len(_read_csv(HASHES)), 9)
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("STAGE-H4 LONG PROPAGATION CHECK PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
