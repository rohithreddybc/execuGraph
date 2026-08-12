"""Tests for the technique catalogue (no chromadb needed)."""

from __future__ import annotations

from execugraph.memory.TECHNIQUES import TECHNIQUES


def test_technique_count() -> None:
    assert len(TECHNIQUES) == 69


def test_each_technique_has_required_fields() -> None:
    required = {"name", "when_to_use", "core_idea", "time", "space", "mistakes"}
    for i, t in enumerate(TECHNIQUES):
        missing = required - set(t.keys())
        assert not missing, f"technique #{i} missing {missing}"
        for key in required:
            assert isinstance(t[key], str) and t[key].strip(), f"technique #{i} {key!r} empty"


def test_unique_names() -> None:
    names = [t["name"] for t in TECHNIQUES]
    assert len(set(names)) == len(names), "technique names should be unique"
