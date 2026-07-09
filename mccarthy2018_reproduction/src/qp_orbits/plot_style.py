"""Shared plot style for thesis-like figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 300,
            "font.family": "serif",
            "mathtext.fontset": "cm",
            "axes.grid": True,
            "grid.alpha": 0.22,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "axes.linewidth": 0.85,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.pad": 3.5,
            "ytick.major.pad": 3.5,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.frameon": False,
            "lines.linewidth": 1.7,
            "figure.constrained_layout.w_pad": 0.035,
            "figure.constrained_layout.h_pad": 0.035,
        }
    )


def _is_3d_axis(ax) -> bool:
    return getattr(ax, "name", "") == "3d" and hasattr(ax, "zaxis")


def style_3d_axis(ax, *, labelpad: float = 3.0, tick_pad: float = 1.8, nbins: int = 4) -> None:
    """Apply publication-safe 3D axis spacing.

    Several thesis-match plots use compact 3D panels. Positive label and tick
    padding prevents tick labels from colliding with the axis frame when saved.
    """

    ax.tick_params(labelsize=7.5, pad=tick_pad, length=2.8, width=0.65)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.labelpad = max(axis.labelpad, labelpad)
        axis.set_major_locator(MaxNLocator(nbins=nbins))
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis.pane.set_edgecolor((0.82, 0.82, 0.82, 0.55))
        axis._axinfo["grid"]["color"] = (0.86, 0.86, 0.86, 0.42)
        axis._axinfo["grid"]["linewidth"] = 0.38
        axis._axinfo["tick"]["inward_factor"] = 0.0
        axis._axinfo["tick"]["outward_factor"] = 0.22


def finalize_figure(fig) -> None:
    """Normalize figure spacing before writing publication artifacts."""

    for ax in fig.axes:
        if _is_3d_axis(ax):
            style_3d_axis(ax)
        else:
            ax.tick_params(direction="out", pad=3.0, length=3.2, width=0.75)
            ax.xaxis.labelpad = max(ax.xaxis.labelpad, 3.0)
            ax.yaxis.labelpad = max(ax.yaxis.labelpad, 3.0)
    fig.align_labels()
    fig.canvas.draw()


def save_figure(fig, figure_id: str, project_root: Path) -> tuple[Path, Path]:
    """Save a Matplotlib figure as PNG and PDF."""

    png_dir = project_root / "outputs" / "figures_png"
    pdf_dir = project_root / "outputs" / "figures_pdf"
    png_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    stem = f"fig_{figure_id.replace('.', '_')}"
    png_path = png_dir / f"{stem}.png"
    pdf_path = pdf_dir / f"{stem}.pdf"
    finalize_figure(fig)
    fig.savefig(png_path, bbox_inches="tight", pad_inches=0.24)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.24)
    return png_path, pdf_path
