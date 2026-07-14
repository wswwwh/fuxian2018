"""Artifact gates for the Chapter 4 state-only epsilon sensitivity sweep."""

from __future__ import annotations

import csv
import hashlib
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"


class Chapter4EpsilonStateSensitivityTests(unittest.TestCase):
    def test_live_container_drift_preserves_frozen_semantic_inputs(self) -> None:
        state_path = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.npz"
        configurations = {
            "halo": DATA / "chapter4_fig43_fig44_global_manifold_audit.npz",
            "vertical": DATA / "chapter4_fig45_fig48_vertical_manifold_audit.npz",
        }
        with np.load(state_path, allow_pickle=False) as frozen:
            for family, live_path in configurations.items():
                digest = hashlib.sha256(live_path.read_bytes()).hexdigest().upper()
                self.assertNotEqual(
                    digest,
                    str(frozen[f"{family}_source_npz_sha256"][0]),
                )
                with np.load(live_path, allow_pickle=False) as live:
                    self.assertTrue(
                        np.array_equal(
                            frozen[f"{family}_source_states"],
                            live["plus_x_source_states"],
                        )
                    )
                    self.assertTrue(
                        np.array_equal(
                            frozen[f"{family}_perturbation_directions"],
                            live["plus_x_perturbation_directions"],
                        )
                    )

    def test_state_sweep_preserves_projection_and_3d_boundaries(self) -> None:
        path = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 112)
        self.assertTrue(all(row["integration_success"] == "true" for row in rows))
        self.assertTrue(
            all(row["projection_metrics_status"] == "not_run_no_thesis_mask_read" for row in rows)
        )
        self.assertTrue(all(row["paper_projection_acceptance"] == "not_run" for row in rows))
        self.assertTrue(all(row["paper_3d_equivalence"] == "false" for row in rows))

    def test_sweep_is_shared_across_signs_and_records_body_radius_boundary(self) -> None:
        path = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len({float(row["epsilon"]) for row in rows}), 7)
        for family in ("halo", "vertical"):
            family_rows = [row for row in rows if row["family"] == family]
            self.assertEqual({row["branch"] for row in family_rows}, {"plus_x", "minus_x"})
            for epsilon in {row["epsilon"] for row in family_rows}:
                selected = [row for row in family_rows if row["epsilon"] == epsilon]
                self.assertEqual({row["branch"] for row in selected}, {"plus_x", "minus_x"})
        self.assertTrue(any(row["moon_body_intersection"] == "true" for row in rows))
        self.assertTrue(all(float(row["moon_radius_km"]) == 1737.4 for row in rows))

        with np.load(
            DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.npz",
            allow_pickle=False,
        ) as evidence:
            self.assertEqual(evidence["halo_snapshot_states"].shape, (7, 2, 4, 121, 9, 6))
            self.assertEqual(
                evidence["vertical_snapshot_states"].shape,
                (7, 2, 4, 121, 33, 6),
            )
            self.assertEqual(evidence["branch_names"].tolist(), ["plus_x", "minus_x"])


if __name__ == "__main__":
    unittest.main()
