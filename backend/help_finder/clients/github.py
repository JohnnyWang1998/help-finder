from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlparse

import httpx

COHORT_OWNER = "rogerSuperBuilderAlpha"
COHORT_REPO = "cursor-boston"
COHORT_REF = "c1w1pm-submission"
SUBMISSIONS_DIR = "content/summer-cohort/c1/w1-pm/submissions"
API_BASE = "https://api.github.com"


class GitHubApiError(Exception):
    def __init__(self, status_code: int, message: str = "") -> None:
        self.status_code = status_code
        super().__init__(message or f"GitHub API error {status_code}")


@runtime_checkable
class GitHubClientProtocol(Protocol):
    def list_submission_files(self) -> list[str]:
        """Return paths to submission JSON files under the cohort submissions directory."""

    def get_file_content(self, path: str) -> str:
        """Return decoded text content for a file in the cohort repo."""

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Return language → byte count map from /repos/{owner}/{repo}/languages."""

    def get_readme(self, owner: str, repo: str) -> str | None:
        """Return README body text, or None if missing."""

    def get_commits(self, owner: str, repo: str, since: datetime) -> list[dict[str, Any]]:
        """Return commit objects since the given UTC datetime."""

    def get_repo_file(self, owner: str, repo: str, file_path: str) -> str | None:
        """Return file content from a participant repo, or None if missing."""


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Input: GitHub repo URL. Output: (owner, repo) tuple."""
    path = urlparse(repo_url).path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid repo URL: {repo_url}")
    return parts[0], parts[1]


class GitHubClient:
    """Live GitHub API client."""

    def __init__(self, token: str | None = None) -> None:
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(base_url=API_BASE, headers=headers, timeout=30.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = self._client.get(path, params=params)
        if response.status_code == 404:
            raise GitHubApiError(404)
        response.raise_for_status()
        return response.json()

    def list_submission_files(self) -> list[str]:
        data = self._get(
            f"/repos/{COHORT_OWNER}/{COHORT_REPO}/contents/{SUBMISSIONS_DIR}",
            params={"ref": COHORT_REF},
        )
        return sorted(
            item["path"]
            for item in data
            if item["type"] == "file" and item["name"].endswith(".json")
        )

    def get_file_content(self, path: str) -> str:
        data = self._get(
            f"/repos/{COHORT_OWNER}/{COHORT_REPO}/contents/{path}",
            params={"ref": COHORT_REF},
        )
        content = data.get("content", "")
        if data.get("encoding") == "base64":
            return base64.b64decode(content).decode("utf-8")
        return content

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        return dict(self._get(f"/repos/{owner}/{repo}/languages"))

    def get_readme(self, owner: str, repo: str) -> str | None:
        try:
            data = self._get(f"/repos/{owner}/{repo}/readme")
        except GitHubApiError as exc:
            if exc.status_code == 404:
                return None
            raise
        content = data.get("content", "")
        if data.get("encoding") == "base64":
            return base64.b64decode(content).decode("utf-8")
        return content

    def get_commits(
        self, owner: str, repo: str, since: datetime
    ) -> list[dict[str, Any]]:
        since_iso = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            return list(
                self._get(
                    f"/repos/{owner}/{repo}/commits",
                    params={"since": since_iso, "per_page": 100},
                )
            )
        except GitHubApiError as exc:
            if exc.status_code == 404:
                return []
            raise

    def get_repo_file(self, owner: str, repo: str, file_path: str) -> str | None:
        """Fetch a single file from a participant repo (e.g. package.json)."""
        try:
            data = self._get(f"/repos/{owner}/{repo}/contents/{file_path}")
        except GitHubApiError as exc:
            if exc.status_code == 404:
                return None
            raise
        content = data.get("content", "")
        if data.get("encoding") == "base64":
            return base64.b64decode(content).decode("utf-8")
        return content


class FakeGitHubClient:
    """Test double returning canned responses from constructor kwargs."""

    def __init__(
        self,
        submission_files: list[str] | None = None,
        file_contents: dict[str, str] | None = None,
        languages: dict[tuple[str, str], dict[str, int]] | None = None,
        readmes: dict[tuple[str, str], str | None] | None = None,
        commits: dict[tuple[str, str], list[dict[str, Any]]] | None = None,
        repo_files: dict[tuple[str, str, str], str | None] | None = None,
        private_repos: set[tuple[str, str]] | None = None,
    ) -> None:
        self.submission_files = submission_files or []
        self.file_contents = file_contents or {}
        self.languages = languages or {}
        self.readmes = readmes or {}
        self.commits = commits or {}
        self.repo_files = repo_files or {}
        self.private_repos = private_repos or set()

    def list_submission_files(self) -> list[str]:
        return list(self.submission_files)

    def get_file_content(self, path: str) -> str:
        return self.file_contents[path]

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        if (owner, repo) in self.private_repos:
            raise GitHubApiError(404)
        return dict(self.languages.get((owner, repo), {}))

    def get_readme(self, owner: str, repo: str) -> str | None:
        if (owner, repo) in self.private_repos:
            return None
        return self.readmes.get((owner, repo))

    def get_commits(
        self, owner: str, repo: str, since: datetime
    ) -> list[dict[str, Any]]:
        if (owner, repo) in self.private_repos:
            return []
        all_commits = self.commits.get((owner, repo), [])
        return [
            c
            for c in all_commits
            if _commit_date(c) >= since.astimezone(timezone.utc)
        ]

    def get_repo_file(self, owner: str, repo: str, file_path: str) -> str | None:
        if (owner, repo) in self.private_repos:
            return None
        return self.repo_files.get((owner, repo, file_path))


def _commit_date(commit: dict[str, Any]) -> datetime:
    commit_data = commit.get("commit", {})
    date_str = commit_data.get("author", {}).get("date") or commit_data.get(
        "committer", {}
    ).get("date", "")
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
