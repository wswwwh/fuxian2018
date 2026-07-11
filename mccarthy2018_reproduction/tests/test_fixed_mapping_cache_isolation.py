"""Tests for isolating fixed-mapping quasi-DRO cache writes."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.quasi_torus import fixed_mapping_dro_cache_path


class FixedMappingCacheIsolationTests(unittest.TestCase):
    def test_cache_directory_can_be_isolated_without_changing_cache_key(self) -> None:
        parameters = {"version": 1, "mu": 0.01215, "target": (2.92249,)}
        default_path = fixed_mapping_dro_cache_path(parameters)
        with tempfile.TemporaryDirectory() as directory:
            isolated_path = fixed_mapping_dro_cache_path(
                parameters,
                cache_directory=Path(directory),
            )

        self.assertEqual(isolated_path.name, default_path.name)
        self.assertNotEqual(isolated_path.parent, default_path.parent)


if __name__ == "__main__":
    unittest.main()
