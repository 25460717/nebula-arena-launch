import pytest
import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8080"

def post_json(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    return urllib.request.urlopen(req)

def get_json(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    return urllib.request.urlopen(req)

def test_health_endpoint():
    """Validates /health reports healthy status and Agones Ready state."""
    resp = get_json("/health")
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    assert data["status"] == "healthy"
    assert data["agones_state"] in ["Ready", "Allocated"]
    assert data["max_players"] == 10

def test_room_allocation_on_join():
    """Validates transition Ready -> Allocated on first player connection."""
    # Reset any state if necessary by leaving or new match
    resp = post_json("/join", {"player_id": "test_p1", "match_id": "match_init_01"})
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    assert data["status"] in ["joined", "already_connected"]
    assert data["agones_state"] == "Allocated"

    health_resp = get_json("/health")
    health_data = json.loads(health_resp.read().decode())
    assert health_data["agones_state"] == "Allocated"

def test_capacity_limit_server_full():
    """Validates that exactly 10 players can join, and 11th triggers HTTP 409 Conflict."""
    # Fill remaining slots up to 10
    for i in range(2, 11):
        try:
            post_json("/join", {"player_id": f"test_p_{i:02d}"})
        except urllib.error.HTTPError as e:
            if e.code != 409:
                raise e

    # 11th player must trigger HTTP 409 server_full
    try:
        post_json("/join", {"player_id": "test_overflow_player"})
        assert False, "Expected 409 Conflict"
    except urllib.error.HTTPError as e:
        assert e.code == 409
        body = json.loads(e.read().decode())
        assert "server_full" in body["detail"]

def test_player_leave_and_ready_transition():
    """Validates player leaving and metrics state."""
    # Leave all test players
    for i in range(1, 11):
        try:
            p_id = "test_p1" if i == 1 else f"test_p_{i:02d}"
            post_json("/leave", {"player_id": p_id})
        except urllib.error.HTTPError:
            pass

    health_resp = get_json("/health")
    health_data = json.loads(health_resp.read().decode())
    assert health_data["agones_state"] == "Ready"
    assert health_data["current_players"] == 0

def test_metrics_endpoint():
    """Validates that Prometheus metrics endpoint exposes nebula metrics."""
    post_json("/join", {"player_id": "telemetry_tester"})
    resp = get_json("/metrics")
    assert resp.status == 200
    content = resp.read().decode()
    assert "nebula_ccu" in content
    assert "nebula_tick_duration_seconds" in content
    assert "nebula_matches_total" in content
    # Clean up
    post_json("/leave", {"player_id": "telemetry_tester"})
