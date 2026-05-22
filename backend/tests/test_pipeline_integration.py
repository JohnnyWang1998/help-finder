import os

import pytest

from help_finder.pipeline import run_ingest


@pytest.mark.integration
def test_run_ingest_live_github(tmp_path):
    if not os.environ.get("GITHUB_TOKEN", "").strip():
        pytest.skip("GITHUB_TOKEN not set")

    out = tmp_path / "participants.json"
    cache = tmp_path / "cache"
    participants = run_ingest(output_path=out, cache_dir=cache)

    assert len(participants) >= 1
    data = out.read_text()
    assert "githubHandle" in data
    first = participants[0]
    assert first.githubHandle
    assert first.name
