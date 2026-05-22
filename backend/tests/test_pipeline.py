import json
from unittest.mock import patch

from help_finder.pipeline import run_ingest


def test_run_ingest_writes_json(fake_github, tmp_path):
    out = tmp_path / "participants.json"
    cache = tmp_path / "cache"

    with patch("help_finder.pipeline.build_llm_client", return_value=None):
        result = run_ingest(
            github=fake_github,
            llm=None,
            output_path=out,
            cache_dir=cache,
        )

    assert len(result) == 2
    data = json.loads(out.read_text())
    assert len(data) == 2
    alice = next(d for d in data if d["githubHandle"] == "alice")
    assert alice["techStack"]
    assert alice["summary"]
    bob = next(d for d in data if d["githubHandle"] == "bob")
    assert bob["repoPrivate"] is True
