# Wrapper to import config from legacy location
from __future__ import annotations

import os
from .sim.util.usd_path import isaaclab_asset_path

DEFAULT_WAREHOUSE_REL = "Environments/Simple_Warehouse/warehouse.usd"


def default_warehouse_spec() -> str:
	return isaaclab_asset_path(DEFAULT_WAREHOUSE_REL)


def get_warehouse_spec() -> str:
	return (os.environ.get("WAREHOUSE_USD", "") or default_warehouse_spec()).strip()


__all__ = ["DEFAULT_WAREHOUSE_REL", "default_warehouse_spec", "get_warehouse_spec"]
