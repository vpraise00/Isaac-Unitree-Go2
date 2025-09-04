"""Keyboard teleoperation for GO2 via carb.input (Isaac Sim 5.0 namespaces).

Notes:
- Imports of carb/pxr happen only after SimulationApp starts to avoid preloading warnings.
- If environment variable EMPTY_STAGE=1 or WAREHOUSE_USD is 'empty'/'none', a blank stage is created.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
import sys

from go2lab.world import open_warehouse

LOGGER = logging.getLogger("teleop")

MAX_VX = float(os.environ.get("TELEOP_MAX_VX", "1.2"))
MAX_VY = float(os.environ.get("TELEOP_MAX_VY", "0.8"))
MAX_WZ = float(os.environ.get("TELEOP_MAX_WZ", "1.5"))

KEY_MAP = None  # populated after carb import


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    renderer = os.environ.get("ISAAC_RENDERER", "RayTracedLighting")
    headless = os.environ.get("HEADLESS", "0") == "1"
    # Ensure EXP_PATH exists to avoid SimulationApp KeyError in some configurations
    try:
        _ = os.environ["EXP_PATH"]
    except KeyError:
        exp_dir = Path(__file__).resolve().parents[4] / "_exp"
        try:
            exp_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        os.environ["EXP_PATH"] = str(exp_dir)
    created_app = False
    app = None
    # If Kit is already running (we were launched via --exec), don't create a new SimulationApp
    # Detect by trying to import omni.kit.app first
    try:
        import omni.kit.app as kit_app  # type: ignore
        app = kit_app.get_app()
    except Exception:
        pass
    if app is None:
        # Create a SimulationApp instance if not already running
        try:
            from isaacsim import SimulationApp  # type: ignore
        except Exception:
            from isaacsim.simulation_app import SimulationApp  # type: ignore
        app = SimulationApp({"headless": headless, "renderer": renderer})
        created_app = True
    try:
        import carb  # import after SimulationApp is initialized
        # Import modules that bring in pxr only after SimulationApp has started
        from go2lab.sim.util.kit import get_stage_and_backends
        from go2lab.sim.scripts.spawn_go2 import spawn_go2, SimpleBaseController, reset_pose

        stage, open_stage, set_on_demand = get_stage_and_backends()
        try:
            set_on_demand()
        except Exception:
            pass

        repo_root = Path(__file__).resolve().parents[4]
        try:
            if os.environ.get("EMPTY_STAGE", "0") == "1" or (os.environ.get("WAREHOUSE_USD", "").strip().lower() in ("empty", "none")):
                # Create a blank stage for smoke testing
                LOGGER.info("Creating new empty stage (no environment loaded)")
                import omni.usd as ou  # type: ignore
                ctx = ou.get_context()
                ctx.new_stage()
                stage = ctx.get_stage()
            else:
                open_warehouse(open_stage, repo_root, strict_missing=False, logger=LOGGER)
        except Exception:
            LOGGER.exception("Failed to open environment; continuing with current stage")

        # Always spawn GO2; input may be disabled separately
        go2_prim = spawn_go2(stage, repo_root)
        # Apply initial pose (env-configurable)
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

        # setup keyboard map now that carb is available
        global KEY_MAP
        try:
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
        except Exception:
            KEY_MAP = None

        try:
            inp = carb.input.acquire_input_interface()
        except Exception:
            inp = None
        # get_keyboard is not present in Isaac Sim 5.0; use device API
        try:
            kb = carb.input.Keyboard
        except Exception:
            kb = None

        skip_input = os.environ.get("SKIP_INPUT", "0") == "1"
        if not skip_input and KEY_MAP is not None and inp is not None:
            LOGGER.info("WASD move, arrows yaw, Space brake, Shift boost")
        else:
            LOGGER.info("Input disabled: rendering only. GO2 spawned at %s", go2_prim.GetPath().pathString)
        for _ in range(100000):
            if not skip_input and kb is not None and KEY_MAP is not None and inp is not None:
                # Isaac Sim 5.0 uses virtual keys state via input interface
                def _down(code):
                    try:
                        return inp.is_key_down(0, code)  # deviceId 0 = system keyboard
                    except Exception:
                        return False
                boost = _down(KEY_MAP["boost"]) if kb else False
                spd = 1.5 if boost else 1.0
                vx = (1.0 if _down(KEY_MAP["forward"]) else 0.0) - (1.0 if _down(KEY_MAP["back"]) else 0.0)
                vy = (1.0 if _down(KEY_MAP["right"]) else 0.0) - (1.0 if _down(KEY_MAP["left"]) else 0.0)
                wz = (1.0 if _down(KEY_MAP["yaw_left"]) else 0.0) - (1.0 if _down(KEY_MAP["yaw_right"]) else 0.0)
                ctrl.set_cmd(vx * MAX_VX * spd, vy * MAX_VY * spd, wz * MAX_WZ * spd)

            # Update the app/frame
            try:
                if created_app:
                    app.update()
                else:
                    # If we didn't create SimulationApp, tick the existing kit app
                    import omni.kit.app as kit_app  # type: ignore
                    kit_app.get_app().update()
            except Exception:
                pass
            ctrl.step(dt=1.0 / 60.0)
        return 0
    except Exception as e:
        LOGGER.exception("Teleop failed: %s", e)
        return 1
    finally:
        try:
            if created_app and app is not None:
                app.close()
        except Exception:
            pass


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
