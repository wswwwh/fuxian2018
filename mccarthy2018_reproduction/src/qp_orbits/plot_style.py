"""Shared plot style for thesis-like figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


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
            "legend.frameon": False,
            "lines.linewidth": 1.7,
        }
    )


def save_figure(fig, figure_id: str, project_root: Path) -> tuple[Path, Path]:
    """Save a Matplotlib figure as PNG and PDF."""

    png_dir = project_root / "outputs" / "figures_png"
    pdf_dir = project_root / "outputs" / "figures_pdf"
    png_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    stem = f"fig_{figure_id.replace('.', '_')}"
    png_path = png_dir / f"{stem}.png"
    pdf_path = pdf_dir / f"{stem}.pdf"
    fig.savefig(png_path, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    return png_path, pdf_path
