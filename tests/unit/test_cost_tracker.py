from execugraph.llm.base import CostAccumulator, LLMResponse


def test_cost_accumulates() -> None:
    cost = CostAccumulator()
    cost.add(LLMResponse(content="a", tokens_in=10, tokens_out=5, wallclock_s=0.1))
    cost.add(LLMResponse(content="b", tokens_in=20, tokens_out=15, wallclock_s=0.2))
    d = cost.to_dict()
    assert d["tokens_in"] == 30
    assert d["tokens_out"] == 20
    assert d["calls"] == 2
    assert d["wallclock_s"] >= 0.3 - 1e-9


def test_zero_state() -> None:
    assert CostAccumulator().to_dict() == {"tokens_in": 0, "tokens_out": 0, "wallclock_s": 0.0, "calls": 0}
