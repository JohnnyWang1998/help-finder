from __future__ import annotations

from rapidfuzz import fuzz

from help_finder.models import Participant, RankedParticipant


def _searchable_text(p: Participant) -> str:
    parts = [
        p.name,
        p.githubHandle,
        p.pitch,
        p.summary,
        " ".join(p.techStack),
    ]
    return " ".join(parts)


def rank_participants(
    query: str,
    participants: list[Participant],
    *,
    limit: int = 3,
) -> list[RankedParticipant]:
    """Input: search query + participants. Output: top matches with fuzzy scores."""
    query = query.strip()
    if not query:
        return []

    public = [p for p in participants if not p.repoPrivate]
    if not public:
        return []

    scored: list[RankedParticipant] = []
    for p in public:
        stack_text = " ".join(p.techStack)
        stack_score = fuzz.WRatio(query, stack_text) if stack_text else 0
        text_score = fuzz.WRatio(query, _searchable_text(p))
        score = max(stack_score * 1.2, text_score)
        if score >= 40:
            scored.append(RankedParticipant(participant=p, score=score))

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]
