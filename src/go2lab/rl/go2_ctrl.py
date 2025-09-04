from __future__ import annotations

import os
import torch

base_vel_cmd_input: torch.Tensor | None = None


def init_base_vel_cmd(num_envs: int) -> None:
    global base_vel_cmd_input
    base_vel_cmd_input = torch.zeros((num_envs, 3), dtype=torch.float32)


def base_vel_cmd(env) -> torch.Tensor:
    # env is expected to have attribute 'device'
    global base_vel_cmd_input
    if base_vel_cmd_input is None:
        return torch.zeros((1, 3), dtype=torch.float32, device=getattr(env, "device", "cpu"))
    return base_vel_cmd_input.clone().to(getattr(env, "device", "cpu"))


def set_cmd_row(row: int, x: float, y: float, yaw: float) -> None:
    global base_vel_cmd_input
    if base_vel_cmd_input is None:
        return
    if 0 <= row < base_vel_cmd_input.shape[0]:
        base_vel_cmd_input[row, 0] = x
        base_vel_cmd_input[row, 1] = y
        base_vel_cmd_input[row, 2] = yaw


def clear_cmds() -> None:
    global base_vel_cmd_input
    if base_vel_cmd_input is not None:
        base_vel_cmd_input.zero_()


# Optional: RSL-RL policy loaders mirroring the user's ergonomics.
def _maybe_import_rsl():
    from omni.isaac.lab_tasks.utils.wrappers.rsl_rl import RslRlVecEnvWrapper, RslRlOnPolicyRunnerCfg  # type: ignore
    from omni.isaac.lab_tasks.utils import get_checkpoint_path  # type: ignore
    from rsl_rl.runners import OnPolicyRunner  # type: ignore
    return RslRlVecEnvWrapper, RslRlOnPolicyRunnerCfg, get_checkpoint_path, OnPolicyRunner


def get_rsl_flat_policy(cfg):
    """Create Isaac-Velocity-Flat-Unitree-Go2-v0 vector env and load policy checkpoint."""
    import gymnasium as gym  # type: ignore
    from .go2_ctrl_cfg import unitree_go2_flat_cfg

    env = gym.make("Isaac-Velocity-Flat-Unitree-Go2-v0", cfg=cfg)
    RslRlVecEnvWrapper, RslRlOnPolicyRunnerCfg, get_checkpoint_path, OnPolicyRunner = _maybe_import_rsl()
    env = RslRlVecEnvWrapper(env)

    agent_cfg = unitree_go2_flat_cfg
    # Allow override via env var
    load_run = os.environ.get("RSL_RUN_DIR", agent_cfg["load_run"])
    load_ckpt = os.environ.get("RSL_CHECKPOINT", agent_cfg["load_checkpoint"])
    ckpt_path = get_checkpoint_path(log_path=os.path.abspath("ckpts"), run_dir=load_run, checkpoint=load_ckpt)
    runner = OnPolicyRunner(env, agent_cfg, log_dir=None, device=agent_cfg["device"])  # type: ignore[arg-type]
    runner.load(ckpt_path)
    policy = runner.get_inference_policy(device=agent_cfg["device"])  # type: ignore[arg-type]
    return env, policy


def get_rsl_rough_policy(cfg):
    import gymnasium as gym  # type: ignore
    from .go2_ctrl_cfg import unitree_go2_rough_cfg

    env = gym.make("Isaac-Velocity-Rough-Unitree-Go2-v0", cfg=cfg)
    RslRlVecEnvWrapper, RslRlOnPolicyRunnerCfg, get_checkpoint_path, OnPolicyRunner = _maybe_import_rsl()
    env = RslRlVecEnvWrapper(env)

    agent_cfg = unitree_go2_rough_cfg
    load_run = os.environ.get("RSL_RUN_DIR", agent_cfg["load_run"])
    load_ckpt = os.environ.get("RSL_CHECKPOINT", agent_cfg["load_checkpoint"])
    ckpt_path = get_checkpoint_path(log_path=os.path.abspath("ckpts"), run_dir=load_run, checkpoint=load_ckpt)
    runner = OnPolicyRunner(env, agent_cfg, log_dir=None, device=agent_cfg["device"])  # type: ignore[arg-type]
    runner.load(ckpt_path)
    policy = runner.get_inference_policy(device=agent_cfg["device"])  # type: ignore[arg-type]
    return env, policy
