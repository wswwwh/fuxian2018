"""Regression tests for the Stage-H5 Sun-Earth expansion campaign."""

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
    / "sun_earth_expansion"
)
SOURCES = OUTPUT / "source_validation.csv"
INDEPENDENCE = OUTPUT / "source_independence.csv"
ATTEMPTS = OUTPUT / "method_attempts.csv"
BENCHMARKS = OUTPUT / "benchmark_comparison.csv"
MANIFOLDS = OUTPUT / "manifold_validation.csv"
RESULTS = OUTPUT / "benchmark_results.npz"
SUMMARY = OUTPUT / "sun_earth_expansion_summary.json"
HASHES = OUTPUT / "artifact_hashes.csv"
AUDIT = OUTPUT / "sun_earth_expansion_audit.md"
FAILURES = OUTPUT / "failure_evidence.md"
SCRIPT = ROOT / "scripts" / "run_submission_candidate_sun_earth_expansion.py"

CASES = {
    "h5_se_active_event_step_1_n21",
    "h5_se_sharpness_stage_4_n21",
    "h5_se_energy_frontier_n21",
}
POINTWISE = "traditional_pointwise_eigendecomposition"
SCHUR = "ordered_partial_real_schur_tracking"
QR = "qr_svd_shifted_cocycle_iteration"
METHODS = {POINTWISE, SCHUR, QR}
IMPROVED = {SCHUR, QR}
SIGNS = {-1, 1}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _sanitize(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


def _key(case_id: str, method: str) -> str:
    return f"{_sanitize(case_id)}__{_sanitize(method)}"


def _manifold_key(case_id: str, method: str, sign: int) -> str:
    key = f"{_key(case_id, method)}__sign_{sign:+d}"
    return key.replace("+", "p").replace("-", "m")


class SubmissionCandidateSunEarthExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = _read_csv(SOURCES)
        cls.independence = _read_csv(INDEPENDENCE)
        cls.attempts = _read_csv(ATTEMPTS)
        cls.benchmarks = _read_csv(BENCHMARKS)
        cls.manifolds = _read_csv(MANIFOLDS)
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    def test_three_preregistered_sources_revalidate_without_promotion(self) -> None:
        self.assertEqual(len(self.sources), 3)
        self.assertEqual({row["case_id"] for row in self.sources}, CASES)
        self.assertEqual(len({row["state_array_sha256"] for row in self.sources}), 3)
        for row in self.sources:
            with self.subTest(case=row["case_id"]):
                self.assertEqual(int(row["spectral_samples"]), 21)
                self.assertEqual(row["source_map_status"], "pass")
                self.assertLessEqual(
                    float(row["recomputed_map_residual"]),
                    float(row["source_map_residual_limit"]),
                )
                self.assertEqual(row["state_artifact_hash_match"], "true")
                self.assertEqual(row["state_array_hash_match"], "true")
                self.assertEqual(row["metadata_fingerprint_match"], "true")
                self.assertEqual(row["new_vs_stage_c_registry"], "true")
                self.assertEqual(row["source_authority_boundary"], "true")
                self.assertEqual(row["status"], "pass")

    def test_pairwise_local_sources_are_distinct_with_explicit_scope(self) -> None:
        self.assertEqual(len(self.independence), 3)
        pairs = {
            frozenset((row["left_case_id"], row["right_case_id"]))
            for row in self.independence
        }
        self.assertEqual(len(pairs), 3)
        for row in self.independence:
            self.assertEqual(row["state_artifact_hash_distinct"], "true")
            self.assertEqual(row["state_array_hash_distinct"], "true")
            self.assertEqual(row["distinct_local_source_artifacts"], "true")
            self.assertGreater(float(row["state_rms_difference"]), 0.0)
            self.assertGreater(float(row["state_max_abs_difference"]), 0.0)
            self.assertGreater(float(row["rho_difference"]), 0.0)
            self.assertEqual(row["status"], "pass")

    def test_method_attempts_use_initial_plus_two_retries(self) -> None:
        self.assertEqual(len(self.attempts), 3 * 7)
        self.assertEqual(
            len([row for row in self.attempts if row["selected_for_benchmark"] == "true"]),
            9,
        )
        for case_id in CASES:
            selected = [row for row in self.attempts if row["case_id"] == case_id]
            self.assertEqual(
                Counter(row["method"] for row in selected),
                {POINTWISE: 1, SCHUR: 3, QR: 3},
            )
            schur = [row for row in selected if row["method"] == SCHUR]
            self.assertEqual(
                {row["variant"] for row in schur},
                {"graph_refinement_0", "graph_refinement_1", "graph_refinement_4"},
            )
            chosen_schur = [
                row for row in schur if row["selected_for_benchmark"] == "true"
            ]
            self.assertEqual(len(chosen_schur), 1)
            self.assertEqual(chosen_schur[0]["variant"], "graph_refinement_4")
            self.assertEqual(chosen_schur[0]["h5_status"], "boundary")

    def test_selected_benchmarks_retain_six_boundaries_and_three_failures(self) -> None:
        self.assertEqual(len(self.benchmarks), 9)
        self.assertEqual({row["case_id"] for row in self.benchmarks}, CASES)
        self.assertEqual({row["method"] for row in self.benchmarks}, METHODS)
        self.assertEqual(
            Counter(row["research_status"] for row in self.benchmarks),
            {"boundary": 6, "fail": 3},
        )
        for row in self.benchmarks:
            self.assertEqual(int(row["bundle_dimension"]), 1)
            self.assertEqual(row["source_authority_boundary"], "true")
            self.assertEqual(row["new_vs_stage_c_registry"], "true")
            if row["method"] in IMPROVED:
                self.assertEqual(row["research_status"], "boundary")
                self.assertGreater(float(row["max_invariance_residual"]), 1.0e-6)
                self.assertLessEqual(
                    float(row["max_invariance_residual"]), 1.0e-3
                )
            else:
                self.assertEqual(row["research_status"], "fail")
                self.assertGreater(float(row["max_invariance_residual"]), 1.0e-3)

    def test_one_map_histories_preserve_boundary_and_failure_semantics(self) -> None:
        self.assertEqual(len(self.manifolds), 3 * 3 * 2)
        self.assertEqual(
            Counter(row["status"] for row in self.manifolds),
            {"boundary": 12, "fail": 6},
        )
        self.assertEqual(
            {int(row["perturbation_sign"]) for row in self.manifolds}, SIGNS
        )
        for row in self.manifolds:
            self.assertEqual(row["manifold_generated"], "true")
            self.assertEqual(row["branch"], "unstable")
            self.assertEqual(row["propagation_direction"], "forward")
            self.assertEqual(int(row["time_samples"]), 41)
            self.assertLess(float(row["manifold_jacobi_drift"]), 1.0e-10)
            self.assertLess(
                abs(float(row["initial_linear_growth_ratio"]) - 1.0), 0.05
            )
            if row["method"] in IMPROVED:
                self.assertEqual(row["status"], "boundary")
                self.assertEqual(row["diagnostic_only"], "false")
            else:
                self.assertEqual(row["status"], "fail")
                self.assertEqual(row["diagnostic_only"], "true")
                self.assertIn("upstream_benchmark_failed", row["failure_reason"])

    def test_npz_and_cocycle_archives_preserve_full_evidence(self) -> None:
        with np.load(RESULTS, allow_pickle=False) as archive:
            self.assertEqual(set(archive["case_ids"].tolist()), CASES)
            for case_id in CASES:
                prefix = _sanitize(case_id)
                self.assertEqual(archive[prefix + "__states"].shape, (21, 6))
                self.assertEqual(archive[prefix + "__stms"].shape, (21, 6, 6))
                self.assertEqual(
                    archive[prefix + "__base_states"].shape, (41, 21, 6)
                )
                for method in METHODS:
                    self.assertEqual(
                        archive[_key(case_id, method) + "__bases"].shape,
                        (21, 6, 1),
                    )
                    for sign in SIGNS:
                        key = _manifold_key(case_id, method, sign)
                        self.assertEqual(
                            archive[key + "__manifold_states"].shape,
                            (41, 21, 6),
                        )
                        self.assertEqual(
                            archive[key + "__linear_separation"].shape,
                            (41, 21),
                        )
        for row in self.sources:
            cache_path = ROOT / row["cocycle_artifact"]
            with np.load(cache_path, allow_pickle=False) as cache:
                self.assertEqual(cache["states"].shape, (21, 6))
                self.assertEqual(cache["stms"].shape, (21, 6, 6))
                self.assertEqual(cache["mapped_states"].shape, (21, 6))

    def test_summary_authority_hashes_and_check_mode(self) -> None:
        self.assertEqual(self.summary["h5_gate_status"], "pass")
        self.assertEqual(self.summary["independent_new_source_benchmarks"], 3)
        self.assertEqual(
            self.summary["cases_with_two_improved_boundary_or_better_methods"], 3
        )
        self.assertEqual(self.summary["source_authority_boundary_cases"], 3)
        audit = AUDIT.read_text(encoding="utf-8")
        self.assertIn(
            "external independent solver or independent physical experiment",
            audit,
        )
        self.assertIn("no numerical method can be promoted above boundary", audit)
        failures = FAILURES.read_text(encoding="utf-8")
        self.assertIn("No failed or boundary row is promoted or omitted", failures)
        self.assertEqual(len(_read_csv(HASHES)), 14)
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(
            "STAGE-H5 SUN-EARTH EXPANSION CHECK PASS", completed.stdout
        )


if __name__ == "__main__":
    unittest.main()
