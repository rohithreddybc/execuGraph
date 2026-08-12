"""Evaluator tests using the deterministic test path (no LLM required)."""

from __future__ import annotations

from execugraph.agents.evaluator import run_evaluator
from execugraph.benchmarks.internal30 import load_internal30
from execugraph.llm.base import CostAccumulator


def _problem(pid: str):
    for p in load_internal30():
        if p.id == pid:
            return p
    raise AssertionError(pid)


def test_evaluator_passes_correct_fib() -> None:
    code = """
def fib(n):
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b
""".strip()
    res = run_evaluator(
        problem=_problem("fib"),
        code=code,
        backend=None,
        cost=CostAccumulator(),
        timeout_s=4.0,
    )
    assert res.passed, res.test_results
    assert res.test_source == "deterministic"
    assert res.tests_passed == res.tests_total


def test_evaluator_rejects_wrong_fib() -> None:
    code = "def fib(n): return n + 1"  # wrong
    res = run_evaluator(
        problem=_problem("fib"),
        code=code,
        backend=None,
        cost=CostAccumulator(),
        timeout_s=4.0,
    )
    assert not res.passed
    assert res.error_class == "wrong_answer"


def test_alias_resolution_climb_stairs() -> None:
    # User defined under an alias: climb_stairs (signature_aliases)
    code = """
def climb_stairs(n):
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(n - 2):
        a, b = b, a + b
    return b
""".strip()
    res = run_evaluator(
        problem=_problem("climb_stairs"),
        code=code,
        backend=None,
        cost=CostAccumulator(),
        timeout_s=4.0,
    )
    assert res.passed, res.test_results


def test_runtime_error_classified() -> None:
    code = "def fib(n): return 1/0"
    res = run_evaluator(
        problem=_problem("fib"),
        code=code,
        backend=None,
        cost=CostAccumulator(),
        timeout_s=4.0,
    )
    assert not res.passed
    assert res.error_class == "runtime"


def test_topo_judge_accepts_valid_orders() -> None:
    code = """
from collections import defaultdict, deque
def findOrder(numCourses, prerequisites):
    g = defaultdict(list)
    indeg = [0]*numCourses
    for a, b in prerequisites:
        g[b].append(a)
        indeg[a] += 1
    q = deque([i for i in range(numCourses) if indeg[i] == 0])
    out = []
    while q:
        u = q.popleft()
        out.append(u)
        for v in g[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return out if len(out) == numCourses else []
""".strip()
    res = run_evaluator(
        problem=_problem("topo_sort"),
        code=code,
        backend=None,
        cost=CostAccumulator(),
        timeout_s=4.0,
    )
    assert res.passed, res.test_results
