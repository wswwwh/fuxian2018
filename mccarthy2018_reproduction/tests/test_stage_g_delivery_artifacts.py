"""Artifact-level checks for the Stage-G adviser delivery package."""

from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = PROJECT_ROOT / "reports" / "mccarthy2018_figure_comparison"
STAGE_G = PROJECT_ROOT / "stage_g_delivery_review"
ADVISER_ROOT = PROJECT_ROOT / "reports" / "adviser_delivery"
DOCX_NAME = "McCarthy2018_54图逐图复现对照报告.docx"
PDF_NAME = "McCarthy2018_54图逐图复现对照报告.pdf"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def canonical_artifact(path: Path) -> tuple[str, bytes]:
    data = path.read_bytes()
    if path.suffix.lower() in {".csv", ".json", ".md", ".txt", ".py", ".js", ".yml", ".yaml"}:
        text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        return "utf8_lf_normalized", text.encode("utf-8")
    return "raw_bytes", data


class StageGDeliveryArtifactsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validation = json.loads((STAGE_G / "delivery_validation.json").read_text(encoding="utf-8"))
        cls.run_config = json.loads((STAGE_G / "stage_g_run_config.json").read_text(encoding="utf-8"))
        cls.audit_rows = read_csv(REPORT_ROOT / "final_placeholder_audit.csv")

    def test_delivery_validation_passes_all_checks(self) -> None:
        self.assertEqual(self.validation["status"], "PASS")
        self.assertEqual(self.validation["coverage"], {"registry": 54, "docx_figure_ids": 54, "pdf_figure_ids": 54})
        self.assertTrue(all(item["pass"] for item in self.validation["checks"].values()))
        self.assertEqual(self.validation["pending"]["registry_field_count"], 0)
        self.assertEqual(self.validation["pending"]["manual_field_count"], 0)
        self.assertEqual(self.validation["pending"]["confirmed_field_count"], 3)
        self.assertEqual(self.validation["docx"]["sha256"], sha256(REPORT_ROOT / DOCX_NAME))
        self.assertEqual(self.validation["pdf"]["sha256"], sha256(REPORT_ROOT / PDF_NAME))

    def test_placeholder_audit_has_expected_scopes(self) -> None:
        self.assertEqual(len(self.audit_rows), 63)
        self.assertEqual(sum(row["status"] == "confirmed_by_user" for row in self.audit_rows), 3)
        self.assertEqual(sum(row["field"] == "coordinate_system" for row in self.audit_rows), 6)
        self.assertEqual(sum(row["field"] == "comparison_asset" for row in self.audit_rows), 54)
        self.assertTrue(all("【待核实】" not in row["current_value"] for row in self.audit_rows if row["scope"] == "registry"))

    def test_adviser_directory_contains_core_and_stage_nine_files(self) -> None:
        expected = {
            DOCX_NAME,
            PDF_NAME,
            "复现情况一页说明.pdf",
            "导师审阅重点.md",
            "invariant_bundle研究摘要_4页.docx",
            "invariant_bundle研究摘要_4页.pdf",
            "给导师的审阅问题.md",
        }
        actual = {path.name for path in ADVISER_ROOT.iterdir() if path.is_file()}
        self.assertEqual(actual, expected)
        self.assertEqual(sha256(REPORT_ROOT / DOCX_NAME), sha256(ADVISER_ROOT / DOCX_NAME))
        self.assertEqual(sha256(REPORT_ROOT / PDF_NAME), sha256(ADVISER_ROOT / PDF_NAME))
        self.assertEqual(len(PdfReader(ADVISER_ROOT / PDF_NAME).pages), 122)
        self.assertEqual(len(PdfReader(ADVISER_ROOT / "复现情况一页说明.pdf").pages), 1)
        self.assertEqual(
            len(PdfReader(ADVISER_ROOT / "invariant_bundle研究摘要_4页.pdf").pages),
            4,
        )

    def test_visual_review_and_frozen_truth_lock_pass(self) -> None:
        self.assertGreater((STAGE_G / "final_pages_contact_sheet.png").stat().st_size, 1_000_000)
        review = (STAGE_G / "selected_pages_review.md").read_text(encoding="utf-8")
        self.assertIn("状态：**PASS**", review)
        self.assertIn("122/122", review)
        self.assertEqual(self.run_config["status"], "PASS")
        self.assertTrue(self.run_config["frozen_truth_unchanged"])
        self.assertEqual(
            self.run_config["frozen_truth_hashes_before"],
            self.run_config["frozen_truth_hashes_after"],
        )

    def test_recorded_artifact_hashes_match_files(self) -> None:
        rows = read_csv(STAGE_G / "artifact_hashes.csv")
        self.assertGreaterEqual(len(rows), 35)
        for row in rows:
            path = PROJECT_ROOT / row["path"]
            self.assertTrue(path.is_file(), row["path"])
            mode, canonical = canonical_artifact(path)
            self.assertEqual(mode, row["hash_mode"], row["path"])
            self.assertEqual(len(canonical), int(row["canonical_bytes"]), row["path"])
            self.assertEqual(hashlib.sha256(canonical).hexdigest(), row["sha256"], row["path"])


if __name__ == "__main__":
    unittest.main()
