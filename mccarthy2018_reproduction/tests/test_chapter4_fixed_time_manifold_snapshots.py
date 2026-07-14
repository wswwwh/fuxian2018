"""Regression tests for Chapter 4 fixed-time torus-manifold snapshots."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import integrate_cr3bp
from qp_orbits.torus_stability import (
    CorrectedTorusManifoldSnapshots,
    corrected_torus_snapshot_validation_row,
)
from qp_orbits.variational import integrate_state_and_stm, integrate_states_and_stms


class FixedTimeManifoldSnapshotTests(unittest.TestCase):
    def test_snapshot_surface_is_not_the_history_prefix(self) -> None:
        history_times = np.array([0.0, 1.0, 2.0])
        phase_times = np.array([0.0, 0.5, 1.0])
        history_states = np.zeros((3, 2, 6))
        history_states[:, :, 0] = history_times[:, None]
        snapshot_states = np.zeros((1, 3, 2, 6))
        snapshot_states[0, :, :, 0] = (2.0 + phase_times)[:, None]

        snapshots = CorrectedTorusManifoldSnapshots(
            dg=None,  # type: ignore[arg-type]
            branch="unstable",
            eigenvalue=2.0 + 0.0j,
            perturbation_sign=1.0,
            perturbation_scale=1.0e-7,
            snapshot_times=np.array([2.0]),
            phase_times=phase_times,
            history_times=history_times,
            base_torus_states=np.zeros((3, 2, 6)),
            base_history_states=np.zeros((3, 2, 6)),
            history_states=history_states,
            base_snapshot_states=np.zeros((1, 3, 2, 6)),
            snapshot_states=snapshot_states,
            perturbation_directions=np.ones((2, 6)),
            linear_history_state_separation_norms=np.ones((3, 2)),
            linear_snapshot_state_separation_norms=np.ones((1, 3, 2)),
            linear_history_position_separation_norms=np.ones((3, 2)),
            linear_snapshot_position_separation_norms=np.ones((1, 3, 2)),
        )

        surface = snapshots.surface_at_snapshot(2.0)
        history = snapshots.history_surface_until(2.0)

        self.assertEqual(surface.shape, (3, 2, 3))
        self.assertEqual(history.shape, (3, 2, 3))
        np.testing.assert_allclose(surface[:, 0, 0], [2.0, 2.5, 3.0])
        np.testing.assert_allclose(history[:, 0, 0], [0.0, 1.0, 2.0])
        self.assertFalse(np.array_equal(surface, history))

    def test_unknown_snapshot_time_is_rejected(self) -> None:
        snapshots = CorrectedTorusManifoldSnapshots(
            dg=None,  # type: ignore[arg-type]
            branch="unstable",
            eigenvalue=2.0 + 0.0j,
            perturbation_sign=1.0,
            perturbation_scale=1.0e-7,
            snapshot_times=np.array([2.0]),
            phase_times=np.array([0.0, 1.0]),
            history_times=np.array([0.0, 2.0]),
            base_torus_states=np.zeros((2, 1, 6)),
            base_history_states=np.zeros((2, 1, 6)),
            history_states=np.zeros((2, 1, 6)),
            base_snapshot_states=np.zeros((1, 2, 1, 6)),
            snapshot_states=np.zeros((1, 2, 1, 6)),
            perturbation_directions=np.ones((1, 6)),
            linear_history_state_separation_norms=np.ones((2, 1)),
            linear_snapshot_state_separation_norms=np.ones((1, 2, 1)),
            linear_history_position_separation_norms=np.ones((2, 1)),
            linear_snapshot_position_separation_norms=np.ones((1, 2, 1)),
        )

        with self.assertRaisesRegex(ValueError, "not a stored fixed-time snapshot"):
            snapshots.surface_at_snapshot(1.5)

    def test_validation_uses_stm_reference_and_full_absolute_duration(self) -> None:
        epsilon = 1.0e-6
        dg = SimpleNamespace(
            mapping_time=1.0,
            rotation_angle_rad=0.2,
            correction=SimpleNamespace(final_residual_norms=np.array([1.0e-12])),
        )
        history_states = np.zeros((2, 1, 6))
        history_states[:, 0, 0] = [epsilon, 3.0 * epsilon]
        snapshot_states = np.zeros((1, 2, 1, 6))
        snapshot_states[0, :, 0, 0] = [5.0 * epsilon, 7.0 * epsilon]
        snapshots = CorrectedTorusManifoldSnapshots(
            dg=dg,  # type: ignore[arg-type]
            branch="unstable",
            eigenvalue=1.0e30 + 0.0j,
            perturbation_sign=1.0,
            perturbation_scale=epsilon,
            snapshot_times=np.array([2.0]),
            phase_times=np.array([0.0, 1.0]),
            history_times=np.array([0.0, 2.0]),
            base_torus_states=np.zeros((2, 1, 6)),
            base_history_states=np.zeros((2, 1, 6)),
            history_states=history_states,
            base_snapshot_states=np.zeros((1, 2, 1, 6)),
            snapshot_states=snapshot_states,
            perturbation_directions=np.ones((1, 6)),
            linear_history_state_separation_norms=np.array(
                [[epsilon], [3.0 * epsilon]]
            ),
            linear_snapshot_state_separation_norms=np.array(
                [[[2.0 * epsilon], [4.0 * epsilon]]]
            ),
            linear_history_position_separation_norms=np.array(
                [[epsilon], [3.0 * epsilon]]
            ),
            linear_snapshot_position_separation_norms=np.array(
                [[[2.0 * epsilon], [4.0 * epsilon]]]
            ),
        )
        system = SYSTEMS["earth_moon"]

        row = corrected_torus_snapshot_validation_row(
            snapshots,
            system,
            figure_id="test",
            family="synthetic",
            branch="unstable",
            source_curve="synthetic",
            uses_proxy_background=False,
            validation_status="generated",
            next_action="audit",
        )

        self.assertAlmostEqual(float(row["expected_growth"]), 3.0)
        self.assertAlmostEqual(float(row["growth_ratio"]), 2.125)
        self.assertAlmostEqual(float(row["snapshot_anchor_days"]), 2.0 * system.time_unit_days)
        self.assertAlmostEqual(
            float(row["max_absolute_propagation_days"]),
            3.0 * system.time_unit_days,
        )
        self.assertEqual(row["linear_reference_method"], "base_trajectory_STM_first_order")

    def test_batched_stm_matches_single_path_and_central_difference(self) -> None:
        system = SYSTEMS["earth_moon"]
        initial = np.array([0.85, 0.01, 0.02, 0.0, 0.12, -0.01])
        times = np.array([0.0, 0.01, 0.02])
        single = integrate_state_and_stm(
            initial,
            (0.0, float(times[-1])),
            system.mu,
            t_eval=times,
            rtol=1.0e-12,
            atol=1.0e-14,
            max_step=0.005,
        )
        batched = integrate_states_and_stms(
            initial[None, :],
            (0.0, float(times[-1])),
            system.mu,
            t_eval=times,
            rtol=1.0e-12,
            atol=1.0e-14,
            max_step=0.005,
        )
        self.assertTrue(single.success)
        self.assertTrue(batched.success)
        np.testing.assert_allclose(batched.y, single.y, rtol=2.0e-12, atol=2.0e-14)

        direction = np.array([0.4, -0.1, 0.2, 0.3, 0.5, -0.2])
        direction /= np.linalg.norm(direction)
        epsilon = 1.0e-7
        plus = integrate_cr3bp(
            initial + epsilon * direction,
            (0.0, float(times[-1])),
            system.mu,
            t_eval=times[-1:],
            rtol=1.0e-12,
            atol=1.0e-14,
            max_step=0.005,
        )
        minus = integrate_cr3bp(
            initial - epsilon * direction,
            (0.0, float(times[-1])),
            system.mu,
            t_eval=times[-1:],
            rtol=1.0e-12,
            atol=1.0e-14,
            max_step=0.005,
        )
        finite_difference = (plus.y[:, -1] - minus.y[:, -1]) / (2.0 * epsilon)
        phi = single.y[6:, -1].reshape(6, 6)
        np.testing.assert_allclose(
            finite_difference,
            phi @ direction,
            rtol=2.0e-7,
            atol=2.0e-9,
        )


if __name__ == "__main__":
    unittest.main()
