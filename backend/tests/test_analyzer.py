from help_finder.analyzer import build_tech_stack, enrich_from_repo, normalize_tech_tags
from help_finder.models import Participant


def test_normalize_tech_tags_react_next():
    tags = normalize_tech_tags(["@types/react", "next"])
    assert tags == ["React", "Next.js"]


def test_build_tech_stack_combines_languages_and_deps():
    stack = build_tech_stack(
        {"TypeScript": 1000, "CSS": 50},
        ["next", "react"],
    )
    assert "TypeScript" in stack
    assert "Next.js" in stack
    assert "React" in stack


def test_enrich_from_repo(fake_github):
    p = Participant.base_from_submission(
        {
            "githubHandle": "alice",
            "name": "Alice",
            "repoUrl": "https://github.com/alice/app",
            "pitch": "x",
        }
    )
    enriched = enrich_from_repo(p, fake_github)
    assert enriched.repoPrivate is False
    assert "TypeScript" in enriched.techStack
    assert "Next.js" in enriched.techStack


def test_enrich_private_repo(fake_github):
    p = Participant.base_from_submission(
        {
            "githubHandle": "bob",
            "name": "Bob",
            "repoUrl": "https://github.com/bob/private-app",
            "pitch": "x",
        }
    )
    enriched = enrich_from_repo(p, fake_github)
    assert enriched.repoPrivate is True
    assert enriched.techStack == []
