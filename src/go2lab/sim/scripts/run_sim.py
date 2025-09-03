"""Run Isaac Sim 5.0 GUI, load default warehouse, and step a few frames."""
from __future__ import annotations

import os
import logging
from pathlib import Path

try:
    from isaacsim import SimulationApp  # type: ignore
except Exception:
    from isaacsim.simulation_app import SimulationApp  # type: ignore

from go2lab.config import get_warehouse_spec
from go2lab.sim.util.usd_path import resolve_usd_spec
from go2lab.sim.util.kit import get_stage_and_backends

DEFAULT_STEPS = int(os.environ.get("SIM_MIN_STEPS", "240"))
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
LOGGER = logging.getLogger("run_sim")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[4]
    spec = get_warehouse_spec()
    kind, target, ok = resolve_usd_spec(spec, repo_root)
    stage_path = Path(target) if kind == "path" else None

    app_args = {"headless": False, "renderer": "RayTracedLighting"}
    if stage_path is not None and stage_path.exists():
        app_args["open_usd"] = str(stage_path)
    sim_app = SimulationApp(app_args)

    try:
        stage, open_stage, set_on_demand = get_stage_and_backends()
        try:
            set_on_demand()
        except Exception:
            pass

        if kind == "url":
            try:
                LOGGER.info("Opening stage from URL: %s", target)
                open_stage(target)
            except Exception as e:
                LOGGER.error("Could not open URL stage '%s': %s", target, e)

        if kind == "path" and (stage_path is not None) and (not stage_path.exists()):
            LOGGER.error("Warehouse USD not found at local path: %s.", stage_path)
            return 2

        steps = max(DEFAULT_STEPS, 1)
        for _ in range(steps):
            sim_app.update()
        return 0
    except Exception as exc:
        LOGGER.exception("Simulation failed: %s", exc)
        return 1
    finally:
        sim_app.close()


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
