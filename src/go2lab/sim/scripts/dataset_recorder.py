"""Dataset recording using isaacsim.replicator.writers (no legacy omni.replicator.isaac)."""
from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
import logging

try:
    from isaacsim import SimulationApp  # type: ignore
except Exception:
    from isaacsim.simulation_app import SimulationApp  # type: ignore

from pxr import Usd, Sdf, Gf, UsdGeom
from isaacsim.replicator import writers as rep_writers
from isaacsim.replicator import core as rep_core

from go2lab.sim.scripts.spawn_go2 import spawn_go2, SimpleBaseController
from go2lab.sim.util.usd_path import resolve_usd_spec, isaaclab_asset_path
from go2lab.sim.util.kit import get_stage_and_backends
import carb

LOGGER = logging.getLogger("recorder")

OUT_ROOT = Path("output")
FPS = float(os.environ.get("REC_FPS", "20"))
WIDTH = int(os.environ.get("REC_WIDTH", "640"))
HEIGHT = int(os.environ.get("REC_HEIGHT", "480"))
ATTACH_TO_GO2 = os.environ.get("REC_ATTACH_TO_GO2", "1") == "1"
CHANNELS = os.environ.get("REC_CHANNELS", "rgb,depth,semantic,instance").split(",")
DURATION_SEC = float(os.environ.get("REC_DURATION_SEC", "30"))

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

MAX_VX = float(os.environ.get("REC_MAX_VX", "1.0"))
MAX_VY = float(os.environ.get("REC_MAX_VY", "0.6"))
MAX_WZ = float(os.environ.get("REC_MAX_WZ", "1.2"))


def setup_camera(stage: Usd.Stage, target_prim: Usd.Prim | None) -> Usd.Prim:
    cam_path = "/World/Cameras/Cam_0"
    cam = UsdGeom.Camera.Define(stage, Sdf.Path(cam_path))
    if target_prim is not None:
        UsdGeom.Xformable(cam.GetPrim()).AddTranslateOp().Set(Gf.Vec3f(0.3, 0.0, 0.25))
    else:
        UsdGeom.Xformable(cam.GetPrim()).AddTranslateOp().Set(Gf.Vec3f(-1.5, 0.0, 1.2))
    return cam.GetPrim()


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = OUT_ROOT / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    app = SimulationApp({"headless": False})
    try:
        stage, open_stage, set_on_demand = get_stage_and_backends()

        repo_root = Path(__file__).resolve().parents[4]
        wh_spec = os.environ.get("WAREHOUSE_USD", "") or isaaclab_asset_path("Environments/Simple_Warehouse/warehouse.usd")
        try:
            kind, target, ok = resolve_usd_spec(wh_spec, repo_root)
            if kind == "url":
                open_stage(target)
            elif kind == "path" and target:
                p = Path(target)
                if p.exists():
                    open_stage(str(p))
        except Exception:
            pass

        go2_prim = spawn_go2(stage, repo_root)
        ctrl = SimpleBaseController(stage, prim_path=go2_prim.GetPath().pathString)

        cam_prim = setup_camera(stage, go2_prim if ATTACH_TO_GO2 else None)

        try:
            set_on_demand()
        except Exception:
            pass

        rp = rep_core.create_render_product(str(cam_prim.GetPath()), resolution=(WIDTH, HEIGHT))
        writer = rep_writers.get("BasicWriter")
        out_dir_str = str(out_dir.resolve())
        writer.initialize(output_dir=out_dir_str, rgb="rgb" in CHANNELS, depth="depth" in CHANNELS,
                          semantic_segmentation="semantic" in CHANNELS, instance_segmentation="instance" in CHANNELS)
        writer.attach([rp])

        inp = carb.input.acquire_input_interface()
        kb = inp.get_keyboard()

        meta_path = out_dir / "meta.jsonl"
        with meta_path.open("w", encoding="utf-8") as meta_file:
            frames = int(DURATION_SEC * FPS)
            for i in range(frames):
                boost = inp.is_key_down(kb, KEY_MAP["boost"]) if kb else False
                spd = 1.5 if boost else 1.0
                vx = (1.0 if inp.is_key_down(kb, KEY_MAP["forward"]) else 0.0) - (1.0 if inp.is_key_down(kb, KEY_MAP["back"]) else 0.0)
                vy = (1.0 if inp.is_key_down(kb, KEY_MAP["right"]) else 0.0) - (1.0 if inp.is_key_down(kb, KEY_MAP["left"]) else 0.0)
                wz = (1.0 if inp.is_key_down(kb, KEY_MAP["yaw_left"]) else 0.0) - (1.0 if inp.is_key_down(kb, KEY_MAP["yaw_right"]) else 0.0)
                ctrl.set_cmd(vx * MAX_VX * spd, vy * MAX_VY * spd, wz * MAX_WZ * spd)

                app.update()
                ctrl.step(dt=1.0 / FPS)

                meta = {
                    "frame": i,
                    "camera": cam_prim.GetPath().pathString,
                    "go2": go2_prim.GetPath().pathString,
                }
                meta_file.write(json.dumps(meta) + "\n")
        return 0
    except Exception as e:
        LOGGER.exception("Recorder failed: %s", e)
        return 1
    finally:
        app.close()


if __name__ == "__main__":
    import sys
    raise SystemExit(main())
