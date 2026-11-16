import json
import functions_framework
from flask import Request, jsonify

# In-memory mock for Firestore database collection 'leaderboard'
leaderboard_db = [
    {"player_id": "Vortex_Sniper", "elo": 2450, "wins": 142, "matches": 160},
    {"player_id": "CyberNova", "elo": 2380, "wins": 128, "matches": 150},
    {"player_id": "Aegis_Prime", "elo": 2310, "wins": 115, "matches": 140},
    {"player_id": "Solaris_X", "elo": 2260, "wins": 104, "matches": 135},
    {"player_id": "QuantumGhost", "elo": 2210, "wins": 98, "matches": 130},
    {"player_id": "Hyperion99", "elo": 2180, "wins": 92, "matches": 125},
    {"player_id": "NebulaStriker", "elo": 2150, "wins": 89, "matches": 120},
    {"player_id": "TitanPulse", "elo": 2110, "wins": 84, "matches": 118},
    {"player_id": "ZeroLatency", "elo": 2080, "wins": 81, "matches": 115},
    {"player_id": "VoidRunner", "elo": 2040, "wins": 76, "matches": 110},
    {"player_id": "RookieGamer", "elo": 1500, "wins": 12, "matches": 30}
]

@functions_framework.http
def leaderboard(request: Request):
    """Serverless Cloud Function for Nebula Arena Leaderboard & Post-Match ELO Updates."""
    # Set CORS headers for public frontend & web portal
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Cache-Control': 'public, max-age=5'  # 5s edge caching for GET requests
    }

    if request.method == 'OPTIONS':
        return ('', 204, headers)

    # 1. GET: Fetch Top 10 Leaderboard
    if request.method == 'GET':
        sorted_leaderboard = sorted(leaderboard_db, key=lambda x: x["elo"], reverse=True)[:10]
        for rank, p in enumerate(sorted_leaderboard, start=1):
            p["rank"] = rank
        return (jsonify({
            "status": "success",
            "count": len(sorted_leaderboard),
            "top10": sorted_leaderboard
        }), 200, headers)

    # 2. POST: Update player stats & ELO after match completion
    if request.method == 'POST':
        try:
            req_data = request.get_json(silent=True) or {}
            player_id = req_data.get("player_id")
            elo_change = req_data.get("elo_change", 0)
            won = req_data.get("won", False)
            match_id = req_data.get("match_id", "match-unknown")

            if not player_id:
                return (jsonify({"error": "Missing player_id"}), 400, headers)

            # Find or insert player
            player = next((p for p in leaderboard_db if p["player_id"] == player_id), None)
            if not player:
                player = {
                    "player_id": player_id,
                    "elo": 1200 + elo_change,
                    "wins": 1 if won else 0,
                    "matches": 1
                }
                leaderboard_db.append(player)
            else:
                player["elo"] += elo_change
                player["matches"] += 1
                if won:
                    player["wins"] += 1

            # Re-rank
            sorted_all = sorted(leaderboard_db, key=lambda x: x["elo"], reverse=True)
            current_rank = next(idx + 1 for idx, p in enumerate(sorted_all) if p["player_id"] == player_id)

            return (jsonify({
                "status": "success",
                "message": f"ELO updated for {player_id}",
                "match_id": match_id,
                "player": {
                    "player_id": player["player_id"],
                    "new_elo": player["elo"],
                    "wins": player["wins"],
                    "total_matches": player["matches"],
                    "current_rank": current_rank
                }
            }), 200, headers)

        except Exception as e:
            return (jsonify({"error": str(e)}), 500, headers)

    return (jsonify({"error": "Method Not Allowed"}), 405, headers)
