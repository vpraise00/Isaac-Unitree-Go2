"""Minimal manager-based test double for Isaac Lab 2.2 style tasks.

This does NOT depend on Isaac Lab runtime. It mirrors the idea of managers:
- ActionManager: scales/clamps actions and applies to controller
- SensorManager: builds observation dict from USD transform, computes vel/height/quat
- RewardManager: combines forward progress, smoothness, survive, lateral penalty, uprightness

Environment runs in Isaac Sim 5.0 via our existing sim scripts/utilities.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import math

from pxr import UsdGeom, Gf  # type: ignore


@dataclass
class ActionSpec:
    scale_lin_xy: float = 0.5
    scale_yaw: float = 0.8


class ActionManager:
    def __init__(self, controller, spec: ActionSpec):
        self.ctrl = controller
        self.spec = spec
        self.prev_action = (0.0, 0.0, 0.0)

    def apply(self, action):
        # action = [ax, ay, ayaw] in [-1, 1]
        ax = max(min(action[0], 1.0), -1.0) * self.spec.scale_lin_xy
        ay = max(min(action[1], 1.0), -1.0) * self.spec.scale_lin_xy
        ayaw = max(min(action[2], 1.0), -1.0) * self.spec.scale_yaw
        self.ctrl.set_cmd(ax, ay, ayaw)
        self.prev_action = (ax, ay, ayaw)


class SensorManager:
    def __init__(self, stage, base_prim):
        self.stage = stage
        self.base = base_prim
        self._prev_pos: Gf.Vec3d | None = None
        self._prev_yaw: float | None = None

    @staticmethod
    def _yaw_from_mat(m: Gf.Matrix4d) -> float:
        # yaw from rotation matrix (z-up)
        # m = [ [r00 r01 r02 ...], [r10 r11 r12 ...], ... ]
        r00 = m[0][0]
        r10 = m[1][0]
        return math.atan2(r10, r00)

    def _read_transform(self) -> Gf.Matrix4d:
        xform = UsdGeom.Xformable(self.base)
        ops = xform.GetOrderedXformOps()
        if ops:
            try:
                return ops[0].GetOpTransform(0.0)
            except Exception:
                pass
        return Gf.Matrix4d(1.0)

    def observe(self, dt: float) -> Dict[str, Any]:
        m = self._read_transform()
        pos = Gf.Vec3d(m.ExtractTranslation())
        yaw = self._yaw_from_mat(m)
        # up vector = third column of rotation (assuming z-up)
        up = Gf.Vec3d(m[0][2], m[1][2], m[2][2])
        up_dot = float(up.GetNormalized().Dot(Gf.Vec3d(0, 0, 1))) if up.GetLength() > 1e-6 else 1.0

        if self._prev_pos is None:
            lin = Gf.Vec3d(0, 0, 0)
            ang_z = 0.0
        else:
            dpos = pos - self._prev_pos
            dyaw = yaw - (self._prev_yaw or 0.0)
            # wrap yaw diff to [-pi, pi]
            dyaw = (dyaw + math.pi) % (2 * math.pi) - math.pi
            lin = dpos / max(dt, 1e-6)
            ang_z = dyaw / max(dt, 1e-6)

        self._prev_pos = pos
        self._prev_yaw = yaw

        # imu quaternion: yaw-only approximation
        half = 0.5 * yaw
        imu_quat = (0.0, 0.0, math.sin(half), math.cos(half))

        return {
            "base_lin_vel": (float(lin[0]), float(lin[1]), float(lin[2])),
            "base_ang_vel": (0.0, 0.0, float(ang_z)),
            "base_height": float(pos[2]),
            "imu_quat": imu_quat,
            "up_dot": up_dot,
            "yaw": float(yaw),
            "pos": (float(pos[0]), float(pos[1]), float(pos[2])),
        }


class RewardManager:
    def __init__(self, action_mgr: ActionManager | None = None):
        self.action_mgr = action_mgr
        self._prev_action = (0.0, 0.0, 0.0)

    def compute(self, obs: Dict[str, Any], action) -> Dict[str, float]:
        # weights (can be tuned)
        w_survive = 0.01
        w_forward = 0.05
        w_smooth = 0.002
        w_lat_pen = 0.02
        w_upright = 0.02

        survive_bonus = w_survive
        forward_progress = w_forward * max(obs.get("base_lin_vel", (0, 0, 0))[0], 0.0)
        # smoothness based on delta action (scaled commands after ActionManager)
        prev = getattr(self.action_mgr, "prev_action", self._prev_action) if self.action_mgr else self._prev_action
        da0 = action[0] - prev[0]
        da1 = action[1] - prev[1]
        da2 = action[2] - prev[2]
        smoothness = -w_smooth * (da0 * da0 + da1 * da1 + da2 * da2)
        lateral_pen = -w_lat_pen * abs(obs.get("base_lin_vel", (0, 0, 0))[1])
        upright = w_upright * max(0.0, obs.get("up_dot", 1.0))

        total = survive_bonus + forward_progress + smoothness + lateral_pen + upright
        self._prev_action = action
        return {
            "survive_bonus": survive_bonus,
            "forward_progress": forward_progress,
            "smoothness": smoothness,
            "lateral_pen": lateral_pen,
            "upright": upright,
            "reward": total,
        }
