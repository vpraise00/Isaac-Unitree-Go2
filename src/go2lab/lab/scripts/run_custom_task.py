"""Run a custom manager-based task in the warehouse environment (no Isaac Lab).

Launches Go2WarehouseEnv and executes a short rollout. Template for custom tasks.
"""
from __future__ import annotations

import argparse
import logging
import random
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("lab.run_custom")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--max-steps", type=int, default=200)
    p.add_argument("--control-hz", type=int, default=30)
    p.add_argument("--headless", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    # Ensure repo root import path
    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))

    from go2lab.lab.envs.go2_warehouse_env import Go2WarehouseEnv

    env = Go2WarehouseEnv(steps_per_episode=args.max_steps, headless=args.headless, control_hz=args.control_hz)
    try:
        obs = env.reset()
        LOGGER.info("Custom task reset obs: %s", {k: (v if isinstance(v, (int, float)) else "...") for k, v in obs.items()})
        ret = 0.0
        for t in range(min(300, args.max_steps)):
            action = (random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
            obs, r, done, info = env.step(action)
            ret += r
            if done:
                break
        LOGGER.info("Custom task finished: steps=%d, return=%.3f", t + 1, ret)
        return 0
    except Exception as e:
        LOGGER.exception("Custom task failed: %s", e)
        return 1
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
