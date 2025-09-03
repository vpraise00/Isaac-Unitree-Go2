"""Preview a manager-based GO2 task (test-double) without Isaac Lab runtime.

Loads YAML for basic params and runs a short rollout using lab.envs.go2_warehouse_env.
"""
from __future__ import annotations

from pathlib import Path
import sys
import random
try:
    import yaml  # type: ignore
except Exception:  # minimal fallback parser for our simple YAML
    yaml = None
import logging

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("lab.preview")

CONFIG = Path(__file__).resolve().parents[1] / "tasks/go2_task_config.yaml"

# Ensure repo root on sys.path for lab.* imports when run by Isaac Sim
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))


def main() -> int:
    if not CONFIG.exists():
        LOGGER.error("Task config missing: %s", CONFIG)
        return 1
    LOGGER.info("Loading task config: %s", CONFIG)
    with CONFIG.open("r", encoding="utf-8") as f:
        if yaml is not None:
            cfg = yaml.safe_load(f)
        else:
            # naive fallback: parse key: value at top level only
            cfg = {}
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line and not line.startswith("-"):
                    k, v = line.split(":", 1)
                    cfg[k.strip()] = v.strip()

    physics_hz = int(cfg.get("physics_hz", 120))
    control_hz = int(cfg.get("control_hz", 30))
    max_len = int(cfg.get("env", {}).get("max_episode_length", 200))

    # Simple rollout: random policy in [-1,1]
    from lab.envs.go2_warehouse_env import Go2WarehouseEnv
    env = Go2WarehouseEnv(steps_per_episode=max_len, headless=False, control_hz=control_hz)
    try:
        obs = env.reset()
        LOGGER.info("Reset obs: %s", {k: (v if isinstance(v, (int, float)) else "...") for k, v in obs.items()})
        steps = min(60, max_len)
        ret = 0.0
        for t in range(steps):
            action = (random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
            obs, r, done, info = env.step(action)
            ret += r
            if done:
                break
        LOGGER.info("Rollout finished: steps=%d, return=%.3f", t + 1, ret)
        return 0
    except Exception as e:
        LOGGER.exception("Preview run failed: %s", e)
        return 1
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
