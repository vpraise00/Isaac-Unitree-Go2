"""Keyboard teleoperation for GO2 via carb.input (Isaac Sim 5.0 namespaces)."""
from __future__ import annotations

import os
import logging
from pathlib import Path
import sys

try:
    from isaacsim import SimulationApp  # type: ignore
except Exception:
    from isaacsim.simulation_app import SimulationApp  # type: ignore

import carb

from go2lab.sim.scripts.spawn_go2 import spawn_go2, SimpleBaseController
from go2lab.world import open_warehouse
from go2lab.sim.util.kit import get_stage_and_backends

LOGGER = logging.getLogger("teleop")

MAX_VX = float(os.environ.get("TELEOP_MAX_VX", "1.2"))
MAX_VY = float(os.environ.get("TELEOP_MAX_VY", "0.8"))
MAX_WZ = float(os.environ.get("TELEOP_MAX_WZ", "1.5"))

KEY_MAP = {
    "forward": carb.input.KeyboardInput.W,
    "back": carb.input.KeyboardInput.S,
    "left": carb.input.KeyboardInput.A,
    "right": carb.input.KeyboardInput.D,
    "yaw_left": carb.input.KeyboardInput.LEFT,
    "yaw_right": carb.input.KeyboardInput.RIGHT,
    "brake": carb.input.KeyboardInput.SPACE,
    "boost": carb.input.KeyboardInput.LEFT_SHIFT,
}


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    app = SimulationApp({"headless": False})
    try:
        stage, open_stage, set_on_demand = get_stage_and_backends()
        try:
            set_on_demand()
        except Exception:
            pass

        repo_root = Path(__file__).resolve().parents[4]
        try:
            open_warehouse(open_stage, repo_root, strict_missing=False, logger=LOGGER)
        except Exception:
            pass

        go2_prim = spawn_go2(stage, repo_root)
        ctrl = SimpleBaseController(stage, prim_path=go2_prim.GetPath().pathString)

        inp = carb.input.acquire_input_interface()
        kb = inp.get_keyboard()

        LOGGER.info("WASD move, arrows yaw, Space brake, Shift boost")
        for _ in range(100000):
            boost = inp.is_key_down(kb, KEY_MAP["boost"]) if kb else False
            spd = 1.5 if boost else 1.0
            vx = (1.0 if inp.is_key_down(kb, KEY_MAP["forward"]) else 0.0) - (1.0 if inp.is_key_down(kb, KEY_MAP["back"]) else 0.0)
            vy = (1.0 if inp.is_key_down(kb, KEY_MAP["right"]) else 0.0) - (1.0 if inp.is_key_down(kb, KEY_MAP["left"]) else 0.0)
            wz = (1.0 if inp.is_key_down(kb, KEY_MAP["yaw_left"]) else 0.0) - (1.0 if inp.is_key_down(kb, KEY_MAP["yaw_right"]) else 0.0)
            ctrl.set_cmd(vx * MAX_VX * spd, vy * MAX_VY * spd, wz * MAX_WZ * spd)

            app.update()
            ctrl.step(dt=1.0 / 60.0)
        return 0
    except Exception as e:
        LOGGER.exception("Teleop failed: %s", e)
        return 1
    finally:
        app.close()


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
