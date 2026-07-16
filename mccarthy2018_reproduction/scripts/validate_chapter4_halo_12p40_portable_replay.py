"""Validate the frozen Chapter 4 halo diagnostic across supported platforms.

The frozen NPZ was generated in the reference Windows environment.  A strict
byte-level recomputation remains available in the original generator, but a
long DOP853 manifold propagation is not bitwise portable across BLAS/libm
implementations.  This validator keeps the frozen artifacts read-only and
separates three contracts:

* provenance, schemas, masks, decisions, and frozen rows remain exact;
* platform-sensitive trajectories stay inside a same-platform step-refinement
  envelope;
* every scientific residual, Jacobi, source-target, and projection gate keeps
  its original threshold and outcome.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import math
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter4_halo_12p40_posthoc_diagnostic as posthoc  # noqa: E402


STRICT_ATOL = 5.0e-13
REFINEMENT_MAX_STEP = 0.005
REFINEMENT_FACTOR = 4.0

REFINED_ARRAY_KEYS = frozenset(
    {
        "candidate_snapshot_states",
        "candidate_base_torus_states",
        "thesis_12p40_n21_4_3_projected_uv",
        "thesis_12p40_n21_4_4_projected_uv",
    }
)
SPECIAL_ARRAY_KEYS = frozenset(
    {
        "candidate_source_states",
        "candidate_perturbation_directions",
        "candidate_dg_eigenvalues",
    }
)

# These are recomputed diagnostics, not promotion thresholds.  The tolerances
# are much tighter than the scientific gates below and only absorb round-off in
# LAPACK and adaptive integration.  All projection metrics and decisions stay
# exact because their underlying raster masks must be exactly equal.
CANDIDATE_ROW_TOLERANCES: dict[str, tuple[float, float]] = {
    "source_period_days": (0.0, 1.0e-9),
    "source_ay_km": (0.0, 1.0e-2),
    "source_az_km": (0.0, 1.0e-2),
    "source_curve_residual": (0.0, 1.0e-11),
    "dg_determinant_error_from_one": (0.0, 2.5e-10),
    "unstable_eigenvalue_real": (5.0e-10, 1.0e-9),
    "unstable_eigenvalue_relative_imaginary": (0.0, 1.0e-10),
    "source_jacobi_span": (0.0, 1.0e-9),
    "manifold_jacobi_drift_max": (0.0, 1.0e-11),
}


@dataclass(frozen=True)
class RefinementComparison:
    observed_max: np.ndarray
    allowed_max: np.ndarray
    observed_rms: np.ndarray
    allowed_rms: np.ndarray

    @property
    def maximum_ratio(self) -> float:
        ratios = np.r_[
            self.observed_max / self.allowed_max,
            self.observed_rms / self.allowed_rms,
        ]
        return float(np.max(ratios, initial=0.0))


def _component_statistics(delta: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if delta.ndim < 1:
        raise ValueError("refined arrays must have a component axis")
    axes = tuple(range(delta.ndim - 1))
    maximum = np.max(delta, axis=axes)
    rms = np.sqrt(np.mean(np.square(delta), axis=axes))
    return np.asarray(maximum, dtype=float), np.asarray(rms, dtype=float)


def compare_with_refinement_envelope(
    key: str,
    stored: np.ndarray,
    recomputed: np.ndarray,
    refined: np.ndarray,
) -> RefinementComparison:
    """Compare a platform replay against a same-platform convergence envelope."""

    stored = np.asarray(stored)
    recomputed = np.asarray(recomputed)
    refined = np.asarray(refined)
    if stored.shape != recomputed.shape or stored.shape != refined.shape:
        raise RuntimeError(f"Portable replay shape drifted: {key}")
    if stored.dtype.kind not in "fc" or recomputed.dtype.kind not in "fc":
        raise RuntimeError(f"Portable replay requires a numerical array: {key}")
    if not (
        np.all(np.isfinite(stored))
        and np.all(np.isfinite(recomputed))
        and np.all(np.isfinite(refined))
    ):
        raise RuntimeError(f"Portable replay contains non-finite values: {key}")

    observed_max, observed_rms = _component_statistics(
        np.abs(stored - recomputed)
    )
    reference_max, reference_rms = _component_statistics(
        np.abs(recomputed - refined)
    )
    allowed_max = np.maximum(STRICT_ATOL, REFINEMENT_FACTOR * reference_max)
    allowed_rms = np.maximum(STRICT_ATOL, REFINEMENT_FACTOR * reference_rms)
    comparison = RefinementComparison(
        observed_max=observed_max,
        allowed_max=allowed_max,
        observed_rms=observed_rms,
        allowed_rms=allowed_rms,
    )
    if np.any(observed_max > allowed_max) or np.any(observed_rms > allowed_rms):
        raise RuntimeError(
            f"Portable replay exceeds the step-refinement envelope: {key}; "
            f"observed_max={observed_max.tolist()}, "
            f"allowed_max={allowed_max.tolist()}, "
            f"observed_rms={observed_rms.tolist()}, "
            f"allowed_rms={allowed_rms.tolist()}"
        )
    return comparison


def _fine_candidate_arrays(expected: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    system = posthoc.SYSTEMS["earth_moon"]
    lock = posthoc.load_chapter4_reproduction_lock(ROOT)
    family = posthoc.corrected_l1_constant_energy_halo_high_order_dg_family(
        system.mu,
        samples=21,
        members=25,
        member_indices=(0, 4, 8, 12, 16, 20, 24),
        tolerance=3.0e-10,
        max_iterations=64,
    )
    periods_days = np.asarray(
        [dg.mapping_time * system.time_unit_days for dg in family], dtype=float
    )
    selected_index = int(np.argmin(np.abs(periods_days - posthoc.THESIS_PERIOD_DAYS)))
    if selected_index != int(np.asarray(expected["selected_family_index"])[0]):
        raise RuntimeError("Portable replay selected a different source family member")
    dg = family[selected_index]
    snapshot_times = tuple(
        value / system.time_unit_days for value in posthoc.SNAPSHOT_DAYS
    )
    candidates = tuple(
        posthoc.corrected_curve_fixed_time_manifold_snapshots(
            system.mu,
            dg=dg,
            snapshot_times=snapshot_times,
            perturbation_scale=lock.epsilon_by_family["halo"],
            perturbation_sign=sign,
            phase_samples=121,
            history_samples=161,
            max_step=REFINEMENT_MAX_STEP,
        )
        for sign in (-1.0, 1.0)
    )
    minus_x, plus_x = sorted(
        candidates,
        key=lambda item: float(np.mean(item.snapshot_states[-1, :, :, 0])),
    )
    candidate_states = np.stack((plus_x.snapshot_states, minus_x.snapshot_states))
    arrays = {
        "candidate_snapshot_states": candidate_states,
        "candidate_base_torus_states": np.asarray(
            plus_x.base_torus_states, dtype=float
        ),
    }
    with np.load(posthoc.CAMERA_NPZ, allow_pickle=False) as camera:
        for figure_id, (_, branch_index) in posthoc.FIGURES.items():
            stem = figure_id.replace(".", "_")
            projection = np.asarray(
                camera[f"fig_{stem}_projection_matrix"], dtype=float
            )
            placement = np.asarray(
                camera[f"fig_{stem}_placement_matrix"], dtype=float
            )
            arrays[f"thesis_12p40_n21_{stem}_projected_uv"] = (
                posthoc.project_surface_uv(
                    candidate_states[
                        branch_index,
                        posthoc.HOLDOUT_PANEL_INDEX,
                    ],
                    projection,
                    placement,
                )
            )
    return arrays


def _compare_direction(stored: np.ndarray, recomputed: np.ndarray) -> None:
    stored = np.asarray(stored, dtype=float)
    recomputed = np.asarray(recomputed, dtype=float)
    if stored.shape != recomputed.shape:
        raise RuntimeError("Candidate perturbation direction shape drifted")
    if float(np.vdot(stored, recomputed).real) < 0.0:
        recomputed = -recomputed
    if not np.allclose(stored, recomputed, rtol=0.0, atol=5.0e-11):
        raise RuntimeError("Candidate perturbation directions drifted")
    norms = np.linalg.norm(recomputed, axis=1)
    if not np.allclose(norms, 1.0, rtol=0.0, atol=5.0e-12):
        raise RuntimeError("Candidate perturbation directions are not normalized")


def _compare_spectrum(stored: np.ndarray, recomputed: np.ndarray) -> None:
    stored = np.asarray(stored, dtype=complex).reshape(-1)
    recomputed = np.asarray(recomputed, dtype=complex).reshape(-1)
    if stored.shape != recomputed.shape:
        raise RuntimeError("Candidate DG spectrum shape drifted")
    costs = np.abs(stored[:, None] - recomputed[None, :])
    stored_indices, recomputed_indices = linear_sum_assignment(costs)
    errors = costs[stored_indices, recomputed_indices]
    limits = 5.0e-12 + 5.0e-13 * np.abs(stored[stored_indices])
    if np.any(errors > limits):
        index = int(np.argmax(errors / limits))
        raise RuntimeError(
            "Candidate DG spectrum drifted: "
            f"error={float(errors[index]):.17e}, "
            f"limit={float(limits[index]):.17e}"
        )


def _compare_stored_arrays(
    expected: dict[str, np.ndarray],
    refined: dict[str, np.ndarray],
) -> dict[str, RefinementComparison]:
    if not posthoc.NPZ_PATH.is_file():
        raise RuntimeError("Stored post-hoc diagnostic NPZ is missing")
    comparisons: dict[str, RefinementComparison] = {}
    with np.load(posthoc.NPZ_PATH, allow_pickle=False) as stored:
        if set(stored.files) != set(expected):
            raise RuntimeError("Stored post-hoc diagnostic NPZ schema is stale")
        if set(refined) != REFINED_ARRAY_KEYS:
            raise RuntimeError("Portable refinement array schema is incomplete")
        for key, values in expected.items():
            observed = np.asarray(stored[key])
            values = np.asarray(values)
            if observed.shape != values.shape or observed.dtype.kind != values.dtype.kind:
                raise RuntimeError(f"Stored NPZ array metadata is stale: {key}")
            if key in REFINED_ARRAY_KEYS:
                comparisons[key] = compare_with_refinement_envelope(
                    key, observed, values, refined[key]
                )
            elif key == "candidate_source_states":
                if not np.allclose(
                    observed, values, rtol=5.0e-13, atol=5.0e-12
                ):
                    raise RuntimeError("Candidate source states drifted")
            elif key == "candidate_perturbation_directions":
                _compare_direction(observed, values)
            elif key == "candidate_dg_eigenvalues":
                _compare_spectrum(observed, values)
            elif values.dtype.kind in "fc":
                if not np.allclose(observed, values, rtol=0.0, atol=STRICT_ATOL):
                    raise RuntimeError(f"Stored NPZ numerical array is stale: {key}")
            elif not np.array_equal(observed, values):
                raise RuntimeError(f"Stored NPZ array is stale: {key}")
    return comparisons


def _read_stored_rows() -> tuple[list[str], list[dict[str, str]]]:
    with posthoc.CSV_PATH.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _verify_candidate_scientific_gates(rows: list[dict[str, str]]) -> None:
    candidate = [row for row in rows if row["source_variant"] == "thesis_12p40_n21"]
    if len(candidate) != 2:
        raise RuntimeError("Expected two candidate projection rows")
    for row in candidate:
        values = {
            key: float(row[key])
            for key in CANDIDATE_ROW_TOLERANCES
        }
        if not all(math.isfinite(value) for value in values.values()):
            raise RuntimeError("Candidate replay contains non-finite diagnostics")
        if abs(values["source_period_days"] - 12.40) > 0.005:
            raise RuntimeError("Candidate period gate failed")
        if abs(values["source_ay_km"] - 41815.0) > 50.0:
            raise RuntimeError("Candidate Ay gate failed")
        if abs(values["source_az_km"] - 35783.0) > 50.0:
            raise RuntimeError("Candidate Az gate failed")
        if not 0.0 <= values["source_curve_residual"] <= 1.0e-9:
            raise RuntimeError("Candidate curve-residual gate failed")
        if not 0.0 <= values["dg_determinant_error_from_one"] <= 5.0e-9:
            raise RuntimeError("Candidate DG-determinant gate failed")
        if values["unstable_eigenvalue_real"] <= 1.0:
            raise RuntimeError("Candidate unstable-eigenvalue gate failed")
        if not (
            0.0
            <= values["unstable_eigenvalue_relative_imaginary"]
            <= 1.0e-10
        ):
            raise RuntimeError("Candidate eigenvalue-reality gate failed")
        if not 0.0 <= values["source_jacobi_span"] <= 1.0e-6:
            raise RuntimeError("Candidate source-Jacobi gate failed")
        if not 0.0 <= values["manifold_jacobi_drift_max"] <= 1.0e-10:
            raise RuntimeError("Candidate manifold-Jacobi gate failed")


def _compare_stored_rows(recomputed_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    npz_hash = posthoc._sha256(posthoc.NPZ_PATH)
    recomputed = [
        dict(row, evidence_npz_sha256=npz_hash) for row in recomputed_rows
    ]
    fieldnames, stored = _read_stored_rows()
    if not recomputed or fieldnames != list(recomputed[0]):
        raise RuntimeError("Stored post-hoc diagnostic CSV schema is stale")
    if len(stored) != len(recomputed):
        raise RuntimeError("Stored post-hoc diagnostic CSV row count is stale")

    for stored_row, current_row in zip(stored, recomputed, strict=True):
        identity = (current_row["source_variant"], current_row["figure_id"])
        if identity != (stored_row["source_variant"], stored_row["figure_id"]):
            raise RuntimeError("Stored post-hoc diagnostic CSV row order is stale")
        tolerant_fields = (
            CANDIDATE_ROW_TOLERANCES
            if current_row["source_variant"] == "thesis_12p40_n21"
            else {}
        )
        for field in fieldnames:
            if field in tolerant_fields:
                rtol, atol = tolerant_fields[field]
                if not math.isclose(
                    float(stored_row[field]),
                    float(current_row[field]),
                    rel_tol=rtol,
                    abs_tol=atol,
                ):
                    raise RuntimeError(
                        f"Candidate replay diagnostic drifted: {identity} {field}"
                    )
            elif stored_row[field] != current_row[field]:
                raise RuntimeError(
                    f"Stored post-hoc diagnostic CSV drifted: {identity} {field}"
                )

    _verify_candidate_scientific_gates(recomputed)
    if any(row["paper_projection_acceptance"] != "fail" for row in recomputed):
        raise RuntimeError("Portable replay altered the frozen projection decision")
    if any(row["paper_3d_equivalence"] != "false" for row in recomputed):
        raise RuntimeError("Portable replay claimed paper 3D equivalence")
    return stored


def _verify_stored_document(stored_rows: list[dict[str, str]]) -> None:
    npz_hash = posthoc._sha256(posthoc.NPZ_PATH)
    if any(row["evidence_npz_sha256"] != npz_hash for row in stored_rows):
        raise RuntimeError("Stored CSV does not reference the frozen NPZ")
    expected_doc = posthoc._render_doc(stored_rows, npz_hash)
    if not posthoc.DOC_PATH.is_file() or (
        posthoc.DOC_PATH.read_text(encoding="utf-8") != expected_doc
    ):
        raise RuntimeError("Stored post-hoc diagnostic report is stale")


def run_validation() -> dict[str, RefinementComparison]:
    rows, arrays = posthoc.analyze()
    posthoc._verify_rows(rows)
    refined = _fine_candidate_arrays(arrays)
    comparisons = _compare_stored_arrays(arrays, refined)
    stored_rows = _compare_stored_rows(rows)
    _verify_stored_document(stored_rows)
    return comparisons


def main() -> int:
    comparisons = run_validation()
    maximum_ratio = max(
        (comparison.maximum_ratio for comparison in comparisons.values()),
        default=0.0,
    )
    print(
        "chapter4_halo_12p40_portable_replay: PASS "
        f"refined_arrays={len(comparisons)}, "
        f"maximum_envelope_ratio={maximum_ratio:.6g}, "
        "candidate_masks=exact, frozen_holdout=fail, paper_3d=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
