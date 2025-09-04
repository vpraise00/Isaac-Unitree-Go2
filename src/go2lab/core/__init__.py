"""go2lab.core public API.

Canonical, dependency-light building blocks used by lab and sim layers.
"""
from __future__ import annotations

from .managers import ActionSpec, ActionManager, SensorManager, RewardManager

__all__ = [
    "ActionSpec",
    "ActionManager",
    "SensorManager",
    "RewardManager",
]
