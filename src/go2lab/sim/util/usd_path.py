"""Utilities for resolving USD path specs consistently and building Isaac Lab URLs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

URL_PREFIXES = ("omniverse://", "omni://", "http://", "https://")


def _strip(spec: str) -> str:
    s = spec.strip().strip('"').strip("'")
    return s


def normalize_spec(spec: str) -> str:
    s = _strip(spec)
    s = os.path.expandvars(s)
    return s.replace("\\", "/")


def classify_spec(spec: str) -> str:
    if not spec:
        return "empty"
    if spec.startswith(URL_PREFIXES):
        return "url"
    return "path"


def isaaclab_asset_path(rel_path: str) -> str:
    rel = rel_path.lstrip("/")
    try:
        import carb  # type: ignore
        root = carb.settings.get_settings().get("/persistent/isaac/asset_root/cloud")
        if isinstance(root, str) and root:
            return f"{root}/Isaac/IsaacLab/{rel}".replace("\\", "/")
    except Exception:
        pass
    return f"omniverse://localhost/NVIDIA/Isaac/IsaacLab/{rel}".replace("\\", "/")


def resolve_usd_spec(spec: str, repo_root: Path | str) -> Tuple[str, str, bool]:
    rr = Path(repo_root)
    s = normalize_spec(spec)
    kind = classify_spec(s)
    if kind == "url":
        return "url", s, True
    p = Path(s)
    if not p.is_absolute():
        p = rr / s
    return "path", str(p), p.exists()


__all__ = ["normalize_spec", "classify_spec", "resolve_usd_spec", "isaaclab_asset_path"]
