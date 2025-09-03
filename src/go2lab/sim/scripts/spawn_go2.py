"""GO2 spawn/reset and simple velocity control utilities for Isaac Sim 5.0.
If no GO2 USD is found, spawn a placeholder multi-body box.
"""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import logging

from pxr import Usd, UsdGeom, Sdf, Gf

LOGGER = logging.getLogger("spawn_go2")

GO2_DEFAULT_PATH = "/World/Go2"
GO2_USD_ENV = "GO2_USD"
GO2_LOCAL_USD = "sim/usd/go2.usd"

MAX_LIN = 1.2
MAX_ANG = 1.5
DAMPING = 0.9


@dataclass
class VelocityCmd:
    vx: float = 0.0
    vy: float = 0.0
    wz: float = 0.0


def _resolve_go2_usd(repo_root: Path) -> tuple[str, str | None]:
    env = os.environ.get(GO2_USD_ENV)
    if env:
        try:
            from go2lab.sim.util.usd_path import resolve_usd_spec
            kind, target, ok = resolve_usd_spec(env, repo_root)
            if kind == "path":
                return ("path", target if ok else None)
            return (kind, target)
        except Exception:
            p = Path(env)
            return ("path", str(p) if p.exists() else None)
    local = repo_root / GO2_LOCAL_USD
    if local.exists():
        return ("path", str(local))
    return ("none", None)


def spawn_placeholder(stage: Usd.Stage, path: str = GO2_DEFAULT_PATH) -> Usd.Prim:
    base = UsdGeom.Capsule.Define(stage, Sdf.Path(path))
    base.AddTranslateOp().Set(Gf.Vec3f(0, 0, 0.4))
    base.AddScaleOp().Set(Gf.Vec3f(0.2, 0.2, 0.4))
    return base.GetPrim()


def spawn_go2(stage: Usd.Stage, repo_root: Path, path: str = GO2_DEFAULT_PATH) -> Usd.Prim:
    mode, target = _resolve_go2_usd(repo_root)
    if target is None:
        return spawn_placeholder(stage, path)
    prim = stage.DefinePrim(path, "Xform")
    prim.GetReferences().AddReference(target)
    return prim


def reset_pose(stage: Usd.Stage, prim_path: str = GO2_DEFAULT_PATH, pos=(0.0, 0.0, 0.45), yaw: float = 0.0) -> None:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim:
        return
    xform = UsdGeom.Xformable(prim)
    rot = Gf.Rotation(Gf.Vec3d(0, 0, 1), yaw)
    xf = Gf.Matrix4d().SetRotate(rot)
    xf.SetTranslate(Gf.Vec3d(*pos))
    xform.MakeMatrixXform().Set(xf)


class SimpleBaseController:
    def __init__(self, stage: Usd.Stage, prim_path: str = GO2_DEFAULT_PATH):
        self.stage = stage
        self.prim_path = prim_path
        self.cmd = VelocityCmd()
        self._vel = VelocityCmd()

    def set_cmd(self, vx: float, vy: float, wz: float) -> None:
        self.cmd.vx = max(min(vx, MAX_LIN), -MAX_LIN)
        self.cmd.vy = max(min(vy, MAX_LIN), -MAX_LIN)
        self.cmd.wz = max(min(wz, MAX_ANG), -MAX_ANG)

    def brake(self) -> None:
        self.cmd = VelocityCmd(0.0, 0.0, 0.0)
        self._vel = VelocityCmd(self._vel.vx * 0.5, self._vel.vy * 0.5, self._vel.wz * 0.5)

    def step(self, dt: float = 1.0 / 60.0) -> None:
        prim = self.stage.GetPrimAtPath(self.prim_path)
        if not prim:
            return
        xform = UsdGeom.Xformable(prim)
        self._vel.vx = DAMPING * self._vel.vx + (1 - DAMPING) * self.cmd.vx
        self._vel.vy = DAMPING * self._vel.vy + (1 - DAMPING) * self.cmd.vy
        self._vel.wz = DAMPING * self._vel.wz + (1 - DAMPING) * self.cmd.wz

        ops = xform.GetOrderedXformOps()
        mat = ops[0].GetOpTransform(0.0) if ops else Gf.Matrix4d(1.0)
        pos = Gf.Vec3d(mat.ExtractTranslation())
        yaw = 0.0
        yaw += self._vel.wz * dt
        pos += Gf.Vec3d(self._vel.vx * dt, self._vel.vy * dt, 0.0)
        rot = Gf.Rotation(Gf.Vec3d(0, 0, 1), yaw)
        new = Gf.Matrix4d().SetRotate(rot)
        new.SetTranslate(pos)
        xform.MakeMatrixXform().Set(new)


__all__ = ["spawn_go2", "reset_pose", "SimpleBaseController", "GO2_DEFAULT_PATH"]
