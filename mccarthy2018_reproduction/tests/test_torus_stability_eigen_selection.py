"""Behavior tests for selecting real hyperbolic DG eigenvalues."""

from __future__ import annotations

import unittest

import numpy as np

from qp_orbits.torus_stability import DiscreteCurveDG, real_hyperbolic_eigen_index


def dg_with_eigenvalues(eigenvalues: list[complex]) -> DiscreteCurveDG:
    size = len(eigenvalues)
    return DiscreteCurveDG(
        correction=None,  # type: ignore[arg-type]
        map_jacobian=np.eye(size),
        interpolation_to_base=np.eye(size),
        stms=np.empty((0, 0, 0)),
        eigenvalues=np.asarray(eigenvalues, dtype=complex),
        eigenvectors=np.eye(size, dtype=complex),
    )


class RealHyperbolicEigenSelectionTests(unittest.TestCase):
    def test_rejects_complex_only_unstable_candidates(self) -> None:
        dg = dg_with_eigenvalues(
            [
                -0.833 + 0.666j,
                -0.833 - 0.666j,
                0.5 + 0.0j,
                2.0 / 3.0 + 0.0j,
            ]
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "no nearly real unstable hyperbolic eigenvalue",
        ):
            real_hyperbolic_eigen_index(dg, branch="unstable")

    def test_prefers_nearly_real_unstable_candidate_over_larger_complex_one(self) -> None:
        dg = dg_with_eigenvalues(
            [3.0 + 1.0j, 2.0 + 1.0e-8j, 0.5 + 0.0j]
        )

        index = real_hyperbolic_eigen_index(dg, branch="unstable")

        self.assertEqual(index, 1)

    def test_selects_nearly_real_stable_candidate(self) -> None:
        dg = dg_with_eigenvalues(
            [0.3 + 0.2j, 0.5 + 1.0e-8j, 2.0 + 0.0j]
        )

        index = real_hyperbolic_eigen_index(dg, branch="stable")

        self.assertEqual(index, 1)


if __name__ == "__main__":
    unittest.main()
