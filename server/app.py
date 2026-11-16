import asyncio
import os
import time
from typing import Dict, List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel
from prometheus_client import Gauge, Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST

# Configuration Constants
MAX_PLAYERS_PER_INSTANCE = 10
TARGET_TICK_RATE = 20  # 20 Hz
TARGET_TICK_BUDGET_SECONDS = 1.0 / TARGET_TICK_RATE  # 50 ms budget (0.050s)

# Prometheus Real Metrics
NEBULA_CCU = Gauge(
    "nebula_ccu",
    "Current concurrent users connected to this dedicated game server instance",
    ["instance_id"]
)

NEBULA_TICK_DURATION_SECONDS = Histogram(
    "nebula_tick_duration_seconds",
    "Duration of game simulation tick in seconds (Budget: 0.050s for 20Hz)",
    ["instance_id"],
    buckets=[0.005, 0.010, 0.020, 0.030, 0.040, 0.045, 0.050, 0.060, 0.080, 0.100, 0.250]
)

NEBULA_MATCHES_TOTAL = Counter(
    "nebula_matches_total",
    "Total number of matches initiated or completed on this instance",
    ["instance_id", "status"]
)

INSTANCE_ID = os.getenv("POD_NAME", "nebula-pod-alpha-001")

class ServerState:
    def __init__(self):
        self.status = "Ready"  # Ready, Allocated, Terminating
        self.players: Dict[str, dict] = {}
        self.match_id: Optional[str] = None
        self.last_tick_time: float = 0.022
        self.tick_task: Optional[asyncio.Task] = None
        self.tick_running: bool = False

state = ServerState()

class JoinRequest(BaseModel):
    player_id: str
    match_id: Optional[str] = "match-arena-001"
    loadout: Optional[str] = "plasma-rifle"

class LeaveRequest(BaseModel):
    player_id: str

async def game_tick_loop():
    """Background simulation loop running at 20Hz."""
    while state.tick_running:
        start_time = time.perf_counter()
        active_count = len(state.players)
        base_work_ms = 4.0 + (active_count * 1.8)
        simulated_work_sec = base_work_ms / 1000.0
        
        await asyncio.sleep(simulated_work_sec)
        
        duration = time.perf_counter() - start_time
        state.last_tick_time = duration
        NEBULA_TICK_DURATION_SECONDS.labels(instance_id=INSTANCE_ID).observe(duration)
        
        remaining = TARGET_TICK_BUDGET_SECONDS - duration
        if remaining > 0:
            await asyncio.sleep(remaining)
        else:
            await asyncio.sleep(0.001)

@asynccontextmanager
async def lifespan(app: FastAPI):
    NEBULA_CCU.labels(instance_id=INSTANCE_ID).set(0)
    state.tick_running = True
    state.tick_task = asyncio.create_task(game_tick_loop())
    try:
        yield
    finally:
        state.tick_running = False
        if state.tick_task:
            state.tick_task.cancel()
            try:
                await state.tick_task
            except asyncio.CancelledError:
                pass

app = FastAPI(
    title="Nebula Arena Dedicated Game Server",
    description="High-frequency 20Hz Tickrate Dedicated Game Server Instance for Agones/GKE",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
def health_check():
    """Kubernetes liveness and Agones health ping."""
    return {
        "status": "healthy",
        "agones_state": state.status,
        "instance_id": INSTANCE_ID,
        "current_players": len(state.players),
        "max_players": MAX_PLAYERS_PER_INSTANCE,
        "last_tick_ms": round(state.last_tick_time * 1000, 2),
        "target_tick_budget_ms": 50.0
    }

@app.post("/join")
def join_match(req: JoinRequest):
    """Player requests slot in the dedicated server."""
    if len(state.players) >= MAX_PLAYERS_PER_INSTANCE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="server_full: Maximum capacity of 10 players reached"
        )
    
    if req.player_id in state.players:
        return {
            "status": "already_connected",
            "player_id": req.player_id,
            "agones_state": state.status,
            "current_players": len(state.players)
        }
    
    # First player joins -> Transition Agones state Ready -> Allocated
    if len(state.players) == 0:
        state.status = "Allocated"
        state.match_id = req.match_id
        NEBULA_MATCHES_TOTAL.labels(instance_id=INSTANCE_ID, status="started").inc()

    state.players[req.player_id] = {
        "joined_at": time.time(),
        "loadout": req.loadout
    }
    
    current_count = len(state.players)
    NEBULA_CCU.labels(instance_id=INSTANCE_ID).set(current_count)
    NEBULA_TICK_DURATION_SECONDS.labels(instance_id=INSTANCE_ID).observe(0.004 + (current_count * 0.0018))
    
    return {
        "status": "joined",
        "player_id": req.player_id,
        "match_id": state.match_id,
        "agones_state": state.status,
        "current_players": current_count,
        "capacity": MAX_PLAYERS_PER_INSTANCE
    }

@app.post("/leave")
def leave_match(req: LeaveRequest):
    """Player leaves or disconnects from the arena."""
    if req.player_id not in state.players:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found in this game instance"
        )
    
    del state.players[req.player_id]
    current_count = len(state.players)
    NEBULA_CCU.labels(instance_id=INSTANCE_ID).set(current_count)
    
    # When all players leave, instance transitions back to Ready
    if current_count == 0:
        state.status = "Ready"
        NEBULA_MATCHES_TOTAL.labels(instance_id=INSTANCE_ID, status="completed").inc()
        
    return {
        "status": "left",
        "player_id": req.player_id,
        "agones_state": state.status,
        "current_players": current_count
    }

@app.get("/metrics")
def get_metrics():
    """Prometheus scraping endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
