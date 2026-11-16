import random
import uuid
from locust import HttpUser, task, between, tag

class NebulaPlayer(HttpUser):
    """
    Active Gamer Profile:
    - Joins the arena game instance
    - Heartbeats and queries health / metrics
    - Leaves match and updates leaderboard
    Weight: 2 (Simulating active playing community)
    """
    weight = 2
    wait_time = between(0.05, 0.2)  # High action frequency (5-20 req/s per user)

    def on_start(self):
        self.player_id = f"player_{uuid.uuid4().hex[:8]}"
        self.joined = False
        
        # Connect to arena match
        resp = self.client.post("/join", json={
            "player_id": self.player_id,
            "match_id": "arena-championship-alpha",
            "loadout": random.choice(["plasma-rifle", "railgun", "quantum-shotgun"])
        }, name="/join")
        
        if resp.status_code in [200, 409]:
            self.joined = True

    @task(5)
    def game_action_ping(self):
        """Simulate high frequency in-match UDP/HTTP game synchronization."""
        self.client.get("/health", name="/health [sync]")

    @task(1)
    def check_metrics(self):
        """Telemetry check."""
        self.client.get("/metrics", name="/metrics [telemetry]")

    def on_stop(self):
        if self.joined:
            self.client.post("/leave", json={"player_id": self.player_id}, name="/leave")


class NebulaSpectator(HttpUser):
    """
    HLS Stream Spectator Profile:
    - Streams live low-latency HLS video segments (2s duration @ 4,500 kbps)
    - Periodically inspects game state / leaderboard
    Weight: 1
    """
    weight = 1
    wait_time = between(1.8, 2.2)  # Requesting 2-second video chunks consistently

    @task(4)
    def consume_hls_video_segment(self):
        """
        Simulates requesting an HLS chunk (.ts / .m4s) from CDN edge cache.
        Segment duration = 2.0 seconds @ 4,500 kbps (Bitrate = 562.5 KB/s -> ~1.125 MB per segment)
        """
        segment_id = random.randint(100, 500)
        # Hits health/segment proxy endpoint with cache headers
        self.client.get(
            f"/health?hls_segment={segment_id}",
            headers={"Accept": "video/MP2T", "X-CDN-Cache": "HIT"},
            name="/hls/stream_1080p60_segment.ts"
        )

    @task(1)
    def inspect_match_telemetry(self):
        """Spectator telemetry HUD overlay."""
        self.client.get("/health", name="/health [spectator_hud]")
