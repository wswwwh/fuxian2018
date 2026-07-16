"""Acceptance contracts for the verified invariant-bundle literature stage."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_invariant_bundle_literature as builder  # noqa: E402


CONFIG = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "configs"
    / "literature_verification.json"
)
PAPER = ROOT / "research" / "invariant_bundles" / "paper"
EVIDENCE = ROOT / "research" / "invariant_bundles" / "literature_validation"
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
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


class InvariantBundleLiteratureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.matrix = read_csv(PAPER / "literature_matrix.csv")
        cls.coverage = read_csv(PAPER / "literature_topic_coverage.csv")
        cls.summary = json.loads(
            (EVIDENCE / "literature_validation_summary.json").read_text(
                encoding="utf-8"
            )
        )

    def test_config_passes_structural_and_truth_boundary_validation(self) -> None:
        stats = builder.validate_config(self.config)
        self.assertEqual(stats["reference_count"], 25)
        self.assertEqual(stats["doi_count"], 21)
        self.assertEqual(stats["no_doi_count"], 4)

    def test_required_literature_matrix_has_exact_schema(self) -> None:
        with (PAPER / "literature_matrix.csv").open(
            "r", encoding="utf-8", newline=""
        ) as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, builder.MATRIX_FIELDS)
        self.assertEqual(len(self.matrix), 25)
        self.assertTrue(all(row["verified"] == "yes" for row in self.matrix))

    def test_every_retained_doi_is_unique_and_syntactically_valid(self) -> None:
        dois = [row["doi"] for row in self.matrix if row["doi"]]
        self.assertEqual(len(dois), 21)
        self.assertEqual(len({doi.casefold() for doi in dois}), len(dois))
        self.assertTrue(all(builder.DOI_PATTERN.fullmatch(doi) for doi in dois))

    def test_absent_dois_are_visible_and_never_guessed(self) -> None:
        no_doi = {row["reference_id"] for row in self.matrix if not row["doi"]}
        self.assertEqual(
            no_doi,
            {
                "McCarthy2018",
                "OlikaraHowell2010",
                "Olikara2010Thesis",
                "McCarthyHowell2021",
            },
        )
        config_by_id = {
            row["reference_id"]: row for row in self.config["references"]
        }
        self.assertTrue(
            all(config_by_id[reference_id]["doi_status"] == "not_assigned" for reference_id in no_doi)
        )

    def test_all_nine_required_topics_are_covered(self) -> None:
        self.assertEqual(len(self.coverage), 9)
        self.assertTrue(all(row["status"] == "covered" for row in self.coverage))
        self.assertTrue(all(int(row["reference_count"]) >= 1 for row in self.coverage))
        self.assertEqual(
            {row["topic_id"] for row in self.coverage},
            {row["topic_id"] for row in self.config["required_topics"]},
        )

    def test_positioning_rejects_methodological_overclaim(self) -> None:
        text = (PAPER / "literature_positioning.md").read_text(encoding="utf-8")
        self.assertIn("`numerical_framework_and_systematic_comparison`", text)
        self.assertIn("does **not** claim a new invariant-bundle theorem", text)
        self.assertIn("`methodological_innovation`: rejected", text)
        self.assertIn("**not_submission_ready**", text)

    def test_frozen_chapter4_and_route_h_boundaries_are_explicit(self) -> None:
        text = (PAPER / "literature_positioning.md").read_text(encoding="utf-8")
        for marker in (
            "`0/4`",
            "`paper_projection=fail`",
            "`paper_3d=false`",
            "two-dimensional real conjugate subspaces",
            "positive control",
        ):
            self.assertIn(marker, text)
        holdout = read_csv(HOLDOUT)
        self.assertEqual(len(holdout), 4)
        self.assertTrue(all(row["holdout_gate"] == "fail" for row in holdout))
        self.assertTrue(
            all(row["paper_projection_acceptance"] == "fail" for row in holdout)
        )
        self.assertTrue(
            all(row["paper_3d_equivalence"] == "false" for row in holdout)
        )

    def test_bibtex_contains_every_verified_reference(self) -> None:
        text = (PAPER / "references_verified.bib").read_text(encoding="utf-8")
        for row in self.matrix:
            self.assertRegex(
                text,
                re.compile(r"@[a-z]+\{" + re.escape(row["reference_id"]) + r",", re.IGNORECASE),
            )
        self.assertNotIn("doi = {}", text)

    def test_npz_is_machine_readable_and_matches_csv(self) -> None:
        with np.load(EVIDENCE / "literature_validation.npz", allow_pickle=False) as archive:
            self.assertEqual(archive["reference_ids"].tolist(), [row["reference_id"] for row in self.matrix])
            self.assertEqual(archive["topic_membership"].shape, (25, 9))
            self.assertTrue(archive["verified"].all())
            self.assertEqual(
                archive["positioning"].tolist(),
                ["numerical_framework_and_systematic_comparison"],
            )

    def test_summary_and_failure_evidence_are_complete(self) -> None:
        self.assertEqual(self.summary["status"], "pass")
        self.assertEqual(self.summary["verified_reference_count"], 25)
        self.assertEqual(self.summary["covered_topic_count"], 9)
        self.assertEqual(self.summary["metadata_failure_count"], 0)
        self.assertEqual(self.summary["submission_readiness"], "not_claimed")
        failure_text = (EVIDENCE / "failure_evidence.md").read_text(
            encoding="utf-8"
        )
        for reference_id in (
            "McCarthy2018",
            "OlikaraHowell2010",
            "Olikara2010Thesis",
            "McCarthyHowell2021",
        ):
            self.assertIn(reference_id, failure_text)

    def test_artifact_hash_manifest_verifies(self) -> None:
        rows = read_csv(EVIDENCE / "artifact_hashes.csv")
        self.assertGreaterEqual(len(rows), 12)
        for row in rows:
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), row["path"])
            self.assertEqual(path.stat().st_size, int(row["bytes"]))
            self.assertEqual(sha256(path), row["sha256"])


if __name__ == "__main__":
    unittest.main()
