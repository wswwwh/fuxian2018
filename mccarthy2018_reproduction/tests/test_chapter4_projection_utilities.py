"""Unit tests for deterministic Chapter 4 projection utilities."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.chapter4_projection import (
    HoldoutLeakageError,
    log2_refinement_grid,
    projection_mask_metrics,
    rasterize_surface_mask,
)


class Chapter4ProjectionUtilityTests(unittest.TestCase):
    def test_curve_seam_is_closed_without_closing_phase(self) -> None:
        uv = np.asarray(
            [
                [[0.2, 0.2], [0.8, 0.2], [0.5, 0.4]],
                [[0.2, 0.8], [0.8, 0.8], [0.5, 0.6]],
            ]
        )
        baseline = rasterize_surface_mask(uv, size=96)
        shifted = rasterize_surface_mask(np.roll(uv, 1, axis=1), size=96)
        np.testing.assert_array_equal(baseline, shifted)

    def test_known_pixel_shift_increases_distance(self) -> None:
        paper = np.zeros((64, 64), dtype=bool)
        paper[20:40, 20:40] = True
        shifted = np.zeros_like(paper)
        shifted[20:40, 25:45] = True
        same = projection_mask_metrics(paper, paper)
        moved = projection_mask_metrics(paper, shifted)
        self.assertEqual(same["projection_loss"], 0.0)
        self.assertGreater(moved["symmetric_chamfer_px"], 0.0)
        self.assertLess(moved["f1_at_0p01_diagonal"], 1.0)

    def test_log_refinement_is_centered(self) -> None:
        grid = log2_refinement_grid(4.5e-7)
        self.assertEqual(grid.shape, (5,))
        self.assertAlmostEqual(grid[2], 4.5e-7)
        self.assertTrue(np.all(np.diff(grid) > 0.0))

    def test_holdout_error_type_is_explicit(self) -> None:
        self.assertTrue(issubclass(HoldoutLeakageError, RuntimeError))


if __name__ == "__main__":
    unittest.main()
