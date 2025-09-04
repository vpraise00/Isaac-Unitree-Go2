from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

from go2lab.lab.integration import ensure_lab_on_path
from go2lab.lab.envs.go2_warehouse_env import Go2WarehouseEnv


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--lab-path", default=None)
    p.add_argument("--policy", required=True, help="Python module path exposing get_policy() -> callable")
    p.add_argument("--steps", type=int, default=300)
    p.add_argument("--headless", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("il_infer")

    used = ensure_lab_on_path(args.lab_path)
    if used is None:
        log.error("Isaac Lab repo not found. Set ISAAC_LAB_PATH or configs/lab2_config.json.")
        return 2

    # Import the IL policy factory from Lab-side module
    try:
        mod = __import__(args.policy, fromlist=["get_policy"])  # type: ignore
        get_policy = getattr(mod, "get_policy")
        policy = get_policy()
    except Exception as e:
        log.error("Failed to import policy %s: %s", args.policy, e)
        return 3

    env = Go2WarehouseEnv(steps_per_episode=args.steps, headless=args.headless)
    try:
        obs = env.reset()
        ret = 0.0
        for t in range(args.steps):
            a = policy(obs)
            obs, r, done, info = env.step(a)
            ret += r
            if done:
                break
        log.info("IL inference finished: steps=%d, return=%.3f", t + 1, ret)
        return 0
    except Exception as e:
        log.exception("Inference failed: %s", e)
        return 1
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
