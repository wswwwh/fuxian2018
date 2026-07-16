"""Path helpers for command-line scripts."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def find_thesis_pdf() -> Path:
    search_roots = (
        PROJECT_ROOT.parent,
        PROJECT_ROOT.parent / "目标论文",
    )
    candidates = sorted(
        candidate
        for root in search_roots
        if root.is_dir()
        for candidate in root.glob("2018_McCarthy*.pdf")
    )
    if not candidates:
        searched = ", ".join(str(root) for root in search_roots)
        raise FileNotFoundError(
            f"Could not find 2018_McCarthy thesis PDF in the approved locations: {searched}"
        )
    return candidates[0]
