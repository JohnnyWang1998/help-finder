from help_finder.submissions import fetch_all_submissions, fetch_participants, parse_submission


def test_parse_submission_minimal(sample_submission_minimal):
    p = parse_submission(sample_submission_minimal)
    assert p.githubHandle == "testuser"
    assert p.liveUrl == "https://my-repo.example.com"


def test_parse_submission_empty_live_url(sample_submission_no_live_url):
    p = parse_submission(sample_submission_no_live_url)
    assert p.liveUrl == ""


def test_fetch_all_submissions(fake_github):
    raw = fetch_all_submissions(fake_github)
    assert len(raw) == 2
    assert raw[0]["githubHandle"] == "alice"


def test_fetch_participants(fake_github):
    participants = fetch_participants(fake_github)
    assert len(participants) == 2
    assert participants[0].name == "Alice"
