from __future__ import annotations

import os
import logging
from pathlib import Path

from go2lab.world import open_warehouse

LOGGER = logging.getLogger("test_runner")


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    renderer = os.environ.get("ISAAC_RENDERER", "RayTracedLighting")
    headless = os.environ.get("HEADLESS", "0") == "1"
    try:
        from isaacsim import SimulationApp  # type: ignore
    except Exception:
        from isaacsim.simulation_app import SimulationApp  # type: ignore
    app = SimulationApp({"headless": headless, "renderer": renderer})
    try:
        from go2lab.sim.util.kit import get_stage_and_backends
        from go2lab.sim.scripts.spawn_go2 import spawn_go2, SimpleBaseController, reset_pose

        stage, open_stage, set_on_demand = get_stage_and_backends()
        try:
            set_on_demand()
        except Exception:
            pass

        repo_root = Path(__file__).resolve().parents[4]
        try:
            open_warehouse(open_stage, repo_root, strict_missing=False, logger=LOGGER)
        except Exception:
            LOGGER.exception("Failed to open environment; continuing with current stage")

        # Always spawn GO2
        go2_prim = spawn_go2(stage, repo_root)

        # Apply initial pose
        def _getf(name: str, default: float) -> float:
            try:
                return float(os.environ.get(name, str(default)))
            except Exception:
                return default

        ix = _getf("GO2_INIT_X", 0.0)
        iy = _getf("GO2_INIT_Y", 0.0)
        iz = _getf("GO2_INIT_Z", 0.45)
        iyaw = _getf("GO2_INIT_YAW", 0.0)
        reset_pose(stage, prim_path=go2_prim.GetPath().pathString, pos=(ix, iy, iz), yaw=iyaw)

        ctrl = SimpleBaseController(stage, prim_path=go2_prim.GetPath().pathString)
        ckpt = os.environ.get("CHECKPOINT_PATH")
        task = os.environ.get("TASK_NAME")
        LOGGER.info("[TEST] checkpoint=%s, task=%s", ckpt, task)

        for _ in range(1000):
            try:
                app.update()
            except Exception:
                pass
            ctrl.step(dt=1.0/60.0)
        return 0
    finally:
        try:
            app.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
