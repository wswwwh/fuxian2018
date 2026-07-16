"""End-to-end regression tests for Stage D-F and paper artifacts."""

from __future__ import annotations

from collections import Counter
import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "invariant_bundles"
METHOD = RESEARCH / "results" / "csv" / "method_comparison.csv"
FIGURES = RESEARCH / "figures" / "research_figure_manifest.csv"
PAPER = RESEARCH / "paper"


class InvariantBundleResearchArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with METHOD.open(newline="", encoding="utf-8") as stream:
            cls.method_rows = list(csv.DictReader(stream))

    def test_method_campaign_preserves_exact_outcome_counts(self) -> None:
        self.assertEqual(len(self.method_rows), 45)
        expected = {
            "traditional_pointwise_eigendecomposition": Counter({"fail": 15}),
            "ordered_partial_real_schur_tracking": Counter(
                {"accepted": 7, "boundary": 4, "fail": 4}
            ),
            "qr_svd_shifted_cocycle_iteration": Counter(
                {"accepted": 10, "fail": 5}
            ),
        }
        for method, counts in expected.items():
            actual = Counter(
                row["research_status"]
                for row in self.method_rows
                if row["method"] == method
            )
            self.assertEqual(actual, counts)

    def test_improved_methods_repeat_advantage_on_three_family_anchors(self) -> None:
        by_key = {
            (row["case_id"], row["method"]): row for row in self.method_rows
        }
        for case_id in (
            "em_halo_12p40_n45",
            "em_vertical_12p66_n57",
            "se_active_geometry_member_468",
        ):
            baseline = float(
                by_key[
                    (case_id, "traditional_pointwise_eigendecomposition")
                ]["max_invariance_residual"]
            )
            for method in (
                "ordered_partial_real_schur_tracking",
                "qr_svd_shifted_cocycle_iteration",
            ):
                improved = by_key[(case_id, method)]
                self.assertEqual(improved["research_status"], "accepted")
                self.assertLess(
                    float(improved["max_invariance_residual"]), baseline / 1.0e4
                )

    def test_route_h_physical_and_legacy_controls_remain_separate(self) -> None:
        by_key = {
            (row["case_id"], row["method"]): row for row in self.method_rows
        }
        physical = by_key[
            ("route_h_member_68", "ordered_partial_real_schur_tracking")
        ]
        legacy = by_key[
            (
                "route_h_member_68_legacy_dg_positive",
                "ordered_partial_real_schur_tracking",
            )
        ]
        self.assertEqual(int(physical["bundle_dimension"]), 2)
        self.assertEqual(physical["research_status"], "fail")
        self.assertEqual(int(legacy["bundle_dimension"]), 1)
        self.assertEqual(legacy["research_status"], "accepted")
        self.assertLess(
            float(physical["source_map_residual_recomputed"]), 1.0e-9
        )
        self.assertGreater(
            float(legacy["source_map_residual_recomputed"]), 1.0e-3
        )

    def test_paper_and_figure_deliverables_cover_required_sections(self) -> None:
        manuscript = (PAPER / "manuscript.md").read_text(encoding="utf-8")
        for section in range(1, 14):
            self.assertIn(f"## {section}.", manuscript)
        for name in (
            "abstract.md",
            "contributions.md",
            "figure_plan.md",
            "tables.md",
            "limitations.md",
            "claim_evidence_matrix.csv",
            "paper_build_manifest.json",
        ):
            self.assertTrue((PAPER / name).is_file(), name)
        with FIGURES.open(newline="", encoding="utf-8") as stream:
            figures = list(csv.DictReader(stream))
        self.assertEqual(len(figures), 12)
        self.assertEqual(len({row["figure_id"] for row in figures}), 6)


if __name__ == "__main__":
    unittest.main()
