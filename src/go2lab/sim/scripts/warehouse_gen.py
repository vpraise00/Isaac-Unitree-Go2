"""Procedural warehouse generator (Isaac Sim 5.0 namespaces)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import logging

from pxr import Usd, UsdGeom, UsdPhysics, Sdf, Gf

LOGGER = logging.getLogger("warehouse_gen")

AISLE_WIDTH = 2.0
RACK_SPACING = 4.0
FLOOR_SIZE = (20.0, 20.0)
WALL_HEIGHT = 3.0


def _add_physics_scene(stage: Usd.Stage) -> None:
    UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))


def _add_ground(stage: Usd.Stage) -> None:
    ground = UsdGeom.Mesh.Define(stage, Sdf.Path("/World/Ground"))
    size_x, size_y = FLOOR_SIZE
    vertices = [
        Gf.Vec3f(-size_x / 2, -size_y / 2, 0.0),
        Gf.Vec3f(size_x / 2, -size_y / 2, 0.0),
        Gf.Vec3f(size_x / 2, size_y / 2, 0.0),
        Gf.Vec3f(-size_x / 2, size_y / 2, 0.0),
    ]
    ground.CreatePointsAttr(vertices)
    ground.CreateFaceVertexCountsAttr([4])
    ground.CreateFaceVertexIndicesAttr([0, 1, 2, 3])


def _add_wall(stage: Usd.Stage, path: str, p0: Gf.Vec3f, p1: Gf.Vec3f) -> None:
    wall = UsdGeom.Cube.Define(stage, Sdf.Path(path))
    length = (p1 - p0).GetLength()
    wall_size = Gf.Vec3f(length, 0.1, WALL_HEIGHT)
    wall.AddTranslateOp().Set((p0 + p1) * 0.5 + Gf.Vec3f(0, 0, WALL_HEIGHT / 2))
    wall.AddScaleOp().Set(wall_size)


def _add_rack(stage: Usd.Stage, path: str, center: Gf.Vec3f) -> None:
    rack = UsdGeom.Cube.Define(stage, Sdf.Path(path))
    rack.AddTranslateOp().Set(center + Gf.Vec3f(0, 0, 1.0))
    rack.AddScaleOp().Set(Gf.Vec3f(0.6, 2.0, 2.0))


def _add_box(stage: Usd.Stage, path: str, center: Gf.Vec3f) -> None:
    box = UsdGeom.Cube.Define(stage, Sdf.Path(path))
    box.AddTranslateOp().Set(center + Gf.Vec3f(0, 0, 0.25))
    box.AddScaleOp().Set(Gf.Vec3f(0.5, 0.5, 0.5))


def build_warehouse(stage: Usd.Stage, save_usd_path: Optional[Path] = None) -> Optional[Path]:
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)

    _add_physics_scene(stage)
    _add_ground(stage)

    size_x, size_y = FLOOR_SIZE
    _add_wall(stage, "/World/Walls/West", Gf.Vec3f(-size_x/2, -size_y/2, 0), Gf.Vec3f(-size_x/2, size_y/2, 0))
    _add_wall(stage, "/World/Walls/East", Gf.Vec3f(size_x/2, -size_y/2, 0), Gf.Vec3f(size_x/2, size_y/2, 0))
    _add_wall(stage, "/World/Walls/South", Gf.Vec3f(-size_x/2, -size_y/2, 0), Gf.Vec3f(size_x/2, -size_y/2, 0))
    _add_wall(stage, "/World/Walls/North", Gf.Vec3f(-size_x/2, size_y/2, 0), Gf.Vec3f(size_x/2, size_y/2, 0))

    y = -size_y/2 + RACK_SPACING
    idx = 0
    while y < size_y/2 - RACK_SPACING:
        _add_rack(stage, f"/World/Racks/Rack_{idx}_L", Gf.Vec3f(-AISLE_WIDTH, y, 0))
        _add_rack(stage, f"/World/Racks/Rack_{idx}_R", Gf.Vec3f(AISLE_WIDTH, y, 0))
        y += RACK_SPACING
        idx += 1

    _add_box(stage, "/World/Boxes/Box_0", Gf.Vec3f(0.0, 0.0, 0.0))
    _add_box(stage, "/World/Boxes/Box_1", Gf.Vec3f(1.0, 1.0, 0.0))

    if save_usd_path:
        save_usd_path.parent.mkdir(parents=True, exist_ok=True)
        stage.GetRootLayer().Export(str(save_usd_path))
        LOGGER.info("Warehouse saved: %s", save_usd_path)
        return save_usd_path
    return None
