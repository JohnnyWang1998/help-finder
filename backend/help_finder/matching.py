from __future__ import annotations

import re

from rapidfuzz import fuzz

from help_finder.clients.llm import LlmClientProtocol
from help_finder.models import Participant, RankedParticipant

# Query token → canonical tech name for fuzzy matching
_QUERY_SYNONYMS: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "next": "next.js",
    "nextjs": "next.js",
    "reactjs": "react",
    "tailwindcss": "tailwind",
    "postgres": "postgresql",
    "db": "database",
}


def normalize_query(query: str) -> str:
    """Input: raw search text. Output: normalized query with synonym expansion."""
    return " ".join(query_tokens(query))


def query_tokens(query: str) -> list[str]:
    """Input: raw search text. Output: normalized tokens for stack matching."""
    query = query.strip()
    if not query:
        return []
    tokens = re.split(r"[\s,;/]+", query.lower())
    expanded: list[str] = []
    for token in tokens:
        if not token:
            continue
        expanded.append(_QUERY_SYNONYMS.get(token, token))
    return expanded


def _normalize_tech(name: str) -> str:
    return re.sub(r"[^a-z0-9.+#-]+", "", name.lower())


_MIN_STACK_MATCH = 70
_MIN_TEXT_MATCH = 75


def resolve_search_query(query: str, llm: LlmClientProtocol | None) -> str:
    """Input: user query + optional LLM. Output: search string for fuzzy matching."""
    normalized = normalize_query(query)
    if not normalized:
        return ""
    if llm is None:
        return normalized
    try:
        parsed = llm.parse_search_query(normalized)
        return normalize_query(parsed) if parsed.strip() else normalized
    except Exception:
        return normalized


def stack_overlap_ratio(stack_a: list[str], stack_b: list[str]) -> float:
    """Input: two tech stacks. Output: Jaccard similarity in [0, 1]."""
    if not stack_a or not stack_b:
        return 0.0
    a = {t.lower() for t in stack_a}
    b = {t.lower() for t in stack_b}
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _prose_text(p: Participant) -> str:
    return " ".join([p.pitch, p.summary])


def _token_tech_score(token: str, tech: str) -> float:
    tok = _normalize_tech(token)
    normalized = _normalize_tech(tech)
    if not tok or not normalized:
        return 0.0
    if tok == normalized:
        return 100.0
    return float(fuzz.ratio(tok, normalized))


def _stack_match_score(tokens: list[str], tech_stack: list[str]) -> float:
    if not tokens or not tech_stack:
        return 0.0
    best = 0.0
    for token in tokens:
        token_best = max(_token_tech_score(token, tech) for tech in tech_stack)
        if token_best > best:
            best = token_best
    return best


def _text_match_score(tokens: list[str], text: str) -> float:
    if not tokens or not text.strip():
        return 0.0
    best = 0.0
    for token in tokens:
        if len(token) < 4:
            continue
        if re.search(rf"\b{re.escape(token)}\b", text, re.IGNORECASE):
            best = max(best, 85.0)
    return best


def _activity_multiplier(p: Participant) -> float:
    """Boost recently active builders in ranking."""
    if p.commitsLast7d >= 5:
        return 1.1
    if p.commitsLast7d >= 1:
        return 1.05
    return 1.0


def _score_participant(tokens: list[str], p: Participant) -> float:
    stack_score = _stack_match_score(tokens, p.techStack)
    text_score = _text_match_score(tokens, _prose_text(p))
    raw = max(stack_score * 1.2, text_score)
    if raw < _MIN_STACK_MATCH:
        return 0.0
    return raw * _activity_multiplier(p)


def rank_participants(
    query: str,
    participants: list[Participant],
    *,
    limit: int = 3,
    llm: LlmClientProtocol | None = None,
) -> list[RankedParticipant]:
    """Input: search query + participants. Output: top matches with fuzzy scores."""
    resolved = resolve_search_query(query, llm)
    tokens = query_tokens(resolved)
    if not tokens:
        return []

    public = [p for p in participants if not p.repoPrivate]
    if not public:
        return []

    scored: list[RankedParticipant] = []
    for p in public:
        score = _score_participant(tokens, p)
        if score > 0:
            scored.append(RankedParticipant(participant=p, score=score))

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]


def rank_by_stack_overlap(
    github_handle: str,
    participants: list[Participant],
    *,
    limit: int = 5,
) -> list[RankedParticipant]:
    """Input: cohort member handle. Output: peers ranked by shared tech stack."""
    handle = github_handle.strip().lstrip("@").lower()
    ref = next(
        (p for p in participants if p.githubHandle.lower() == handle),
        None,
    )
    if ref is None or ref.repoPrivate:
        return []

    scored: list[RankedParticipant] = []
    for p in participants:
        if p.repoPrivate or p.githubHandle.lower() == handle:
            continue
        ratio = stack_overlap_ratio(ref.techStack, p.techStack)
        if ratio > 0:
            scored.append(
                RankedParticipant(participant=p, score=round(ratio * 100, 1))
            )

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]
