from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "invariant_bundles"
CONFIG = RESEARCH / "configs" / "qr_svd_failure_classification.json"
SUMMARY = RESEARCH / "results" / "csv" / "qr_svd_failure_classification.csv"
EXPERIMENTS = RESEARCH / "results" / "csv" / "qr_svd_failure_experiments.csv"
NPZ = RESEARCH / "results" / "npz" / "qr_svd_failure_experiments.npz"
HASHES = RESEARCH / "results" / "logs" / "qr_svd_failure_artifact_hashes.csv"
DOC = RESEARCH / "docs" / "qr_svd_failure_analysis.md"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class QrSvdFailureClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.summary = rows(SUMMARY)
        cls.experiments = rows(EXPERIMENTS)

    def test_exact_five_failure_cases_and_bounded_grid(self) -> None:
        self.assertEqual([row["case_id"] for row in self.summary], self.config["failure_cases"])
        self.assertEqual(len(self.summary), 5)
        self.assertEqual(len(self.experiments), 5 * 3 * 3 * 2)
        for case in self.config["failure_cases"]:
            subset = [row for row in self.experiments if row["case_id"] == case]
            self.assertEqual({row["initialization"] for row in subset}, set(self.config["initializations"]))
            self.assertEqual({int(row["iteration_cap"]) for row in subset}, {200, 500, 1000})
            self.assertEqual({row["resolution_id"] for row in subset}, {"native_n45", "fourier_lift_n67"})

    def test_only_allowed_labels_and_negative_results_retained(self) -> None:
        allowed = set(self.config["allowed_final_labels"])
        self.assertTrue(all(row["final_label"] in allowed for row in self.summary))
        self.assertTrue(all(row["negative_result_retained"] == "true" for row in self.summary))
        physical = [row for row in self.summary if "legacy" not in row["case_id"]]
        self.assertTrue(all(row["independent_schur_dimension"] == "2" for row in physical))
        self.assertTrue(all(row["final_label"] in {"no_accepted_1d_bundle", "accepted_2d_real_subspace"} for row in physical))

    def test_legacy_control_remains_separate_and_initialization_sensitive(self) -> None:
        legacy = next(row for row in self.summary if "legacy" in row["case_id"])
        self.assertEqual(legacy["independent_schur_dimension"], "1")
        self.assertEqual(legacy["final_label"], "method_initialization_sensitive")
        self.assertEqual(legacy["initialization_sensitivity_observed"], "true")
        self.assertEqual(legacy["native_schur_seed_status"], "accepted")

    def test_npz_histories_bases_and_high_precision_rows_exist(self) -> None:
        with np.load(NPZ, allow_pickle=False) as archive:
            self.assertEqual(len(archive["high_precision_case_ids"]), 5)
            self.assertTrue(np.all(np.isfinite(archive["high_precision_max_invariance_residuals"])))
            for case in self.config["failure_cases"]:
                for resolution in ("native_n45", "fourier_lift_n67"):
                    for initialization in self.config["initializations"]:
                        self.assertIn(
                            f"{case}__{resolution}__{initialization}__convergence_history_deg",
                            archive.files,
                        )

    def test_hashes_and_truth_boundary(self) -> None:
        for row in rows(HASHES):
            path = ROOT / row["artifact"]
            self.assertEqual(int(row["bytes"]), path.stat().st_size)
            self.assertEqual(row["sha256"], sha256(path))
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("paper_projection=fail", text)
        self.assertIn("not presented", text)


if __name__ == "__main__":
    unittest.main()
