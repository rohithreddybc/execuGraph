"""Regenerate ``trials.jsonl`` deterministically. SYNTHETIC DATA — do not cite."""

from __future__ import annotations

import json
import random
from pathlib import Path

from execugraph.benchmarks.internal30 import load_internal30


def main() -> None:
    random.seed(0)
    out = Path(__file__).parent / "trials.jsonl"
    problems = load_internal30()
    records = []
    for p in problems:
        for cond, base_pass in [("single-oneshot", 0.55), ("single-retry", 0.85), ("multi-full", 0.92)]:
            for trial in range(3):
                passed = random.random() < base_pass
                err = "none" if passed else random.choice(["wrong_answer", "runtime", "syntax", "timeout"])
                records.append({
                    "problem_id": p.id, "category": p.category, "source": p.source,
                    "condition": cond,
                    "model_planner": "qwen2.5:7b-instruct-q4_K_M",
                    "model_generator": "qwen2.5-coder:7b-instruct-q4_K_M",
                    "seed": trial, "trial": trial, "retry_budget": 2,
                    "passed": passed, "tests_total": len(p.tests),
                    "tests_passed": len(p.tests) if passed else 0,
                    "retries_used": 0 if cond == "single-oneshot" else (0 if passed else 2),
                    "error_class": err, "test_source": "deterministic",
                    "wallclock_s": 1.0 if cond == "single-oneshot" else (3.0 if cond == "single-retry" else 4.5),
                    "tokens_in": 200, "tokens_out": 150,
                    "llm_calls": 1 if cond == "single-oneshot" else (3 if cond == "single-retry" else 5),
                    "code": "", "stderr": "" if passed else err, "timestamp": 0.0,
                })
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(records)} synthetic records to {out}")


if __name__ == "__main__":
    main()
