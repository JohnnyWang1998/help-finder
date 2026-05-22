from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from help_finder.activity import enrich_activity_from_client
from help_finder.analyzer import enrich_from_repo
from help_finder.clients.github import GitHubClient, GitHubClientProtocol
from help_finder.clients.llm import LlmClientProtocol, build_llm_client
from help_finder.models import Participant
from help_finder.submissions import fetch_participants
from help_finder.summarizer import enrich_summary


def default_paths() -> tuple[Path, Path, Path]:
    """Return (output_json, cache_dir, repo_root) relative to project layout."""
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent
    return (
        repo_root / "data" / "participants.json",
        repo_root / "data" / "cache",
        repo_root,
    )


def run_ingest(
    *,
    github: GitHubClientProtocol | None = None,
    llm: LlmClientProtocol | None = None,
    output_path: Path | None = None,
    cache_dir: Path | None = None,
) -> list[Participant]:
    """Run full ingest pipeline A2→A5 and write participants.json."""
    load_dotenv()

    out, cache, _ = default_paths()
    if output_path is not None:
        out = output_path
    if cache_dir is not None:
        cache = cache_dir

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token and github is None:
        print(
            "Warning: GITHUB_TOKEN not set — ingest will hit rate limits quickly. "
            "Add it to backend/.env",
            flush=True,
        )
    owns_client = github is None
    client = github or GitHubClient(token=token or None)
    llm_client = llm if llm is not None else build_llm_client()

    try:
        participants = fetch_participants(client)
        enriched: list[Participant] = []
        for p in participants:
            p = enrich_from_repo(p, client)
            p = enrich_summary(p, client, llm_client, cache)
            p = enrich_activity_from_client(p, client)
            enriched.append(p)

        out.parent.mkdir(parents=True, exist_ok=True)
        payload = [p.to_dict() for p in enriched]
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return enriched
    finally:
        if owns_client and isinstance(client, GitHubClient):
            client.close()
