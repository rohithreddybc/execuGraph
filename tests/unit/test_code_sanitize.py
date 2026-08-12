from execugraph.execution.code_sanitize import extract_python_block, sanitize_code


def test_strips_fences() -> None:
    assert sanitize_code("```python\ndef f(): return 1\n```").startswith("def f")


def test_strips_polite_preamble() -> None:
    s = "Sure! Here is the solution:\ndef f(): return 1\n"
    out = sanitize_code(s)
    assert out.startswith("def f")


def test_extract_block_picks_python_first() -> None:
    src = "noise\n```python\ndef f(): return 1\n```\nmore noise"
    assert extract_python_block(src) == "def f(): return 1"


def test_no_fence_falls_through() -> None:
    src = "def g(): return 2"
    assert "def g" in extract_python_block(src)


def test_empty_input_safe() -> None:
    assert sanitize_code("") == ""
    assert extract_python_block("") == ""
