"""Command-line entrypoint: ``execugraph-run``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..benchmarks.internal30 import load_internal30
from ..graph.workflow import WorkflowDeps
from ..llm.base import CostAccumulator
from ..llm.factory import build_backend
from .batch_runner import run_batch


def _load_problems(name: str, *, limit: int | None = None):
    """Resolve a benchmark name to a list of :class:`Problem`."""
    name = name.lower()
    if name in {"internal30", "internal-30", "internal_30"}:
        ps = load_internal30()
    elif name in {"humaneval", "human-eval"}:
        from ..benchmarks.humaneval import load_humaneval
        ps = load_humaneval(limit=limit)
        return ps  # limit applied inside loader
    elif name in {"apps", "apps_intro", "apps-intro", "apps-introductory"}:
        from ..benchmarks.apps_intro import load_apps_intro
        ps = load_apps_intro()
    elif name in {"humaneval_plus", "humanevalplus", "humaneval+"}:
        from ..benchmarks.humaneval_plus import load_humaneval_plus
        ps = load_humaneval_plus(limit=limit)
        return ps
    elif name in {"mbpp", "mbpp_sanitized"}:
        from ..benchmarks.mbpp import load_mbpp
        ps = load_mbpp(limit=limit)
        return ps
    else:
        raise ValueError(f"unknown benchmark: {name!r}")
    if limit is not None:
        ps = ps[:limit]
    return ps


def _load_yaml(path: Path) -> dict:
    import yaml  # local import to keep import-time cheap
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="execugraph-run")
    p.add_argument("--config", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--condition", required=True, choices=[
        "single-oneshot", "single-retry", "multi-full",
        "multi-no-planner", "multi-no-reviewer", "multi-no-optimizer", "rag-on",
    ])
    p.add_argument("--n-trials", type=int, default=5)
    p.add_argument("--retry-budget", type=int, default=2)
    p.add_argument("--limit", type=int, default=None,
                   help="Run only the first N problems (smoke testing).")
    p.add_argument("--benchmark", default="internal30",
                   choices=["internal30", "humaneval", "humaneval_plus", "apps_intro", "mbpp"],
                   help="Which benchmark to run against. Default: internal30.")
    args = p.parse_args(argv)

    # Fast-exit: if this output dir already has a completed run_summary, skip.
    summary_path = Path(args.output) / "run_summary.json"
    if summary_path.exists():
        import json as _json
        _s = _json.loads(summary_path.read_text(encoding="utf-8"))
        print(
            f"[skip] {args.output.name} already complete "
            f"(pass_rate={_s.get('pass_rate', '?'):.3f}). Remove run_summary.json to re-run.",
            flush=True,
        )
        return 0

    cfg = _load_yaml(args.config)
    planner_llm = build_backend(cfg["models"]["planner"])
    generator_llm = build_backend(cfg["models"]["generator"])
    reviewer_llm = build_backend(cfg["models"].get("reviewer", cfg["models"]["planner"]))
    optimizer_llm = build_backend(cfg["models"].get("optimizer", cfg["models"]["generator"]))
    explainer_llm = build_backend(cfg["models"].get("explainer", cfg["models"]["planner"]))

    deps = WorkflowDeps(
        planner_llm=planner_llm,
        generator_llm=generator_llm,
        reviewer_llm=reviewer_llm,
        optimizer_llm=optimizer_llm,
        explainer_llm=explainer_llm,
        cost=CostAccumulator(),
        timeout_s=cfg.get("execution", {}).get("timeout_s", 5.0),
    )

    problems = _load_problems(args.benchmark, limit=args.limit)
    print(f"loaded {len(problems)} problems from {args.benchmark}")

    flags = {
        "single-oneshot": dict(),
        "single-retry": dict(),
        "multi-full": dict(),
        "multi-no-planner": dict(enable_planner=False),
        "multi-no-reviewer": dict(enable_reviewer=False),
        "multi-no-optimizer": dict(enable_optimizer=False),
        "rag-on": dict(enable_rag=True),
    }[args.condition]

    summary = run_batch(
        problems=problems,
        deps=deps,
        condition="multi-full" if args.condition.startswith(("multi-", "rag-")) else args.condition,
        n_trials=args.n_trials,
        retry_budget=args.retry_budget,
        output_dir=args.output,
        config_meta={"config_path": str(args.config), **cfg},
        **flags,
    )
    print(f"\n=== summary ===\n  pass_rate: {summary['pass_rate']:.3f}\n  total: {summary['trials_total']}", flush=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
