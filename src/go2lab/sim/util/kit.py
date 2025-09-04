"""Isaac Sim 5.0 helpers for stage access and OmniGraph compute mode.

This module avoids legacy, pre-5.0 APIs and uses carb settings to enable on-demand compute.
"""
from __future__ import annotations

from typing import Callable, Tuple


def get_stage_and_backends():
	import omni.usd as ou  # type: ignore

	ctx = ou.get_context()
	stage = ctx.get_stage()

	def _open(uri: str) -> None:
		ctx.open_stage(uri)

	def _on_demand() -> None:
		# Preferred path: set OmniGraph compute mode via carb settings
		try:
			import carb  # type: ignore

			settings = carb.settings.get_settings()  # type: ignore[attr-defined]
			# Known settings path for OmniGraph compute mode
			settings.set_string("/omni/graph/computeMode", "on_demand")
		except Exception:
			# Best-effort: ignore if unavailable
			pass

	return stage, _open, _on_demand


__all__ = ["get_stage_and_backends"]
