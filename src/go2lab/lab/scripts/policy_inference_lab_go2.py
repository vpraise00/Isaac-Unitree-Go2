from __future__ import annotations

import argparse
import logging
import random
from pathlib import Path
import sys


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True, help="Path to .pt/.pth checkpoint to load")
    p.add_argument("--steps", type=int, default=300)
    p.add_argument("--control-hz", type=int, default=30)
    p.add_argument("--headless", action="store_true")
    return p.parse_args()


def _obs_to_vec(obs: dict) -> list[float]:
    vec: list[float] = []
    vec += list(obs.get("base_lin_vel", (0.0, 0.0, 0.0)))
    vec += list(obs.get("base_ang_vel", (0.0, 0.0, 0.0)))
    vec += [float(obs.get("base_height", 0.0))]
    vec += [float(obs.get("up_dot", 1.0))]
    vec += [float(obs.get("yaw", 0.0))]
    return vec


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("policy_infer")

    # Ensure repo root import path
    repo_root = Path(__file__).resolve().parents[4]
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))

    # Lazy import torch if available
    torch = None
    try:
        import torch as _torch  # type: ignore
        torch = _torch
    except Exception:
        log.warning("PyTorch not available; falling back to random actions")

    from go2lab.lab.envs.go2_warehouse_env import Go2WarehouseEnv

    env = Go2WarehouseEnv(steps_per_episode=args.steps, headless=args.headless, control_hz=args.control_hz)
    try:
        # Load checkpoint if possible
        model = None
        if torch is not None:
            try:
                ckpt_path = Path(args.checkpoint)
                if ckpt_path.exists():
                    obj = torch.load(str(ckpt_path), map_location="cpu")
                    model = obj if hasattr(obj, "forward") else None
                    if model is None:
                        log.warning("Checkpoint loaded but no callable model.forward found; using random policy")
                else:
                    log.error("Checkpoint not found: %s", ckpt_path)
            except Exception as e:
                log.warning("Failed to load checkpoint: %s", e)

        obs = env.reset()
        total = 0.0
        for t in range(args.steps):
            if model is not None and torch is not None:
                with torch.no_grad():
                    x = torch.tensor(_obs_to_vec(obs), dtype=torch.float32).unsqueeze(0)
                    act = model(x)
                    if hasattr(act, "cpu"):
                        act = act.cpu()
                    a = act.squeeze(0).tolist()
                    action = (
                        float(a[0]) if len(a) > 0 else 0.0,
                        float(a[1]) if len(a) > 1 else 0.0,
                        float(a[2]) if len(a) > 2 else 0.0,
                    )
            else:
                action = (random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
            obs, r, done, info = env.step(action)
            total += r
            if done:
                break
        log.info("Inference finished: steps=%d, return=%.3f", t + 1, total)
        return 0
    except Exception as e:
        log.exception("Inference failed: %s", e)
        return 1
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
