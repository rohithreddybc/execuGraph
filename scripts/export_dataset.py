"""Export the internal-30 benchmark to a HuggingFace-ready dataset.

Produces a single JSONL file with one record per problem. Each record carries
the full problem specification and its deterministic test cases, so the suite
can be loaded with ``datasets.load_dataset("json", data_files=...)`` without
importing this package.

Usage::

    python scripts/export_dataset.py --out dataset/internal30.jsonl

The custom equality ``judge`` callables (used by a few graph problems whose
answers are not uniquely ordered) cannot be serialised; records flag them via
``has_custom_judge`` and fall back to exact-match for portability.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from execugraph.benchmarks.internal30 import load_internal30


def _jsonable(value):
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


def _problem_to_record(p) -> dict:
    return {
        "id": p.id,
        "category": p.category,
        "source": p.source,
        "difficulty": p.difficulty,
        "statement": p.statement,
        "primary_function": p.primary_function,
        "signature_aliases": list(p.signature_aliases),
        "selection_rationale": p.selection_rationale,
        "timeout_s": p.timeout_s,
        # ``args`` and ``expected`` are JSON-encoded as strings so the column
        # schema stays uniform across problems (their native types vary between
        # int, list, bool, ...). Parse them back with ``json.loads`` on load;
        # this keeps the file loadable by ``datasets.load_dataset`` / Arrow.
        "tests": [
            {
                "args": json.dumps(_jsonable(t.args)),
                "expected": json.dumps(_jsonable(t.expected)),
                "call": t.call,
                "description": t.description,
                "kind": t.kind,
                "has_custom_judge": t.judge is not None,
            }
            for t in p.tests
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("dataset/internal30.jsonl"))
    args = ap.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    problems = load_internal30()
    with args.out.open("w", encoding="utf-8") as fh:
        for p in problems:
            fh.write(json.dumps(_problem_to_record(p), ensure_ascii=False) + "\n")

    by_cat: dict[str, int] = {}
    n_tests = 0
    for p in problems:
        by_cat[p.category] = by_cat.get(p.category, 0) + 1
        n_tests += len(p.tests)
    print(f"wrote {len(problems)} problems ({n_tests} test cases) to {args.out}")
    print(f"by category: {by_cat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
