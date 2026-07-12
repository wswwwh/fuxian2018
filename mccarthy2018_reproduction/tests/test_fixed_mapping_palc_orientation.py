"""Regression tests for fixed-mapping pseudo-arclength orientation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.quasi_torus import _fixed_mapping_pseudo_arclength_geometry


class FixedMappingPalcOrientationTests(unittest.TestCase):
    def test_negative_rotation_secant_is_not_reversed_at_a_fold(self) -> None:
        phases = np.linspace(0.0, 2.0 * np.pi, 5, endpoint=False)
        seed = SimpleNamespace(mu=0.01215, orbit_period=1.25, phases=phases)
        previous_states = np.zeros((5, 6), dtype=float)
        previous_states[:, 2] = np.sin(phases)
        current_states = previous_states.copy()
        current_states[:, 0] += 1.0e-3 * np.cos(phases)
        previous = SimpleNamespace(
            seed=seed,
            corrected_states=previous_states,
            rotation_angle_rad=1.2,
        )
        current = SimpleNamespace(
            seed=seed,
            corrected_states=current_states,
            rotation_angle_rad=1.19,
        )

        _, tangent, _, natural_step = _fixed_mapping_pseudo_arclength_geometry(
            previous,
            current,
        )

        self.assertGreater(natural_step, 0.0)
        self.assertLess(tangent[-1], 0.0)


if __name__ == "__main__":
    unittest.main()
