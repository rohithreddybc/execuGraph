"""Evaluator agent: the acceptance authority.

Runs the candidate code in a subprocess sandbox and applies a hybrid
testing strategy:

1. If the problem ships its own deterministic test list (the curated
   benchmark), use that.
2. Else, ask a code-LLM to emit a JSON test-suite and run it.
3. Else, fall back to a smoke test (executes-without-error) and mark
   the trial as test-poor.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ..benchmarks.base import Problem, TestCase
from ..execution.code_sanitize import sanitize_code
from ..execution.sandbox import run_in_sandbox
from ..llm.base import CostAccumulator, LLMBackend
from .base import load_prompt


@dataclass
class EvaluationResult:
    passed: bool
    test_results: list[dict[str, Any]] = field(default_factory=list)
    error_class: str = "none"
    stderr: str = ""
    test_source: str = "deterministic"  # one of: deterministic, llm, smoke
    tests_total: int = 0
    tests_passed: int = 0


def _try_parse_value(s: str):
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        return s


def _aliased_call(call: str, aliases: list[str]) -> str:
    """Replace the function name in ``call`` with each alias until one matches the candidate."""
    return call


def _build_call(case: TestCase, candidate_function_names: list[str], primary: str) -> str:
    """Build a Python call expression. The first function name from
    ``candidate_function_names`` actually present in the namespace will be tried."""
    if case.call:
        return case.call
    args = ", ".join(repr(a) for a in case.args or ())
    return f"{primary}({args})"


def _equal(a: Any, b: Any) -> bool:
    """Robust equality that tolerates list-vs-tuple and value-string roundtrips."""
    if a == b:
        return True
    try:
        return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    except Exception:
        return repr(a) == repr(b)


def _evaluate_with_tests(
    code: str, tests: list[TestCase], primary_name: str, aliases: list[str], timeout_s: float
) -> EvaluationResult:
    sanitized = sanitize_code(code)

    # Script-mode: APPS-style problems where every test has a pre-built call
    # expression and no named function is expected.  Skip the probe entirely.
    script_mode = primary_name == "__script__" or all(c.call for c in tests)

    if script_mode:
        fn_name = "__script__"
    else:
        # Determine which function name in the candidate is actually callable.
        probe = run_in_sandbox(
            sanitized,
            call=f"[n for n in {aliases + [primary_name]!r} if n in globals() and callable(globals()[n])]",
            timeout_s=timeout_s,
        )
        if not probe.ok:
            return EvaluationResult(
                passed=False,
                error_class=probe.error_class,
                stderr=probe.stderr,
                test_source="deterministic",
                tests_total=len(tests),
                tests_passed=0,
            )
        available = probe.return_value or []
        if not isinstance(available, list) or not available:
            return EvaluationResult(
                passed=False,
                error_class="runtime",
                stderr=f"none of {aliases + [primary_name]} were defined",
                test_source="deterministic",
                tests_total=len(tests),
                tests_passed=0,
            )
        fn_name = available[0]

    results: list[dict[str, Any]] = []
    n_pass = 0
    overall_error = "none"
    for case in tests:
        call = case.call or _build_call(case, [], fn_name)
        # If the user-supplied call hardcodes an alias, swap it (function mode only).
        if case.call and not script_mode:
            for alias in aliases + [primary_name]:
                if alias != fn_name:
                    call = re.sub(rf"\b{re.escape(alias)}\b", fn_name, call)
        r = run_in_sandbox(sanitized, call=call, timeout_s=timeout_s)
        if not r.ok:
            results.append({
                "description": case.description,
                "call": call,
                "expected": case.expected,
                "got": None,
                "error": r.error_class,
                "stderr": r.stderr[:400],
                "passed": False,
            })
            if overall_error == "none":
                overall_error = r.error_class
            continue
        ok = case.judge(r.return_value) if case.judge else _equal(r.return_value, case.expected)
        results.append({
            "description": case.description,
            "call": call,
            "expected": case.expected,
            "got": r.return_value,
            "passed": bool(ok),
            "error": "none",
            "stderr": "",
        })
        if ok:
            n_pass += 1
        elif overall_error == "none":
            overall_error = "wrong_answer"
    passed = (n_pass == len(tests)) and bool(tests)
    return EvaluationResult(
        passed=passed,
        test_results=results,
        error_class="none" if passed else overall_error,
        stderr="" if passed else (results[-1]["stderr"] if results else ""),
        test_source="deterministic",
        tests_total=len(tests),
        tests_passed=n_pass,
    )


def _llm_generate_tests(
    problem_text: str, code: str, backend: LLMBackend, cost: CostAccumulator, seed: int | None
) -> list[TestCase]:
    prompt = load_prompt("evaluator").format(problem=problem_text, code=code)
    resp = backend.invoke(prompt, temperature=0.2, max_tokens=512, seed=seed)
    cost.add(resp)
    m = re.search(r"\{.*\}", resp.content, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out: list[TestCase] = []
    for t in data.get("tests", []):
        call = t.get("call")
        expected = t.get("expected")
        if isinstance(expected, str):
            expected = _try_parse_value(expected)
        if isinstance(call, str) and call.strip():
            out.append(
                TestCase(
                    args=(),
                    expected=expected,
                    description=t.get("description", "llm-generated"),
                    call=call,
                    kind="llm",
                )
            )
    return out


def run_evaluator(
    *,
    problem: Problem,
    code: str,
    backend: LLMBackend | None,
    cost: CostAccumulator,
    seed: int | None = None,
    timeout_s: float = 5.0,
) -> EvaluationResult:
    if problem.tests:
        return _evaluate_with_tests(
            code,
            problem.tests,
            primary_name=problem.primary_function,
            aliases=problem.signature_aliases,
            timeout_s=timeout_s,
        )
    if backend is not None:
        tests = _llm_generate_tests(problem.statement, code, backend, cost, seed)
        if tests:
            res = _evaluate_with_tests(
                code, tests, primary_name=problem.primary_function,
                aliases=problem.signature_aliases, timeout_s=timeout_s,
            )
            res.test_source = "llm"
            return res
    # Smoke fallback: just check that the code parses and executes.
    sanitized = sanitize_code(code)
    r = run_in_sandbox(sanitized, call=None, timeout_s=timeout_s)
    return EvaluationResult(
        passed=r.ok,
        test_results=[{"description": "smoke", "passed": r.ok, "error": r.error_class}],
        error_class=r.error_class,
        stderr=r.stderr,
        test_source="smoke",
        tests_total=1,
        tests_passed=1 if r.ok else 0,
    )
