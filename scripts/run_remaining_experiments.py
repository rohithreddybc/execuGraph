"""Unattended driver for the experiments still missing from the paper.

Ordered by scientific value, so that a partial run still yields the most
important result. Every stage is idempotent: the runner CLI skips any output
directory that already contains a completed ``run_summary.json``, so this
script can be re-invoked after an interruption and will resume.

Priority order and why:

1-3. Single-retry on HumanEval, APPS-introductory, and the DeepSeek backbone.
     Single-retry is the configuration the paper recommends, yet it was only
     ever run on the 30-problem internal suite. Every external and cross-model
     comparison contrasted one-shot against multi-full only, so the headline
     recommendation rested on the suite the paper itself calls a fast-iteration
     testbed. These three runs close that gap and are the highest-value work
     remaining.

4.   Retry budget 1. The sweep was run at {0, 2} only, which establishes that
     retries help but cannot distinguish a saturating curve from a linear one.
     Adding budget 1 gives the sweep an interior point.

5-8. Ablations at N=5, matching the headline baseline's trial count. The
     ablations were run at N=2 against an N=5 baseline, so the planner-distractor
     effect (the paper's main mechanistic claim) rests on roughly two trial
     flips. Re-running at N=5 puts every ablation on the baseline's footing.

Usage:
    python scripts/run_remaining_experiments.py [--only STAGE_ID] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results" / "submission-20260811-followup"
LOG = RESULTS / "driver.log"
DONE_MARKER = RESULTS / "ALL_STAGES_COMPLETE.json"

# (stage_id, config, condition, benchmark, n_trials, retry_budget, rationale)
STAGES = [
    ("e2_he_sr",        "default.yaml",    "single-retry",       "humaneval",  1, 2,
     "SR on HumanEval: recommended config, never externally validated"),
    ("e3_apps_sr",      "default.yaml",    "single-retry",       "apps_intro", 1, 2,
     "SR on APPS-introductory"),
    ("e7_xm_sr",        "crossmodel.yaml", "single-retry",       "internal30", 2, 2,
     "SR on DeepSeek backbone: completes the cross-model row"),
    ("e2_he_so_164",    "default.yaml",    "single-oneshot",     "humaneval",  1, 0,
     "SO on the full 164-problem HumanEval, to match the SR run's coverage"),
    ("e2_he_mf_164",    "default.yaml",    "multi-full",         "humaneval",  1, 2,
     "MF on the full 164-problem HumanEval, to match the SR run's coverage"),
    ("e5_rb1",          "default.yaml",    "multi-full",         "internal30", 2, 1,
     "Retry budget 1: interior point for the sweep"),
    ("e4_no_planner_n5", "default.yaml",   "multi-no-planner",   "internal30", 5, 2,
     "Planner ablation at N=5, matching the headline baseline"),
    ("e4_no_reviewer_n5", "default.yaml",  "multi-no-reviewer",  "internal30", 5, 2,
     "Reviewer ablation at N=5"),
    ("e4_no_optimizer_n5", "default.yaml", "multi-no-optimizer", "internal30", 5, 2,
     "Optimizer ablation at N=5"),
    ("e4_rag_on_n5",    "default.yaml",    "rag-on",             "internal30", 5, 2,
     "Retrieval ablation at N=5"),
]


def log(msg: str) -> None:
    stamp = datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def ollama_up(timeout: float = 5.0) -> bool:
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=timeout)
        return True
    except Exception:
        return False


def ensure_ollama() -> bool:
    """Ollama normally runs as a background service; start it if it is not up."""
    if ollama_up():
        return True
    log("ollama not responding; attempting to start it")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except FileNotFoundError:
        log("FATAL: ollama executable not found on PATH")
        return False
    for _ in range(30):
        time.sleep(2)
        if ollama_up():
            log("ollama is up")
            return True
    log("FATAL: ollama did not come up within 60s")
    return False


def run_stage(stage, dry_run: bool = False) -> dict:
    stage_id, config, condition, benchmark, n_trials, budget, rationale = stage
    out_dir = RESULTS / stage_id
    summary = out_dir / "run_summary.json"

    if summary.exists():
        data = json.loads(summary.read_text(encoding="utf-8"))
        log(f"SKIP  {stage_id} (already complete, pass_rate={data.get('pass_rate')})")
        return {"stage": stage_id, "status": "already_complete", **data}

    cmd = [
        sys.executable, "-m", "execugraph.runner.cli",
        "--config", str(REPO / "configs" / config),
        "--output", str(out_dir),
        "--condition", condition,
        "--benchmark", benchmark,
        "--n-trials", str(n_trials),
        "--retry-budget", str(budget),
    ]
    log(f"START {stage_id}: {rationale}")
    log(f"      {' '.join(cmd[1:])}")
    if dry_run:
        return {"stage": stage_id, "status": "dry_run"}

    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, cwd=str(REPO), env=env, capture_output=True, text=True,
            timeout=6 * 60 * 60,
        )
    except subprocess.TimeoutExpired:
        log(f"FAIL  {stage_id}: exceeded 6h timeout")
        return {"stage": stage_id, "status": "timeout"}

    elapsed = time.time() - t0
    tail = (proc.stdout or "").strip().splitlines()[-6:]
    for line in tail:
        log(f"      | {line}")

    if proc.returncode != 0:
        log(f"FAIL  {stage_id}: exit {proc.returncode}")
        for line in (proc.stderr or "").strip().splitlines()[-10:]:
            log(f"      ! {line}")
        return {"stage": stage_id, "status": "failed", "returncode": proc.returncode}

    result = {"stage": stage_id, "status": "ok", "elapsed_s": round(elapsed, 1)}
    if summary.exists():
        result.update(json.loads(summary.read_text(encoding="utf-8")))
    log(f"DONE  {stage_id} in {elapsed / 60:.1f} min  pass_rate={result.get('pass_rate')}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="Run a single stage id.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    log("=" * 70)
    log(f"driver start  repo={REPO}")
    log(f"python={sys.version.split()[0]}  cwd={os.getcwd()}")

    if not args.dry_run and not ensure_ollama():
        log("ABORT: no Ollama backend")
        return 2

    stages = [s for s in STAGES if args.only is None or s[0] == args.only]
    results = []
    t0 = time.time()
    for stage in stages:
        try:
            results.append(run_stage(stage, dry_run=args.dry_run))
        except Exception as exc:  # keep going; a later stage may still succeed
            log(f"FAIL  {stage[0]}: unhandled {type(exc).__name__}: {exc}")
            results.append({"stage": stage[0], "status": "exception", "error": str(exc)})

    ok = [r for r in results if r.get("status") in ("ok", "already_complete")]
    log(f"driver finished: {len(ok)}/{len(results)} stages complete "
        f"in {(time.time() - t0) / 60:.1f} min")

    payload = {
        "finished_at": datetime.now(UTC).astimezone().isoformat(),
        "stages_total": len(results),
        "stages_complete": len(ok),
        "all_complete": len(ok) == len(results),
        "results": results,
    }
    DONE_MARKER.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    log(f"wrote {DONE_MARKER}")
    return 0 if len(ok) == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
