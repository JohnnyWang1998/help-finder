import json
from pathlib import Path

from help_finder.models import Participant

SCHEMA_KEYS = {
    "githubHandle",
    "name",
    "avatarUrl",
    "repoUrl",
    "liveUrl",
    "pitch",
    "summary",
    "techStack",
    "languages",
    "lastCommitAt",
    "commitsLast7d",
    "repoPrivate",
}


def test_round_trip_serialization():
    p = Participant(
        githubHandle="user",
        name="User",
        avatarUrl="https://github.com/user.png",
        repoUrl="https://github.com/user/repo",
        liveUrl="",
        pitch="Hi",
        summary="Summary",
        techStack=["Python"],
        languages={"Python": 100},
        lastCommitAt="2026-05-01T00:00:00Z",
        commitsLast7d=3,
        repoPrivate=False,
    )
    restored = Participant.from_dict(p.to_dict())
    assert restored == p


def test_sample_json_matches_schema():
    repo_root = Path(__file__).resolve().parents[2]
    sample_path = repo_root / "data" / "participants.sample.json"
    data = json.loads(sample_path.read_text())
    assert len(data) == 3
    for entry in data:
        assert set(entry.keys()) == SCHEMA_KEYS
        Participant.from_dict(entry)


def test_base_from_submission(sample_submission_minimal):
    p = Participant.base_from_submission(sample_submission_minimal)
    assert p.githubHandle == "testuser"
    assert p.avatarUrl == "https://github.com/testuser.png"
    assert p.summary == ""
    assert p.techStack == []
