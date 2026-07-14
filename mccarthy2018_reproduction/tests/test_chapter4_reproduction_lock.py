"""Tests for the bound Chapter 4 reproduction configuration."""

from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import patch
from pathlib import Path

import qp_orbits.chapter4_reproduction_lock as lock_module
from qp_orbits.chapter4_reproduction_lock import load_chapter4_reproduction_lock


ROOT = Path(__file__).resolve().parents[1]


class Chapter4ReproductionLockTests(unittest.TestCase):
    def test_live_camera_drift_is_rejected(self) -> None:
        cameras = dict(lock_module.CHAPTER4_PAPER_CAMERAS)
        cameras["4.3"] = replace(
            cameras["4.3"],
            azimuth_deg=cameras["4.3"].azimuth_deg + 1.0,
        )
        with patch.object(lock_module, "CHAPTER4_PAPER_CAMERAS", cameras):
            with self.assertRaisesRegex(RuntimeError, "camera drifted"):
                load_chapter4_reproduction_lock(ROOT)

    def test_current_lock_preserves_failed_projection_boundary(self) -> None:
        lock = load_chapter4_reproduction_lock(ROOT)
        self.assertEqual(lock.selected_model, "H0_global")
        self.assertEqual(lock.epsilon_by_family["halo"], 4.90728479699366e-7)
        self.assertEqual(lock.epsilon_by_family["halo"], lock.epsilon_by_family["vertical"])
        self.assertEqual(
            lock.camera_config_sha256,
            "7FE3D12CF319A3CBD60B540FFDAD005B5C7B51C8B5F3A2D924B7CFECBC26DFA0",
        )
        self.assertEqual(
            lock.holdout_run_id,
            "B18B82934AE43D3F3F451ACA000BCBA5BD3095AF91AF8F20A57B5133E009C27B",
        )
        self.assertEqual(lock.paper_projection_acceptance, "fail")
        self.assertEqual(lock.paper_projection_status, "paper_projection_holdout_fail")
        self.assertEqual(lock.holdout_passes, 0)
        self.assertFalse(lock.paper_3d_equivalence)


if __name__ == "__main__":
    unittest.main()
