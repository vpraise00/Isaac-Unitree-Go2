from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# This runner is executed by Isaac Sim's --exec. It dispatches per the new schema.
RUN_CHOICES = [
    "train",
    "test",
    "teleoperation",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    # New schema
    p.add_argument("--run_cfg", required=False, choices=RUN_CHOICES, help="train | test | teleoperation")
    p.add_argument("--env", default=None, help="Warehouse env name or direct USD spec. Omit for empty world.")
    p.add_argument(
        "--task",
        choices=["locomotion", "locomanipulation"],
        default=None,
        help="Task type. If omitted, task is unspecified. locomanipulation is a placeholder for now.",
    )
    p.add_argument("--algorithm", choices=["RL", "IL"], default=None, help="Only valid with --run_cfg train")
    p.add_argument("--checkpoint", default=None, help=".pt file for test inference (valid with --run_cfg test)")
    p.add_argument("--headless", action="store_true")
    p.add_argument(
        "--render_mode",
        "--rendering_mode",
        dest="render_mode",
        choices=["performance", "quality", "pathtraced"],
        default=None,
        help="Renderer preset: performance/quality/pathtraced. Maps to SimulationApp renderer.",
    )
    # Some Kit launchers can drop argv; support a fallback via env
    argv = sys.argv[1:]
    if not argv:
        raw = os.environ.get("ISAAC_RUN_ARGS", "").strip()
        if raw:
            argv = raw.split()
    args = p.parse_args(argv)
    # Validate cross-arg dependencies
    if args.algorithm and args.run_cfg != "train":
        p.error("--algorithm is only valid with --run_cfg train")
    if args.checkpoint and args.run_cfg != "test":
        p.error("--checkpoint is only valid with --run_cfg test")
    return args


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"

    # Make repo importable for our helper modules
    for p in (repo_root, src_root):
        if str(p) not in sys.path:
            sys.path.append(str(p))

    # Resolve env spec (name or direct path/url). If omitted, leave empty (no warehouse).
    target = None
    if args.env:
        try:
            from go2lab.env_registry import resolve_env
            kind, target, ok = resolve_env(args.env, repo_root)
            if ok and (target or "").strip().lower() not in ("", "empty", "none"):
                os.environ["WAREHOUSE_USD"] = target
            else:
                os.environ["WAREHOUSE_USD"] = "empty"
        except Exception:
            # Best-effort: if a direct path/url was given, pass it through
            os.environ["WAREHOUSE_USD"] = args.env
    else:
        os.environ["WAREHOUSE_USD"] = "empty"

    # Task and mode flags
    if args.task:
        os.environ["TASK_NAME"] = args.task
    if args.algorithm:
        os.environ["ALGORITHM"] = args.algorithm
    if args.checkpoint:
        os.environ["CHECKPOINT_PATH"] = args.checkpoint
    if args.render_mode:
        # Export chosen render mode for downstream scripts
        os.environ["RENDER_MODE"] = args.render_mode
        # Map to SimulationApp 'renderer' arg for Isaac Sim 5.0
        # - performance/quality -> RayTracedLighting (real-time RTX)
        # - pathtraced -> PathTracing (offline-quality; slow)
        mapped = "PathTracing" if args.render_mode == "pathtraced" else "RayTracedLighting"
        os.environ["ISAAC_RENDERER"] = mapped

    # Dispatch per new schema
    if args.headless:
        os.environ["HEADLESS"] = "1"

    if args.run_cfg == "teleoperation":
        # Enable keyboard loop
        os.environ.pop("SKIP_INPUT", None)
        exec_path = repo_root / "src/go2lab/sim/scripts/teleop_keyboard.py"
        return run_exec(exec_path)
    if args.run_cfg == "train":
        # For locomotion task without warehouse env, run Isaac-Velocity-Flat-Unitree-Go2-v0 RL loop
        if (args.task == "locomotion") and (os.environ.get("WAREHOUSE_USD", "empty") in ("empty", "none", "")):
            exec_path = repo_root / "src/go2lab/sim/scripts/locomotion_runner.py"
            return run_exec(exec_path)
        exec_path = repo_root / "src/go2lab/sim/scripts/train_runner.py"
        return run_exec(exec_path)
    if args.run_cfg == "test":
        exec_path = repo_root / "src/go2lab/sim/scripts/test_runner.py"
        return run_exec(exec_path)

    # No run_cfg provided:
    # - If locomotion task selected and no env set, run the locomotion RL viewer (policy inference)
    if (args.task == "locomotion") and (os.environ.get("WAREHOUSE_USD", "empty") in ("empty", "none", "")):
        exec_path = repo_root / "src/go2lab/sim/scripts/locomotion_runner.py"
        return run_exec(exec_path)
    # - Otherwise: compose env and spawn GO2 without input loop
    os.environ["SKIP_INPUT"] = "1"
    exec_path = repo_root / "src/go2lab/sim/scripts/teleop_keyboard.py"
    return run_exec(exec_path)


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
