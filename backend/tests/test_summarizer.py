from unittest.mock import MagicMock

from help_finder.models import Participant
from help_finder.summarizer import enrich_summary, fallback_summary, summarize_readme


README = """# My App

Builds a Next.js dashboard for the cohort.

## Setup
pip install
"""


def test_fallback_summary_first_paragraph():
    summary = fallback_summary(README)
    assert "Next.js dashboard" in summary
    assert "##" not in summary


def test_summarize_readme_uses_cache(tmp_cache):
    llm = MagicMock()
    llm.summarize.return_value = "LLM summary"

    key = "test/repo:abc"
    s1 = summarize_readme(README, llm, key, tmp_cache)
    s2 = summarize_readme(README, llm, key, tmp_cache)

    assert s1 == "LLM summary"
    assert s2 == s1
    llm.summarize.assert_called_once()


def test_summarize_readme_no_llm_uses_fallback(tmp_cache):
    summary = summarize_readme(README, None, "key2", tmp_cache)
    assert "Next.js" in summary


def test_enrich_summary(fake_github, tmp_cache):
    p = Participant.base_from_submission(
        {
            "githubHandle": "alice",
            "name": "Alice",
            "repoUrl": "https://github.com/alice/app",
            "pitch": "pitch",
        }
    )
    p.repoPrivate = False
    enriched = enrich_summary(p, fake_github, None, tmp_cache)
    assert "Next.js" in enriched.summary
