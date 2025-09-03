from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# This runner is executed by Isaac Sim's --exec. It dispatches to scripts based on --run_cfg.
# Example: --run_cfg teleoperation --env warehouse_multiple_shelves --task go2-locomotion

RUN_CHOICES = [
    "teleoperation",        # sim/scripts/teleop_keyboard.py
    "dataset_record",       # sim/scripts/dataset_recorder.py
    "lab_preview",          # lab/scripts/preview_task.py
    "lab_task_module",      # lab/scripts/run_lab2_task.py (requires --task-module)
    "custom_task",          # lab/scripts/run_custom_task.py
    "script_runner",        # sim/scripts/run_sim.py
    "policy_inference",     # lab/scripts/policy_inference_lab_go2.py (requires --checkpoint)
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--run_cfg", required=True, choices=RUN_CHOICES)
    p.add_argument("--env", default="warehouse", help="Env name or direct USD spec (see env/registry.yaml).")
    p.add_argument("--task", default="go2-locomotion", help="Task name (for logging or future dispatch)")
    p.add_argument("--task-module", default=None, help="When run_cfg=lab_task_module, python module path to run")
    p.add_argument("--agents", choices=["single", "multi"], default="single", help="Agent mode")
    p.add_argument("--checkpoint", default=None, help="When run_cfg=policy_inference, path to checkpoint .pt/.pth")
    p.add_argument("--headless", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"

    # Make repo importable for our helper modules
    for p in (repo_root, src_root):
        if str(p) not in sys.path:
            sys.path.append(str(p))

    # Allow selection of env by name or direct spec
    # Prefer go2lab namespace if available
    try:
        from go2lab.env_registry import resolve_env
    except Exception:
        from sim.env_registry import resolve_env
    kind, target, ok = resolve_env(args.env, repo_root)
    # Expose the resolved env choice via WAREHOUSE_USD so underlying scripts pick it up
    os.environ["WAREHOUSE_USD"] = target
    os.environ["TASK_NAME"] = args.task
    os.environ["AGENT_MODE"] = args.agents

    headless_flag = "--headless" if args.headless else ""

    # Dispatch to underlying scripts (all of them already read WAREHOUSE_USD)
    if args.run_cfg == "teleoperation":
        # Prefer src/go2lab scripts when present
        exec_path = (repo_root / "src/go2lab/sim/scripts/teleop_keyboard.py")
        if not exec_path.exists():
            exec_path = repo_root / "sim/scripts/teleop_keyboard.py"
        return run_exec(exec_path)
    if args.run_cfg == "dataset_record":
        exec_path = (repo_root / "src/go2lab/sim/scripts/dataset_recorder.py")
        if not exec_path.exists():
            exec_path = repo_root / "sim/scripts/dataset_recorder.py"
        return run_exec(exec_path)
    if args.run_cfg == "lab_preview":
        exec_path = repo_root / "lab/scripts/preview_task.py"
        return run_exec(exec_path)
    if args.run_cfg == "lab_task_module":
        exec_path = repo_root / "lab/scripts/run_lab2_task.py"
        # pass through task module if provided
        if args.task_module:
            sys.argv = [str(exec_path), "--task-module", args.task_module, *( ["--headless"] if args.headless else [] )]
        return run_module_exec(exec_path)
    if args.run_cfg == "custom_task":
        exec_path = repo_root / "lab/scripts/run_custom_task.py"
        return run_exec(exec_path, extra=["--headless"] if args.headless else [])
    if args.run_cfg == "script_runner":
        exec_path = (repo_root / "src/go2lab/sim/scripts/run_sim.py")
        if not exec_path.exists():
            exec_path = repo_root / "sim/scripts/run_sim.py"
        return run_exec(exec_path)
    if args.run_cfg == "policy_inference":
        exec_path = repo_root / "lab/scripts/policy_inference_lab_go2.py"
        extra: list[str] = []
        if args.checkpoint:
            extra += ["--checkpoint", args.checkpoint]
        if args.headless:
            extra += ["--headless"]
        return run_exec(exec_path, extra=extra)

    raise SystemExit(2)


def run_exec(script: Path, extra: list[str] | None = None) -> int:
    # Run the given script as __main__ using runpy
    import runpy
    sys.argv = [str(script)] + (extra or [])
    try:
        runpy.run_path(str(script), run_name="__main__")
        return 0
    except SystemExit as se:
        return int(getattr(se, "code", 0) or 0)
    except Exception:
        raise


def run_module_exec(script: Path) -> int:
    import runpy
    try:
        runpy.run_path(str(script), run_name="__main__")
        return 0
    except SystemExit as se:
        return int(getattr(se, "code", 0) or 0)
    except Exception:
        raise


if __name__ == "__main__":
    raise SystemExit(main())
