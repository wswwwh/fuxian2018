"""Leakage and artifact gates for the locked Chapter 4 projection fit."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from qp_orbits.chapter4_projection import HoldoutLeakageError, load_reference_panel_mask


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class Chapter4ProjectionFitTests(unittest.TestCase):
    def test_loader_rejects_holdout_before_opening_source(self) -> None:
        with self.assertRaises(HoldoutLeakageError):
            load_reference_panel_mask(ROOT, {"panel_id": "d"})

    def test_fit_artifacts_contain_no_holdout_rows(self) -> None:
        metrics = _rows(DATA / "chapter4_fig43_fig46_projection_fit_metrics.csv")
        selection = _rows(DATA / "chapter4_fig43_fig46_epsilon_model_selection.csv")
        lock = json.loads(
            (DATA / "chapter4_fig43_fig46_projection_fit_lock.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(metrics)
        self.assertEqual({row["panel_id"] for row in metrics}, {"a", "b", "c"})
        self.assertTrue(all(row["holdout_red_mask_read"] == "false" for row in metrics))
        self.assertTrue(all(row["paper_projection_acceptance"] == "not_run" for row in metrics))
        self.assertEqual(len(selection), 2)
        self.assertEqual(sum(row["selected_model"] == "true" for row in selection), 1)
        self.assertFalse(lock["holdout_red_mask_read"])
        self.assertEqual(lock["holdout_panel"], "d")
        self.assertIn(lock["selected_model"], {"H0_global", "H1_family"})
        self.assertFalse(lock["paper_3d_equivalence"])


if __name__ == "__main__":
    unittest.main()
