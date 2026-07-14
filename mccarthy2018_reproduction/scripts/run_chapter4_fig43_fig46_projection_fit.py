"""Fit Chapter 4 epsilon hypotheses on panels (a),(b) and validate on (c).

The camera is already frozen from static fiducials.  This script hard-rejects
panel-(d) red-mask access, selects H0/H1 without per-figure or per-branch
epsilon, writes a lock artifact, and leaves paper projection acceptance
``not_run`` until a later, separately committed holdout audit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.chapter4_projection import (  # noqa: E402
    HoldoutLeakageError,
    load_reference_panel_mask,
    log2_refinement_grid,
    project_surface_uv,
    projection_mask_metrics,
    rasterize_surface_mask,
)
from qp_orbits.cr3bp import integrate_states_cr3bp, jacobi_constant  # noqa: E402


SCHEMA_VERSION = "chapter4_projection_fit_lock_v1"
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
PROTOCOL_PATH = DATA / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
CAMERA_NPZ = DATA / "chapter4_fig43_fig46_camera_calibration.npz"
CAMERA_METRICS = DATA / "chapter4_fig43_fig46_camera_static_metrics.csv"
STATE_NPZ = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.npz"
STATE_CSV = DATA / "chapter4_fig43_fig46_epsilon_state_sensitivity.csv"
METRIC_CSV = DATA / "chapter4_fig43_fig46_projection_fit_metrics.csv"
SELECTION_CSV = DATA / "chapter4_fig43_fig46_epsilon_model_selection.csv"
FIT_NPZ = DATA / "chapter4_fig43_fig46_projection_fit_evidence.npz"
FIT_LOCK = DATA / "chapter4_fig43_fig46_projection_fit_lock.json"
DOC_PATH = DOCS / "chapter4_fig43_fig46_projection_fit.md"

FIGURES = {
    "4.3": ("halo", 0),
    "4.4": ("halo", 1),
    "4.5": ("vertical", 0),
    "4.6": ("vertical", 1),
}
FAMILIES = ("halo", "vertical")
BRANCHES = ("plus_x", "minus_x")
DEVELOPMENT_PANELS = ("a", "b", "c")
TRAIN_PANELS = ("a", "b")
VALIDATION_PANEL = "c"
HOLDOUT_PANEL = "d"
H1_IMPROVEMENT_MIN = 0.10
JACOBI_DRIFT_LIMIT = 1.0e-10
LOCAL_ERROR_LIMIT = 1.0e-3
RTOL = 1.0e-12
ATOL = 1.0e-14
MAX_STEP = 0.01


def _display(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _fmt(value: Any) -> str:
    if isinstance(value, (bool, np.bool_)):
        return str(bool(value)).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not np.isfinite(number):
            return ""
        return f"{number:.15g}"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _key(epsilon: float) -> str:
    return f"{float(epsilon):.15g}"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _protocol() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["figure_id"], row["panel_id"]): row for row in _read_csv(PROTOCOL_PATH)}


def _coarse_validity() -> dict[tuple[str, str], bool]:
    grouped: dict[tuple[str, str], list[bool]] = {}
    for row in _read_csv(STATE_CSV):
        grouped.setdefault((row["family"], _key(float(row["epsilon"]))), []).append(
            row["numerical_acceptance"] == "pass"
        )
    return {key: all(values) for key, values in grouped.items()}


def _camera_inputs() -> tuple[dict[str, np.ndarray], str]:
    values: dict[str, np.ndarray] = {}
    with np.load(CAMERA_NPZ, allow_pickle=False) as evidence:
        camera_hash = str(evidence["camera_config_sha256"][0])
        for figure_id in FIGURES:
            stem = figure_id.replace(".", "_")
            values[f"{figure_id}_projection"] = np.asarray(
                evidence[f"fig_{stem}_projection_matrix"], dtype=float
            )
            values[f"{figure_id}_placement"] = np.asarray(
                evidence[f"fig_{stem}_placement_matrix"], dtype=float
            )
    return values, camera_hash


def _load_coarse_states() -> tuple[
    np.ndarray,
    dict[str, dict[str, np.ndarray]],
    dict[str, dict[str, Any]],
]:
    stores: dict[str, dict[str, np.ndarray]] = {family: {} for family in FAMILIES}
    family_inputs: dict[str, dict[str, Any]] = {}
    with np.load(STATE_NPZ, allow_pickle=False) as evidence:
        epsilon_grid = np.asarray(evidence["epsilon_grid"], dtype=float)
        for family in FAMILIES:
            snapshots = np.asarray(evidence[f"{family}_snapshot_states"], dtype=float)
            for index, epsilon in enumerate(epsilon_grid):
                stores[family][_key(epsilon)] = snapshots[index]
            family_inputs[family] = {
                "source_states": np.asarray(evidence[f"{family}_source_states"], dtype=float),
                "directions": np.asarray(
                    evidence[f"{family}_perturbation_directions"], dtype=float
                ),
                "branch_signs": np.asarray(evidence[f"{family}_branch_signs"], dtype=float),
                "phase_times": np.asarray(evidence[f"{family}_phase_times_nd"], dtype=float),
                "history_times": np.asarray(evidence[f"{family}_history_times_nd"], dtype=float),
                "snapshot_times": np.asarray(evidence[f"{family}_snapshot_times_nd"], dtype=float),
                "evaluation_times": np.asarray(
                    evidence[f"{family}_evaluation_times_nd"], dtype=float
                ),
                "base_history": np.asarray(
                    evidence[f"{family}_base_history_states"], dtype=float
                ),
                "scale_free_linear": np.asarray(
                    evidence[f"{family}_scale_free_linear_history_norms"], dtype=float
                ),
            }
    return epsilon_grid, stores, family_inputs


def _indices_for_times(grid: np.ndarray, requested: np.ndarray) -> np.ndarray:
    indices = np.searchsorted(grid, requested)
    if np.any(indices >= grid.size):
        raise RuntimeError("Fine-grid evaluation time is missing")
    if float(np.max(np.abs(grid[indices] - requested), initial=0.0)) > 1.0e-12:
        raise RuntimeError("Fine-grid evaluation time is missing")
    return indices


def _integrate_fine_candidate(
    family_input: dict[str, Any], epsilon: float, mu: float
) -> tuple[np.ndarray, bool, dict[str, float]]:
    source = family_input["source_states"]
    direction = family_input["directions"]
    times = family_input["evaluation_times"]
    history_indices = _indices_for_times(times, family_input["history_times"])
    snapshot_times = family_input["snapshot_times"]
    phase_times = family_input["phase_times"]
    snapshot_indices = _indices_for_times(
        times,
        np.concatenate([elapsed + phase_times for elapsed in snapshot_times]),
    ).reshape(snapshot_times.size, phase_times.size)
    branch_snapshots = np.empty(
        (len(BRANCHES), snapshot_times.size, phase_times.size, source.shape[0], 6),
        dtype=float,
    )
    max_jacobi = 0.0
    max_local_error = 0.0
    total_nfev = 0
    all_finite = True
    for branch_index, sign in enumerate(family_input["branch_signs"]):
        solution = integrate_states_cr3bp(
            source + float(sign) * float(epsilon) * direction,
            (0.0, float(times[-1])),
            mu,
            t_eval=times,
            rtol=RTOL,
            atol=ATOL,
            max_step=MAX_STEP,
        )
        if not solution.success:
            return branch_snapshots, False, {
                "max_jacobi_drift": float("inf"),
                "max_local_error": float("inf"),
                "nfev": float(solution.nfev),
            }
        evaluated = solution.y.T.reshape(times.size, source.shape[0], 6)
        all_finite = all_finite and bool(np.all(np.isfinite(evaluated)))
        branch_snapshots[branch_index] = evaluated[snapshot_indices]
        jacobi = jacobi_constant(evaluated.reshape(-1, 6), mu).reshape(
            evaluated.shape[:2]
        )
        max_jacobi = max(max_jacobi, float(np.max(np.ptp(jacobi, axis=0))))
        history = evaluated[history_indices]
        measured = np.linalg.norm(history - family_input["base_history"], axis=2)
        expected = float(epsilon) * family_input["scale_free_linear"]
        mask = (family_input["scale_free_linear"] <= 100.0) & (expected > 0.0)
        local = np.abs(measured - expected) / np.maximum(expected, np.finfo(float).tiny)
        if np.any(mask):
            max_local_error = max(max_local_error, float(np.max(local[mask])))
        total_nfev += int(solution.nfev)
    valid = bool(
        all_finite
        and max_jacobi <= JACOBI_DRIFT_LIMIT
        and max_local_error <= LOCAL_ERROR_LIMIT
    )
    return branch_snapshots, valid, {
        "max_jacobi_drift": max_jacobi,
        "max_local_error": max_local_error,
        "nfev": float(total_nfev),
    }


def _evaluate_family_candidates(
    *,
    family: str,
    candidate_keys: list[str],
    stores: dict[str, dict[str, np.ndarray]],
    tags: dict[str, set[str]],
    validity: dict[tuple[str, str], bool],
    references: dict[tuple[str, str], np.ndarray],
    cameras: dict[str, np.ndarray],
    camera_hash: str,
    input_hashes: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    family_figures = [item for item in FIGURES.items() if item[1][0] == family]
    for epsilon_key in candidate_keys:
        epsilon = float(epsilon_key)
        state = stores[family][epsilon_key]
        numerical = validity[(family, epsilon_key)]
        for figure_id, (_, branch_index) in family_figures:
            for panel_index, panel_id in enumerate(DEVELOPMENT_PANELS):
                surface = state[branch_index, panel_index]
                uv = project_surface_uv(
                    surface,
                    cameras[f"{figure_id}_projection"],
                    cameras[f"{figure_id}_placement"],
                )
                prediction = rasterize_surface_mask(uv)
                paper = references[(figure_id, panel_id)]
                metrics = projection_mask_metrics(paper, prediction)
                rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "family": family,
                        "epsilon": epsilon,
                        "candidate_tags": ";".join(sorted(tags[epsilon_key])),
                        "numerical_acceptance": "pass" if numerical else "fail",
                        "figure_id": figure_id,
                        "branch": BRANCHES[branch_index],
                        "panel_id": panel_id,
                        "panel_role": "train" if panel_id in TRAIN_PANELS else "validation",
                        "paper_mask_pixels": int(np.count_nonzero(paper)),
                        "prediction_mask_pixels": int(np.count_nonzero(prediction)),
                        **metrics,
                        "renderer": "orthographic_projected_quad_union_curve_seam_only",
                        "normalized_panel_size": 512,
                        "camera_config_sha256": camera_hash,
                        "protocol_sha256": input_hashes["protocol"],
                        "camera_evidence_sha256": input_hashes["camera"],
                        "state_evidence_sha256": input_hashes["state"],
                        "holdout_red_mask_read": False,
                        "paper_projection_acceptance": "not_run",
                        "paper_3d_equivalence": False,
                    }
                )
    return rows


def _mean_loss(
    rows: list[dict[str, Any]],
    *,
    epsilon: float,
    panels: tuple[str, ...],
    family: str | None = None,
) -> float:
    selected = [
        row
        for row in rows
        if _key(row["epsilon"]) == _key(epsilon)
        and row["panel_id"] in panels
        and (family is None or row["family"] == family)
    ]
    expected = len(panels) * (2 if family is not None else 4)
    if len(selected) != expected:
        raise RuntimeError(
            f"Incomplete loss rows for epsilon={epsilon}, family={family}: "
            f"{len(selected)} != {expected}"
        )
    return float(np.mean([row["projection_loss"] for row in selected]))


def _best(
    rows: list[dict[str, Any]],
    epsilons: list[float],
    *,
    panels: tuple[str, ...],
    family: str | None = None,
) -> tuple[float, float]:
    candidates = [
        (epsilon, _mean_loss(rows, epsilon=epsilon, panels=panels, family=family))
        for epsilon in epsilons
    ]
    return min(candidates, key=lambda item: (item[1], item[0]))


def analyze() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    dict[str, np.ndarray],
    dict[str, Any],
]:
    protocol = _protocol()
    references: dict[tuple[str, str], np.ndarray] = {}
    for figure_id in FIGURES:
        for panel_id in DEVELOPMENT_PANELS:
            references[(figure_id, panel_id)] = load_reference_panel_mask(
                ROOT, protocol[(figure_id, panel_id)]
            )
    cameras, camera_hash = _camera_inputs()
    epsilon_grid, stores, family_inputs = _load_coarse_states()
    validity = _coarse_validity()
    input_hashes = {
        "protocol": _sha256(PROTOCOL_PATH),
        "camera": _sha256(CAMERA_NPZ),
        "camera_metrics": _sha256(CAMERA_METRICS),
        "state": _sha256(STATE_NPZ),
        "state_rows": _sha256(STATE_CSV),
        "generator": _sha256(Path(__file__)),
        "projection_core": _sha256(ROOT / "src" / "qp_orbits" / "chapter4_projection.py"),
    }
    tags: dict[str, dict[str, set[str]]] = {family: {} for family in FAMILIES}
    for family in FAMILIES:
        for epsilon in epsilon_grid:
            tags[family][_key(epsilon)] = {"coarse"}

    coarse_rows_unformatted: list[dict[str, Any]] = []
    for family in FAMILIES:
        coarse_rows_unformatted.extend(
            _evaluate_family_candidates(
                family=family,
                candidate_keys=[_key(value) for value in epsilon_grid],
                stores=stores,
                tags=tags[family],
                validity=validity,
                references=references,
                cameras=cameras,
                camera_hash=camera_hash,
                input_hashes=input_hashes,
            )
        )

    h0_coarse_candidates = [
        float(epsilon)
        for epsilon in epsilon_grid
        if all(validity[(family, _key(epsilon))] for family in FAMILIES)
    ]
    h0_center, h0_coarse_loss = _best(
        coarse_rows_unformatted,
        h0_coarse_candidates,
        panels=TRAIN_PANELS,
    )
    h1_centers: dict[str, float] = {}
    h1_coarse_losses: dict[str, float] = {}
    for family in FAMILIES:
        candidates = [
            float(epsilon)
            for epsilon in epsilon_grid
            if validity[(family, _key(epsilon))]
        ]
        center, loss = _best(
            coarse_rows_unformatted,
            candidates,
            panels=TRAIN_PANELS,
            family=family,
        )
        h1_centers[family] = center
        h1_coarse_losses[family] = loss

    refinement_status = {
        "H0": "not_run_coarse_optimum_at_grid_boundary",
        "H1_halo": "not_run_coarse_optimum_at_grid_boundary",
        "H1_vertical": "not_run_coarse_optimum_at_grid_boundary",
    }
    refine_requests: dict[str, dict[str, set[str]]] = {
        family: {} for family in FAMILIES
    }
    if _key(h0_center) not in {_key(epsilon_grid[0]), _key(epsilon_grid[-1])}:
        refinement_status["H0"] = "five_point_log2_refinement_run"
        for family in FAMILIES:
            for epsilon in log2_refinement_grid(h0_center):
                refine_requests[family].setdefault(_key(epsilon), set()).add("fine_H0")
    for family in FAMILIES:
        center = h1_centers[family]
        label = f"H1_{family}"
        if _key(center) not in {_key(epsilon_grid[0]), _key(epsilon_grid[-1])}:
            refinement_status[label] = "five_point_log2_refinement_run"
            for epsilon in log2_refinement_grid(center):
                refine_requests[family].setdefault(_key(epsilon), set()).add(label)

    mu = 0.012150585609624
    fine_details: dict[tuple[str, str], dict[str, float]] = {}
    for family in FAMILIES:
        for epsilon_key, request_tags in refine_requests[family].items():
            tags[family].setdefault(epsilon_key, set()).update(request_tags)
            if epsilon_key in stores[family]:
                continue
            epsilon = float(epsilon_key)
            snapshots, valid, details = _integrate_fine_candidate(
                family_inputs[family], epsilon, mu
            )
            stores[family][epsilon_key] = snapshots
            validity[(family, epsilon_key)] = valid
            fine_details[(family, epsilon_key)] = details

    fine_rows_unformatted: list[dict[str, Any]] = []
    for family in FAMILIES:
        fine_keys = [key for key in refine_requests[family] if "coarse" not in tags[family][key]]
        if fine_keys:
            fine_rows_unformatted.extend(
                _evaluate_family_candidates(
                    family=family,
                    candidate_keys=sorted(fine_keys, key=float),
                    stores=stores,
                    tags=tags[family],
                    validity=validity,
                    references=references,
                    cameras=cameras,
                    camera_hash=camera_hash,
                    input_hashes=input_hashes,
                )
            )
    rows_unformatted = coarse_rows_unformatted + fine_rows_unformatted

    h0_selected = h0_center
    h0_train_loss = h0_coarse_loss
    if refinement_status["H0"] == "five_point_log2_refinement_run":
        h0_fine = [
            float(key)
            for key, candidate_tags in refine_requests["halo"].items()
            if "fine_H0" in candidate_tags
            and all(validity[(family, key)] for family in FAMILIES)
        ]
        h0_selected, h0_train_loss = _best(
            rows_unformatted, h0_fine, panels=TRAIN_PANELS
        )

    h1_selected = dict(h1_centers)
    h1_train_loss_by_family = dict(h1_coarse_losses)
    for family in FAMILIES:
        label = f"H1_{family}"
        if refinement_status[label] == "five_point_log2_refinement_run":
            candidates = [
                float(key)
                for key, candidate_tags in refine_requests[family].items()
                if label in candidate_tags and validity[(family, key)]
            ]
            h1_selected[family], h1_train_loss_by_family[family] = _best(
                rows_unformatted,
                candidates,
                panels=TRAIN_PANELS,
                family=family,
            )
    h1_train_loss = float(np.mean(list(h1_train_loss_by_family.values())))

    h0_validation_by_family = {
        family: _mean_loss(
            rows_unformatted,
            epsilon=h0_selected,
            panels=(VALIDATION_PANEL,),
            family=family,
        )
        for family in FAMILIES
    }
    h1_validation_by_family = {
        family: _mean_loss(
            rows_unformatted,
            epsilon=h1_selected[family],
            panels=(VALIDATION_PANEL,),
            family=family,
        )
        for family in FAMILIES
    }
    h0_validation = float(np.mean(list(h0_validation_by_family.values())))
    h1_validation = float(np.mean(list(h1_validation_by_family.values())))
    improvement = (h0_validation - h1_validation) / h0_validation
    neither_family_worse = all(
        h1_validation_by_family[family] <= h0_validation_by_family[family]
        for family in FAMILIES
    )
    h1_admissible = bool(improvement >= H1_IMPROVEMENT_MIN and neither_family_worse)
    selected_model = "H1_family" if h1_admissible else "H0_global"
    selected_epsilon = (
        h1_selected
        if h1_admissible
        else {family: h0_selected for family in FAMILIES}
    )

    selection_unformatted = [
        {
            "schema_version": SCHEMA_VERSION,
            "model": "H0_global",
            "halo_epsilon": h0_selected,
            "vertical_epsilon": h0_selected,
            "training_loss": h0_train_loss,
            "validation_loss": h0_validation,
            "halo_validation_loss": h0_validation_by_family["halo"],
            "vertical_validation_loss": h0_validation_by_family["vertical"],
            "relative_validation_improvement_over_H0": 0.0,
            "neither_family_worse_than_H0": True,
            "model_admissible": True,
            "selected_model": selected_model == "H0_global",
            "decision_rule": "baseline_parsimony_model",
            "refinement_status": refinement_status["H0"],
            "holdout_red_mask_read": False,
            "paper_projection_acceptance": "not_run",
            "paper_3d_equivalence": False,
        },
        {
            "schema_version": SCHEMA_VERSION,
            "model": "H1_family",
            "halo_epsilon": h1_selected["halo"],
            "vertical_epsilon": h1_selected["vertical"],
            "training_loss": h1_train_loss,
            "validation_loss": h1_validation,
            "halo_validation_loss": h1_validation_by_family["halo"],
            "vertical_validation_loss": h1_validation_by_family["vertical"],
            "relative_validation_improvement_over_H0": improvement,
            "neither_family_worse_than_H0": neither_family_worse,
            "model_admissible": h1_admissible,
            "selected_model": selected_model == "H1_family",
            "decision_rule": (
                "validation_improvement_ge_0.10_and_neither_family_worse"
            ),
            "refinement_status": (
                f"halo:{refinement_status['H1_halo']};"
                f"vertical:{refinement_status['H1_vertical']}"
            ),
            "holdout_red_mask_read": False,
            "paper_projection_acceptance": "not_run",
            "paper_3d_equivalence": False,
        },
    ]

    paper_hashes = {
        figure_id: protocol[(figure_id, "a")]["paper_source_sha256"]
        for figure_id in FIGURES
    }
    lock = {
        "schema_version": SCHEMA_VERSION,
        "evidence_class": "programmatic_frozen_holdout_with_historical_exposure",
        "historical_exposure": True,
        "development_panels": list(DEVELOPMENT_PANELS),
        "holdout_panel": HOLDOUT_PANEL,
        "holdout_red_mask_read": False,
        "selected_model": selected_model,
        "epsilon_by_family": selected_epsilon,
        "h0_epsilon": h0_selected,
        "h1_epsilon_by_family": h1_selected,
        "h1_relative_validation_improvement": improvement,
        "h1_neither_family_worse": neither_family_worse,
        "h1_admissible": h1_admissible,
        "refinement_status": refinement_status,
        "camera_config_sha256": camera_hash,
        "renderer": "orthographic_projected_quad_union_curve_seam_only",
        "mask_rule": "R>=55;R-max(G,B)>=14;R>=1.10*max(G,B);morphology=none",
        "normalized_panel_size": 512,
        "projection_loss": (
            "chamfer/D+0.5*(1-F1@0.01D)+0.25*abs(log(area_ratio))+0.25*HD95/D"
        ),
        "h1_validation_improvement_min": H1_IMPROVEMENT_MIN,
        "per_panel_transform": "forbidden",
        "input_sha256": input_hashes,
        "paper_source_sha256": paper_hashes,
        "paper_projection_acceptance": "not_run",
        "paper_3d_equivalence": False,
    }

    final_masks_reference: list[np.ndarray] = []
    final_masks_prediction: list[np.ndarray] = []
    panel_keys: list[str] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "camera_config_sha256": np.asarray([camera_hash]),
        "selected_model": np.asarray([selected_model]),
        "selected_halo_epsilon": np.asarray([selected_epsilon["halo"]]),
        "selected_vertical_epsilon": np.asarray([selected_epsilon["vertical"]]),
    }
    for family in FAMILIES:
        arrays[f"selected_{family}_snapshot_states"] = stores[family][
            _key(selected_epsilon[family])
        ]
    for figure_id, (family, branch_index) in FIGURES.items():
        epsilon = selected_epsilon[family]
        states = stores[family][_key(epsilon)]
        for panel_index, panel_id in enumerate(DEVELOPMENT_PANELS):
            reference = references[(figure_id, panel_id)]
            prediction = rasterize_surface_mask(
                project_surface_uv(
                    states[branch_index, panel_index],
                    cameras[f"{figure_id}_projection"],
                    cameras[f"{figure_id}_placement"],
                )
            )
            final_masks_reference.append(reference)
            final_masks_prediction.append(prediction)
            panel_keys.append(f"{figure_id}{panel_id}")
    arrays["development_panel_keys"] = np.asarray(panel_keys)
    arrays["development_reference_masks"] = np.asarray(final_masks_reference, dtype=bool)
    arrays["development_prediction_masks"] = np.asarray(final_masks_prediction, dtype=bool)

    for row in rows_unformatted:
        row["selected_for_final_model"] = bool(
            _key(row["epsilon"]) == _key(selected_epsilon[row["family"]])
        )
        row["selected_model"] = selected_model
    metric_rows = [{key: _fmt(value) for key, value in row.items()} for row in rows_unformatted]
    selection_rows = [
        {key: _fmt(value) for key, value in row.items()}
        for row in selection_unformatted
    ]
    return metric_rows, selection_rows, arrays, lock


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _lock_bytes(lock: dict[str, Any]) -> bytes:
    return (
        json.dumps(lock, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _render_doc(
    metrics: list[dict[str, str]],
    selection: list[dict[str, str]],
    lock: dict[str, Any],
    lock_hash: str,
    npz_hash: str,
) -> str:
    selected_metrics = [row for row in metrics if row["selected_for_final_model"] == "true"]
    lines = [
        "# Chapter 4 Figures 4.3-4.6 projection fit lock",
        "",
        "Generated by `scripts/run_chapter4_fig43_fig46_projection_fit.py`.",
        "",
        "## Leakage boundary",
        "",
        "- Panels (a),(b) train epsilon; panel (c) selects H0 versus H1.",
        "- The loader hard-rejects panel-(d) red pixels. No panel-(d) metric exists",
        "  in these artifacts, and `holdout_red_mask_read=false` is locked.",
        "- Camera parameters and per-figure placement are frozen from static anchors;",
        "  no panel-specific image transform is permitted.",
        "- Paper projection acceptance remains `not_run`; paper 3D equivalence remains",
        "  `false` until the separately committed holdout evaluator runs.",
        "",
        "## Model selection",
        "",
        "| Model | Halo epsilon | Vertical epsilon | Train loss | Validation loss | Improvement vs H0 | Admissible | Selected |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in selection:
        lines.append(
            f"| {row['model']} | {float(row['halo_epsilon']):.6e} | "
            f"{float(row['vertical_epsilon']):.6e} | "
            f"{float(row['training_loss']):.4f} | "
            f"{float(row['validation_loss']):.4f} | "
            f"{float(row['relative_validation_improvement_over_H0']):.3f} | "
            f"{row['model_admissible']} | {row['selected_model']} |"
        )
    lines.extend(
        [
            "",
            f"Selected model: `{lock['selected_model']}` with epsilon map "
            f"`{lock['epsilon_by_family']}`.",
            "",
            "## Selected development-panel metrics",
            "",
            "| Figure | Panel | Role | Epsilon | Chamfer/D | F1 | HD95/D | Area ratio | Loss |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in selected_metrics:
        lines.append(
            f"| {row['figure_id']} | ({row['panel_id']}) | {row['panel_role']} | "
            f"{float(row['epsilon']):.6e} | "
            f"{float(row['symmetric_chamfer_diagonal_fraction']):.4f} | "
            f"{float(row['f1_at_0p01_diagonal']):.3f} | "
            f"{float(row['hd95_diagonal_fraction']):.4f} | "
            f"{float(row['area_ratio_prediction_over_paper']):.3f} | "
            f"{float(row['projection_loss']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Traceability",
            "",
            f"- Fit lock: `{_display(FIT_LOCK)}` (SHA256 `{lock_hash}`).",
            f"- Metrics: `{_display(METRIC_CSV)}`.",
            f"- Model selection: `{_display(SELECTION_CSV)}`.",
            f"- Evidence arrays: `{_display(FIT_NPZ)}` (SHA256 `{npz_hash}`).",
            f"- Camera config SHA256: `{lock['camera_config_sha256']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def _verify(metrics: list[dict[str, str]], selection: list[dict[str, str]], lock: dict[str, Any]) -> None:
    if any(row["panel_id"] == HOLDOUT_PANEL for row in metrics):
        raise HoldoutLeakageError("Panel (d) escaped into projection fit metrics")
    if not all(row["holdout_red_mask_read"] == "false" for row in metrics + selection):
        raise HoldoutLeakageError("Projection fit claims holdout access")
    if lock["holdout_red_mask_read"] is not False:
        raise HoldoutLeakageError("Fit lock claims holdout access")
    if lock["selected_model"] not in {"H0_global", "H1_family"}:
        raise RuntimeError("No epsilon model was selected")
    if sum(row["selected_model"] == "true" for row in selection) != 1:
        raise RuntimeError("Expected exactly one selected epsilon model")


def _compare_arrays(expected: dict[str, np.ndarray]) -> None:
    with np.load(FIT_NPZ, allow_pickle=False) as stored:
        if set(stored.files) != set(expected):
            raise RuntimeError("Stored projection fit NPZ schema is stale")
        for key, values in expected.items():
            observed = np.asarray(stored[key])
            values = np.asarray(values)
            if observed.shape != values.shape:
                raise RuntimeError(f"Stored projection fit array shape is stale: {key}")
            if values.dtype.kind in "fc":
                if not np.allclose(observed, values, rtol=0.0, atol=5.0e-13):
                    raise RuntimeError(f"Stored projection fit array is stale: {key}")
            elif not np.array_equal(observed, values):
                raise RuntimeError(f"Stored projection fit array is stale: {key}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metrics, selection, arrays, lock = analyze()
    _verify(metrics, selection, lock)
    lock_payload = _lock_bytes(lock)
    lock_hash = _sha256_bytes(lock_payload)
    arrays["fit_lock_sha256"] = np.asarray([lock_hash])
    if args.check:
        if not FIT_LOCK.is_file() or FIT_LOCK.read_bytes() != lock_payload:
            raise RuntimeError("Stored projection fit lock is stale")
        _compare_arrays(arrays)
        npz_hash = _sha256(FIT_NPZ)
        enriched_metrics = [
            dict(row, fit_lock_sha256=lock_hash, evidence_npz_sha256=npz_hash)
            for row in metrics
        ]
        enriched_selection = [
            dict(row, fit_lock_sha256=lock_hash, evidence_npz_sha256=npz_hash)
            for row in selection
        ]
        if not METRIC_CSV.is_file() or METRIC_CSV.read_bytes() != _csv_bytes(enriched_metrics):
            raise RuntimeError("Stored projection fit metrics are stale")
        if not SELECTION_CSV.is_file() or SELECTION_CSV.read_bytes() != _csv_bytes(enriched_selection):
            raise RuntimeError("Stored epsilon model selection is stale")
        expected_doc = _render_doc(
            enriched_metrics, enriched_selection, lock, lock_hash, npz_hash
        )
        if not DOC_PATH.is_file() or DOC_PATH.read_text(encoding="utf-8") != expected_doc:
            raise RuntimeError("Stored projection fit report is stale")
        print(
            "chapter4_projection_fit_check: "
            f"selected_model={lock['selected_model']}, holdout_red_mask_read=false, "
            "paper_projection_acceptance=not_run"
        )
        return 0

    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    FIT_LOCK.write_bytes(lock_payload)
    np.savez_compressed(FIT_NPZ, **arrays)
    npz_hash = _sha256(FIT_NPZ)
    enriched_metrics = [
        dict(row, fit_lock_sha256=lock_hash, evidence_npz_sha256=npz_hash)
        for row in metrics
    ]
    enriched_selection = [
        dict(row, fit_lock_sha256=lock_hash, evidence_npz_sha256=npz_hash)
        for row in selection
    ]
    METRIC_CSV.write_bytes(_csv_bytes(enriched_metrics))
    SELECTION_CSV.write_bytes(_csv_bytes(enriched_selection))
    DOC_PATH.write_text(
        _render_doc(enriched_metrics, enriched_selection, lock, lock_hash, npz_hash),
        encoding="utf-8",
    )
    for path in (FIT_LOCK, FIT_NPZ, METRIC_CSV, SELECTION_CSV, DOC_PATH):
        print(f"wrote {_display(path)}")
    print(
        "chapter4_projection_fit: "
        f"selected_model={lock['selected_model']}, holdout_red_mask_read=false, "
        "paper_projection_acceptance=not_run"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
