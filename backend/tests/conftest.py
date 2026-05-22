from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from help_finder.clients.github import FakeGitHubClient
from help_finder.models import Participant

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_submission_minimal() -> dict[str, Any]:
    return json.loads((FIXTURES / "submission_minimal.json").read_text())


@pytest.fixture
def sample_submission_no_live_url() -> dict[str, Any]:
    return json.loads((FIXTURES / "submission_no_live_url.json").read_text())


@pytest.fixture
def sample_participants() -> list[Participant]:
    return [
        Participant(
            githubHandle="alaska-lam",
            name="Alaska Lam",
            avatarUrl="https://github.com/alaska-lam.png",
            repoUrl="https://github.com/alaska-lam/cohort-dashboard",
            liveUrl="",
            pitch="Streamlit dashboard",
            summary="Analytics with Streamlit",
            techStack=["Python", "Streamlit", "Plotly", "TypeScript"],
            languages={"Python": 1000},
            lastCommitAt="2026-05-18T09:15:00Z",
            commitsLast7d=5,
        ),
        Participant(
            githubHandle="bme3412",
            name="Brendan Erhard",
            avatarUrl="https://github.com/bme3412.png",
            repoUrl="https://github.com/bme3412/boston-cursor-week-1",
            liveUrl="https://example.com",
            pitch="Launchpad feed",
            summary="Next.js cohort feed",
            techStack=["Next.js", "React", "TypeScript"],
            languages={"TypeScript": 200000},
            lastCommitAt="2026-05-19T14:30:00Z",
            commitsLast7d=10,
        ),
    ]


@pytest.fixture
def fake_github() -> FakeGitHubClient:
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    older = (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    package_json = json.dumps(
        {
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.0.0",
                "@types/react": "^18.0.0",
            }
        }
    )

    return FakeGitHubClient(
        submission_files=[
            "content/summer-cohort/c1/w1-pm/submissions/alice.json",
            "content/summer-cohort/c1/w1-pm/submissions/bob.json",
        ],
        file_contents={
            "content/summer-cohort/c1/w1-pm/submissions/alice.json": json.dumps(
                {
                    "githubHandle": "alice",
                    "name": "Alice",
                    "repoUrl": "https://github.com/alice/app",
                    "liveUrl": "https://alice.dev",
                    "pitch": "Alice app",
                }
            ),
            "content/summer-cohort/c1/w1-pm/submissions/bob.json": json.dumps(
                {
                    "githubHandle": "bob",
                    "name": "Bob",
                    "repoUrl": "https://github.com/bob/private-app",
                    "pitch": "Bob WIP",
                }
            ),
        },
        languages={
            ("alice", "app"): {"TypeScript": 5000, "CSS": 200},
        },
        readmes={
            ("alice", "app"): "# Alice App\n\nBuilds a Next.js dashboard for the cohort.\n\n## Setup\n",
        },
        commits={
            ("alice", "app"): [
                {"commit": {"author": {"date": recent}}},
                {"commit": {"author": {"date": recent}}},
                {"commit": {"author": {"date": older}}},
            ],
        },
        repo_files={
            ("alice", "app", "package.json"): package_json,
        },
        private_repos={("bob", "private-app")},
    )


@pytest.fixture
def tmp_cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"
