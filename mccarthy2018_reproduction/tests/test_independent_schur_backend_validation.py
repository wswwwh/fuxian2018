from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "invariant_bundles"
CONFIG = RESEARCH / "configs" / "independent_schur_backend_validation.json"
CSV_PATH = RESEARCH / "results" / "csv" / "independent_schur_backend_comparison.csv"
NPZ_PATH = RESEARCH / "results" / "npz" / "independent_schur_backend_bases.npz"
DOC_PATH = RESEARCH / "docs" / "independent_schur_backend_validation.md"
HASH_PATH = RESEARCH / "results" / "logs" / "independent_schur_backend_artifact_hashes.csv"
FAILURE_PATH = RESEARCH / "results" / "logs" / "independent_schur_backend_failure_evidence.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class IndependentSchurBackendValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.rows = read_csv(CSV_PATH)

    def test_exact_predeclared_case_set_and_backend(self) -> None:
        self.assertEqual([row["case_id"] for row in self.rows], self.config["cases"])
        self.assertEqual(len(self.rows), 12)
        self.assertTrue(all(row["backend"] == "matlab_schur_ordschur" for row in self.rows))

    def test_dimension_classification_status_and_preset_metrics_agree(self) -> None:
        self.assertTrue(all(row["dimension_agreement"] == "true" for row in self.rows))
        self.assertTrue(all(row["classification_agreement"] == "true" for row in self.rows))
        self.assertTrue(all(row["status_agreement"] == "true" for row in self.rows))
        self.assertTrue(all(row["validation_verdict"] == "accepted" for row in self.rows))
        self.assertTrue(
            all(
                float(row["invariant_subspace_principal_angle_max_deg"])
                <= float(row["principal_angle_tolerance_deg"])
                for row in self.rows
            )
        )

    def test_route_h_truth_boundary_is_retained(self) -> None:
        physical = [
            row
            for row in self.rows
            if row["case_id"].startswith("route_h_member_") and "legacy" not in row["case_id"]
        ]
        self.assertEqual(len(physical), 4)
        self.assertTrue(all(row["independent_selected_block_dimension"] == "2" for row in physical))
        self.assertTrue(all(row["independent_research_status"] == "fail" for row in physical))
        legacy = next(
            row for row in self.rows if row["case_id"] == "route_h_member_68_legacy_dg_positive"
        )
        self.assertEqual(legacy["independent_selected_block_dimension"], "1")
        self.assertEqual(legacy["independent_research_status"], "accepted")

    def test_npz_contains_auditable_basis_for_every_case(self) -> None:
        with np.load(NPZ_PATH, allow_pickle=False) as archive:
            np.testing.assert_array_equal(archive["case_ids"], np.asarray(self.config["cases"]))
            for row in self.rows:
                key = f"{row['case_id']}__basis"
                self.assertIn(key, archive.files)
                basis = archive[key]
                self.assertEqual(basis.shape[0], int(row["spectral_samples"]))
                self.assertEqual(basis.shape[1], 6)
                self.assertEqual(basis.shape[2], int(row["independent_selected_block_dimension"]))

    def test_hash_manifest_and_failure_evidence(self) -> None:
        for row in read_csv(HASH_PATH):
            path = ROOT / row["artifact"]
            self.assertTrue(path.is_file(), row["artifact"])
            self.assertEqual(int(row["bytes"]), path.stat().st_size)
            self.assertEqual(row["sha256"], sha256(path))
        evidence = FAILURE_PATH.read_text(encoding="utf-8")
        self.assertIn("metadata_resolution_stalled_then_terminated", evidence)
        self.assertIn("MATLAB `schur`/`ordschur`", evidence)
        document = DOC_PATH.read_text(encoding="utf-8")
        self.assertIn("0/4", document)
        self.assertIn("paper_projection=fail", document)


if __name__ == "__main__":
    unittest.main()
