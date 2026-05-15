from api.server import SessionStore, describe_engine


def test_create_session_returns_shareable_state(monkeypatch, tmp_path):
    monkeypatch.setenv("ADVENTURE_DB", str(tmp_path / "api_game.db"))
    store = SessionStore()
    session_id = store.create("WebHero", "mage")
    state = describe_engine(store.get(session_id), session_id)

    assert state["session_id"] == session_id
    assert state["current_node"] == "A0"
    assert state["neighbors"]
    assert state["party"][0]["name"] == "WebHero"
    assert state["party"][0]["class"] == "Mage"


def test_describe_engine_reports_events_after_move(monkeypatch, tmp_path):
    monkeypatch.setenv("ADVENTURE_DB", str(tmp_path / "api_game.db"))
    store = SessionStore()
    session_id = store.create("Walker", "player")
    engine = store.get(session_id)
    destination = engine.neighbors()[0]

    events = engine.move_to(destination)
    state = describe_engine(engine, session_id, events)

    assert state["current_node"] == destination
    assert "events" in state
    assert state["in_battle"] is engine.in_battle()
