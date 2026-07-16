"""Stored-reproducibility tests for the Stage-C benchmark registry."""

from __future__ import annotations

import csv
import hashlib
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "benchmarks"
    / "benchmark_registry.csv"
)
REQUIRED_FIELDS = {
    "case_id",
    "family",
    "member_id",
    "system",
    "mu",
    "jacobi_or_energy",
    "mapping_time",
    "rho",
    "spectral_samples",
    "state_artifact",
    "source_residual",
    "expected_bundle_type",
    "positive_or_negative_control",
    "provenance",
    "git_commit",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class InvariantBundleBenchmarkRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with REGISTRY.open(newline="", encoding="utf-8") as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_required_case_and_family_coverage_is_frozen(self) -> None:
        self.assertEqual(len(self.rows), 15)
        self.assertEqual(len({row["case_id"] for row in self.rows}), 15)
        self.assertEqual(len({row["family"] for row in self.rows}), 4)
        self.assertTrue(REQUIRED_FIELDS.issubset(self.rows[0]))
        required_cases = {
            "em_halo_12p40_n21",
            "em_halo_12p40_n33",
            "em_halo_12p40_n45",
            "em_halo_12p097_n9_lowres_negative",
            "em_vertical_12p66_n33",
            "em_vertical_12p66_n45",
            "em_vertical_12p66_n57",
            "route_h_member_68",
            "route_h_member_17",
            "route_h_member_32",
            "route_h_member_54",
            "route_h_member_68_legacy_dg_positive",
            "se_active_geometry_member_468",
            "se_quasi_halo_small_n21",
        }
        self.assertTrue(required_cases.issubset({row["case_id"] for row in self.rows}))

    def test_all_state_artifacts_and_keys_match_frozen_hashes(self) -> None:
        for row in self.rows:
            with self.subTest(case=row["case_id"]):
                artifact = ROOT / row["state_artifact"]
                self.assertTrue(artifact.is_file())
                self.assertEqual(sha256(artifact), row["state_artifact_sha256"])
                with np.load(artifact, allow_pickle=False) as archive:
                    self.assertIn(row["state_key"], archive.files)
                    states = np.asarray(archive[row["state_key"]])
                self.assertEqual(
                    states.shape,
                    (int(row["spectral_samples"]), 6),
                )
                self.assertTrue(np.all(np.isfinite(states)))

    def test_failed_and_boundary_controls_are_not_hidden(self) -> None:
        controls = [row["positive_or_negative_control"] for row in self.rows]
        self.assertGreaterEqual(controls.count("negative"), 5)
        self.assertGreaterEqual(controls.count("boundary"), 3)
        by_case = {row["case_id"]: row for row in self.rows}
        self.assertIn(
            "legacy_dg_pass",
            by_case["route_h_member_68"]["source_gate_status"],
        )
        self.assertIn(
            "legacy_dg_fail",
            by_case["route_h_member_17"]["source_gate_status"],
        )
        self.assertEqual(
            by_case["route_h_member_68_legacy_dg_positive"]["source_gate_status"],
            "pass",
        )
        self.assertIn(
            "projection_fail",
            by_case["em_halo_12p097_n9_lowres_negative"]["source_gate_status"],
        )


if __name__ == "__main__":
    unittest.main()
