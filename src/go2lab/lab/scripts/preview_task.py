"""Preview a manager-based GO2 task (test-double) without Isaac Lab runtime.

Loads YAML for basic params and runs a short rollout using go2lab.lab.envs.go2_warehouse_env.
"""
from __future__ import annotations

from pathlib import Path
import sys
import random
import logging

try:
    import yaml  # type: ignore
except Exception:  # minimal fallback parser for our simple YAML
    yaml = None

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("lab.preview")


def _repo_root() -> Path:
    # src/go2lab/lab/scripts -> repo
    return Path(__file__).resolve().parents[4]


def _load_config() -> dict:
    cfg_path = _repo_root() / "configs/go2_task_config.yaml"
    if not cfg_path.exists():
        LOGGER.error("Task config missing: %s", cfg_path)
        return {}
    with cfg_path.open("r", encoding="utf-8") as f:
        if yaml is not None:
            return yaml.safe_load(f) or {}
        # naive fallback: parse key: value at top level only
        cfg: dict = {}
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line and not line.startswith("-"):
                k, v = line.split(":", 1)
                cfg[k.strip()] = v.strip()
        return cfg


def main() -> int:
    # Ensure repo root on sys.path for go2lab.* imports when run by Isaac Sim
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))

    cfg = _load_config()
    if not cfg:
        return 1

    physics_hz = int(cfg.get("physics_hz", 120))
    control_hz = int(cfg.get("control_hz", 30))
    max_len = int(cfg.get("env", {}).get("max_episode_length", 200))

    # Simple rollout: random policy in [-1,1]
    from go2lab.lab.envs.go2_warehouse_env import Go2WarehouseEnv
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
