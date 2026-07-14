"""Gates for the frozen static Chapter 4 camera calibration."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

import numpy as np

from qp_orbits.chapter4_camera import (
    CHAPTER4_PAPER_CAMERAS,
    chapter4_axis_corner_positions,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"
DIGITIZED = ROOT / "data" / "digitized"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class Chapter4CameraCalibrationTests(unittest.TestCase):
    def test_frozen_camera_values_and_axis_corners(self) -> None:
        self.assertEqual(set(CHAPTER4_PAPER_CAMERAS), {"4.3", "4.4", "4.5", "4.6"})
        self.assertEqual(CHAPTER4_PAPER_CAMERAS["4.3"].azimuth_deg, -45.0)
        self.assertEqual(CHAPTER4_PAPER_CAMERAS["4.5"].azimuth_deg, -65.0)
        self.assertEqual(CHAPTER4_PAPER_CAMERAS["4.6"].azimuth_deg, 110.0)
        self.assertEqual(chapter4_axis_corner_positions("4.3").shape, (4, 3))
        np.testing.assert_allclose(
            chapter4_axis_corner_positions("4.6")[0],
            [1.0, 0.4, -0.15],
        )

    def test_all_static_panels_pass_without_red_mask_or_panel_transform(self) -> None:
        metrics = _rows(DATA / "chapter4_fig43_fig46_camera_static_metrics.csv")
        parameters = _rows(DATA / "chapter4_fig43_fig46_camera_parameters.csv")
        anchors = _rows(DIGITIZED / "chapter4_fig43_fig46_camera_anchors.csv")
        self.assertEqual(len(metrics), 16)
        self.assertEqual(len(parameters), 4)
        self.assertTrue(all(row["static_camera_gate"] == "pass" for row in metrics))
        self.assertTrue(all(row["red_mask_read"] == "false" for row in metrics))
        self.assertTrue(all(row["red_mask_read"] == "false" for row in parameters))
        self.assertTrue(all(row["per_panel_transform"] == "forbidden" for row in parameters))
        self.assertTrue(
            all(row["used_for_fit"] == "false" for row in anchors if row["panel_id"] == "d")
        )
        self.assertTrue(
            all(float(row["anchor_rmse_px_on_512_grid"]) <= 4.0 for row in metrics)
        )
        self.assertTrue(
            all(float(row["anchor_max_error_px_on_512_grid"]) <= 8.0 for row in metrics)
        )


if __name__ == "__main__":
    unittest.main()
