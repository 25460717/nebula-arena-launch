import pytest
from flask import Flask
from serverless.main import leaderboard

@pytest.fixture
def test_app():
    app = Flask(__name__)
    return app

def test_leaderboard_get_top10(test_app):
    with test_app.test_request_context(method="GET", path="/"):
        from flask import request
        resp, code, headers = leaderboard(request)
        assert code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert len(data["top10"]) == 10
        assert data["top10"][0]["rank"] == 1
        assert data["top10"][0]["player_id"] == "Vortex_Sniper"

def test_leaderboard_post_update_elo(test_app):
    payload = {
        "player_id": "Vortex_Sniper",
        "elo_change": 25,
        "won": True,
        "match_id": "match-grand-finals-01"
    }
    with test_app.test_request_context(method="POST", path="/", json=payload):
        from flask import request
        resp, code, headers = leaderboard(request)
        assert code == 200
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["player"]["player_id"] == "Vortex_Sniper"
        assert data["player"]["new_elo"] == 2475
        assert data["player"]["wins"] == 143

def test_leaderboard_post_missing_player(test_app):
    with test_app.test_request_context(method="POST", path="/", json={"elo_change": 10}):
        from flask import request
        resp, code, headers = leaderboard(request)
        assert code == 400
        data = resp.get_json()
        assert "Missing player_id" in data["error"]
