"""Shim: run the src/go2lab teleop implementation to avoid duplication."""
from __future__ import annotations

from pathlib import Path
import runpy
import sys


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    target = repo_root / "src/go2lab/sim/scripts/teleop_keyboard.py"
    sys.argv = [str(target)]
    try:
        runpy.run_path(str(target), run_name="__main__")
        return 0
    except SystemExit as se:
        return int(getattr(se, "code", 0) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
