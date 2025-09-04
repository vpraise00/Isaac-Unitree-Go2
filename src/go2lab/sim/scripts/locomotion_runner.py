from __future__ import annotations

import logging
import os


LOGGER = logging.getLogger("locomotion_runner")


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    renderer = os.environ.get("ISAAC_RENDERER", "RayTracedLighting")
    headless = os.environ.get("HEADLESS", "0") == "1"
    try:
        from isaacsim import SimulationApp  # type: ignore
    except Exception:
        from isaacsim.simulation_app import SimulationApp  # type: ignore
    app = SimulationApp({"headless": headless, "renderer": renderer})
    try:
        # Defer heavy imports after SimulationApp init
        from go2lab.rl.envs.go2_env import Go2RSLEnvCfg
        from go2lab.rl.go2_ctrl import init_base_vel_cmd, get_rsl_flat_policy

        # Build Isaac Lab env for locomotion (Velocity-Flat-Unitree-Go2)
        cfg = Go2RSLEnvCfg()

        # Instantiate RL policy + vec env
        env, policy = get_rsl_flat_policy(cfg)
        num_envs = env.num_envs if hasattr(env, "num_envs") else 1
        init_base_vel_cmd(num_envs)

        # Minimal rollout loop
        obs, _ = env.reset()
        for _ in range(1000):
            try:
                app.update()
            except Exception:
                pass
            with torch.no_grad():  # type: ignore[name-defined]
                import torch  # local import to avoid global dependency before SimulationApp
                action = policy(obs)
            obs, _, _, _, _ = env.step(action)
        return 0
    finally:
        try:
            app.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
