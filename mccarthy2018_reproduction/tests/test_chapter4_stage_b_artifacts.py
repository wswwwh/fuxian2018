"""Artifact-level tests for Stage B negative controls and conclusion."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class Chapter4StageBArtifactTests(unittest.TestCase):
    def test_negative_controls_are_one_factor_and_do_not_promote_holdout(self) -> None:
        rows = read_rows(DATA / "chapter4_projection_semantics_negative_controls.csv")
        self.assertEqual(len(rows), 24)
        self.assertEqual(
            {row["control_id"] for row in rows},
            {
                "panel_time_mapping",
                "mask_extraction_order",
                "quad_rasterizer",
                "surface_renderer",
                "explicit_stm_transport",
            },
        )
        self.assertTrue(all(row["fixed_camera"] == "true" for row in rows))
        self.assertTrue(all(row["fixed_epsilon"] == "true" for row in rows))
        self.assertTrue(all(row["fixed_crop"] == "true" for row in rows))
        self.assertTrue(all(row["fixed_thresholds"] == "true" for row in rows))
        self.assertTrue(all(row["paper_projection_acceptance"] == "fail" for row in rows))
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in rows))

    def test_simple_rendering_controls_are_close_but_transport_is_material(self) -> None:
        rows = read_rows(DATA / "chapter4_projection_semantics_negative_controls.csv")
        for control in (
            "mask_extraction_order",
            "quad_rasterizer",
            "surface_renderer",
        ):
            subset = [row for row in rows if row["control_id"] == control]
            self.assertEqual(len(subset), 4)
            self.assertTrue(
                all(row["semantic_similarity_gate"] == "close" for row in subset)
            )
        panel = [row for row in rows if row["control_id"] == "panel_time_mapping"]
        self.assertTrue(
            all(float(row["delta_projection_loss_from_canonical"]) >= 0.0 for row in panel)
        )
        transport = [
            row for row in rows if row["control_id"] == "explicit_stm_transport"
        ]
        self.assertEqual(len(transport), 8)
        self.assertTrue(
            all(
                row["semantic_similarity_gate"] == "material_difference"
                for row in transport
            )
        )

    def test_stage_b_conclusion_is_complete_but_not_a_numerical_pass(self) -> None:
        rows = read_rows(DATA / "chapter4_invariant_bundle_stage_b_conclusion.csv")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(
            row["stage_b_status"],
            "complete_with_negative_and_boundary_results",
        )
        self.assertEqual(row["halo_cross_resolution_pass_rows"], "0/2")
        self.assertEqual(row["vertical_cross_resolution_pass_rows"], "0/2")
        self.assertEqual(row["halo_posthoc_projection_pass_rows"], "0/6")
        self.assertEqual(row["vertical_posthoc_projection_pass_rows"], "0/6")
        self.assertEqual(row["frozen_holdout_status"], "fail_0_of_4_unchanged")
        self.assertEqual(row["paper_projection_acceptance"], "fail")
        self.assertEqual(row["paper_3d_equivalence"], "false")
        self.assertIn("not_unique_proof", row["pointwise_eigenvector_judgment"])

    def test_stage_b_report_keeps_research_and_reproduction_separate(self) -> None:
        text = (
            ROOT / "docs" / "chapter4_invariant_bundle_stage_b_conclusion.md"
        ).read_text(encoding="utf-8")
        self.assertIn("complete with negative and boundary results", text)
        self.assertIn("does not mean the numerical gates passed", text)
        self.assertIn("figure_validation_table.csv", text)
        self.assertIn("paper_projection=fail", text)


if __name__ == "__main__":
    unittest.main()
