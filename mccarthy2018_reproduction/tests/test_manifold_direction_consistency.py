"""Tests for branch-sign consistency of bundle-derived manifold seeds."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.invariant_bundles import (
    periodic_interpolation_matrix,
    qr_svd_cocycle_bundle_iteration,
)


def rotation(angle: float) -> np.ndarray:
    return np.array(
        [
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ]
    )


class ManifoldDirectionConsistencyTests(unittest.TestCase):
    def test_unstable_transport_keeps_one_branch_orientation(self) -> None:
        phases = np.linspace(0.0, 2.0 * np.pi, 9, endpoint=False)
        rho = 0.41

        def frame(theta: float) -> np.ndarray:
            value = np.eye(3)
            value[:2, :2] = rotation(theta)
            return value

        cocycle = np.asarray(
            [
                frame(theta + rho)
                @ np.diag([1.8, 0.55, 0.8])
                @ frame(theta).T
                for theta in phases
            ]
        )
        initial = np.asarray([frame(theta)[:, [0]] for theta in phases])
        initial[1::2] *= -1.0

        result = qr_svd_cocycle_bundle_iteration(
            cocycle,
            phases,
            rho,
            bundle_dimension=1,
            initial_bases=initial,
            max_iterations=60,
        )
        shifted = np.einsum(
            "ij,jdk->idk",
            periodic_interpolation_matrix(phases, phases + rho),
            result.bases,
        )
        shifted /= np.linalg.norm(shifted, axis=1, keepdims=True)
        transported = np.einsum("nij,njk->nik", cocycle, result.bases)
        signed_growth = np.einsum(
            "ndk,ndk->n", transported, shifted
        )

        self.assertTrue(result.converged)
        self.assertLess(result.max_invariance_residual, 1.0e-8)
        self.assertTrue(np.all(signed_growth > 0.0))
        np.testing.assert_allclose(signed_growth, 1.8, atol=1.0e-8)


if __name__ == "__main__":
    unittest.main()
