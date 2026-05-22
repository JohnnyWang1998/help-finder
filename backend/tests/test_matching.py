from unittest.mock import MagicMock

from help_finder.matching import (
    normalize_query,
    rank_by_stack_overlap,
    rank_participants,
    resolve_search_query,
    stack_overlap_ratio,
)


def test_rank_participants_streamlit(sample_participants):
    ranked = rank_participants("streamlit", sample_participants, limit=3)
    assert len(ranked) >= 1
    assert ranked[0].participant.githubHandle == "alaska-lam"


def test_rank_participants_react(sample_participants):
    ranked = rank_participants("react", sample_participants, limit=3)
    assert ranked[0].participant.githubHandle == "bme3412"


def test_rank_participants_empty_query(sample_participants):
    assert rank_participants("", sample_participants) == []


def test_normalize_query_synonyms():
    assert "javascript" in normalize_query("js react")
    assert "next.js" in normalize_query("next app")


def test_resolve_search_query_uses_llm():
    llm = MagicMock()
    llm.parse_search_query.return_value = "streamlit, python"
    assert "streamlit" in resolve_search_query("help with my dashboard", llm)
    llm.parse_search_query.assert_called_once()


def test_resolve_search_query_llm_failure_falls_back():
    llm = MagicMock()
    llm.parse_search_query.side_effect = RuntimeError("api down")
    result = resolve_search_query("react", llm)
    assert result == "react"


def test_stack_overlap_ratio():
    a = ["Next.js", "React", "TypeScript"]
    b = ["Next.js", "React", "Python"]
    assert stack_overlap_ratio(a, b) == 2 / 4


def test_rank_by_stack_overlap(sample_participants):
    ranked = rank_by_stack_overlap("bme3412", sample_participants, limit=3)
    assert len(ranked) >= 1
    assert all(r.participant.githubHandle != "bme3412" for r in ranked)
    assert ranked[0].score > 0


def test_rank_by_stack_overlap_unknown_handle(sample_participants):
    assert rank_by_stack_overlap("nobody", sample_participants) == []
