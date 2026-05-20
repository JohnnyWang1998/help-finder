from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from help_finder.activity import enrich_activity
from help_finder.models import Participant


def _commit(iso_date: str) -> dict[str, Any]:
    return {"commit": {"author": {"date": iso_date}}}


def test_enrich_activity_counts_last_7_days():
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old = (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    p = Participant(
        githubHandle="u",
        name="U",
        avatarUrl="",
        repoUrl="https://github.com/u/r",
        liveUrl="",
        pitch="",
    )
    commits = [_commit(recent), _commit(recent), _commit(old)]
    enriched = enrich_activity(p, commits)

    assert enriched.commitsLast7d == 2
    assert enriched.lastCommitAt.endswith("Z")


def test_enrich_activity_empty():
    p = Participant(
        githubHandle="u",
        name="U",
        avatarUrl="",
        repoUrl="https://github.com/u/r",
        liveUrl="",
        pitch="",
    )
    enriched = enrich_activity(p, [])
    assert enriched.commitsLast7d == 0
    assert enriched.lastCommitAt == ""
