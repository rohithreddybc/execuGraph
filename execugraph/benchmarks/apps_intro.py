"""APPS-introductory subset loader.

We take a fixed 50-problem random subset of the APPS-introductory test
split, drawn with a deterministic seed so the subset is reproducible.
Each problem ships with a list of stdin/stdout pairs in the
``input_output`` field; we adapt that into our :class:`TestCase` schema
by wrapping each pair in a tiny driver that captures stdout.

Reference: Hendrycks et al., "Measuring Coding Challenge Competence with
APPS", ICLR 2021.
"""

from __future__ import annotations

import json
import random
from typing import Any

from .base import Problem, TestCase

_DATASET_NAME = "codeparrot/apps"
_SUBSET_SIZE_DEFAULT = 50
_SEED_DEFAULT = 0


def _io_pairs(record: dict) -> list[tuple[Any, Any]]:
    raw = record.get("input_output")
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
    inputs = raw.get("inputs") or []
    outputs = raw.get("outputs") or []
    return list(zip(inputs, outputs, strict=False))


def _build_driver_call(test_input: Any, expected_stdout: Any) -> str:
    """Build a sandbox call expression that:
    1. captures stdin from `test_input`,
    2. runs the candidate's __main__ (which APPS solutions typically use),
    3. returns the captured stdout for comparison.

    APPS solutions are written as scripts that read from stdin and write
    to stdout, so we do not assume a specific function name; instead the
    candidate's source is `exec`-ed under our io redirection.
    """
    in_str = test_input if isinstance(test_input, str) else "".join(test_input)
    return (
        "(lambda: ("
        "  __import__('io').StringIO('').getvalue() or"
        "  (lambda buf=__import__('io').StringIO(): ("
        "    [setattr(__import__('sys'), 'stdin', __import__('io').StringIO("
        f"     {in_str!r})), "
        "     setattr(__import__('sys'), 'stdout', buf), "
        "     exec(compile(globals().get('__apps_source__', ''), '<apps>', 'exec'),"
        "          {'__name__': '__main__'}, {}), "
        "     buf.getvalue()][-1]"
        "  ))()"
        "))()"
    )


def _normalize(s: str) -> str:
    """APPS expected outputs sometimes have trailing newlines or spaces."""
    return "\n".join(line.rstrip() for line in s.rstrip("\n").splitlines())


def _build_problem(record: dict, idx: int) -> Problem | None:
    pairs = _io_pairs(record)
    if not pairs:
        return None
    statement = (
        record.get("question", "").strip()
        + "\n\nWrite a complete Python program that reads from stdin and writes "
        "the answer to stdout. Define module-level variable __apps_source__ "
        "containing the candidate program's source if you are wrapping in a "
        "function; otherwise leave the program at module scope."
    )
    tests: list[TestCase] = []
    for i, (inp, exp) in enumerate(pairs[:5]):  # cap at 5 IO pairs per problem
        if not isinstance(exp, str):
            exp = "\n".join(map(str, exp))
        tests.append(
            TestCase(
                call=_build_driver_call(inp, exp),
                expected=_normalize(exp),
                description=f"io-pair-{i}",
                kind="deterministic",
                judge=(lambda expected: (lambda got: _normalize(str(got)) == expected))(_normalize(exp)),
            )
        )
    if not tests:
        return None
    return Problem(
        id=f"apps_intro_{idx:03d}",
        category="apps",
        source=f"apps-introductory/{record.get('problem_id', idx)}",
        statement=statement,
        primary_function="__script__",  # script-mode: no function probe, uses pre-built calls
        signature_aliases=[],
        tests=tests,
        selection_rationale="APPS-introductory subset for external-validity anchoring.",
        difficulty=record.get("difficulty", "introductory"),
        timeout_s=10.0,
    )


def load_apps_intro(*, subset_size: int = _SUBSET_SIZE_DEFAULT, seed: int = _SEED_DEFAULT) -> list[Problem]:
    """Load a fixed random subset of APPS-introductory.

    The subset is deterministic given (subset_size, seed).
    """
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "Loading APPS requires the `datasets` package. "
            "Run `pip install -e .` or `pip install datasets`."
        ) from e
    ds = load_dataset(_DATASET_NAME, split="test", trust_remote_code=True)
    intro = [r for r in ds if r.get("difficulty") == "introductory"]
    rng = random.Random(seed)
    sample = rng.sample(intro, k=min(subset_size, len(intro)))
    out: list[Problem] = []
    for i, record in enumerate(sample):
        p = _build_problem(record, i)
        if p is not None:
            out.append(p)
    return out


if __name__ == "__main__":  # pragma: no cover
    ps = load_apps_intro(subset_size=3)
    for p in ps:
        print(p.id, p.source, len(p.tests), "tests")
