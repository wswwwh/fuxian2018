"""Artifact and leakage gates for the Chapter 4 frozen camera protocol."""

from __future__ import annotations

import csv
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = (
    ROOT / "data" / "computed" / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
)
CHECK_SCRIPT = ROOT / "scripts" / "register_chapter4_camera_holdout_protocol.py"


class Chapter4CameraHoldoutProtocolTests(unittest.TestCase):
    def test_frozen_protocol_check_uses_pre_fit_source_binding(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECK_SCRIPT), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("source_binding=historical_pre_fit", result.stdout)

    def test_protocol_is_explicitly_nonblind_and_projection_is_not_run(self) -> None:
        with CSV_PATH.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(row["historical_exposure"] == "true" for row in rows))
        self.assertTrue(
            all(row["paper_projection_acceptance"] == "not_run" for row in rows)
        )
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in rows))

    def test_holdout_and_transform_boundaries_are_frozen(self) -> None:
        with CSV_PATH.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        holdout = [row for row in rows if row["panel_id"] == "d"]
        self.assertEqual(len(holdout), 4)
        self.assertTrue(
            all(row["panel_role"] == "programmatic_frozen_holdout" for row in holdout)
        )
        self.assertTrue(
            all(row["holdout_red_mask_allowed_during_fit"] == "false" for row in rows)
        )
        self.assertTrue(all(row["per_panel_transform_allowed"] == "false" for row in rows))
        self.assertEqual(
            {row["epsilon_scope"] for row in rows},
            {"nested_H0_global_or_H1_family;never_branch_figure_panel"},
        )
        self.assertEqual({row["paper_epsilon_numeric"] for row in rows}, {"not_reported"})
        self.assertEqual({row["epsilon_hypotheses"] for row in rows}, {"H0_global;H1_family"})


if __name__ == "__main__":
    unittest.main()
