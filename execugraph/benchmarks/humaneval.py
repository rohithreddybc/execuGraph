"""HumanEval benchmark loader.

Loads the 164 HumanEval problems via the ``datasets`` library and converts
each instance to an ExecuGraph :class:`Problem`. The official tests are
embedded in each problem's `test` field as a Python source string that
defines a ``check(candidate)`` function; we wrap that as a single
:class:`TestCase` whose ``call`` invokes ``check`` against the entry
point that the model was asked to implement.

Reference: Chen et al., "Evaluating Large Language Models Trained on
Code", arXiv:2107.03374, 2021.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .base import Problem, TestCase

_DATASET_NAME = "openai_humaneval"


def _split_into_signature_aliases(entry_point: str) -> list[str]:
    """HumanEval uses one canonical entry point per task. We pass it as the
    primary function and accept a couple of common stylistic variants
    (snake_case <-> camelCase) as aliases."""
    aliases = [entry_point]
    if "_" in entry_point:
        # snake_case -> camelCase
        head, *rest = entry_point.split("_")
        aliases.append(head + "".join(p.capitalize() for p in rest))
    elif re.search(r"[a-z][A-Z]", entry_point):
        # camelCase -> snake_case
        aliases.append(re.sub(r"(?<!^)(?=[A-Z])", "_", entry_point).lower())
    return aliases


def _build_problem(record: dict) -> Problem:
    """Convert one HuggingFace HumanEval record to a :class:`Problem`."""
    task_id: str = record["task_id"]  # e.g. "HumanEval/0"
    entry_point: str = record["entry_point"]
    prompt: str = record["prompt"]
    tests_src: str = record["test"]

    statement = (
        "Implement the function whose signature and docstring are given below.\n\n"
        f"{prompt}\n\n"
        "Return only the body / completed function source. The reference "
        f"check function is named 'check' and is invoked as check({entry_point})."
    )

    # The driver that runs in the sandbox: install the candidate, install the
    # check function the dataset provides, then invoke check(entry_point).
    # We surface a 1-tuple result for the judge (True if no AssertionError).
    driver_call = (
        "(lambda: ("
        f"exec(compile({tests_src!r}, '<humaneval-test>', 'exec'), globals(), globals()) "
        f"or check({entry_point}) or True))()"
    )

    return Problem(
        id=task_id.replace("/", "_").lower(),
        category="humaneval",
        source=f"humaneval/{task_id.split('/')[-1]}",
        statement=statement,
        primary_function=entry_point,
        signature_aliases=_split_into_signature_aliases(entry_point),
        tests=[
            TestCase(
                call=driver_call,
                expected=True,
                description=task_id,
                kind="deterministic",
            )
        ],
        selection_rationale="Official HumanEval task.",
        difficulty="medium",
        timeout_s=10.0,
    )


def load_humaneval(*, limit: int | None = None) -> list[Problem]:
    """Load the HumanEval test split.

    Requires ``datasets`` (already in ``pyproject.toml``). The first call
    will download ~3 MB into the HuggingFace cache.
    """
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise RuntimeError(
            "Loading HumanEval requires the `datasets` package. "
            "Run `pip install -e .` or `pip install datasets`."
        ) from e
    ds = load_dataset(_DATASET_NAME, split="test")
    out: list[Problem] = []
    for i, record in enumerate(ds):
        if limit is not None and i >= limit:
            break
        out.append(_build_problem(record))
    return out


def iter_humaneval() -> Iterable[Problem]:
    yield from load_humaneval()


if __name__ == "__main__":  # pragma: no cover
    ps = load_humaneval(limit=3)
    for p in ps:
        print(p.id, "->", p.primary_function)
