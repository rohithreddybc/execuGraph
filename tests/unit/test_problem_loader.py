from execugraph.benchmarks.internal30 import load_internal30


def test_loads_30_problems() -> None:
    problems = load_internal30()
    assert len(problems) == 30


def test_category_counts() -> None:
    problems = load_internal30()
    counts: dict[str, int] = {}
    for p in problems:
        counts[p.category] = counts.get(p.category, 0) + 1
    assert counts == {"dp": 10, "graph": 10, "ds": 10}


def test_each_problem_has_tests_and_rationale() -> None:
    for p in load_internal30():
        assert p.tests, f"{p.id}: no tests"
        assert p.selection_rationale, f"{p.id}: no selection rationale"
        assert p.statement.strip(), f"{p.id}: empty statement"
        assert p.primary_function, f"{p.id}: no primary function"


def test_apps_problems_marked() -> None:
    problems = load_internal30()
    apps = [p for p in problems if "apps" in p.source]
    assert len(apps) == 3
    assert {p.id for p in apps} == {"subset_sum", "grid_shortest_path", "valid_parentheses"}
