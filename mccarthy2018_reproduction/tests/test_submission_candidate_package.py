"""Regression tests for the adviser-facing submission-candidate package."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "submission_candidate"
    / "package"
)
CONFIG = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "submission_candidate"
    / "configs"
    / "submission_candidate_package.json"
)
SCRIPT = ROOT / "scripts" / "build_submission_candidate_package.py"
HOLDOUT = (
    ROOT
    / "data"
    / "computed"
    / "chapter4_fig43_fig46_projection_holdout_audit.csv"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def docx_text_and_media(path: Path) -> tuple[str, int]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        text = "".join(node.text or "" for node in root.iter(ns + "t"))
        media = sum(name.startswith("word/media/") for name in archive.namelist())
    return text, media


class SubmissionCandidatePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.summary = json.loads(
            (PACKAGE / "submission_candidate_summary.json").read_text(
                encoding="utf-8"
            )
        )
        cls.claims = read_csv(PACKAGE / "claim_evidence_matrix.csv")
        cls.zh = (PACKAGE / "manuscript_zh.md").read_text(encoding="utf-8")
        cls.en = (PACKAGE / "manuscript_en.md").read_text(encoding="utf-8")

    def test_required_outputs_and_exact_status_exist(self) -> None:
        for name in self.config["required_outputs"]:
            self.assertTrue((PACKAGE / name).is_file(), name)
        self.assertEqual(
            self.config["package_status"],
            "adviser_submission_decision_candidate",
        )
        self.assertFalse(self.config["external_submission_authorized"])
        self.assertFalse(self.config["target_journal_selected"])
        self.assertEqual(
            self.summary["package_status"],
            "adviser_submission_decision_candidate",
        )
        self.assertFalse(self.summary["external_submission_authorized"])
        self.assertFalse(self.summary["target_journal_selected"])

    def test_bilingual_manuscripts_cover_all_stage_h_campaigns(self) -> None:
        for token in (
            "Stage H",
            "稳定子束",
            "Route H 二维",
            "三周期传播",
            "三个新增 Sun–Earth",
            "adviser_submission_decision_candidate",
        ):
            self.assertIn(token, self.zh)
        for token in (
            "Preregistered Stage-H extensions",
            "Stable bundles",
            "rank-two",
            "Three-period propagation",
            "Three additional local Sun–Earth sources",
            "adviser_submission_decision_candidate",
        ):
            self.assertIn(token, self.en)
        self.assertNotIn("stable-bundle manifold campaign, two-dimensional", self.en)

    def test_claim_matrix_is_complete_and_boundary_aware(self) -> None:
        self.assertEqual(len(self.claims), 20)
        self.assertEqual(
            [row["claim_id"] for row in self.claims],
            [f"SC{index:02d}" for index in range(1, 21)],
        )
        by_id = {row["claim_id"]: row for row in self.claims}
        self.assertEqual(by_id["SC02"]["status"], "supported_negative")
        self.assertEqual(by_id["SC10"]["status"], "supported_with_bounded_scope")
        self.assertEqual(by_id["SC15"]["status"], "supported_boundary")
        self.assertIn("not an external independent solver", by_id["SC13"]["authority_boundary"])
        self.assertIn("outside the authorized scope", by_id["SC20"]["authority_boundary"])

    def test_frozen_baseline_and_holdout_are_not_promoted(self) -> None:
        self.assertEqual(self.summary["reproduction_target_rows"], 54)
        self.assertEqual(self.summary["chapter4_frozen_holdout"], "0/4")
        self.assertTrue(self.summary["authority_boundaries_preserved"])
        holdout = read_csv(HOLDOUT)
        self.assertEqual(len(holdout), 4)
        self.assertTrue(
            all(row["paper_projection_acceptance"] == "fail" for row in holdout)
        )
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in holdout))

    def test_stage_h_summary_counts_are_exact(self) -> None:
        self.assertEqual(self.summary["h2_stable_bundle"]["accepted_improved_rows"], 6)
        self.assertEqual(self.summary["h2_stable_manifold"]["rows"], 54)
        self.assertEqual(self.summary["h2_stable_manifold"]["accepted_improved_rows"], 36)
        self.assertEqual(self.summary["h3_route_h_2d"]["cases"], 2)
        self.assertEqual(self.summary["h3_route_h_2d"]["accepted_schur_manifold_rows"], 4)
        self.assertTrue(self.summary["h3_route_h_2d"]["never_one_dimensional"])
        self.assertEqual(self.summary["h4_long_propagation"]["accepted_rows"], 8)
        self.assertEqual(self.summary["h4_long_propagation"]["physical_boundary_rows"], 4)
        self.assertEqual(self.summary["h5_sun_earth"]["distinct_local_sources"], 3)
        self.assertEqual(
            self.summary["h5_sun_earth"]["benchmark_status_counts"],
            {"boundary": 6, "fail": 3},
        )

    def test_docx_containers_embed_expected_text_and_figures(self) -> None:
        expected = {
            "manuscript_zh.docx": 6,
            "manuscript_en.docx": 3,
            "adviser_decision_summary.docx": 0,
        }
        for name, minimum_media in expected.items():
            path = PACKAGE / name
            self.assertGreater(path.stat().st_size, 10_000)
            text, media = docx_text_and_media(path)
            self.assertIn("adviser_submission_decision_candidate", text)
            self.assertGreaterEqual(media, minimum_media)

    def test_repository_relative_hash_manifest_matches(self) -> None:
        rows = read_csv(PACKAGE / "artifact_hashes.csv")
        self.assertGreaterEqual(len(rows), 20)
        for row in rows:
            self.assertNotIn("\\", row["path"])
            artifact = ROOT / row["path"]
            self.assertTrue(artifact.is_file(), row["path"])
            self.assertEqual(artifact.stat().st_size, int(row["bytes"]))
            self.assertEqual(sha256(artifact), row["sha256"])

    def test_builder_check_mode_passes(self) -> None:
        environment = dict(**__import__("os").environ)
        environment["PYTHONPATH"] = "src"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SUBMISSION-CANDIDATE PACKAGE CHECK PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
