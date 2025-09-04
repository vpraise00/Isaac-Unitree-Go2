"""Run an external Isaac Lab 2.2 manager-based task module under Isaac Sim 5.0.

This wrapper avoids copying Isaac Lab. Point it to your local Isaac Lab 2.2 repo.
"""
from __future__ import annotations

import argparse
import json
import logging
import runpy
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("lab.run_lab2")


def _repo_root() -> Path:
    # src/go2lab/lab/scripts -> repo
    return Path(__file__).resolve().parents[4]


DEFAULT_CFG = _repo_root() / "configs/lab2_config.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--task-module", required=True, help="Python module path to run (e.g., omni.isaac.lab_tasks.manager_based.locomotion.run)")
    p.add_argument("--lab-path", default=None, help="Path to Isaac Lab 2.2 repo (overrides lab2_config.json)")
    p.add_argument("--headless", action="store_true", help="Run Isaac Sim headless")
    p.add_argument("--no-preload-app", action="store_true", help="Do not create SimulationApp before running module")
    return p.parse_args()


def load_lab_path(cli_value: str | None) -> Path | None:
    if cli_value:
        return Path(cli_value)
    if DEFAULT_CFG.exists():
        try:
            cfg = json.loads(DEFAULT_CFG.read_text(encoding="utf-8"))
            if isinstance(cfg, dict) and cfg.get("lab_repo"):
                return Path(cfg["lab_repo"]).expanduser()
        except Exception as e:
            LOGGER.warning("Failed to parse %s: %s", DEFAULT_CFG, e)
    return None


def main() -> int:
    args = parse_args()

    # Ensure repo root is importable (for our go2lab.* modules if needed)
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))

    lab_repo = load_lab_path(args.lab_path)
    if lab_repo is None or not lab_repo.exists():
        LOGGER.error("Isaac Lab repo path not found. Provide --lab-path or set lab2_config.json 'lab_repo'.")
        return 2

    # Add Isaac Lab repo to PYTHONPATH
    sys.path.append(str(lab_repo))

    # Import SimulationApp lazily if requested
    app = None
    if not args.no_preload_app:
        try:
            try:
                from isaacsim import SimulationApp  # type: ignore
            except Exception:
                from isaacsim.simulation_app import SimulationApp  # type: ignore
            import os
            renderer = os.environ.get("ISAAC_RENDERER", "RayTracedLighting")
            app = SimulationApp({"headless": bool(args.headless), "renderer": renderer})
            LOGGER.info("SimulationApp created (headless=%s)", bool(args.headless))
        except Exception as e:
            LOGGER.error("Failed to create SimulationApp: %s", e)
            return 3

    try:
        LOGGER.info("Running Isaac Lab module: %s", args.task_module)
        runpy.run_module(args.task_module, run_name="__main__")
        return 0
    except SystemExit as se:
        code = int(getattr(se, "code", 0) or 0)
        LOGGER.info("Module exited with code=%s", code)
        return code
    except Exception as e:
        LOGGER.exception("Module run failed: %s", e)
        return 1
    finally:
        if app is not None:
            try:
                app.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
