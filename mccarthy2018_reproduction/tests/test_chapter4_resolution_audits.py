"""Regression tests for the Stage B Chapter 4 resolution evidence."""

from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter4_resolution_audits as resolution  # noqa: E402


class Chapter4ResolutionAuditTests(unittest.TestCase):
    def test_phase_alignment_recovers_cyclic_shift_and_global_sign(self) -> None:
        phases = np.linspace(
            0.0,
            2.0 * np.pi,
            resolution.COMMON_PHASE_SAMPLES,
            endpoint=False,
        )
        reference_states = np.zeros((phases.size, 6))
        reference_states[:, 0] = np.cos(phases)
        reference_states[:, 1] = np.sin(phases)
        reference_directions = np.zeros_like(reference_states)
        reference_directions[:, 2] = 1.0
        shift = 17
        candidate_states = np.roll(reference_states, -shift, axis=0)
        candidate_directions = -np.roll(reference_directions, -shift, axis=0)

        aligned = resolution._align_common(
            reference_states,
            reference_directions,
            candidate_states,
            candidate_directions,
        )

        self.assertLess(aligned["state_rms"], 1.0e-14)
        self.assertLess(aligned["angle_max"], 1.0e-6)
        self.assertEqual(aligned["sign"], -1.0)

    def test_symmetric_hd95_is_zero_for_identity_and_positive_for_shift(self) -> None:
        grid = np.stack(
            np.meshgrid(
                np.linspace(0.0, 1.0, 9),
                np.linspace(0.0, 1.0, 7),
                indexing="ij",
            ),
            axis=2,
        )
        surface = np.zeros((9, 7, 3))
        surface[..., :2] = grid
        raw, normalized = resolution._symmetric_hd95(surface, surface.copy())
        self.assertEqual(raw, 0.0)
        self.assertEqual(normalized, 0.0)
        shifted = surface.copy()
        shifted[..., 2] += 0.1
        raw, normalized = resolution._symmetric_hd95(surface, shifted)
        self.assertGreater(raw, 0.09)
        self.assertGreater(normalized, 0.0)

    def test_saved_resolution_rows_preserve_failures_and_holdout(self) -> None:
        paths = {
            "halo": (
                ROOT / "data" / "computed" / "research_halo_12p40_resolution_audit.csv",
                [21, 33, 45],
            ),
            "vertical": (
                ROOT / "data" / "computed" / "research_vertical_12p66_resolution_audit.csv",
                [33, 45, 57],
            ),
        }
        for family, (path, expected_resolutions) in paths.items():
            with self.subTest(family=family), path.open(
                newline="",
                encoding="utf-8",
            ) as stream:
                rows = list(csv.DictReader(stream))
                self.assertEqual(
                    [int(row["spectral_samples"]) for row in rows],
                    expected_resolutions,
                )
                self.assertTrue(
                    all(row["source_selection_red_mask_read"] == "false" for row in rows)
                )
                self.assertTrue(
                    all(row["projection_red_mask_read"] == "true" for row in rows)
                )
                self.assertTrue(
                    all(row["frozen_holdout_status"] == "fail_0_of_4" for row in rows)
                )
                self.assertTrue(
                    all(row["paper_projection_acceptance"] == "fail" for row in rows)
                )
                self.assertTrue(
                    all(row["paper_3d_equivalence"] == "false" for row in rows)
                )
                self.assertTrue(
                    any(row["cross_resolution_gate"] == "fail" for row in rows[1:])
                )

    def test_saved_npz_contains_each_resolution_and_aligned_directions(self) -> None:
        paths = (
            (
                ROOT
                / "data"
                / "computed"
                / "research_halo_12p40_resolution_states.npz",
                (21, 33, 45),
            ),
            (
                ROOT
                / "data"
                / "computed"
                / "research_vertical_12p66_resolution_states.npz",
                (33, 45, 57),
            ),
        )
        for path, resolutions in paths:
            with self.subTest(path=path), np.load(path, allow_pickle=False) as stored:
                for samples in resolutions:
                    prefix = f"n{samples}"
                    self.assertIn(prefix + "_source_states", stored.files)
                    self.assertIn(prefix + "_common_directions_aligned", stored.files)
                    self.assertIn(prefix + "_positive_x_snapshot_states", stored.files)
                    self.assertIn(prefix + "_negative_x_snapshot_states", stored.files)


if __name__ == "__main__":
    unittest.main()
