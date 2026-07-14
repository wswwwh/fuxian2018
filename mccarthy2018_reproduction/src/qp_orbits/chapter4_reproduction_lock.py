"""Load and validate the frozen Chapter 4 camera/epsilon reproduction lock."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import string
from typing import Any

import matplotlib
from matplotlib.figure import Figure
import numpy as np

from .chapter4_camera import (
    CHAPTER4_PAPER_CAMERAS,
    apply_chapter4_paper_camera,
)


FIT_SCHEMA = "chapter4_projection_fit_lock_v1"
HOLDOUT_SCHEMA = "chapter4_projection_holdout_audit_v1"
FROZEN_FIT_LOCK_SHA256 = (
    "D2767E61A3EBF428ED8242CA00EDE441FF2C0666189E062397AA928277E43374"
)
FROZEN_HOLDOUT_CSV_SHA256 = (
    "6C5390F938E6E0D882152E59BBDD05BAA4EA04EAC2FA092052DF9AB624688FB1"
)
FROZEN_HOLDOUT_NPZ_SHA256 = (
    "3AF30BCD66C39C68A86AB09E3F453634724E04D643BF2C5A32AC8A9CB7E942A6"
)
FROZEN_HOLDOUT_RUN_ID = (
    "B18B82934AE43D3F3F451ACA000BCBA5BD3095AF91AF8F20A57B5133E009C27B"
)


@dataclass(frozen=True)
class Chapter4ReproductionLock:
    selected_model: str
    epsilon_by_family: dict[str, float]
    fit_lock_sha256: str
    fit_lock_commit: str
    evaluator_commit: str
    holdout_run_id: str
    camera_config_sha256: str
    paper_projection_acceptance: str
    paper_projection_status: str
    paper_3d_equivalence: bool
    holdout_rows: int
    holdout_passes: int
    holdout_csv_sha256: str

    @property
    def epsilon_selection_status(self) -> str:
        return (
            "development_projection_fit_locked_holdout_passed"
            if self.paper_projection_acceptance == "pass"
            else "development_projection_fit_locked_holdout_failed"
        )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _single(rows: list[dict[str, str]], field: str) -> str:
    values = {row[field] for row in rows}
    if len(values) != 1:
        raise RuntimeError(f"Chapter 4 holdout field is not unique: {field}")
    return next(iter(values))


def _require_hex(value: str, length: int, label: str) -> None:
    if len(value) != length or any(character not in string.hexdigits for character in value):
        raise RuntimeError(f"Chapter 4 {label} is malformed")


def _validate_fit_inputs(root: Path, fit: dict[str, Any]) -> None:
    paths = {
        "protocol": root
        / "data"
        / "computed"
        / "chapter4_fig43_fig46_camera_holdout_protocol.csv",
        "camera": root
        / "data"
        / "computed"
        / "chapter4_fig43_fig46_camera_calibration.npz",
        "camera_metrics": root
        / "data"
        / "computed"
        / "chapter4_fig43_fig46_camera_static_metrics.csv",
        "state": root
        / "data"
        / "computed"
        / "chapter4_fig43_fig46_epsilon_state_sensitivity.npz",
        "state_rows": root
        / "data"
        / "computed"
        / "chapter4_fig43_fig46_epsilon_state_sensitivity.csv",
        "generator": root
        / "scripts"
        / "run_chapter4_fig43_fig46_projection_fit.py",
        "projection_core": root / "src" / "qp_orbits" / "chapter4_projection.py",
    }
    expected = fit.get("input_sha256")
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise RuntimeError("Chapter 4 fit lock has an invalid input-hash scope")
    for name, path in paths.items():
        if _sha256(path) != expected[name]:
            raise RuntimeError(f"Chapter 4 fit input drifted: {name}")


def _validate_live_camera(root: Path, fit: dict[str, Any]) -> str:
    data = root / "data" / "computed"
    parameter_path = data / "chapter4_fig43_fig46_camera_parameters.csv"
    evidence_path = data / "chapter4_fig43_fig46_camera_calibration.npz"
    with parameter_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if {row["figure_id"] for row in rows} != set(CHAPTER4_PAPER_CAMERAS):
        raise RuntimeError("Chapter 4 camera parameter rows are incomplete")
    row_by_id = {row["figure_id"]: row for row in rows}
    numeric_fields = {
        "elevation_deg": "elevation_deg",
        "azimuth_deg": "azimuth_deg",
        "roll_deg": "roll_deg",
        "x_min": ("xlim", 0),
        "x_max": ("xlim", 1),
        "y_min": ("ylim", 0),
        "y_max": ("ylim", 1),
        "z_min": ("zlim", 0),
        "z_max": ("zlim", 1),
        "box_aspect_x": ("box_aspect", 0),
        "box_aspect_y": ("box_aspect", 1),
        "box_aspect_z": ("box_aspect", 2),
    }
    for figure_id, camera in CHAPTER4_PAPER_CAMERAS.items():
        row = row_by_id[figure_id]
        if row["projection_type"] != camera.projection_type:
            raise RuntimeError(f"Live Chapter 4 camera drifted: {figure_id} projection")
        for field, attribute in numeric_fields.items():
            if isinstance(attribute, tuple):
                value = getattr(camera, attribute[0])[attribute[1]]
            else:
                value = getattr(camera, attribute)
            if abs(float(row[field]) - float(value)) > 1.0e-12:
                raise RuntimeError(f"Live Chapter 4 camera drifted: {figure_id} {field}")
    camera_hash = str(fit["camera_config_sha256"])
    if {row["camera_config_sha256"] for row in rows} != {camera_hash}:
        raise RuntimeError("Camera parameter rows do not bind the fit camera")
    evidence_hash = _sha256(evidence_path)
    if {row["evidence_npz_sha256"] for row in rows} != {evidence_hash}:
        raise RuntimeError("Camera parameter rows do not bind the camera evidence")
    with np.load(evidence_path, allow_pickle=False) as evidence:
        if str(evidence["camera_config_sha256"][0]) != camera_hash:
            raise RuntimeError("Camera evidence does not bind the fit camera")
        if str(evidence["matplotlib_version"][0]) != matplotlib.__version__:
            raise RuntimeError("Matplotlib version drifted from the camera lock")
        for figure_id in CHAPTER4_PAPER_CAMERAS:
            figure = Figure(figsize=(4.0, 4.0))
            axis = figure.add_subplot(111, projection="3d")
            apply_chapter4_paper_camera(axis, figure_id)
            observed = np.asarray(axis.get_proj(), dtype=float)
            key = f"fig_{figure_id.replace('.', '_')}_projection_matrix"
            if not np.allclose(
                observed,
                np.asarray(evidence[key], dtype=float),
                rtol=0.0,
                atol=1.0e-13,
            ):
                raise RuntimeError(
                    f"Live Chapter 4 projection matrix drifted: {figure_id}"
                )
    return camera_hash


def load_chapter4_reproduction_lock(project_root: Path) -> Chapter4ReproductionLock:
    root = Path(project_root)
    data = root / "data" / "computed"
    fit_lock_path = data / "chapter4_fig43_fig46_projection_fit_lock.json"
    holdout_path = data / "chapter4_fig43_fig46_projection_holdout_audit.csv"
    fit = json.loads(fit_lock_path.read_text(encoding="utf-8"))
    with holdout_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    expected_rows = {
        ("4.3", "d", "halo", "plus_x"),
        ("4.4", "d", "halo", "minus_x"),
        ("4.5", "d", "vertical", "plus_x"),
        ("4.6", "d", "vertical", "minus_x"),
    }
    observed_rows = {
        (row["figure_id"], row["panel_id"], row["family"], row["branch"])
        for row in rows
    }
    if len(rows) != 4 or observed_rows != expected_rows:
        raise RuntimeError("Chapter 4 reproduction lock requires four panel-(d) rows")
    if fit.get("schema_version") != FIT_SCHEMA:
        raise RuntimeError("Chapter 4 fit-lock schema is invalid")
    if {row["schema_version"] for row in rows} != {HOLDOUT_SCHEMA}:
        raise RuntimeError("Chapter 4 holdout schema is invalid")
    _validate_fit_inputs(root, fit)
    camera_hash = _validate_live_camera(root, fit)
    fit_hash = _sha256(fit_lock_path)
    holdout_hash = _sha256(holdout_path)
    holdout_npz_path = data / "chapter4_fig43_fig46_projection_holdout_audit.npz"
    holdout_npz_hash = _sha256(holdout_npz_path)
    if fit_hash != FROZEN_FIT_LOCK_SHA256:
        raise RuntimeError("Chapter 4 fit lock differs from the frozen v1 manifest")
    if holdout_hash != FROZEN_HOLDOUT_CSV_SHA256:
        raise RuntimeError("Chapter 4 holdout CSV differs from the frozen v1 manifest")
    if holdout_npz_hash != FROZEN_HOLDOUT_NPZ_SHA256:
        raise RuntimeError("Chapter 4 holdout NPZ differs from the frozen v1 manifest")
    if {row["fit_lock_sha256"] for row in rows} != {fit_hash}:
        raise RuntimeError("Chapter 4 holdout rows do not bind the current fit lock")
    if _single(rows, "evidence_npz_sha256") != holdout_npz_hash:
        raise RuntimeError("Chapter 4 holdout rows do not bind the evidence NPZ")
    if any(row["paper_3d_equivalence"] != "false" for row in rows):
        raise RuntimeError("Projection evidence cannot claim paper 3D equivalence")
    if fit.get("paper_3d_equivalence") is not False:
        raise RuntimeError("Fit lock cannot claim paper 3D equivalence")
    if fit.get("paper_projection_acceptance") != "not_run":
        raise RuntimeError("Fit lock must predate holdout projection acceptance")
    if fit.get("holdout_red_mask_read") is not False:
        raise RuntimeError("Fit lock read the holdout red mask")
    passes = sum(row["holdout_gate"] == "pass" for row in rows)
    for row in rows:
        gate = row["holdout_gate"]
        if gate not in {"pass", "fail"}:
            raise RuntimeError("Chapter 4 holdout gate is invalid")
        if row["paper_projection_acceptance"] != gate:
            raise RuntimeError("Chapter 4 row acceptance disagrees with its gate")
        if row["paper_projection_status"] != f"paper_projection_holdout_{gate}":
            raise RuntimeError("Chapter 4 row status disagrees with its gate")
        if (gate == "pass") != (row["failure_items"] == "none"):
            raise RuntimeError("Chapter 4 row failures disagree with its gate")
    acceptance = "pass" if passes == len(rows) else "fail"
    status = (
        "paper_projection_holdout_pass"
        if acceptance == "pass"
        else "paper_projection_holdout_fail"
    )
    epsilon_by_family = {
        family: float(value) for family, value in fit["epsilon_by_family"].items()
    }
    if set(epsilon_by_family) != {"halo", "vertical"}:
        raise RuntimeError("Chapter 4 fit lock has an invalid epsilon scope")
    selected_model = str(fit["selected_model"])
    if _single(rows, "selected_model") != selected_model:
        raise RuntimeError("Holdout model does not match the fit lock")
    for row in rows:
        if float(row["selected_epsilon"]) != epsilon_by_family[row["family"]]:
            raise RuntimeError("Holdout epsilon does not match the fit lock")
    if _single(rows, "camera_config_sha256") != camera_hash:
        raise RuntimeError("Holdout camera does not match the fit lock")
    fit_commit = _single(rows, "fit_lock_commit")
    evaluator_commit = _single(rows, "evaluator_commit")
    holdout_run_id = _single(rows, "holdout_run_id")
    _require_hex(fit_commit, 40, "fit-lock commit")
    _require_hex(evaluator_commit, 40, "evaluator commit")
    _require_hex(holdout_run_id, 64, "holdout run ID")
    _require_hex(_single(rows, "generator_sha256"), 64, "evaluator hash")
    _require_hex(_single(rows, "projection_core_sha256"), 64, "projection-core hash")
    if holdout_run_id != FROZEN_HOLDOUT_RUN_ID:
        raise RuntimeError("Chapter 4 holdout run differs from the frozen v1 manifest")
    if _single(rows, "generator_sha256") != _sha256(
        root / "scripts" / "run_chapter4_fig43_fig46_projection_holdout_audit.py"
    ):
        raise RuntimeError("Chapter 4 holdout evaluator drifted")
    if _single(rows, "projection_core_sha256") != _sha256(
        root / "src" / "qp_orbits" / "chapter4_projection.py"
    ):
        raise RuntimeError("Chapter 4 projection core drifted")
    for row in rows:
        if row["paper_source_sha256"] != _sha256(root / row["paper_source"]):
            raise RuntimeError(f"Chapter 4 paper source drifted: {row['figure_id']}")
    return Chapter4ReproductionLock(
        selected_model=selected_model,
        epsilon_by_family=epsilon_by_family,
        fit_lock_sha256=fit_hash,
        fit_lock_commit=fit_commit,
        evaluator_commit=evaluator_commit,
        holdout_run_id=holdout_run_id,
        camera_config_sha256=camera_hash,
        paper_projection_acceptance=acceptance,
        paper_projection_status=status,
        paper_3d_equivalence=False,
        holdout_rows=len(rows),
        holdout_passes=passes,
        holdout_csv_sha256=holdout_hash,
    )
