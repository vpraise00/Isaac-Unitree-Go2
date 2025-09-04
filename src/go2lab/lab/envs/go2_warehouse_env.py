"""Canonical GO2 warehouse test-double environment (under go2lab namespace)."""
from __future__ import annotations

import logging
from pathlib import Path
import os
from typing import Tuple

try:
    from isaacsim import SimulationApp  # type: ignore
except Exception:  # pragma: no cover - fallback for type checkers
    from isaacsim.simulation_app import SimulationApp  # type: ignore

from pxr import Usd  # type: ignore

from go2lab.core.managers import ActionManager, SensorManager, RewardManager, ActionSpec
from go2lab.sim.scripts.spawn_go2 import spawn_go2, SimpleBaseController
from go2lab.sim.util.kit import get_stage_and_backends
from go2lab.sim.util.usd_path import resolve_usd_spec, isaaclab_asset_path

LOGGER = logging.getLogger("lab.env.go2")


class Go2WarehouseEnv:
    def __init__(self, steps_per_episode: int = 200, headless: bool = False, action_spec: ActionSpec | None = None, control_hz: int = 60):
        self.steps_per_episode = steps_per_episode
        renderer = os.environ.get("ISAAC_RENDERER", "RayTracedLighting")
        self.app = SimulationApp({"headless": headless, "renderer": renderer})
        self.dt = 1.0 / max(1, int(control_hz))

        self.stage, self._open_stage, _set_on_demand = get_stage_and_backends()
        try:
            _set_on_demand()
        except Exception:
            pass

        repo_root = Path(__file__).resolve().parents[4]
        # Open warehouse USD (Isaac Lab style). Do not auto-generate a USD.
        try:
            wh_spec = os.environ.get("WAREHOUSE_USD", "") or isaaclab_asset_path("Environments/Simple_Warehouse/warehouse.usd")
            kind, target, ok = resolve_usd_spec(wh_spec, repo_root)
            if kind == "url":
                self._open_stage(target)
            else:
                p = Path(target)
                if p.exists():
                    self._open_stage(str(p))
                else:
                    LOGGER.error("Warehouse USD not found at local path: %s.", p)
                    raise FileNotFoundError(str(p))
        except Exception:
            # Non-fatal: continue with empty stage
            pass

        self.go2_prim = spawn_go2(self.stage, repo_root)
        self.ctrl = SimpleBaseController(self.stage, prim_path=self.go2_prim.GetPath().pathString)

        self.act_mgr = ActionManager(self.ctrl, action_spec or ActionSpec())
        self.sns_mgr = SensorManager(self.stage, self.go2_prim)
        self.rwd_mgr = RewardManager(self.act_mgr)

        self.t = 0

    def reset(self):
        self.t = 0
        self.ctrl.brake()
        return self.sns_mgr.observe(dt=self.dt)

    def step(self, action: Tuple[float, float, float]):
        self.act_mgr.apply(action)
        self.app.update()
        self.ctrl.step(dt=self.dt)
        obs = self.sns_mgr.observe(dt=self.dt)
        rew = self.rwd_mgr.compute(obs, action)
        self.t += 1
        done = self.t >= self.steps_per_episode
        return obs, rew["reward"], done, {"rewards": rew}

    def close(self):
        self.app.close()


__all__ = ["Go2WarehouseEnv"]
