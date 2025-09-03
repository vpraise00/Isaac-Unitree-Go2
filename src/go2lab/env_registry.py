# Wrapper to import env registry from legacy location
from __future__ import annotations

from pathlib import Path
from typing import Tuple

from .sim.util.usd_path import resolve_usd_spec, isaaclab_asset_path

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "env/registry.yaml"


def _expand_spec(spec: str) -> str:
	s = (spec or "").strip()
	if s.startswith("isaaclab://"):
		rel = s[len("isaaclab://"):]
		return isaaclab_asset_path(rel)
	return s


def _load_mapping() -> dict:
	if not REGISTRY_PATH.exists():
		return {}
	text = REGISTRY_PATH.read_text(encoding="utf-8")
	try:
		import yaml  # type: ignore
		data = yaml.safe_load(text)
		return data or {}
	except Exception:
		pass
	mapping: dict[str, str] = {}
	for line in text.splitlines():
		s = line.strip()
		if not s or s.startswith("#"):
			continue
		if ":" in s:
			k, v = s.split(":", 1)
			mapping[k.strip()] = v.strip()
	return mapping


def resolve_env(name_or_spec: str, repo_root: Path | str) -> Tuple[str, str, bool]:
	rr = Path(repo_root)
	key = (name_or_spec or "").strip()
	mapping = _load_mapping()
	spec = mapping.get(key, key)
	expanded = _expand_spec(spec)
	return resolve_usd_spec(expanded, rr)


__all__ = ["resolve_env", "REGISTRY_PATH"]
