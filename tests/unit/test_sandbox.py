"""Sandbox safety + correctness tests."""

from __future__ import annotations

import pytest

from execugraph.execution.sandbox import run_in_sandbox


def test_valid_function_call() -> None:
    r = run_in_sandbox("def f(n): return n*n", call="f(7)")
    assert r.ok
    assert r.return_value == 49
    assert r.error_class == "none"


def test_blocks_os_import() -> None:
    r = run_in_sandbox("import os\nx = os.getcwd()", call="x")
    assert not r.ok
    assert r.error_class == "sandbox_violation"
    assert "sandbox" in r.stderr.lower()


def test_blocks_subprocess_import() -> None:
    r = run_in_sandbox("import subprocess", call=None)
    assert not r.ok
    assert r.error_class == "sandbox_violation"


def test_blocks_socket_import() -> None:
    r = run_in_sandbox("import socket", call=None)
    assert not r.ok


def test_runtime_error_classified() -> None:
    r = run_in_sandbox("def f():\n    return 1/0", call="f()")
    assert not r.ok
    assert r.error_class == "runtime"


def test_syntax_error_classified() -> None:
    r = run_in_sandbox("def broken(:", call="broken()")
    assert not r.ok
    assert r.error_class == "syntax"


def test_timeout() -> None:
    r = run_in_sandbox("while True: pass", call=None, timeout_s=1.0)
    assert not r.ok
    assert r.error_class == "timeout"


def test_allowed_module_import() -> None:
    r = run_in_sandbox(
        "from collections import deque\n"
        "def f(): q = deque([1,2,3]); return list(q)",
        call="f()",
    )
    assert r.ok, r.stderr
    assert r.return_value == [1, 2, 3]


def test_open_is_removed() -> None:
    r = run_in_sandbox("def f(): return open('x')", call="f()")
    assert not r.ok


# ---------------------------------------------------------------------------
# Reference-solution control.
#
# The original experiment grid was scored by a sandbox whose import guard
# rejected allow-listed modules through their private C accelerators
# (``bisect`` -> ``_bisect``), so textbook-correct programs were recorded as
# sandbox violations. The defect was invisible because nothing asserted that a
# known-good solution actually passes. These tests are that assertion: if the
# import policy regresses, they fail here rather than in a results table.
# ---------------------------------------------------------------------------

REFERENCE_SOLUTIONS = [
    (
        "bisect",
        "import bisect\n"
        "def lengthOfLIS(nums):\n"
        "    dp = []\n"
        "    for n in nums:\n"
        "        i = bisect.bisect_left(dp, n)\n"
        "        if i == len(dp): dp.append(n)\n"
        "        else: dp[i] = n\n"
        "    return len(dp)",
        "lengthOfLIS([10,9,2,5,3,7,101,18])",
        4,
    ),
    (
        "heapq",
        "import heapq\n"
        "def kth_smallest(xs, k):\n"
        "    h = list(xs); heapq.heapify(h)\n"
        "    for _ in range(k-1): heapq.heappop(h)\n"
        "    return heapq.heappop(h)",
        "kth_smallest([7,10,4,3,20,15], 3)",
        7,
    ),
    (
        "collections",
        "from collections import defaultdict, deque\n"
        "def bfs_order(n, edges):\n"
        "    g = defaultdict(list)\n"
        "    for a, b in edges: g[a].append(b)\n"
        "    seen, out, q = {0}, [], deque([0])\n"
        "    while q:\n"
        "        u = q.popleft(); out.append(u)\n"
        "        for v in g[u]:\n"
        "            if v not in seen: seen.add(v); q.append(v)\n"
        "    return out",
        "bfs_order(4, [[0,1],[0,2],[1,3]])",
        [0, 1, 2, 3],
    ),
    (
        "functools",
        "import functools\n"
        "@functools.lru_cache(None)\n"
        "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)",
        "fib(30)",
        832040,
    ),
    (
        "itertools+math",
        "import itertools, math\n"
        "def f(): return len(list(itertools.permutations([1,2,3]))) + int(math.sqrt(9))",
        "f()",
        9,
    ),
    (
        "re",
        r"import re" "\n" r"def f(): return len(re.findall(r'\d+', 'a1b22c333'))",
        "f()",
        3,
    ),
]


@pytest.mark.parametrize(
    "label,code,call,expected",
    REFERENCE_SOLUTIONS,
    ids=[s[0] for s in REFERENCE_SOLUTIONS],
)
def test_reference_solution_passes(label, code, call, expected) -> None:
    """A known-correct solution must pass; a sandbox that fails it is broken."""
    r = run_in_sandbox(code, call=call, timeout_s=10.0)
    assert r.ok, f"{label}: correct program rejected -> {r.error_class}: {r.stderr}"
    assert r.error_class == "none", f"{label}: {r.error_class}"
    assert r.return_value == expected, f"{label}: got {r.return_value!r}"


def test_no_spurious_sandbox_violation_on_stdlib() -> None:
    """No allow-listed stdlib import may report a sandbox violation."""
    for module in ("bisect", "heapq", "collections", "itertools", "functools",
                   "math", "re", "json", "string", "array", "statistics"):
        r = run_in_sandbox(f"import {module}\ndef f(): return 1", call="f()")
        assert r.error_class != "sandbox_violation", (
            f"allow-listed module {module!r} reported a sandbox violation: {r.stderr}"
        )


def test_parent_environment_is_not_inherited(monkeypatch) -> None:
    """Generated code must not be able to read parent credentials."""
    monkeypatch.setenv("HF_TOKEN", "SECRET_canary_value")
    r = run_in_sandbox(
        "import sys\ndef f(): return sys.modules['os'].environ.get('HF_TOKEN')",
        call="f()",
    )
    assert r.return_value != "SECRET_canary_value", "parent environment leaked"


def test_module_graph_escape_is_blocked() -> None:
    """sys.modules must not be reachable as a route to os."""
    r = run_in_sandbox("import sys\ndef f(): return sys.modules['os'].name", call="f()")
    assert not r.ok


def test_io_open_is_blocked() -> None:
    """io.open is builtins.open under another name and must not write files."""
    r = run_in_sandbox(
        "import io\ndef f():\n    io.open('pwned.txt','w').write('x')\n    return 'wrote'",
        call="f()",
    )
    assert not r.ok
