"""Tests for sign alignment and phase-order covariance."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.invariant_bundles import (
    align_bundle_phase,
    real_schur_bundle_tracking,
)


def rotation(angle: float) -> np.ndarray:
    return np.array(
        [
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ]
    )


class BundlePhaseAlignmentTests(unittest.TestCase):
    def test_alternating_signs_are_aligned_without_changing_subspaces(self) -> None:
        sample_count = 9
        phases = np.linspace(0.0, 2.0 * np.pi, sample_count, endpoint=False)
        bases = np.zeros((sample_count, 3, 1))
        bases[:, :2, 0] = np.column_stack((np.cos(phases), np.sin(phases)))
        bases[1::2] *= -1.0

        aligned, flips = align_bundle_phase(bases, phases)

        order = np.argsort(phases)
        adjacent = [
            float(
                aligned[order[index], :, 0]
                @ aligned[order[(index + 1) % sample_count], :, 0]
            )
            for index in range(sample_count)
        ]
        self.assertGreater(flips, 0)
        self.assertTrue(all(value > 0.0 for value in adjacent))
        np.testing.assert_allclose(
            np.abs(np.sum(aligned * bases, axis=1)),
            1.0,
            atol=1.0e-12,
        )

    def test_real_schur_result_is_covariant_to_phase_permutation(self) -> None:
        phases = np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False)
        rho = 0.29

        def frame(theta: float) -> np.ndarray:
            value = np.eye(3)
            value[:2, :2] = rotation(theta)
            return value

        cocycle = np.asarray(
            [
                frame(theta + rho)
                @ np.diag([1.8, 0.6, 0.9])
                @ frame(theta).T
                for theta in phases
            ]
        )
        reference = real_schur_bundle_tracking(cocycle, phases, rho)
        permutation = np.asarray([4, 0, 8, 2, 6, 1, 7, 3, 5])
        permuted = real_schur_bundle_tracking(
            cocycle[permutation], phases[permutation], rho
        )
        inverse = np.argsort(permutation)

        overlaps = np.abs(
            np.einsum(
                "nd,nd->n",
                reference.bases[:, :, 0],
                permuted.bases[inverse, :, 0],
            )
        )
        np.testing.assert_allclose(overlaps, 1.0, atol=1.0e-10)
        self.assertLess(permuted.max_invariance_residual, 1.0e-12)


if __name__ == "__main__":
    unittest.main()
