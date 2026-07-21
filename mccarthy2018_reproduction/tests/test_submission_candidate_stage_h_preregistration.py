"""Regression tests for the isolated Stage-H preregistration."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
STAGE_H = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "submission_candidate"
)
REGISTRY = STAGE_H / "benchmarks" / "stage_h_case_registry.csv"
LOCK = STAGE_H / "benchmarks" / "stage_h_preregistration_lock.json"
REPORT = STAGE_H / "benchmarks" / "stage_h_preregistration.md"
SCRIPT = ROOT / "scripts" / "build_submission_candidate_stage_h_registry.py"


def state_array_sha256(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    header = json.dumps(
        {"dtype": array.dtype.str, "shape": list(array.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(header + b"\0" + array.tobytes()).hexdigest().upper()


class SubmissionCandidateStageHPreregistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with REGISTRY.open(newline="", encoding="utf-8") as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.lock = json.loads(LOCK.read_text(encoding="utf-8"))

    def test_exact_campaign_counts_and_unique_case_ids(self) -> None:
        self.assertEqual(len(self.rows), 11)
        self.assertEqual(len({row["case_id"] for row in self.rows}), 11)
        self.assertEqual(
            Counter(row["campaign"] for row in self.rows),
            {
                "H2_stable_bundle": 3,
                "H3_route_h_2d_manifold": 2,
                "H4_long_propagation": 3,
                "H5_sun_earth_expansion": 3,
            },
        )

    def test_stable_and_route_h_dimension_contracts_are_frozen(self) -> None:
        stable = [
            row for row in self.rows if row["campaign"] == "H2_stable_bundle"
        ]
        self.assertEqual({row["branch"] for row in stable}, {"stable"})
        self.assertEqual(
            {row["expected_bundle_dimension"] for row in stable}, {"1"}
        )
        self.assertEqual(
            {row["propagation_direction"] for row in stable}, {"backward"}
        )
        route_h = [
            row
            for row in self.rows
            if row["campaign"] == "H3_route_h_2d_manifold"
        ]
        self.assertEqual(
            {row["source_case_id"] for row in route_h},
            {"route_h_member_68", "route_h_member_32"},
        )
        self.assertEqual(
            {row["expected_bundle_dimension"] for row in route_h}, {"2"}
        )
        self.assertEqual(
            {int(row["subspace_angular_samples"]) for row in route_h}, {8}
        )

    def test_long_propagation_is_three_periods_and_bounded(self) -> None:
        long_rows = [
            row for row in self.rows if row["campaign"] == "H4_long_propagation"
        ]
        self.assertEqual(
            {float(row["duration_mapping_periods"]) for row in long_rows},
            {3.0},
        )
        self.assertEqual({int(row["time_samples"]) for row in long_rows}, {121})
        self.assertTrue(
            all("exit_diagnostics" in row["event_condition"] for row in long_rows)
        )
        self.assertEqual({int(row["max_retries"]) for row in long_rows}, {1})

    def test_sun_earth_cases_use_three_distinct_frozen_checkpoints(self) -> None:
        sun = [
            row
            for row in self.rows
            if row["campaign"] == "H5_sun_earth_expansion"
        ]
        self.assertEqual({row["system"] for row in sun}, {"sun_earth"})
        self.assertEqual(len({row["state_artifact"] for row in sun}), 3)
        self.assertEqual({row["source_case_id"] for row in sun}, {""})
        self.assertTrue(
            all(
                row["state_artifact"].startswith("data/computed/")
                for row in sun
            )
        )

    def test_source_state_arrays_match_preregistered_hashes(self) -> None:
        for row in self.rows:
            with self.subTest(case=row["case_id"]):
                path = ROOT / row["state_artifact"]
                self.assertTrue(path.is_file())
                with np.load(path, allow_pickle=False) as archive:
                    self.assertIn(row["state_key"], archive.files)
                    states = np.asarray(archive[row["state_key"]], dtype=float)
                self.assertEqual(states.shape, (int(row["spectral_samples"]), 6))
                self.assertTrue(np.all(np.isfinite(states)))
                self.assertEqual(
                    state_array_sha256(states), row["state_array_sha256"]
                )

    def test_frozen_reproduction_truth_remains_failed_where_required(self) -> None:
        truth = self.lock["frozen_truth"]
        self.assertEqual(
            truth["baseline_metrics"],
            {
                "target_rows": "54",
                "v0_targets": "13",
                "v2_targets": "41",
                "chapter4_frozen_holdout_pass": "0",
                "chapter4_frozen_holdout_total": "4",
                "chapter5_bcr4bp_numerical_pass": "2",
                "chapter5_bcr4bp_paper_equivalence_pass": "0",
            },
        )
        self.assertEqual(truth["chapter4_holdout"]["rows"], 4)
        self.assertEqual(truth["chapter4_holdout"]["passes"], 0)
        self.assertEqual(truth["chapter4_holdout"]["paper_3d_true"], 0)

    def test_generator_check_and_report_contract(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("STAGE-H PREREGISTRATION CHECK PASS", completed.stdout)
        report = REPORT.read_text(encoding="utf-8")
        self.assertIn("0/4", report)
        self.assertIn("two-dimensional", report)
        self.assertIn("three distinct frozen Sun-Earth", report)


if __name__ == "__main__":
    unittest.main()
