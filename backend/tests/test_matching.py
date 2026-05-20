from help_finder.matching import rank_participants


def test_rank_participants_streamlit(sample_participants):
    ranked = rank_participants("streamlit", sample_participants, limit=3)
    assert len(ranked) >= 1
    assert ranked[0].participant.githubHandle == "alaska-lam"


def test_rank_participants_react(sample_participants):
    ranked = rank_participants("react", sample_participants, limit=3)
    assert ranked[0].participant.githubHandle == "bme3412"


def test_rank_participants_empty_query(sample_participants):
    assert rank_participants("", sample_participants) == []
