# Wrapper to import world helpers from legacy location
from __future__ import annotations

from pathlib import Path
from typing import Callable

from .sim.util.usd_path import resolve_usd_spec
from .config import get_warehouse_spec



def open_warehouse(open_stage: Callable[[str], None], repo_root: Path, spec: str | None = None,
				   strict_missing: bool = False, logger=None) -> bool:
	effective = (spec or get_warehouse_spec()).strip()
	if effective.lower() in ("", "empty", "none"):
		if logger:
			logger.info("No environment specified (spec='%s'); skipping stage open.", effective)
		return False
	kind, target, ok = resolve_usd_spec(effective, repo_root)
	if kind == "url":
		if logger:
			logger.info("Opening stage from URL: %s", target)
		open_stage(target)
		return True
	p = Path(target)
	if p.exists():
		if logger:
			logger.info("Opening local stage: %s", p)
		open_stage(str(p))
		return True
	if strict_missing:
		if logger:
			logger.error("Warehouse USD not found at local path: %s", p)
		raise FileNotFoundError(str(p))
	if logger:
		logger.error("Warehouse USD not found at local path: %s", p)
	return False


__all__ = ["open_warehouse"]
