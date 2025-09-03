# Wrapper to import kit helpers from legacy location
"""Isaac Sim 5.0 helpers to get/open stage and set on-demand compute (packaged)."""
from __future__ import annotations

from typing import Callable, Tuple


def get_stage_and_backends():
	try:
		from isaacsim.core.api import core as core_api  # type: ignore
		from pxr import Usd  # noqa: F401

		core = core_api.get_core()
		stage = core.get_stage()

		def _open(uri: str) -> None:
			core.open_stage(uri)  # type: ignore[attr-defined]

		def _on_demand() -> None:
			try:
				from isaacsim.core.nodes import og  # type: ignore
				og.set_compute_mode("on_demand")
			except Exception:
				pass

		return stage, _open, _on_demand
	except Exception:
		pass

	import omni.usd as ou  # type: ignore

	ctx = ou.get_context()
	stage = ctx.get_stage()

	def _open(uri: str) -> None:
		ctx.open_stage(uri)

	def _on_demand() -> None:
		try:
			from isaacsim.core.nodes import og  # type: ignore
			og.set_compute_mode("on_demand")
		except Exception:
			pass

	return stage, _open, _on_demand


__all__ = ["get_stage_and_backends"]
