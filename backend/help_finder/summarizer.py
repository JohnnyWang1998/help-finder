from __future__ import annotations

import hashlib
import re
from pathlib import Path

from help_finder.clients.github import GitHubClientProtocol, parse_repo_url
from help_finder.clients.llm import LlmClientProtocol
from help_finder.models import Participant


def fallback_summary(readme_text: str) -> str:
    """Input: README markdown. Output: first non-empty paragraph as one line."""
    lines = readme_text.replace("\r\n", "\n").split("\n")
    paragraph_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if paragraph_lines:
                break
            continue
        if not stripped:
            if paragraph_lines:
                break
            continue
        paragraph_lines.append(stripped)
    text = " ".join(paragraph_lines).strip()
    if not text:
        return ""
    # collapse whitespace
    return re.sub(r"\s+", " ", text)[:300]


def _cache_path(cache_dir: Path, cache_key: str) -> Path:
    digest = hashlib.sha256(cache_key.encode()).hexdigest()[:16]
    return cache_dir / f"{digest}.txt"


def summarize_readme(
    readme_text: str,
    llm: LlmClientProtocol | None,
    cache_key: str,
    cache_dir: Path,
) -> str:
    """Input: README text, optional LLM, cache key/dir. Output: one-line summary."""
    cache_file = _cache_path(cache_dir, cache_key)
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8").strip()

    if llm is not None:
        try:
            summary = llm.summarize(readme_text)
        except Exception:
            summary = fallback_summary(readme_text)
    else:
        summary = fallback_summary(readme_text)

    if summary:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(summary, encoding="utf-8")
    return summary


def enrich_summary(
    participant: Participant,
    client: GitHubClientProtocol,
    llm: LlmClientProtocol | None,
    cache_dir: Path,
) -> Participant:
    """Fetch README and set participant.summary."""
    if participant.repoPrivate:
        return participant

    owner, repo = parse_repo_url(participant.repoUrl)
    readme = client.get_readme(owner, repo)
    if not readme:
        participant.summary = participant.pitch[:300] if participant.pitch else ""
        return participant

    cache_key = f"{owner}/{repo}:{hashlib.sha256(readme.encode()).hexdigest()[:12]}"
    participant.summary = summarize_readme(readme, llm, cache_key, cache_dir)
    return participant
