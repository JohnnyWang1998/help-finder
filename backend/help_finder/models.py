from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Participant(BaseModel):
    """Cohort participant — matches shared schema in TICKETS.md."""

    githubHandle: str
    name: str
    avatarUrl: str
    repoUrl: str
    liveUrl: str = ""
    pitch: str
    summary: str = ""
    techStack: list[str] = Field(default_factory=list)
    languages: dict[str, int] = Field(default_factory=dict)
    lastCommitAt: str = ""
    commitsLast7d: int = 0
    repoPrivate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Participant:
        return cls.model_validate(data)

    @classmethod
    def base_from_submission(cls, raw: dict[str, Any]) -> Participant:
        """Input: cohort submission JSON. Output: Participant with base fields only."""
        handle = raw["githubHandle"]
        return cls(
            githubHandle=handle,
            name=raw["name"],
            avatarUrl=f"https://github.com/{handle}.png",
            repoUrl=raw["repoUrl"],
            liveUrl=raw.get("liveUrl") or "",
            pitch=raw.get("pitch", ""),
        )


class RankedParticipant(BaseModel):
    participant: Participant
    score: float
