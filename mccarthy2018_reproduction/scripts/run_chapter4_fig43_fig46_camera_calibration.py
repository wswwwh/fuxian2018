"""Lock the Chapter 4 thesis cameras from static PDF-native fiducials.

Only measured axis corners and visible Moon/L1/L2 marker centers are used.
No red manifold mask is opened.  Panels (a),(b) fit one placement matrix per
figure; panels (c),(d) are static-fiducial validation/audit rows and never
receive panel-specific transforms.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mpl_toolkits.mplot3d import proj3d  # noqa: E402
import numpy as np  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.chapter4_camera import (  # noqa: E402
    CHAPTER4_PAPER_CAMERAS,
    apply_chapter4_paper_camera,
    chapter4_axis_corner_positions,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.libration_points import compute_libration_points  # noqa: E402


SCHEMA_VERSION = "chapter4_static_camera_calibration_v1"
DATA = ROOT / "data" / "computed"
DIGITIZED = ROOT / "data" / "digitized"
DOCS = ROOT / "docs"
PROTOCOL_PATH = DATA / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
ANCHOR_CSV = DIGITIZED / "chapter4_fig43_fig46_camera_anchors.csv"
PARAMETER_CSV = DATA / "chapter4_fig43_fig46_camera_parameters.csv"
METRIC_CSV = DATA / "chapter4_fig43_fig46_camera_static_metrics.csv"
NPZ_PATH = DATA / "chapter4_fig43_fig46_camera_calibration.npz"
DOC_PATH = DOCS / "chapter4_fig43_fig46_camera_calibration.md"

NORMALIZED_SIZE = 512.0
ANCHOR_RMSE_MAX_PX = 4.0
ANCHOR_MAX_ERROR_MAX_PX = 8.0
PANEL_ROLES = {
    "a": "train",
    "b": "train",
    "c": "validation",
    "d": "programmatic_frozen_holdout",
}

# Full-reference-image pixel coordinates measured from the native embedded
# panel rasters.  Figure 4.3 bottom panels are assigned by the visible (c)/(d)
# labels, correcting the PDF xref's reversed bottom-row ordering.
AXIS_PIXELS: dict[str, dict[str, tuple[tuple[float, float], ...]]] = {
    "4.3": {
        "a": ((85.32, 214.41), (261.24, 316.03), (399.33, 236.99), (85.32, 106.32)),
        "b": ((506.39, 213.26), (685.18, 316.29), (821.25, 238.32), (506.39, 106.37)),
        "c": ((83.33, 599.67), (259.04, 701.32), (395.48, 622.55), (83.33, 489.74)),
        "d": ((501.00, 597.43), (678.13, 699.73), (814.23, 621.56), (501.00, 490.78)),
    },
    "4.4": {
        "a": ((78.99, 159.50), (287.80, 280.42), (419.36, 204.65), (78.99, 95.91)),
        "b": ((520.11, 160.62), (726.39, 280.30), (854.45, 206.54), (520.11, 96.07)),
        "c": ((77.85, 507.53), (281.74, 627.00), (411.29, 552.30), (77.85, 444.24)),
        "d": ((510.09, 508.52), (716.34, 628.17), (846.08, 553.48), (510.09, 444.34)),
    },
    "4.5": {
        "a": ((90.63, 244.15), (306.22, 302.13), (385.09, 204.94), (90.63, 140.18)),
        "b": ((524.87, 244.15), (740.46, 302.13), (819.33, 204.94), (524.87, 140.21)),
        "c": ((86.73, 621.23), (302.32, 679.21), (381.19, 582.01), (86.73, 517.22)),
        "d": ((520.96, 621.23), (736.56, 679.21), (815.42, 582.01), (520.96, 517.23)),
    },
    "4.6": {
        "a": ((78.41, 193.25), (335.68, 246.91), (392.12, 157.21), (78.41, 119.30)),
        "b": ((515.73, 194.36), (771.83, 248.07), (828.49, 157.97), (515.73, 120.68)),
        "c": ((75.88, 513.37), (330.73, 566.61), (386.74, 477.47), (75.88, 439.97)),
        "d": ((509.91, 513.64), (766.08, 567.46), (822.65, 477.33), (509.91, 440.33)),
    },
}

MARKER_PIXELS: dict[str, dict[str, dict[str, tuple[float, float]]]] = {
    "4.3": {
        "a": {"L1": (171.98, 131.31), "L2": (319.71, 215.83), "Moon": (241.67, 171.18)},
        "b": {"L2": (744.96, 214.69), "Moon": (665.57, 169.38)},
        "c": {"L2": (317.41, 601.24)},
        "d": {"L2": (736.78, 599.13)},
    },
    "4.4": {
        "a": {"L1": (284.78, 202.51), "Moon": (324.18, 225.30)},
        "b": {"L1": (723.54, 203.82), "Moon": (762.35, 225.89)},
        "c": {"L1": (279.69, 550.24), "Moon": (318.26, 572.36)},
        "d": {"L1": (713.48, 551.40), "Moon": (752.32, 573.63)},
    },
    "4.5": {
        "a": {"L2": (332.41, 198.06), "Moon": (236.93, 172.59)},
        "b": {"L2": (766.64, 198.06)},
        "c": {"L2": (328.51, 575.14), "Moon": (233.03, 549.66)},
        "d": {"L2": (762.74, 575.14), "Moon": (667.27, 549.66)},
    },
    "4.6": {
        "a": {"Moon": (123.16, 91.25)},
        "b": {"Moon": (560.32, 92.93)},
        "c": {"Moon": (120.02, 412.25)},
        "d": {"Moon": (554.52, 412.14)},
    },
}


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


def _protocol() -> dict[tuple[str, str], dict[str, str]]:
    with PROTOCOL_PATH.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return {(row["figure_id"], row["panel_id"]): row for row in rows}


def _marker_positions() -> dict[str, np.ndarray]:
    system = SYSTEMS["earth_moon"]
    points = compute_libration_points(system.mu)
    return {
        "Moon": np.asarray((1.0 - system.mu, 0.0, 0.0), dtype=float),
        "L1": np.asarray((points["L1"].x, 0.0, 0.0), dtype=float),
        "L2": np.asarray((points["L2"].x, 0.0, 0.0), dtype=float),
    }


def _projection(figure_id: str) -> tuple[np.ndarray, np.ndarray]:
    figure = plt.figure(figsize=(4.0, 4.0))
    axis = figure.add_subplot(111, projection="3d")
    apply_chapter4_paper_camera(axis, figure_id)
    matrix = np.asarray(axis.get_proj(), dtype=float)
    corners = chapter4_axis_corner_positions(figure_id)
    x, y, _ = proj3d.proj_transform(
        corners[:, 0], corners[:, 1], corners[:, 2], matrix
    )
    plt.close(figure)
    return matrix, np.column_stack((x, y))


def _project_xyz(matrix: np.ndarray, xyz: np.ndarray) -> np.ndarray:
    values = np.asarray(xyz, dtype=float)
    x, y, _ = proj3d.proj_transform(
        values[..., 0], values[..., 1], values[..., 2], matrix
    )
    return np.column_stack((np.ravel(x), np.ravel(y)))


def _normalize_pixel(
    pixel: tuple[float, float], protocol_row: dict[str, str]
) -> np.ndarray:
    x0 = float(protocol_row["panel_rect_x0"])
    y0 = float(protocol_row["panel_rect_y0"])
    x1 = float(protocol_row["panel_rect_x1"])
    y1 = float(protocol_row["panel_rect_y1"])
    return np.asarray(((pixel[0] - x0) / (x1 - x0), (pixel[1] - y0) / (y1 - y0)))


def _raw_anchor_digest() -> str:
    payload = {
        "axis_pixels": AXIS_PIXELS,
        "marker_pixels": MARKER_PIXELS,
        "cameras": {key: asdict(value) for key, value in CHAPTER4_PAPER_CAMERAS.items()},
        "protocol_sha256": _sha256(PROTOCOL_PATH),
    }
    return _sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def analyze() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    dict[str, np.ndarray],
    str,
]:
    protocol = _protocol()
    marker_xyz = _marker_positions()
    raw_digest = _raw_anchor_digest()
    protocol_hash = _sha256(PROTOCOL_PATH)
    anchor_rows_unformatted: list[dict[str, Any]] = []
    parameter_rows_unformatted: list[dict[str, Any]] = []
    metric_rows_unformatted: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "figure_ids": np.asarray(tuple(CHAPTER4_PAPER_CAMERAS)),
        "protocol_sha256": np.asarray([protocol_hash]),
        "raw_anchor_digest": np.asarray([raw_digest]),
        "matplotlib_version": np.asarray([matplotlib.__version__]),
    }
    camera_hash_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "raw_anchor_digest": raw_digest,
        "matplotlib_version": matplotlib.__version__,
        "figures": {},
    }

    for figure_id, camera in CHAPTER4_PAPER_CAMERAS.items():
        projection_matrix, projected_corners = _projection(figure_id)
        design_rows: list[np.ndarray] = []
        observed_rows: list[np.ndarray] = []
        for panel_id in ("a", "b"):
            row = protocol[(figure_id, panel_id)]
            observed = np.vstack(
                [_normalize_pixel(pixel, row) for pixel in AXIS_PIXELS[figure_id][panel_id]]
            )
            design_rows.append(
                np.column_stack((projected_corners, np.ones(projected_corners.shape[0])))
            )
            observed_rows.append(observed)
        placement = np.linalg.lstsq(
            np.vstack(design_rows), np.vstack(observed_rows), rcond=None
        )[0]
        arrays[f"fig_{figure_id.replace('.', '_')}_projection_matrix"] = projection_matrix
        arrays[f"fig_{figure_id.replace('.', '_')}_placement_matrix"] = placement
        camera_hash_payload["figures"][figure_id] = {
            "camera": asdict(camera),
            "placement_matrix": placement.tolist(),
        }

        all_anchors: dict[str, list[dict[str, Any]]] = {}
        for panel_id in ("a", "b", "c", "d"):
            protocol_row = protocol[(figure_id, panel_id)]
            paper_source = ROOT / protocol_row["paper_source"]
            panel: list[dict[str, Any]] = []
            corner_xyz = chapter4_axis_corner_positions(figure_id)
            corner_ndc = projected_corners
            for corner_index, corner_name in enumerate(("A", "B", "C", "D")):
                pixel = AXIS_PIXELS[figure_id][panel_id][corner_index]
                observed = _normalize_pixel(pixel, protocol_row)
                predicted = np.r_[corner_ndc[corner_index], 1.0] @ placement
                error = float(np.linalg.norm((predicted - observed) * NORMALIZED_SIZE))
                uncertainty = 1.5 if corner_name == "C" else 0.5
                panel.append(
                    {
                        "anchor_id": f"{figure_id}_{panel_id}_axis_{corner_name}",
                        "anchor_type": "axis_corner",
                        "anchor_name": corner_name,
                        "xyz": corner_xyz[corner_index],
                        "pixel": pixel,
                        "observed": observed,
                        "predicted": predicted,
                        "error": error,
                        "measurement_uncertainty_reference_px": uncertainty,
                        "used_for_fit": panel_id in {"a", "b"},
                        "visibility": "visible",
                    }
                )
            for marker_name, pixel in MARKER_PIXELS[figure_id][panel_id].items():
                xyz = marker_xyz[marker_name]
                ndc = _project_xyz(projection_matrix, xyz[None, :])[0]
                observed = _normalize_pixel(pixel, protocol_row)
                predicted = np.r_[ndc, 1.0] @ placement
                error = float(np.linalg.norm((predicted - observed) * NORMALIZED_SIZE))
                panel.append(
                    {
                        "anchor_id": f"{figure_id}_{panel_id}_{marker_name}",
                        "anchor_type": "physical_marker",
                        "anchor_name": marker_name,
                        "xyz": xyz,
                        "pixel": pixel,
                        "observed": observed,
                        "predicted": predicted,
                        "error": error,
                        "measurement_uncertainty_reference_px": 0.5,
                        "used_for_fit": False,
                        "visibility": "visible_unoccluded",
                    }
                )
            all_anchors[panel_id] = panel
            errors = np.asarray([item["error"] for item in panel])
            rmse = float(np.sqrt(np.mean(errors**2)))
            maximum = float(np.max(errors))
            gate = bool(rmse <= ANCHOR_RMSE_MAX_PX and maximum <= ANCHOR_MAX_ERROR_MAX_PX)
            metric_rows_unformatted.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "figure_id": figure_id,
                    "panel_id": panel_id,
                    "panel_role": PANEL_ROLES[panel_id],
                    "anchor_count": len(panel),
                    "axis_anchor_count": sum(item["anchor_type"] == "axis_corner" for item in panel),
                    "marker_anchor_count": sum(item["anchor_type"] == "physical_marker" for item in panel),
                    "anchor_rmse_px_on_512_grid": rmse,
                    "anchor_max_error_px_on_512_grid": maximum,
                    "anchor_rmse_limit_px": ANCHOR_RMSE_MAX_PX,
                    "anchor_max_error_limit_px": ANCHOR_MAX_ERROR_MAX_PX,
                    "static_camera_gate": "pass" if gate else "fail",
                    "red_mask_read": False,
                    "paper_projection_acceptance": "not_run",
                    "paper_3d_equivalence": False,
                    "paper_source": protocol_row["paper_source"],
                    "paper_source_sha256": protocol_row["paper_source_sha256"],
                    "protocol_sha256": protocol_hash,
                    "raw_anchor_digest": raw_digest,
                }
            )
            for item in panel:
                x0 = float(protocol_row["panel_rect_x0"])
                y0 = float(protocol_row["panel_rect_y0"])
                x1 = float(protocol_row["panel_rect_x1"])
                y1 = float(protocol_row["panel_rect_y1"])
                uncertainty = item["measurement_uncertainty_reference_px"]
                anchor_rows_unformatted.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "anchor_id": item["anchor_id"],
                        "figure_id": figure_id,
                        "panel_id": panel_id,
                        "panel_role": PANEL_ROLES[panel_id],
                        "anchor_type": item["anchor_type"],
                        "anchor_name": item["anchor_name"],
                        "x_nd": item["xyz"][0],
                        "y_nd": item["xyz"][1],
                        "z_nd": item["xyz"][2],
                        "observed_full_x_px": item["pixel"][0],
                        "observed_full_y_px": item["pixel"][1],
                        "panel_rect_x0": x0,
                        "panel_rect_y0": y0,
                        "panel_rect_x1": x1,
                        "panel_rect_y1": y1,
                        "observed_normalized_u": item["observed"][0],
                        "observed_normalized_v": item["observed"][1],
                        "predicted_normalized_u": item["predicted"][0],
                        "predicted_normalized_v": item["predicted"][1],
                        "error_px_on_512_grid": item["error"],
                        "measurement_uncertainty_reference_px": uncertainty,
                        "measurement_uncertainty_u_on_512_grid": uncertainty * NORMALIZED_SIZE / (x1 - x0),
                        "measurement_uncertainty_v_on_512_grid": uncertainty * NORMALIZED_SIZE / (y1 - y0),
                        "used_for_fit": item["used_for_fit"],
                        "visibility": item["visibility"],
                        "measurement_method": "manual_pdf_native_raster_axis_marker_center",
                        "paper_source": _display(paper_source),
                        "paper_source_sha256": protocol_row["paper_source_sha256"],
                        "protocol_sha256": protocol_hash,
                        "raw_anchor_digest": raw_digest,
                    }
                )

        parameter_rows_unformatted.append(
            {
                "schema_version": SCHEMA_VERSION,
                "figure_id": figure_id,
                "projection_type": camera.projection_type,
                "elevation_deg": camera.elevation_deg,
                "azimuth_deg": camera.azimuth_deg,
                "roll_deg": camera.roll_deg,
                "x_min": camera.xlim[0],
                "x_max": camera.xlim[1],
                "y_min": camera.ylim[0],
                "y_max": camera.ylim[1],
                "z_min": camera.zlim[0],
                "z_max": camera.zlim[1],
                "box_aspect_x": camera.box_aspect[0],
                "box_aspect_y": camera.box_aspect[1],
                "box_aspect_z": camera.box_aspect[2],
                "placement_00": placement[0, 0],
                "placement_01": placement[0, 1],
                "placement_10": placement[1, 0],
                "placement_11": placement[1, 1],
                "placement_20": placement[2, 0],
                "placement_21": placement[2, 1],
                "placement_scope": "shared_across_all_four_panels_within_figure",
                "placement_fit_inputs": "axis_corners_panels_a_b_only",
                "per_panel_transform": "forbidden",
                "red_mask_read": False,
                "protocol_sha256": protocol_hash,
                "raw_anchor_digest": raw_digest,
                "matplotlib_version": matplotlib.__version__,
            }
        )

    camera_config_hash = _sha256_bytes(
        json.dumps(camera_hash_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    arrays["camera_config_sha256"] = np.asarray([camera_config_hash])
    for collection in (
        anchor_rows_unformatted,
        parameter_rows_unformatted,
        metric_rows_unformatted,
    ):
        for row in collection:
            row["camera_config_sha256"] = camera_config_hash
    anchor_rows = [{key: _fmt(value) for key, value in row.items()} for row in anchor_rows_unformatted]
    parameter_rows = [{key: _fmt(value) for key, value in row.items()} for row in parameter_rows_unformatted]
    metric_rows = [{key: _fmt(value) for key, value in row.items()} for row in metric_rows_unformatted]
    arrays["anchor_xyz"] = np.asarray(
        [[float(row[key]) for key in ("x_nd", "y_nd", "z_nd")] for row in anchor_rows]
    )
    arrays["anchor_observed_uv"] = np.asarray(
        [[float(row[key]) for key in ("observed_normalized_u", "observed_normalized_v")] for row in anchor_rows]
    )
    arrays["anchor_predicted_uv"] = np.asarray(
        [[float(row[key]) for key in ("predicted_normalized_u", "predicted_normalized_v")] for row in anchor_rows]
    )
    arrays["anchor_ids"] = np.asarray([row["anchor_id"] for row in anchor_rows])
    return anchor_rows, parameter_rows, metric_rows, arrays, camera_config_hash


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _render_doc(
    parameters: list[dict[str, str]],
    metrics: list[dict[str, str]],
    camera_hash: str,
    npz_hash: str,
) -> str:
    failures = [row for row in metrics if row["static_camera_gate"] != "pass"]
    lines = [
        "# Chapter 4 Figures 4.3-4.6 static camera calibration",
        "",
        "Generated by `scripts/run_chapter4_fig43_fig46_camera_calibration.py`.",
        "",
        "## Boundary",
        "",
        "- Camera fitting reads only PDF-native axis-corner measurements from panels",
        "  (a),(b). Visible Moon/L1/L2 markers are independent static checks.",
        "- No red manifold mask is opened. Panel-(d) red geometry remains unevaluated",
        "  by the new frozen protocol, so paper projection acceptance is still",
        "  `not_run` and paper 3D equivalence remains `false`.",
        "- One orthographic camera and one NDC-to-panel affine placement are shared",
        "  by all four panels of each figure. Panel-specific registration is forbidden.",
        "",
        "## Frozen cameras",
        "",
        "| Figure | Elevation | Azimuth | X limits | Y limits | Z limits | Static panels passing |",
        "|---|---:|---:|---|---|---|---:|",
    ]
    for row in parameters:
        figure_metrics = [metric for metric in metrics if metric["figure_id"] == row["figure_id"]]
        passes = sum(metric["static_camera_gate"] == "pass" for metric in figure_metrics)
        lines.append(
            f"| {row['figure_id']} | {float(row['elevation_deg']):.6f} | "
            f"{float(row['azimuth_deg']):.3f} | "
            f"[{row['x_min']}, {row['x_max']}] | "
            f"[{row['y_min']}, {row['y_max']}] | "
            f"[{row['z_min']}, {row['z_max']}] | {passes}/4 |"
        )
    lines.extend(
        [
            "",
            "## Panel static-anchor metrics",
            "",
            "| Figure | Panel | Role | Anchors | RMSE [px/512] | Max [px/512] | Gate |",
            "|---|---:|---|---:|---:|---:|---|",
        ]
    )
    for row in metrics:
        lines.append(
            f"| {row['figure_id']} | ({row['panel_id']}) | `{row['panel_role']}` | "
            f"{row['anchor_count']} | {float(row['anchor_rmse_px_on_512_grid']):.3f} | "
            f"{float(row['anchor_max_error_px_on_512_grid']):.3f} | "
            f"{row['static_camera_gate']} |"
        )
    lines.extend(
        [
            "",
            f"All-panel static camera result: `{'pass' if not failures else 'fail'}` "
            f"({len(metrics) - len(failures)}/{len(metrics)} panels).",
            "",
            "## Traceability",
            "",
            f"- Camera configuration SHA256: `{camera_hash}`.",
            f"- Protocol: `{_display(PROTOCOL_PATH)}` (SHA256 `{_sha256(PROTOCOL_PATH)}`).",
            f"- Raw anchors: `{_display(ANCHOR_CSV)}`.",
            f"- Parameters: `{_display(PARAMETER_CSV)}`.",
            f"- Static metrics: `{_display(METRIC_CSV)}`.",
            f"- Evidence arrays: `{_display(NPZ_PATH)}` (SHA256 `{npz_hash}`).",
            "",
        ]
    )
    return "\n".join(lines)


def _verify(
    anchors: list[dict[str, str]],
    parameters: list[dict[str, str]],
    metrics: list[dict[str, str]],
) -> None:
    if len(parameters) != 4 or len(metrics) != 16:
        raise RuntimeError("Unexpected camera parameter/metric row count")
    if not all(row["static_camera_gate"] == "pass" for row in metrics):
        failed = [f"{row['figure_id']}{row['panel_id']}" for row in metrics if row["static_camera_gate"] != "pass"]
        raise RuntimeError(f"Static camera gate failed: {failed}")
    if any(row["red_mask_read"] != "false" for row in parameters + metrics):
        raise RuntimeError("Camera calibration escaped its static-only boundary")
    if any(row["panel_id"] == "d" and row["used_for_fit"] != "false" for row in anchors):
        raise RuntimeError("Panel (d) leaked into the camera fit")
    if any(row["per_panel_transform"] != "forbidden" for row in parameters):
        raise RuntimeError("A per-panel transform escaped the schema")


def _compare_arrays(expected: dict[str, np.ndarray]) -> None:
    with np.load(NPZ_PATH, allow_pickle=False) as stored:
        if set(stored.files) != set(expected):
            raise RuntimeError("Stored camera calibration NPZ schema is stale")
        for key, values in expected.items():
            observed = np.asarray(stored[key])
            values = np.asarray(values)
            if observed.shape != values.shape:
                raise RuntimeError(f"Stored camera array shape is stale: {key}")
            if values.dtype.kind in "fc":
                if not np.allclose(observed, values, rtol=0.0, atol=1.0e-13):
                    raise RuntimeError(f"Stored camera numerical array is stale: {key}")
            elif not np.array_equal(observed, values):
                raise RuntimeError(f"Stored camera array is stale: {key}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    anchors, parameters, metrics, arrays, camera_hash = analyze()
    _verify(anchors, parameters, metrics)
    if args.check:
        _compare_arrays(arrays)
        npz_hash = _sha256(NPZ_PATH)
        enriched_anchors = [dict(row, evidence_npz_sha256=npz_hash) for row in anchors]
        enriched_parameters = [dict(row, evidence_npz_sha256=npz_hash) for row in parameters]
        enriched_metrics = [dict(row, evidence_npz_sha256=npz_hash) for row in metrics]
        for path, rows in (
            (ANCHOR_CSV, enriched_anchors),
            (PARAMETER_CSV, enriched_parameters),
            (METRIC_CSV, enriched_metrics),
        ):
            if not path.is_file() or path.read_bytes() != _csv_bytes(rows):
                raise RuntimeError(f"Stored camera artifact is stale: {path.name}")
        expected_doc = _render_doc(
            enriched_parameters, enriched_metrics, camera_hash, npz_hash
        )
        if not DOC_PATH.is_file() or DOC_PATH.read_text(encoding="utf-8") != expected_doc:
            raise RuntimeError("Stored camera calibration report is stale")
        print(
            "chapter4_camera_calibration_check: panels=16/16, "
            f"camera_config_sha256={camera_hash}, red_mask_read=false"
        )
        return 0

    DIGITIZED.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ_PATH, **arrays)
    npz_hash = _sha256(NPZ_PATH)
    enriched_anchors = [dict(row, evidence_npz_sha256=npz_hash) for row in anchors]
    enriched_parameters = [dict(row, evidence_npz_sha256=npz_hash) for row in parameters]
    enriched_metrics = [dict(row, evidence_npz_sha256=npz_hash) for row in metrics]
    ANCHOR_CSV.write_bytes(_csv_bytes(enriched_anchors))
    PARAMETER_CSV.write_bytes(_csv_bytes(enriched_parameters))
    METRIC_CSV.write_bytes(_csv_bytes(enriched_metrics))
    DOC_PATH.write_text(
        _render_doc(enriched_parameters, enriched_metrics, camera_hash, npz_hash),
        encoding="utf-8",
    )
    for path in (ANCHOR_CSV, PARAMETER_CSV, METRIC_CSV, NPZ_PATH, DOC_PATH):
        print(f"wrote {_display(path)}")
    print(
        "chapter4_camera_calibration: panels=16/16, "
        f"camera_config_sha256={camera_hash}, red_mask_read=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
