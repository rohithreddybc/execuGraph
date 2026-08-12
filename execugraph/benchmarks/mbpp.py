"""MBPP benchmark loader.

We load the ``sanitized`` split of MBPP \\cite{austin2021mbpp}, which
removes the noisiest items. Each problem ships an ``assert``-style test
list; we wrap each assert as a sandboxed `TestCase`.
"""

from __future__ import annotations

import re

from .base import Problem, TestCase

_DATASET_NAME = "google-research-datasets/mbpp"
_CONFIG = "sanitized"


_FN_NAME_RE = re.compile(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _entry_point_from_code(code: str) -> str | None:
    m = _FN_NAME_RE.search(code)
    return m.group(1) if m else None


def _build_problem(record: dict, idx: int) -> Problem | None:
    code: str = record.get("code") or record.get("source_code") or ""
    entry_point = _entry_point_from_code(code)
    if not entry_point:
        return None
    asserts: list[str] = record.get("test_list") or []
    if not asserts:
        return None
    statement = (
        record.get("text") or record.get("prompt") or ""
    ).strip() + (
        f"\n\nImplement a Python function named ``{entry_point}`` that satisfies the "
        "examples."
    )
    tests: list[TestCase] = []
    for i, a in enumerate(asserts[:5]):
        a = a.strip()
        # An assert statement runs to True iff the candidate is correct.
        # We exec the assert and convert to a value via a try/except.
        driver = (
            "(lambda: ("
            "  (lambda: ("
            f"    exec({a!r}, globals(), globals()) or True"
            "  ))() if True else None))()"
        )
        # If the assert fails it raises AssertionError, which run_in_sandbox
        # records as error_class='runtime' and the judge below returns False.
        tests.append(
            TestCase(
                call=driver,
                expected=True,
                description=f"assert-{i}",
                kind="deterministic",
            )
        )
    return Problem(
        id=f"mbpp_{record.get('task_id', idx):03d}",
        category="mbpp",
        source=f"mbpp/{record.get('task_id', idx)}",
        statement=statement,
        primary_function=entry_point,
        signature_aliases=[entry_point],
        tests=tests,
        selection_rationale="MBPP-sanitized task.",
        difficulty="easy",
        timeout_s=8.0,
    )


def load_mbpp(*, limit: int | None = None) -> list[Problem]:
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("Run `pip install datasets` to load MBPP.") from e
    ds = load_dataset(_DATASET_NAME, _CONFIG, split="test")
    out: list[Problem] = []
    for i, r in enumerate(ds):
        if limit is not None and len(out) >= limit:
            break
        p = _build_problem(r, i)
        if p is not None:
            out.append(p)
    return out
