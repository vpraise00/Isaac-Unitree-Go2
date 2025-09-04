"""Isaac Lab (2.2) integration helpers for RL/IL code usage from go2lab.

Features:
- Resolve Isaac Lab repo path from env or configs/lab2_config.json
- Add Lab repo to sys.path on-demand
- Convenience import function to load Lab modules dynamically

Usage:
    from go2lab.lab.integration import ensure_lab_on_path, lab_import
    ensure_lab_on_path()  # uses configs/lab2_config.json or ISAAC_LAB_PATH
    lab_rl = lab_import("omni.isaac.lab")  # example
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Optional


def _repo_root() -> Path:
    # src/go2lab/lab/integration.py -> repo
    return Path(__file__).resolve().parents[4]


def resolve_lab_repo(explicit: Optional[str] = None) -> Optional[Path]:
    """Resolve the local Isaac Lab repository path.

    Priority:
    1) explicit argument
    2) env ISAAC_LAB_PATH
    3) configs/lab2_config.json {"lab_repo": "..."}
    """
    if explicit:
        p = Path(explicit).expanduser()
        return p if p.exists() else None
    env = os.environ.get("ISAAC_LAB_PATH")
    if env:
        p = Path(env).expanduser()
        return p if p.exists() else None
    cfg = _repo_root() / "configs/lab2_config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("lab_repo"):
                p = Path(data["lab_repo"]).expanduser()
                return p if p.exists() else None
        except Exception:
            pass
    return None


def ensure_lab_on_path(lab_repo: Optional[str | Path] = None) -> Optional[Path]:
    """Ensure Isaac Lab repo is present on sys.path; return the path used.

    If lab_repo is None, resolve via resolve_lab_repo().
    """
    p: Optional[Path]
    if lab_repo is None:
        p = resolve_lab_repo()
    else:
        p = Path(lab_repo)
    if p is None:
        return None
    if str(p) not in sys.path:
        sys.path.append(str(p))
    return p


def lab_import(module: str):
    """Import an Isaac Lab module by name after ensuring path.

    Example: lab_import("omni.isaac.lab_tasks")
    """
    if ensure_lab_on_path() is None:
        raise ModuleNotFoundError(
            "Isaac Lab repo path not found. Set ISAAC_LAB_PATH or configs/lab2_config.json 'lab_repo'."
        )
    return importlib.import_module(module)


__all__ = ["resolve_lab_repo", "ensure_lab_on_path", "lab_import"]
