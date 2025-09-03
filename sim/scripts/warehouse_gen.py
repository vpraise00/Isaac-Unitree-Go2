"""Shim: re-export warehouse generator from src/go2lab implementation to avoid duplication."""
from __future__ import annotations

from go2lab.sim.scripts.warehouse_gen import *  # type: ignore  # noqa: F401,F403
