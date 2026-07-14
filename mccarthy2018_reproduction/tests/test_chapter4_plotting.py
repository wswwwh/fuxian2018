"""Fast geometry tests for the Chapter 4 plotting helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "figures"))

from _chapter4_plotting import _close_periodic_curve_axis  # noqa: E402


class Chapter4PlottingTests(unittest.TestCase):
    def test_periodic_curve_axis_is_closed_without_mutating_input(self) -> None:
        surface = np.arange(3 * 4 * 3, dtype=float).reshape(3, 4, 3)

        closed = _close_periodic_curve_axis(surface)

        self.assertEqual(closed.shape, (3, 5, 3))
        np.testing.assert_array_equal(closed[:, :-1], surface)
        np.testing.assert_array_equal(closed[:, -1], surface[:, 0])
        self.assertEqual(surface.shape, (3, 4, 3))

    def test_invalid_surface_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "surface must have shape"):
            _close_periodic_curve_axis(np.zeros((4, 3)))


if __name__ == "__main__":
    unittest.main()
