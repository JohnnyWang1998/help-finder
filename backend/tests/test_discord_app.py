from help_finder.discord_app import format_help_reply
from help_finder.matching import rank_participants


def test_format_help_reply(sample_participants):
    ranked = rank_participants("streamlit", sample_participants, limit=1)
    msg = format_help_reply(ranked, dashboard_base_url="http://localhost:3000")
    assert "Alaska Lam" in msg
    assert "streamlit" in msg.lower() or "Streamlit" in msg
    assert "localhost:3000" in msg


def test_format_help_reply_empty():
    msg = format_help_reply([], dashboard_base_url="http://localhost:3000")
    assert "No matches" in msg
