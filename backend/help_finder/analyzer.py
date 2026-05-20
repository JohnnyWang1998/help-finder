from __future__ import annotations

import json
import re
from typing import Any

from help_finder.clients.github import GitHubApiError, GitHubClientProtocol, parse_repo_url
from help_finder.models import Participant

# dependency / language name → display tag
_TAG_MAP: dict[str, str] = {
    "next": "Next.js",
    "react": "React",
    "@types/react": "React",
    "vue": "Vue",
    "svelte": "Svelte",
    "tailwindcss": "Tailwind",
    "typescript": "TypeScript",
    "@types/node": "TypeScript",
    "streamlit": "Streamlit",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "supabase": "Supabase",
    "@supabase/supabase-js": "Supabase",
    "prisma": "Prisma",
    "@prisma/client": "Prisma",
    "shadcn": "Shadcn",
    "shadcn-ui": "Shadcn",
}


def normalize_tech_tags(dependency_names: list[str]) -> list[str]:
    """Input: raw dependency/package names. Output: normalized tech tag list."""
    tags: list[str] = []
    seen: set[str] = set()
    for name in dependency_names:
        key = name.lower().strip()
        tag = _TAG_MAP.get(key)
        if not tag:
            # Title-case simple names (e.g. "pandas" → skip unless mapped)
            if key in ("react", "vue", "django"):
                tag = key.title()
            else:
                continue
        if tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def _extract_deps_from_package_json(content: str) -> list[str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []
    deps: list[str] = []
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        deps.extend(data.get(section, {}).keys())
    return deps


def _extract_deps_from_requirements(content: str) -> list[str]:
    names: list[str] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[<>=!~\[]", line)[0].strip()
        if name:
            names.append(name.lower())
    return names


def _extract_deps_from_pyproject(content: str) -> list[str]:
    names: list[str] = []
    in_deps = False
    for line in content.splitlines():
        if re.match(r"\[project\.optional-dependencies\]", line):
            in_deps = False
        if re.match(r"\[project\.dependencies\]", line) or re.match(
            r"dependencies\s*=\s*\[", line
        ):
            in_deps = True
            continue
        if in_deps:
            match = re.search(r'["\']([^"\']+)["\']', line)
            if match:
                pkg = re.split(r"[<>=!~\[]", match.group(1))[0].strip()
                if pkg:
                    names.append(pkg.lower())
    return names


def _language_tags(languages: dict[str, int]) -> list[str]:
    """Map GitHub language names to stack tags for prominent languages."""
    mapping = {
        "TypeScript": "TypeScript",
        "JavaScript": "JavaScript",
        "Python": "Python",
        "Go": "Go",
        "Rust": "Rust",
        "Ruby": "Ruby",
        "Java": "Java",
        "CSS": "CSS",
        "HTML": "HTML",
    }
    tags: list[str] = []
    for lang in sorted(languages, key=languages.get, reverse=True):
        if lang in mapping and mapping[lang] not in tags:
            tags.append(mapping[lang])
    return tags


def build_tech_stack(
    languages: dict[str, int], manifest_deps: list[str]
) -> list[str]:
    """Input: GitHub languages map + manifest dependency names. Output: techStack list."""
    tags = _language_tags(languages)
    tags.extend(normalize_tech_tags(manifest_deps))
    # dedupe preserving order
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def _collect_manifest_deps(
    client: GitHubClientProtocol, owner: str, repo: str
) -> list[str]:
    deps: list[str] = []
    get_file = getattr(client, "get_repo_file", None)
    if not get_file:
        return deps

    package_json = get_file(owner, repo, "package.json")
    if package_json:
        deps.extend(_extract_deps_from_package_json(package_json))

    requirements = get_file(owner, repo, "requirements.txt")
    if requirements:
        deps.extend(_extract_deps_from_requirements(requirements))

    pyproject = get_file(owner, repo, "pyproject.toml")
    if pyproject:
        deps.extend(_extract_deps_from_pyproject(pyproject))

    return deps


def enrich_from_repo(
    participant: Participant, client: GitHubClientProtocol
) -> Participant:
    """Input: base participant + GitHub client. Output: participant with repo enrichment."""
    try:
        owner, repo = parse_repo_url(participant.repoUrl)
    except ValueError:
        participant.repoPrivate = True
        return participant

    try:
        languages = client.get_languages(owner, repo)
    except GitHubApiError as exc:
        if exc.status_code == 404:
            participant.repoPrivate = True
            return participant
        raise

    manifest_deps = _collect_manifest_deps(client, owner, repo)
    participant.languages = languages
    participant.techStack = build_tech_stack(languages, manifest_deps)
    participant.repoPrivate = False
    return participant
