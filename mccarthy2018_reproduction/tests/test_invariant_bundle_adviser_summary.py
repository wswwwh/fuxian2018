"""Acceptance tests for the strict four-page invariant-bundle adviser summary."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile

import numpy as np
from pypdf import PdfReader

from qp_orbits.artifact_fingerprints import fingerprint_matches


ROOT = Path(__file__).resolve().parents[1]
CONFIG = (
    ROOT / "research" / "invariant_bundles" / "configs" / "adviser_summary.json"
)
ADVISER = ROOT / "reports" / "adviser_delivery"
DOCX = ADVISER / "invariant_bundle研究摘要_4页.docx"
PDF = ADVISER / "invariant_bundle研究摘要_4页.pdf"
QUESTIONS = ADVISER / "给导师的审阅问题.md"
EVIDENCE = (
    ROOT / "research" / "invariant_bundles" / "adviser_summary_validation"
)
STAGE_G_HASHES = ROOT / "stage_g_delivery_review" / "artifact_hashes.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def recorded_sha256(path: Path, hash_mode: str) -> str:
    data = path.read_bytes()
    if hash_mode == "utf8_lf_normalized":
        text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        data = text.encode("utf-8")
    elif hash_mode != "raw_bytes":
        raise ValueError(f"unsupported recorded hash mode: {hash_mode}")
    return hashlib.sha256(data).hexdigest().upper()


class InvariantBundleAdviserSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.summary = json.loads(
            (EVIDENCE / "adviser_summary_summary.json").read_text(
                encoding="utf-8"
            )
        )
        cls.render = json.loads(
            (EVIDENCE / "render_validation.json").read_text(encoding="utf-8")
        )

    def test_final_adviser_package_has_exactly_seven_requested_files(self) -> None:
        expected = {
            "McCarthy2018_54图逐图复现对照报告.docx",
            "McCarthy2018_54图逐图复现对照报告.pdf",
            "复现情况一页说明.pdf",
            "导师审阅重点.md",
            "invariant_bundle研究摘要_4页.docx",
            "invariant_bundle研究摘要_4页.pdf",
            "给导师的审阅问题.md",
        }
        self.assertEqual(
            {path.name for path in ADVISER.iterdir() if path.is_file()}, expected
        )

    def test_stage_g_core_delivery_hashes_remain_unchanged(self) -> None:
        rows = {
            row["path"]: row for row in read_csv(STAGE_G_HASHES)
            if row["path"].startswith("reports/adviser_delivery/")
        }
        self.assertEqual(len(rows), 4)
        for relative, row in rows.items():
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(
                recorded_sha256(path, row["hash_mode"]),
                row["sha256"].upper(),
                relative,
            )

    def test_summary_is_exactly_four_rendered_pages(self) -> None:
        self.assertEqual(len(PdfReader(PDF).pages), 4)
        self.assertEqual(self.summary["pdf_pages"], 4)
        self.assertEqual(self.render["pdf_pages"], 4)
        self.assertEqual(self.render["libreoffice_return_code"], 0)
        self.assertGreater(DOCX.stat().st_size, 40_000)
        self.assertGreater(PDF.stat().st_size, 50_000)

    def test_docx_contains_identity_and_all_eight_required_content_items(self) -> None:
        with zipfile.ZipFile(DOCX) as archive:
            xml = archive.read("word/document.xml").decode("utf-8")
        for marker in (
            "兀文昊",
            "张晨",
            "中国科学院大学",
            *self.config["required_content"],
            "not_submission_ready",
        ):
            self.assertIn(marker, xml)

    def test_summary_exposes_all_method_and_failure_counts(self) -> None:
        with zipfile.ZipFile(DOCX) as archive:
            text = archive.read("word/document.xml").decode("utf-8")
        for marker in (
            "Pointwise eig 0/15",
            "7 通过/4 边界/4 失败",
            "10 通过/5 失败",
            "12/12 一致",
            "36 accepted、90 fail",
            "4 no_accepted_1d_bundle",
            "method_initialization_sensitive",
            "5301 科学检查",
        ):
            self.assertIn(marker, text)

    def test_truth_boundaries_are_visible_without_overclaim(self) -> None:
        combined = ""
        with zipfile.ZipFile(DOCX) as archive:
            combined += archive.read("word/document.xml").decode("utf-8")
        combined += QUESTIONS.read_text(encoding="utf-8")
        for marker in (
            "0/4",
            "paper_projection=fail",
            "paper_3d=false",
            "二维实子空间",
            "正控制不能替代",
            "not_submission_ready",
        ):
            self.assertIn(marker, combined)
        for overclaim in ("本文首次提出", "已达到投稿条件", "Route H physical 已通过"):
            self.assertNotIn(overclaim, combined)

    def test_question_file_contains_exactly_five_clear_questions(self) -> None:
        text = QUESTIONS.read_text(encoding="utf-8")
        questions = re.findall(r"^\d+\. .+？$", text, re.MULTILINE)
        self.assertEqual(len(questions), 5)
        self.assertEqual(len(self.config["review_questions"]), 5)
        for question in self.config["review_questions"]:
            self.assertIn(question, text)

    def test_metric_csv_and_npz_preserve_negative_results(self) -> None:
        metrics = {row["metric_id"]: row for row in read_csv(EVIDENCE / "adviser_summary_metrics.csv")}
        self.assertEqual(len(metrics), 12)
        self.assertEqual(metrics["pointwise_status"]["value"], "0 accepted;15 fail")
        self.assertIn("4 no_accepted_1d_bundle", metrics["qr_failure_cases"]["value"])
        self.assertEqual(metrics["chapter4_holdout"]["value"], "0/4;paper_projection=fail;paper_3d=false")
        with np.load(
            EVIDENCE / "adviser_summary_validation.npz", allow_pickle=False
        ) as archive:
            self.assertEqual(archive["case_ids"].shape, (15,))
            self.assertEqual(archive["method_status"].shape, (45,))
            self.assertEqual(archive["independent_schur_dimensions"].shape, (12,))
            self.assertEqual(archive["qr_failure_labels"].shape, (5,))
            self.assertEqual(archive["manifold_status"].shape, (126,))
            self.assertEqual(archive["pdf_pages"].tolist(), [4])
            self.assertEqual(archive["chapter4_holdout"].tolist(), [0, 4])
            self.assertEqual(archive["submission_readiness"].tolist(), ["not_claimed"])

    def test_all_four_pages_and_contact_sheet_are_preserved(self) -> None:
        previews = self.render["preview_paths"]
        self.assertEqual(len(previews), 5)
        self.assertEqual(
            sum("preview_page_" in relative for relative in previews), 4
        )
        self.assertEqual(
            sum("four_page_contact_sheet" in relative for relative in previews), 1
        )
        for relative in previews:
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertGreater(path.stat().st_size, 20_000, relative)

    def test_summary_status_and_positioning_are_bounded(self) -> None:
        self.assertEqual(self.summary["status"], "pass")
        self.assertEqual(self.summary["author"], "兀文昊")
        self.assertEqual(self.summary["adviser"], "张晨")
        self.assertEqual(self.summary["institution"], "中国科学院大学")
        self.assertEqual(self.summary["required_content"], "8/8")
        self.assertEqual(self.summary["review_questions"], 5)
        self.assertEqual(
            self.summary["positioning"],
            "numerical_framework_and_systematic_comparison",
        )
        self.assertEqual(self.summary["submission_readiness"], "not_claimed")
        self.assertEqual(self.summary["truth_boundary_status"], "preserved")

    def test_artifact_hash_manifest_verifies(self) -> None:
        rows = read_csv(EVIDENCE / "artifact_hashes.csv")
        self.assertGreaterEqual(len(rows), 35)
        for row in rows:
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), row["path"])
            self.assertTrue(
                fingerprint_matches(
                    path,
                    expected_bytes=int(row["bytes"]),
                    expected_sha256=row["sha256"],
                    hash_mode=row["hash_mode"],
                ),
                row["path"],
            )


if __name__ == "__main__":
    unittest.main()
