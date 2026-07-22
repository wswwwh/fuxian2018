"""Regression gates for the adviser-flagged figure correction campaign."""

from __future__ import annotations

import csv
from hashlib import sha256
import unittest
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "computed"
REPORT = PROJECT_ROOT / "reports" / "adviser_figure_correction_verification"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest().upper()


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "pass"}


class AdviserFigureCorrectionVerificationTests(unittest.TestCase):
    def test_all_25_flagged_figures_pass_presentation_correctness_only(self) -> None:
        rows = _rows(REPORT / "current_figure_correction_verification.csv")
        self.assertEqual(len(rows), 25)
        self.assertEqual(sum(row["previous_priority"] == "P0" for row in rows), 18)
        self.assertEqual(sum(row["previous_priority"] == "P1" for row in rows), 7)
        self.assertTrue(all(row["presentation_correctness"] == "pass" for row in rows))
        self.assertTrue(all(row["full_paper_equivalence"] == "not_claimed" for row in rows))
        for row in rows:
            for field in (
                "source_truth_gate",
                "metadata_gate",
                "numerical_boundary_gate",
                "artifact_gate",
                "visual_hash_gate",
            ):
                self.assertEqual(row[field], "true", f"{row['figure_id']} {field}")

    def test_visual_review_manifest_is_bound_to_current_png_bytes(self) -> None:
        rows = _rows(REPORT / "visual_review_manifest.csv")
        self.assertEqual(len(rows), 25)
        for row in rows:
            png = PROJECT_ROOT / "outputs" / "figures_png" / f"fig_{row['figure_id'].replace('.', '_')}.png"
            self.assertEqual(row["verdict"], "pass")
            self.assertEqual(row["png_sha256"], _sha(png))

    def test_high_risk_numerical_boundaries_are_not_promoted(self) -> None:
        period_q = {row["resonance"]: row for row in _rows(DATA / "chapter3_period_q_per_figure_audit.csv")}
        self.assertEqual(period_q["2"]["strict_acceptance"], "true")
        self.assertEqual(period_q["3"]["strict_acceptance"], "true")
        self.assertEqual(period_q["8"]["strict_acceptance"], "false")

        fig42 = _rows(DATA / "chapter4_fig42_digitized_comparison_audit.csv")[0]
        self.assertTrue(_truthy(fig42["pointwise_overlap_acceptance"]))
        self.assertFalse(_truthy(fig42["full_curve_coverage"]))
        self.assertGreater(float(fig42["computed_tail_time_gap_days"]), 0.04)

        holdout = _rows(DATA / "chapter4_fig43_fig46_projection_holdout_audit.csv")
        self.assertEqual({row["figure_id"] for row in holdout}, {"4.3", "4.4", "4.5", "4.6"})
        self.assertTrue(all(row["holdout_gate"] == "fail" for row in holdout))
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in holdout))

        fig510 = _rows(DATA / "chapter5_fig510_bcr4bp_transfer_audit.csv")
        self.assertEqual(sum(_truthy(row["numerical_acceptance"]) for row in fig510), 2)
        self.assertEqual(sum(_truthy(row["paper_equivalence"]) for row in fig510), 0)

        rendezvous = _rows(DATA / "chapter5_nrho_rendezvous_per_figure_audit.csv")
        self.assertEqual(
            max(float(row["arrival_offset_hours"]) for row in rendezvous if _truthy(row["acceptance"])),
            11.0,
        )

    def test_fig41_geometry_and_fig514_leo_target_are_explicit(self) -> None:
        rows = _rows(DATA / "chapter4_fig41_reported_precision_states.csv")
        time_count = 1 + max(int(row["time_index"]) for row in rows)
        curve_count = 1 + max(int(row["curve_index"]) for row in rows)
        surface = np.asarray(
            [[float(row[name]) for name in ("x", "y", "z")] for row in rows]
        ).reshape(time_count, curve_count, 3)
        width_km = max(
            float(np.max(np.linalg.norm(item[:, None] - item[None, :], axis=2)))
            for item in surface
        ) * 384400.0
        self.assertLess(width_km, 0.01)
        self.assertNotIn(
            "ax3d.plot_surface",
            (PROJECT_ROOT / "figures" / "fig_4_01.py").read_text(encoding="utf-8"),
        )

        leo = _rows(DATA / "chapter5_active_geometry_leo_transfer_audit.csv")[0]
        self.assertTrue(_truthy(leo["acceptance"]))
        self.assertAlmostEqual(float(leo["target_periapsis_radius_km"]), 6563.0, places=10)
        self.assertLessEqual(float(leo["periapsis_target_error_km"]), 5.0)


if __name__ == "__main__":
    unittest.main()
