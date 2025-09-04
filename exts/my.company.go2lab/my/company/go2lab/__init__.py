"""Extension on_startup: prepare stage, build/load warehouse, spawn GO2, set On Demand compute.

USD path resolution follows the same rules as src/go2lab/sim/scripts/run_sim.py:
- Env var WAREHOUSE_USD may be an Omniverse URL or a local path.
- If not provided, defaults to the Isaac Lab Simple Warehouse on Nucleus.
This implementation avoids legacy isaacsim.core.* imports and toggles OmniGraph compute via carb settings.
"""
from __future__ import annotations

import logging
from pathlib import Path
import os
import sys

from pxr import Usd  # type: ignore
import omni.usd as ou  # type: ignore
import carb  # type: ignore

# Ensure repo root on sys.path before importing local sim modules
# File path depth: <repo>/exts/my.company.go2lab/my/company/go2lab/__init__.py
# parents[5] == <repo>
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))
# Also add src/ to import path for go2lab.* package
_SRC_ROOT = _REPO_ROOT / "src"
if _SRC_ROOT.exists() and str(_SRC_ROOT) not in sys.path:
    sys.path.append(str(_SRC_ROOT))

from go2lab.sim.scripts.spawn_go2 import spawn_go2  # type: ignore
from go2lab.sim.util.usd_path import isaaclab_asset_path  # type: ignore

LOGGER = logging.getLogger("go2lab.ext")


def on_startup(ext_id: str):  # type: ignore[override]
    ctx = ou.get_context()
    stage: Usd.Stage = ctx.get_stage()

    repo_root = _REPO_ROOT
    # Resolve warehouse USD path from env or default to Isaac Lab Simple Warehouse on Nucleus
    spec = (os.environ.get("WAREHOUSE_USD", "") or isaaclab_asset_path("Environments/Simple_Warehouse/warehouse.usd")).replace("\\", "/")
    try:
        # Filesystem path: absolute or repo-relative; otherwise treat as URL
        candidate = Path(spec)
        usd_path = candidate if candidate.is_absolute() else (repo_root / spec)
        if usd_path.exists():
            LOGGER.info("[ext] Opening local USD: %s", usd_path)
            ctx.open_stage(str(usd_path))
            stage = ctx.get_stage()
        else:
            LOGGER.info("[ext] Opening USD from URL: %s", spec)
            ctx.open_stage(spec)
            stage = ctx.get_stage()
    except Exception as e:
        LOGGER.error("[ext] Warehouse setup failed: %s", e)

    # Enable on-demand compute via settings
    try:
        settings = carb.settings.get_settings()  # type: ignore[attr-defined]
        settings.set_string("/omni/graph/computeMode", "on_demand")
    except Exception as e:
        LOGGER.warning("Failed to set On Demand compute: %s", e)

    spawn_go2(stage, repo_root)


def on_shutdown():  # type: ignore[override]
    pass
