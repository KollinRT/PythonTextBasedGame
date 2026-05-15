import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from api.app import app, _sessions


def test_api_starts_session_and_returns_playable_state():
    _sessions.clear()
    client = TestClient(app)

    response = client.post("/sessions", json={"name": "WebHero", "player_class": "mage"})

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"]
    assert data["hero"]["name"] == "WebHero"
    assert data["hero"]["type"] == "Mage"
    assert data["map"]["current_node"] == "A0"
    assert data["map"]["neighbors"]
    assert data["battle"] is None


def test_api_rejects_invalid_move_with_400():
    _sessions.clear()
    client = TestClient(app)
    session = client.post("/sessions", json={"name": "WebHero", "player_class": "player"}).json()

    response = client.post(f"/sessions/{session['session_id']}/move", json={"destination": "NOPE"})

    assert response.status_code == 400
    assert "Cannot move" in response.json()["detail"]
