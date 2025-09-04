from __future__ import annotations

"""Tiny harness that imports Isaac Lab RL training entry and runs it.

It expects your Isaac Lab repo path to be configured via ISAAC_LAB_PATH or configs/lab2_config.json.
"""
import argparse
import logging
from pathlib import Path
import sys

from go2lab.lab.integration import ensure_lab_on_path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--lab-path", default=None, help="Path to Isaac Lab repo (overrides config/env)")
    p.add_argument("--entry", default="omni.isaac.lab_tasks.manager_based.locomotion.train",
                   help="Isaac Lab training module to run")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    used = ensure_lab_on_path(args.lab_path)
    if used is None:
        print("Isaac Lab repo not found. Set ISAAC_LAB_PATH or configs/lab2_config.json.")
        return 2

    import runpy

    # Allow the lab entry module to read argv as usual
    sys.argv = [args.entry]
    try:
        runpy.run_module(args.entry, run_name="__main__")
        return 0
    except SystemExit as se:
        return int(getattr(se, "code", 0) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
