from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from help_finder.clients.github import GitHubClientProtocol, _commit_date, parse_repo_url
from help_finder.models import Participant


def enrich_activity(
    participant: Participant, commits: list[dict[str, Any]]
) -> Participant:
    """Input: participant + commit payloads. Output: participant with activity fields."""
    if not commits:
        participant.lastCommitAt = ""
        participant.commitsLast7d = 0
        return participant

    dates = [_commit_date(c) for c in commits]
    latest = max(dates)
    participant.lastCommitAt = latest.astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    participant.commitsLast7d = sum(1 for d in dates if d >= cutoff)
    return participant


def enrich_activity_from_client(
    participant: Participant,
    client: GitHubClientProtocol,
    *,
    days: int = 7,
) -> Participant:
    """Fetch commits via GitHub client and enrich activity fields."""
    if participant.repoPrivate:
        return participant

    owner, repo = parse_repo_url(participant.repoUrl)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    commits = client.get_commits(owner, repo, since)
    return enrich_activity(participant, commits)
