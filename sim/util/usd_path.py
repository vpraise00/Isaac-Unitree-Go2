"""Utilities for resolving USD path specs consistently (URLs/local paths) and
constructing Isaac Lab Nucleus paths like the upstream project.

Designed to mirror Isaac Lab behavior:
- Supports omniverse/HTTP(S) URLs and local filesystem paths.
- Expands environment variables and normalizes slashes.
- Joins relative paths against the provided repo_root when given a relative path.
- Provides ``isaaclab_asset_path()`` that builds URLs using the configured Nucleus root
    setting (``/persistent/isaac/asset_root/cloud``) → ``<root>/Isaac/IsaacLab/<rel>``.
"""
from __future__ import annotations

# Backward-compatible re-exports to go2lab implementation
from go2lab.sim.util.usd_path import (  # type: ignore
    normalize_spec,
    classify_spec,
    resolve_usd_spec,
    isaaclab_asset_path,
)

__all__ = ["normalize_spec", "classify_spec", "resolve_usd_spec", "isaaclab_asset_path"]
