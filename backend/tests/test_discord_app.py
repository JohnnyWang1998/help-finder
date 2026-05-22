from help_finder.discord_app import format_help_reply, format_peers_reply
from help_finder.matching import rank_by_stack_overlap, rank_participants


def test_format_help_reply(sample_participants):
    ranked = rank_participants("streamlit", sample_participants, limit=1)
    msg = format_help_reply(ranked, dashboard_base_url="http://localhost:3000")
    assert "Alaska Lam" in msg
    assert "streamlit" in msg.lower() or "Streamlit" in msg
    assert "localhost:3000" in msg


def test_format_help_reply_empty():
    msg = format_help_reply([], dashboard_base_url="http://localhost:3000")
    assert "No matches" in msg


def test_format_peers_reply(sample_participants):
    ranked = rank_by_stack_overlap("bme3412", sample_participants, limit=2)
    msg = format_peers_reply(
        ranked,
        reference_handle="bme3412",
        dashboard_base_url="http://localhost:3000",
    )
    assert "Peers like @bme3412" in msg
    assert "overlap" in msg.lower()
    assert "localhost:3000" in msg
