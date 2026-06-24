"""Create side-by-side comparison sheets for implemented figures."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from _paths import PROJECT_ROOT


IMPLEMENTED = [
    "2.1",
    "2.2",
    "2.3",
    "2.4",
    "2.5",
    "2.6",
    "2.7",
    "2.8",
    "2.9",
    "2.10",
    "2.11",
    "2.12",
    "2.13",
    "2.14",
    "2.15",
    "3.1",
    "3.2",
    "3.3",
    "3.4",
    "3.5",
    "3.6",
    "3.7",
    "3.8",
    "3.9",
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.14",
    "3.15",
    "3.16",
    "3.17",
    "4.1",
    "4.2",
    "4.3",
    "4.4",
    "4.5",
    "4.6",
    "4.7",
    "4.8",
    "5.1",
    "5.2",
    "5.3",
    "5.4",
    "5.5",
    "5.6",
    "5.7",
    "5.8",
    "5.9",
    "5.10",
    "5.11",
    "5.12",
    "5.13",
    "5.14",
]


def load_image(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGB")


def fit_width(image: Image.Image, width: int) -> Image.Image:
    scale = width / image.width
    height = max(1, int(image.height * scale))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def make_sheet(figure_id: str) -> Path:
    stem = f"fig_{figure_id.replace('.', '_')}"
    reference = load_image(PROJECT_ROOT / "outputs" / "reference_pages" / f"{stem}_reference.png")
    generated = load_image(PROJECT_ROOT / "outputs" / "figures_png" / f"{stem}.png")

    target_width = 760
    reference = fit_width(reference, target_width)
    generated = fit_width(generated, target_width)

    label_h = 42
    gap = 32
    width = reference.width + generated.width + gap
    height = max(reference.height, generated.height) + label_h + 24
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    draw.text((0, 8), f"Figure {figure_id} reference", fill="black", font=font)
    draw.text((reference.width + gap, 8), f"Figure {figure_id} reproduction", fill="black", font=font)
    canvas.paste(reference, (0, label_h))
    canvas.paste(generated, (reference.width + gap, label_h))

    output_dir = PROJECT_ROOT / "outputs" / "comparison_contact_sheets"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{stem}_comparison.png"
    canvas.save(out_path)
    return out_path


def main() -> None:
    outputs = [make_sheet(figure_id) for figure_id in IMPLEMENTED]
    for path in outputs:
        print(path)
    print(f"Wrote {len(outputs)} comparison sheets")


if __name__ == "__main__":
    main()
