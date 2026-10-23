"""Motor predictivo y alias tests."""

from __future__ import annotations

from pathlib import Path

from abril.services.sqlite_memory import SQLiteMemory
from abril.services.predictive import PredictiveEngine, build_predictive_engine


def test_predictive_engine_learns_alias(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    engine = PredictiveEngine(db)

    engine.learn_from_interaction("gh", "git status")
    engine.learn_from_interaction("gh", "git status")
    engine.learn_from_interaction("gh", "git status")

    aliases = engine.list_aliases()
    assert len(aliases) == 1
    assert aliases[0].trigger == "gh"
    assert aliases[0].expansion == "git status"
    assert aliases[0].count == 3


def test_predictive_expand_alias_above_threshold(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    engine = PredictiveEngine(db, min_count=2, min_confidence=0.5)

    engine.learn_from_interaction("gh", "git status")
    engine.learn_from_interaction("gh", "git status")

    expanded = engine.expand_alias("gh")
    assert expanded == "git status"

    expanded = engine.expand_alias("gh extra")
    assert expanded == "git status extra"


def test_predictive_no_expand_below_threshold(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    engine = PredictiveEngine(db, min_count=3, min_confidence=0.7)

    engine.learn_from_interaction("gh", "git status")
    engine.learn_from_interaction("gh", "git status")

    expanded = engine.expand_alias("gh")
    assert expanded == "gh"  # no expande


def test_predictive_suggestions_include_aliases(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    engine = PredictiveEngine(db)

    engine.learn_from_interaction("gh", "git status")
    engine.learn_from_interaction("gh", "git status")
    engine.learn_from_interaction("gh", "git status")

    suggestions = engine.get_suggestions("g", limit=5)
    assert any(s.kind == "alias" and s.metadata["trigger"] == "gh" for s in suggestions)


def test_predictive_suggestions_include_completions(tmp_path: Path):
    db = SQLiteMemory(tmp_path / "test.db")
    engine = PredictiveEngine(db)

    suggestions = engine.get_suggestions("/ana", limit=5)
    assert any(s.kind == "completion" and s.metadata["command"] == "/analizar" for s in suggestions)


def test_build_predictive_engine():
    db = SQLiteMemory(Path("/tmp/test.db"))
    engine = build_predictive_engine(db)
    assert isinstance(engine, PredictiveEngine)