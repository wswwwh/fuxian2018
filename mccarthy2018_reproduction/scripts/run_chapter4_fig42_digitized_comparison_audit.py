"""Digitize the native thesis Fig. 4.2 curve and audit the DG overlap.

The source bitmap is extracted losslessly from PDF page 103.  Pixel-space
calibration and color thresholds are recorded explicitly so that the result is
traceable but remains lower-authority than the corrected dynamics data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from _paths import PROJECT_ROOT, find_thesis_pdf
from qp_orbits.plot_style import apply_style, finalize_figure


PDF_PAGE_1BASED = 103
EXPECTED_NATIVE_SIZE = (1517, 682)

FAMILY = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter4_fig42_stability_family_audit.csv"
)
NATIVE_REFERENCE = (
    PROJECT_ROOT / "outputs" / "reference_pages" / "fig_4_2_reference_native.png"
)
CALIBRATION_OUTPUT = (
    PROJECT_ROOT / "data" / "digitized" / "fig_4_2_axis_calibration.csv"
)
DIGITIZED_OUTPUT = (
    PROJECT_ROOT / "data" / "digitized" / "fig_4_2_digitized_points.csv"
)
COMPARISON_OUTPUT = (
    PROJECT_ROOT / "data" / "digitized" / "fig_4_2_computed_vs_digitized.csv"
)
AUDIT_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "chapter4_fig42_digitized_comparison_audit.csv"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter4_fig42_digitized_comparison_audit.md"
PLOT_PNG = PROJECT_ROOT / "outputs" / "diagnostics" / "fig_4_2_digitized_comparison.png"
PLOT_PDF = PROJECT_ROOT / "outputs" / "diagnostics" / "fig_4_2_digitized_comparison.pdf"

# Native embedded-bitmap calibration.  Interior grid lines identify the same
# locations independently; the outer frame supplies the 12.0/12.5 and 600/800
# endpoints.
X_TICKS = ((197.0, 12.0), (432.0, 12.1), (667.0, 12.2), (902.0, 12.3),
           (1137.0, 12.4), (1372.0, 12.5))
Y_TICKS = ((563.0, 600.0), (435.0, 650.0), (307.0, 700.0),
           (179.0, 750.0), (51.0, 800.0))

MIN_BLUE_COLUMNS = 1000
MIN_OVERLAP_ROWS = 10
MIN_REFERENCE_COVERAGE = 0.85
X_PIXEL_UNCERTAINTY = 3.0
Y_PIXEL_UNCERTAINTY = 5.0


@dataclass(frozen=True)
class AxisFit:
    axis: str
    slope: float
    intercept: float
    ticks: tuple[tuple[float, float], ...]
    max_abs_residual: float

    def map(self, pixel: np.ndarray | float) -> np.ndarray | float:
        return self.slope * pixel + self.intercept


@dataclass
class AuditResult:
    image_rgb: np.ndarray
    blue_pixel_x: np.ndarray
    blue_pixel_y: np.ndarray
    orange_pixel_x: float
    orange_pixel_y: float
    reference_time: np.ndarray
    reference_nu: np.ndarray
    family_rows: list[dict[str, str]]
    comparison_rows: list[dict[str, str]]
    calibration_rows: list[dict[str, str]]
    digitized_rows: list[dict[str, str]]
    summary: dict[str, str]


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not np.isfinite(number):
            return ""
        return f"{number:.16g}"
    return str(value)


def _bool(value: str) -> bool:
    return value.strip().lower() == "true"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, str]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _display_path(path: Path) -> str:
    return os.path.relpath(path, PROJECT_ROOT).replace("\\", "/")


def _fit_axis(axis: str, ticks: tuple[tuple[float, float], ...]) -> AxisFit:
    pixels = np.asarray([tick[0] for tick in ticks], dtype=float)
    values = np.asarray([tick[1] for tick in ticks], dtype=float)
    slope, intercept = np.polyfit(pixels, values, 1)
    residuals = slope * pixels + intercept - values
    return AxisFit(
        axis=axis,
        slope=float(slope),
        intercept=float(intercept),
        ticks=ticks,
        max_abs_residual=float(np.max(np.abs(residuals))),
    )


def _calibration_rows(x_fit: AxisFit, y_fit: AxisFit) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for fit in (x_fit, y_fit):
        for pixel, value in fit.ticks:
            fitted = float(fit.map(pixel))
            rows.append(
                {
                    "axis": fit.axis,
                    "tick_value": _fmt(value),
                    "pixel_coordinate": _fmt(pixel),
                    "fitted_value": _fmt(fitted),
                    "residual_data_units": _fmt(fitted - value),
                    "fit_slope_data_per_pixel": _fmt(fit.slope),
                    "fit_intercept": _fmt(fit.intercept),
                }
            )
    return rows


def extract_native_reference(pdf_path: Path, output: Path = NATIVE_REFERENCE) -> dict[str, Any]:
    """Extract the largest embedded image from the Fig. 4.2 PDF page."""

    with fitz.open(pdf_path) as document:
        page = document.load_page(PDF_PAGE_1BASED - 1)
        images = page.get_images(full=True)
        if not images:
            raise RuntimeError(f"No embedded image on PDF page {PDF_PAGE_1BASED}")
        selected = max(images, key=lambda item: int(item[2]) * int(item[3]))
        xref = int(selected[0])
        extracted = document.extract_image(xref)
    raw = extracted["image"]
    with Image.open(io.BytesIO(raw)) as image:
        size = image.size
    if size != EXPECTED_NATIVE_SIZE:
        raise RuntimeError(
            f"Unexpected native Fig. 4.2 size {size}; expected {EXPECTED_NATIVE_SIZE}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return {
        "pdf_path": pdf_path,
        "pdf_page": PDF_PAGE_1BASED,
        "xref": xref,
        "width": size[0],
        "height": size[1],
        "extension": extracted["ext"],
    }


def inspect_native_reference(pdf_path: Path) -> dict[str, Any]:
    """Read PDF image provenance without rewriting the extracted bitmap."""

    with fitz.open(pdf_path) as document:
        page = document.load_page(PDF_PAGE_1BASED - 1)
        images = page.get_images(full=True)
        if not images:
            raise RuntimeError(f"No embedded image on PDF page {PDF_PAGE_1BASED}")
        selected = max(images, key=lambda item: int(item[2]) * int(item[3]))
    size = (int(selected[2]), int(selected[3]))
    if size != EXPECTED_NATIVE_SIZE:
        raise RuntimeError(
            f"Unexpected native Fig. 4.2 size {size}; expected {EXPECTED_NATIVE_SIZE}"
        )
    return {
        "pdf_path": pdf_path,
        "pdf_page": PDF_PAGE_1BASED,
        "xref": int(selected[0]),
        "width": size[0],
        "height": size[1],
        "extension": "png",
    }


def _extract_colored_reference(image_rgb: np.ndarray) -> dict[str, Any]:
    red = image_rgb[:, :, 0]
    green = image_rgb[:, :, 1]
    blue = image_rgb[:, :, 2]
    blue_mask = (
        (red < 80)
        & (green > 60)
        & (green < 180)
        & (blue > 120)
    )
    orange_mask = (
        (red > 150)
        & (green > 30)
        & (green < 130)
        & (blue < 100)
        & (red > 1.4 * green)
    )
    pixel_y, pixel_x = np.where(blue_mask)
    orange_y, orange_x = np.where(orange_mask)
    if orange_x.size < 20:
        raise RuntimeError(f"Orange periodic anchor extraction too small: {orange_x.size}")
    unique_x = np.unique(pixel_x)
    if unique_x.size < MIN_BLUE_COLUMNS:
        raise RuntimeError(
            f"Blue curve extraction has {unique_x.size} columns; expected >= {MIN_BLUE_COLUMNS}"
        )
    center_y = np.asarray(
        [np.median(pixel_y[pixel_x == column]) for column in unique_x],
        dtype=float,
    )
    return {
        "blue_pixel_x": unique_x.astype(float),
        "blue_pixel_y": center_y,
        "orange_pixel_x": float(np.median(orange_x)),
        "orange_pixel_y": float(np.median(orange_y)),
        "blue_mask_pixels": int(pixel_x.size),
        "orange_mask_pixels": int(orange_x.size),
    }


def analyze(
    reference_path: Path = NATIVE_REFERENCE,
    family_path: Path = FAMILY,
    *,
    pdf_metadata: dict[str, Any] | None = None,
) -> AuditResult:
    """Return the deterministic digitization and comparison without writing."""

    with Image.open(reference_path) as image:
        if image.size != EXPECTED_NATIVE_SIZE:
            raise RuntimeError(
                f"Unexpected native reference size {image.size}; expected {EXPECTED_NATIVE_SIZE}"
            )
        image_rgb = np.asarray(image.convert("RGB"))
    x_fit = _fit_axis("mapping_time_days", X_TICKS)
    y_fit = _fit_axis("stability_index", Y_TICKS)
    extracted = _extract_colored_reference(image_rgb)

    blue_time = np.asarray(x_fit.map(extracted["blue_pixel_x"]), dtype=float)
    blue_nu = np.asarray(y_fit.map(extracted["blue_pixel_y"]), dtype=float)
    anchor_time = float(x_fit.map(extracted["orange_pixel_x"]))
    anchor_nu = float(y_fit.map(extracted["orange_pixel_y"]))
    reference_time = np.concatenate(([anchor_time], blue_time))
    reference_nu = np.concatenate(([anchor_nu], blue_nu))
    order = np.argsort(reference_time)
    reference_time = reference_time[order]
    reference_nu = reference_nu[order]

    x_uncertainty = x_fit.max_abs_residual + X_PIXEL_UNCERTAINTY * abs(x_fit.slope)
    y_uncertainty = y_fit.max_abs_residual + Y_PIXEL_UNCERTAINTY * abs(y_fit.slope)
    calibration_pixel_residuals = [
        abs(float(row["residual_data_units"]))
        / abs(x_fit.slope if row["axis"] == "mapping_time_days" else y_fit.slope)
        for row in _calibration_rows(x_fit, y_fit)
    ]
    calibration_rmse_px = float(
        np.sqrt(np.mean(np.asarray(calibration_pixel_residuals, dtype=float) ** 2))
    )
    calibration_max_px = float(max(calibration_pixel_residuals))
    family_rows = _read_csv(family_path)
    accepted_quasi = sorted(
        [
            row
            for row in family_rows
            if row["kind"] == "quasi_halo" and row["acceptance"] == "pass"
        ],
        key=lambda row: float(row["mapping_time_days"]),
    )
    rejected_quasi = [
        row
        for row in family_rows
        if row["kind"] == "quasi_halo" and row["acceptance"] != "pass"
    ]
    periodic = next(row for row in family_rows if row["kind"] == "periodic_halo_anchor")

    reference_min = float(reference_time.min())
    reference_max = float(reference_time.max())
    computed_min = min(float(row["mapping_time_days"]) for row in accepted_quasi)
    computed_max = max(float(row["mapping_time_days"]) for row in accepted_quasi)
    overlap_min = max(reference_min, computed_min)
    overlap_max = min(reference_max, computed_max)
    coverage = max(0.0, overlap_max - overlap_min) / (reference_max - reference_min)

    comparison_rows: list[dict[str, str]] = []
    periodic_time = float(periodic["mapping_time_days"])
    periodic_nu = float(periodic["stability_index"])
    anchor_time_error = periodic_time - anchor_time
    anchor_nu_error = periodic_nu - anchor_nu
    comparison_rows.append(
        {
            "comparison_role": "periodic_anchor",
            "source_branch": periodic["source_branch"],
            "curve_samples": periodic["curve_samples"],
            "mapping_time_days": _fmt(periodic_time),
            "computed_stability_index": _fmt(periodic_nu),
            "digitized_stability_index": _fmt(anchor_nu),
            "stability_index_error": _fmt(anchor_nu_error),
            "absolute_error": _fmt(abs(anchor_nu_error)),
            "time_error_days": _fmt(anchor_time_error),
            "within_reference_range": "true",
            "within_digitization_uncertainty": _fmt(
                abs(anchor_time_error) <= x_uncertainty
                and abs(anchor_nu_error) <= y_uncertainty
            ),
            "curve_residual_norm": periodic["curve_residual_norm"],
            "determinant_error": periodic["determinant_error"],
        }
    )

    overlap_errors: list[float] = []
    for row in accepted_quasi:
        time = float(row["mapping_time_days"])
        computed_nu = float(row["stability_index"])
        within = reference_min <= time <= reference_max
        digitized_nu = float(np.interp(time, reference_time, reference_nu)) if within else np.nan
        error = computed_nu - digitized_nu if within else np.nan
        if within:
            overlap_errors.append(error)
        comparison_rows.append(
            {
                "comparison_role": "accepted_quasi_curve",
                "source_branch": row["source_branch"],
                "curve_samples": row["curve_samples"],
                "mapping_time_days": _fmt(time),
                "computed_stability_index": _fmt(computed_nu),
                "digitized_stability_index": _fmt(digitized_nu),
                "stability_index_error": _fmt(error),
                "absolute_error": _fmt(abs(error)),
                "time_error_days": "0" if within else "",
                "within_reference_range": _fmt(within),
                "within_digitization_uncertainty": _fmt(
                    within and abs(error) <= y_uncertainty
                ),
                "curve_residual_norm": row["curve_residual_norm"],
                "determinant_error": row["determinant_error"],
            }
        )

    errors = np.asarray(overlap_errors, dtype=float)
    rmse = float(np.sqrt(np.mean(errors**2)))
    mae = float(np.mean(np.abs(errors)))
    max_error = float(np.max(np.abs(errors)))
    mean_error = float(np.mean(errors))
    overlap_pass = bool(
        len(errors) >= MIN_OVERLAP_ROWS
        and coverage >= MIN_REFERENCE_COVERAGE
        and rmse <= y_uncertainty
        and max_error <= y_uncertainty
        and abs(anchor_time_error) <= x_uncertainty
        and abs(anchor_nu_error) <= y_uncertainty
        and calibration_max_px <= 1.5
    )
    full_coverage = bool(computed_max >= reference_max - x_uncertainty)
    status = (
        "pointwise_overlap_pass_full_curve_coverage_pass"
        if overlap_pass and full_coverage
        else "pointwise_overlap_pass_full_curve_coverage_boundary"
        if overlap_pass
        else "pointwise_overlap_fail"
    )
    reference_at_computed_max = float(
        np.interp(computed_max, reference_time, reference_nu)
    )

    provenance = pdf_metadata or {}
    summary_values: dict[str, Any] = {
        "figure_id": "4.2",
        "source_pdf": _display_path(Path(provenance["pdf_path"]))
        if provenance.get("pdf_path")
        else "",
        "source_pdf_page": provenance.get("pdf_page", PDF_PAGE_1BASED),
        "source_pdf_xref": provenance.get("xref", ""),
        "source_pdf_sha256": _sha256(Path(provenance["pdf_path"]))
        if provenance.get("pdf_path")
        else "",
        "source_image": _display_path(reference_path),
        "source_image_width": image_rgb.shape[1],
        "source_image_height": image_rgb.shape[0],
        "source_image_sha256": _sha256(reference_path),
        "computed_family": _display_path(family_path),
        "computed_family_sha256": _sha256(family_path),
        "blue_mask_pixels": extracted["blue_mask_pixels"],
        "blue_curve_columns": extracted["blue_pixel_x"].size,
        "orange_mask_pixels": extracted["orange_mask_pixels"],
        "reference_time_min_days": reference_min,
        "reference_time_max_days": reference_max,
        "reference_nu_min": float(reference_nu.min()),
        "reference_nu_max": float(reference_nu.max()),
        "accepted_quasi_rows": len(accepted_quasi),
        "rejected_quasi_rows": len(rejected_quasi),
        "overlap_comparison_rows": len(errors),
        "overlap_time_min_days": overlap_min,
        "overlap_time_max_days": overlap_max,
        "reference_time_coverage_fraction": coverage,
        "pointwise_mae_nu": mae,
        "pointwise_rmse_nu": rmse,
        "pointwise_max_abs_error_nu": max_error,
        "pointwise_mean_error_nu": mean_error,
        "periodic_anchor_time_abs_error_days": abs(anchor_time_error),
        "periodic_anchor_nu_abs_error": abs(anchor_nu_error),
        "estimated_x_uncertainty_days": x_uncertainty,
        "estimated_y_uncertainty_nu": y_uncertainty,
        "axis_calibration_rmse_px": calibration_rmse_px,
        "axis_calibration_max_abs_residual_px": calibration_max_px,
        "computed_tail_time_gap_days": max(0.0, reference_max - computed_max),
        "computed_tail_reference_nu_gap": float(reference_nu.max() - reference_at_computed_max),
        "pointwise_overlap_acceptance": overlap_pass,
        "full_curve_coverage": full_coverage,
        "overall_status": status,
    }
    summary = {key: _fmt(value) for key, value in summary_values.items()}

    digitized_rows: list[dict[str, str]] = [
        {
            "series": "periodic_anchor",
            "pixel_x": _fmt(extracted["orange_pixel_x"]),
            "pixel_y": _fmt(extracted["orange_pixel_y"]),
            "mapping_time_days": _fmt(anchor_time),
            "stability_index": _fmt(anchor_nu),
            "source_image": _display_path(reference_path),
            "digitization_method": "native_pdf_rgb_threshold_median",
            "estimated_x_uncertainty_days": _fmt(x_uncertainty),
            "estimated_y_uncertainty_nu": _fmt(y_uncertainty),
        }
    ]
    digitized_rows.extend(
        {
            "series": "blue_stability_curve",
            "pixel_x": _fmt(pixel_x),
            "pixel_y": _fmt(pixel_y),
            "mapping_time_days": _fmt(time),
            "stability_index": _fmt(nu),
            "source_image": _display_path(reference_path),
            "digitization_method": "native_pdf_rgb_threshold_median",
            "estimated_x_uncertainty_days": _fmt(x_uncertainty),
            "estimated_y_uncertainty_nu": _fmt(y_uncertainty),
        }
        for pixel_x, pixel_y, time, nu in zip(
            extracted["blue_pixel_x"], extracted["blue_pixel_y"], blue_time, blue_nu
        )
    )
    return AuditResult(
        image_rgb=image_rgb,
        blue_pixel_x=extracted["blue_pixel_x"],
        blue_pixel_y=extracted["blue_pixel_y"],
        orange_pixel_x=extracted["orange_pixel_x"],
        orange_pixel_y=extracted["orange_pixel_y"],
        reference_time=reference_time,
        reference_nu=reference_nu,
        family_rows=family_rows,
        comparison_rows=comparison_rows,
        calibration_rows=_calibration_rows(x_fit, y_fit),
        digitized_rows=digitized_rows,
        summary=summary,
    )


def _render_plot(result: AuditResult) -> None:
    apply_style()
    figure = plt.figure(figsize=(11.0, 7.4), constrained_layout=True)
    grid = figure.add_gridspec(2, 2, height_ratios=(1.0, 0.9))
    image_axis = figure.add_subplot(grid[0, :])
    comparison_axis = figure.add_subplot(grid[1, 0])
    residual_axis = figure.add_subplot(grid[1, 1])

    image_axis.imshow(result.image_rgb)
    stride = max(1, result.blue_pixel_x.size // 180)
    image_axis.scatter(
        result.blue_pixel_x[::stride],
        result.blue_pixel_y[::stride],
        s=5,
        facecolors="none",
        edgecolors="#d73027",
        linewidths=0.45,
        label="extracted blue centerline",
    )
    image_axis.scatter(
        [result.orange_pixel_x],
        [result.orange_pixel_y],
        marker="x",
        s=32,
        color="#6a3d9a",
        linewidths=1.2,
        label="extracted periodic anchor",
    )
    image_axis.set_title(
        "Native PDF bitmap (red circles: extracted centerline; purple x: anchor)"
    )
    image_axis.set_axis_off()

    uncertainty = float(result.summary["estimated_y_uncertainty_nu"])
    comparison_axis.fill_between(
        result.reference_time,
        result.reference_nu - uncertainty,
        result.reference_nu + uncertainty,
        color="#0072bd",
        alpha=0.12,
        label="digitization uncertainty",
    )
    comparison_axis.plot(
        result.reference_time,
        result.reference_nu,
        color="#0072bd",
        linewidth=1.3,
        label="digitized thesis curve",
    )
    accepted = [
        row
        for row in result.comparison_rows
        if row["comparison_role"] == "accepted_quasi_curve"
    ]
    times = np.asarray([float(row["mapping_time_days"]) for row in accepted])
    values = np.asarray([float(row["computed_stability_index"]) for row in accepted])
    comparison_axis.plot(
        times,
        values,
        "o-",
        color="#d95319",
        markersize=3.4,
        linewidth=1.1,
        label="accepted corrected DG family",
    )
    computed_max = times.max()
    reference_max = result.reference_time.max()
    comparison_axis.axvspan(
        computed_max,
        reference_max,
        color="#9e9e9e",
        alpha=0.17,
        label="uncovered thesis tail",
    )
    comparison_axis.set_xlabel("Mapping Time [days]")
    comparison_axis.set_ylabel(r"Stability Index, $\nu$")
    comparison_axis.set_title("Data-space overlap and explicit tail boundary")
    comparison_axis.legend(fontsize=7.4)

    overlap = [
        row
        for row in accepted
        if _bool(row["within_reference_range"])
    ]
    overlap_times = np.asarray([float(row["mapping_time_days"]) for row in overlap])
    errors = np.asarray([float(row["stability_index_error"]) for row in overlap])
    residual_axis.axhspan(-uncertainty, uncertainty, color="#b2df8a", alpha=0.25)
    residual_axis.axhline(0.0, color="#4d4d4d", linewidth=0.8)
    residual_axis.plot(overlap_times, errors, "o-", color="#6a3d9a", markersize=3.4)
    residual_axis.set_xlabel("Mapping Time [days]")
    residual_axis.set_ylabel(r"Computed $-$ digitized $\Delta\nu$")
    residual_axis.set_title(
        "Overlap residuals: "
        f"RMSE={float(result.summary['pointwise_rmse_nu']):.3f}, "
        f"max={float(result.summary['pointwise_max_abs_error_nu']):.3f}"
    )

    figure.suptitle(
        "McCarthy Fig. 4.2: native-image digitization versus corrected DG family",
        fontsize=12,
    )
    PLOT_PNG.parent.mkdir(parents=True, exist_ok=True)
    finalize_figure(figure)
    figure.savefig(PLOT_PNG, dpi=240, bbox_inches="tight", pad_inches=0.18)
    figure.savefig(PLOT_PDF, bbox_inches="tight", pad_inches=0.18)
    plt.close(figure)


def _render_doc(result: AuditResult) -> None:
    summary = result.summary
    status = summary["overall_status"]
    lines = [
        "# Chapter 4 Figure 4.2 digitized comparison audit",
        "",
        "Generated by `scripts/run_chapter4_fig42_digitized_comparison_audit.py`.",
        "The reference curve is lower-authority image-derived evidence; the corrected",
        "DG family remains the numerical source of record.",
        "",
        "## Result",
        "",
        f"- Status: `{status}`.",
        f"- Native source: `{summary['source_image']}` "
        f"({summary['source_image_width']}x{summary['source_image_height']} px).",
        f"- Extracted blue columns: `{summary['blue_curve_columns']}`.",
        f"- Accepted corrected quasi-halo rows: `{summary['accepted_quasi_rows']}`; "
        f"overlap comparisons: `{summary['overlap_comparison_rows']}`.",
        f"- Thesis-time coverage: `{float(summary['reference_time_coverage_fraction']):.6%}`.",
        f"- Pointwise MAE / RMSE / maximum absolute error: "
        f"`{float(summary['pointwise_mae_nu']):.6f}` / "
        f"`{float(summary['pointwise_rmse_nu']):.6f}` / "
        f"`{float(summary['pointwise_max_abs_error_nu']):.6f}` in stability index.",
        f"- Estimated digitization uncertainty: "
        f"`+/-{float(summary['estimated_x_uncertainty_days']):.6f}` days and "
        f"`+/-{float(summary['estimated_y_uncertainty_nu']):.6f}` in stability index.",
        f"- Axis-calibration RMSE / maximum residual: "
        f"`{float(summary['axis_calibration_rmse_px']):.6g}` / "
        f"`{float(summary['axis_calibration_max_abs_residual_px']):.6g}` native px.",
        f"- Periodic-anchor absolute errors: "
        f"`{float(summary['periodic_anchor_time_abs_error_days']):.6f}` days and "
        f"`{float(summary['periodic_anchor_nu_abs_error']):.6f}`.",
        f"- Missing thesis tail: `{float(summary['computed_tail_time_gap_days']):.6f}` days "
        f"and about `{float(summary['computed_tail_reference_nu_gap']):.6f}` in the "
        "digitized reference curve.",
        "",
        "The pointwise overlap passes the image-reading uncertainty gate. This closes",
        "the previously missing 2D paper-digitization subtask over the common interval.",
        "It does **not** establish full Fig. 4.2 equivalence: the accepted computed",
        "branch stops before the final thesis segment and no values are extrapolated.",
        "",
        "## Calibration and acceptance",
        "",
        "- Linear axes are fitted from all visible native-bitmap tick/frame positions.",
        f"- Minimum blue columns: `{MIN_BLUE_COLUMNS}`; observed "
        f"`{summary['blue_curve_columns']}`.",
        f"- Minimum overlap rows: `{MIN_OVERLAP_ROWS}`; observed "
        f"`{summary['overlap_comparison_rows']}`.",
        f"- Minimum thesis-time coverage: `{MIN_REFERENCE_COVERAGE:.0%}`; observed "
        f"`{float(summary['reference_time_coverage_fraction']):.6%}`.",
        "- RMSE, maximum pointwise error, and periodic-anchor error must stay inside",
        "  the recorded pixel/calibration uncertainty.",
        f"- Pointwise-overlap acceptance: `{summary['pointwise_overlap_acceptance']}`.",
        f"- Full-curve coverage: `{summary['full_curve_coverage']}`.",
        "",
        "## Provenance",
        "",
        f"- Thesis PDF: `{summary['source_pdf']}`; page "
        f"`{summary['source_pdf_page']}`; xref `{summary['source_pdf_xref']}`.",
        f"- Thesis PDF SHA256: `{summary['source_pdf_sha256']}`.",
        f"- Native image SHA256: `{summary['source_image_sha256']}`.",
        f"- Corrected-family SHA256: `{summary['computed_family_sha256']}`.",
        f"- Axis calibration: `{_display_path(CALIBRATION_OUTPUT)}`.",
        f"- Digitized points: `{_display_path(DIGITIZED_OUTPUT)}`.",
        f"- Pointwise comparison: `{_display_path(COMPARISON_OUTPUT)}`.",
        f"- Summary row: `{_display_path(AUDIT_OUTPUT)}`.",
        f"- Diagnostic plot: `{_display_path(PLOT_PNG)}` and "
        f"`{_display_path(PLOT_PDF)}`.",
        "",
    ]
    DOC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(result: AuditResult) -> None:
    _write_csv(
        CALIBRATION_OUTPUT,
        result.calibration_rows,
        (
            "axis",
            "tick_value",
            "pixel_coordinate",
            "fitted_value",
            "residual_data_units",
            "fit_slope_data_per_pixel",
            "fit_intercept",
        ),
    )
    _write_csv(
        DIGITIZED_OUTPUT,
        result.digitized_rows,
        (
            "series",
            "pixel_x",
            "pixel_y",
            "mapping_time_days",
            "stability_index",
            "source_image",
            "digitization_method",
            "estimated_x_uncertainty_days",
            "estimated_y_uncertainty_nu",
        ),
    )
    _write_csv(
        COMPARISON_OUTPUT,
        result.comparison_rows,
        (
            "comparison_role",
            "source_branch",
            "curve_samples",
            "mapping_time_days",
            "computed_stability_index",
            "digitized_stability_index",
            "stability_index_error",
            "absolute_error",
            "time_error_days",
            "within_reference_range",
            "within_digitization_uncertainty",
            "curve_residual_norm",
            "determinant_error",
        ),
    )
    _write_csv(AUDIT_OUTPUT, [result.summary], tuple(result.summary))
    _render_plot(result)
    _render_doc(result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, help="Override the McCarthy thesis PDF path.")
    parser.add_argument(
        "--reuse-native-reference",
        action="store_true",
        help="Do not re-extract the native PDF bitmap; use the tracked PNG.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Analyze current artifacts without rewriting them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata: dict[str, Any] | None = None
    if args.check or args.reuse_native_reference:
        if not NATIVE_REFERENCE.exists():
            raise FileNotFoundError(NATIVE_REFERENCE)
        try:
            pdf_path = (args.pdf or find_thesis_pdf()).resolve()
        except FileNotFoundError:
            pdf_path = None
        if pdf_path is not None:
            metadata = inspect_native_reference(pdf_path)
    else:
        pdf_path = (args.pdf or find_thesis_pdf()).resolve()
        metadata = extract_native_reference(pdf_path)
    result = analyze(pdf_metadata=metadata)
    if not _bool(result.summary["pointwise_overlap_acceptance"]):
        raise SystemExit("Fig. 4.2 pointwise-overlap acceptance failed")
    if args.check:
        print(
            "fig42_digitization_check: "
            f"status={result.summary['overall_status']}, "
            f"overlap_rows={result.summary['overlap_comparison_rows']}, "
            f"coverage={result.summary['reference_time_coverage_fraction']}, "
            f"rmse={result.summary['pointwise_rmse_nu']}, "
            f"max_error={result.summary['pointwise_max_abs_error_nu']}"
        )
        return 0
    write_outputs(result)
    print(f"wrote {_display_path(AUDIT_OUTPUT)}")
    print(f"wrote {_display_path(DOC_OUTPUT)}")
    print(f"wrote {_display_path(PLOT_PNG)}")
    print(
        "fig42_digitization: "
        f"status={result.summary['overall_status']}, "
        f"overlap_rows={result.summary['overlap_comparison_rows']}, "
        f"coverage={result.summary['reference_time_coverage_fraction']}, "
        f"rmse={result.summary['pointwise_rmse_nu']}, "
        f"max_error={result.summary['pointwise_max_abs_error_nu']}, "
        f"tail_days={result.summary['computed_tail_time_gap_days']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
