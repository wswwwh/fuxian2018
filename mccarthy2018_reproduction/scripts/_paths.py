"""Path helpers for command-line scripts."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def find_thesis_pdf() -> Path:
    candidates = sorted(PROJECT_ROOT.parent.glob("2018_McCarthy*.pdf"))
    if not candidates:
        raise FileNotFoundError("Could not find 2018_McCarthy thesis PDF next to the project.")
    return candidates[0]
