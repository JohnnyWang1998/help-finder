from __future__ import annotations

import json
from typing import Any

from help_finder.clients.github import GitHubClientProtocol
from help_finder.models import Participant


def parse_submission(raw: dict[str, Any]) -> Participant:
    """Input: cohort submission JSON. Output: Participant with base fields only."""
    return Participant.base_from_submission(raw)


def fetch_all_submissions(client: GitHubClientProtocol) -> list[dict[str, Any]]:
    """Input: GitHub client. Output: list of raw submission dicts."""
    paths = client.list_submission_files()
    submissions: list[dict[str, Any]] = []
    for path in paths:
        content = client.get_file_content(path)
        submissions.append(json.loads(content))
    return submissions


def fetch_participants(client: GitHubClientProtocol) -> list[Participant]:
    """Fetch and parse all cohort submissions into base participants."""
    return [parse_submission(raw) for raw in fetch_all_submissions(client)]
