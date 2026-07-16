"""Acceptance tests for the complete Chinese invariant-bundle paper release."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import unittest
import zipfile

import numpy as np

from qp_orbits.artifact_fingerprints import fingerprint_matches


ROOT = Path(__file__).resolve().parents[1]
CONFIG = (
    ROOT / "research" / "invariant_bundles" / "configs" / "paper_release.json"
)
RELEASE = ROOT / "research" / "invariant_bundles" / "paper_release"
EVIDENCE = ROOT / "research" / "invariant_bundles" / "paper_release_validation"
PAPER = ROOT / "research" / "invariant_bundles" / "paper"
HOLDOUT = (
    ROOT
    / "data"
    / "computed"
    / "chapter4_fig43_fig46_projection_holdout_audit.csv"
)
CLAIM_FIELDS = [
    "claim_id",
    "claim_text",
    "supporting_cases",
    "supporting_csv",
    "supporting_figure",
    "acceptance_threshold",
    "status",
    "limitation",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


class InvariantBundlePaperReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.manuscript = (RELEASE / "manuscript_zh.md").read_text(
            encoding="utf-8"
        )
        cls.claims = read_csv(RELEASE / "claim_evidence_matrix.csv")
        cls.summary = json.loads(
            (EVIDENCE / "paper_release_summary.json").read_text(encoding="utf-8")
        )

    def test_identity_title_and_positioning_are_exact(self) -> None:
        self.assertEqual(self.config["author"], "兀文昊")
        self.assertEqual(self.config["adviser"], "张晨")
        self.assertEqual(self.config["institution"], "中国科学院大学")
        self.assertEqual(
            self.config["title"],
            "拟周期轨道实不变子束计算方法的数值比较与可靠性分析",
        )
        self.assertEqual(
            self.config["study_positioning"],
            "numerical_framework_and_systematic_comparison",
        )
        self.assertEqual(self.config["submission_readiness"], "not_claimed")

    def test_release_has_every_required_top_level_deliverable(self) -> None:
        required = {
            "manuscript_zh.md",
            "manuscript_zh.docx",
            "figures",
            "tables",
            "references.bib",
            "claim_evidence_matrix.csv",
            "limitations.md",
            "reviewer_quick_assessment.md",
        }
        self.assertTrue(required.issubset({path.name for path in RELEASE.iterdir()}))
        self.assertTrue((RELEASE / "figures").is_dir())
        self.assertTrue((RELEASE / "tables").is_dir())

    def test_manuscript_is_complete_chinese_draft_with_13_sections(self) -> None:
        self.assertGreater(len(self.manuscript), 18000)
        for index, section in enumerate(self.config["required_sections"], start=1):
            self.assertIn(f"## {index}. {section}", self.manuscript)
        self.assertIn("## 摘要", self.manuscript)
        self.assertIn("## 参考文献", self.manuscript)
        self.assertIn("**关键词：**", self.manuscript)
        self.assertGreaterEqual(self.manuscript.count("!["), 9)

    def test_seven_required_scientific_questions_are_answered(self) -> None:
        for marker in (
            "pointwise eig 不是 cocycle invariant bundle",
            "复共轭对不能被投影或重命名为一维实方向",
            "Schur 与 QR/SVD 解决的问题不同",
            "哪些案例上两种改进方法有效",
            "哪些案例上仍失败",
            "失败来源需要分层",
            "局部 bundle 收敛与全局 manifold sheet 收敛",
        ):
            if marker in ("哪些案例上两种改进方法有效", "哪些案例上仍失败"):
                # These two answers are expressed concretely rather than as question labels.
                continue
            self.assertIn(marker, self.manuscript)
        self.assertIn("Halo N45、Vertical N57、Sun–Earth 468", self.manuscript)
        self.assertIn("physical Route H 四案和低分辨率全片收敛仍失败", self.manuscript)

    def test_claim_evidence_matrix_has_exact_schema_and_bound_evidence(self) -> None:
        with (RELEASE / "claim_evidence_matrix.csv").open(
            "r", encoding="utf-8", newline=""
        ) as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, CLAIM_FIELDS)
        self.assertEqual(len(self.claims), 15)
        self.assertEqual(len({row["claim_id"] for row in self.claims}), 15)
        self.assertTrue(all(row["status"] and row["limitation"] for row in self.claims))
        for row in self.claims:
            for relative in filter(None, row["supporting_csv"].split(";")):
                self.assertTrue((ROOT / relative).is_file(), relative)
            for relative in filter(None, row["supporting_figure"].split(";")):
                self.assertTrue((RELEASE / relative).is_file(), relative)

    def test_references_are_exactly_the_verified_bibliography(self) -> None:
        self.assertEqual(
            sha256(RELEASE / "references.bib"),
            sha256(PAPER / "references_verified.bib"),
        )
        bibliography = (RELEASE / "references.bib").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"^@[a-z]+\{", bibliography, re.MULTILINE)), 25)
        self.assertNotIn("doi = {}", bibliography)

    def test_figures_and_summary_tables_are_complete(self) -> None:
        figure_manifest = read_csv(RELEASE / "figures" / "figure_manifest.csv")
        self.assertEqual(len(figure_manifest), 9)
        for row in figure_manifest:
            png = RELEASE / "figures" / row["file"]
            self.assertTrue(png.is_file())
            self.assertEqual(sha256(png), row["source_sha256"])
            self.assertTrue(png.with_suffix(".pdf").is_file())
        expected_tables = {
            "table_15_case_summary.csv": 15,
            "table_high_resolution_anchors.csv": 9,
            "table_independent_schur_validation.csv": 12,
            "table_qr_svd_failure_classification.csv": 5,
            "table_ablation_variant_summary.csv": 7,
            "table_manifold_case_summary.csv": 21,
            "table_runtime_anchor_summary.csv": 9,
            "table_reproduction_truth_boundary.csv": 9,
        }
        for name, count in expected_tables.items():
            self.assertEqual(len(read_csv(RELEASE / "tables" / name)), count, name)

    def test_docx_is_valid_contains_identity_and_embeds_figures(self) -> None:
        path = RELEASE / "manuscript_zh.docx"
        self.assertGreater(path.stat().st_size, 500_000)
        with zipfile.ZipFile(path) as archive:
            self.assertIn("word/document.xml", archive.namelist())
            xml = archive.read("word/document.xml").decode("utf-8")
            media = [name for name in archive.namelist() if name.startswith("word/media/")]
        for marker in (
            self.config["title"],
            "兀文昊",
            "张晨",
            "中国科学院大学",
            "Chapter 4",
            "not_submission_ready",
        ):
            self.assertIn(marker, xml)
        self.assertGreaterEqual(len(media), 9)

    def test_render_validation_has_representative_page_previews(self) -> None:
        render = json.loads(
            (EVIDENCE / "render_validation.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(render["pdf_pages"], 12)
        self.assertEqual(render["libreoffice_return_code"], 0)
        self.assertTrue((ROOT / render["pdf_path"]).is_file())
        self.assertEqual(len(render["preview_paths"]), 3)
        for relative in render["preview_paths"]:
            self.assertTrue((ROOT / relative).is_file())

    def test_limitations_retain_every_nonnegotiable_boundary(self) -> None:
        text = (RELEASE / "limitations.md").read_text(encoding="utf-8")
        for marker in (
            "0/4",
            "paper_projection=fail",
            "paper_3d=false",
            "二维实共轭子空间",
            "80 位运算只重算残差",
            "局部 bundle 通过不能覆盖全局 manifold sheet 失败",
            "可重复不等于可投稿",
            "submission_readiness=not_claimed",
        ):
            self.assertIn(marker, text)

    def test_frozen_chapter4_holdout_is_unchanged(self) -> None:
        rows = read_csv(HOLDOUT)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(row["holdout_gate"] == "fail" for row in rows))
        self.assertTrue(
            all(row["paper_projection_acceptance"] == "fail" for row in rows)
        )
        self.assertTrue(
            all(row["paper_3d_equivalence"] == "false" for row in rows)
        )

    def test_npz_and_summary_match_release_truth(self) -> None:
        with np.load(
            EVIDENCE / "paper_release_validation.npz", allow_pickle=False
        ) as archive:
            self.assertEqual(archive["case_ids"].shape, (15,))
            self.assertEqual(archive["method_status"].shape, (45,))
            self.assertEqual(archive["manifold_status"].shape, (126,))
            self.assertEqual(archive["chapter4_holdout"].tolist(), [0, 4])
            self.assertEqual(archive["submission_readiness"].tolist(), ["not_claimed"])
        self.assertEqual(self.summary["status"], "pass")
        self.assertEqual(self.summary["claim_evidence_rows"], 15)
        self.assertEqual(self.summary["formal_references"], 25)
        self.assertEqual(self.summary["truth_boundary_status"], "preserved")
        self.assertEqual(self.summary["submission_readiness"], "not_claimed")

    def test_no_unresolved_placeholders_or_positive_submission_claim(self) -> None:
        combined = "\n".join(
            [
                self.manuscript,
                (RELEASE / "limitations.md").read_text(encoding="utf-8"),
                (RELEASE / "reviewer_quick_assessment.md").read_text(
                    encoding="utf-8"
                ),
            ]
        )
        for marker in ("TBD", "TODO", "待补", "<作者>", "<导师>", "<单位>"):
            self.assertNotIn(marker, combined)
        for overclaim in ("本文首次提出", "本文证明了全局收敛", "本稿已经达到投稿条件"):
            self.assertNotIn(overclaim, combined)

    def test_artifact_hash_manifest_verifies(self) -> None:
        rows = read_csv(EVIDENCE / "artifact_hashes.csv")
        self.assertGreaterEqual(len(rows), 55)
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
