"""
Pulls Rust (appid 252490) stats for each Steam ID in config.json
straight from the Steam Web API and writes docs/data.json for the site.

Requires env var STEAM_API_KEY (free key from steamcommunity.com/dev/apikey).
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests

APP_ID = 252490
API = "https://api.steampowered.com"

# Display stat -> candidate Steam stat keys (first one found wins).
# If a column shows 0 for everyone, check the "raw" block in data.json
# for the real key name and add it here.
STAT_MAP = {
    "kills":   ["kill_player"],
    "deaths":  ["deaths", "death"],
    "wood":    ["harvested_wood"],
    "stone":   ["harvested_stones", "harvested_stone"],
    "metal":   ["acquired_metal.ore", "harvested_metal.ore"],
    "scrap":   ["acquired_scrap"],
    "sulfur":  ["acquired_sulfur.ore", "harvested_sulfur.ore", "harvested_sulfur"],
    "barrels": ["destroyed_barrels", "barrels_destroyed"],
    "builds":  ["placed_blocks", "blocks_placed"],
}


def get_summaries(key, steam_ids):
    """Names + avatars, one batched call."""
    r = requests.get(
        f"{API}/ISteamUser/GetPlayerSummaries/v0002/",
        params={"key": key, "steamids": ",".join(steam_ids)},
        timeout=30,
    )
    r.raise_for_status()
    players = r.json().get("response", {}).get("players", [])
    return {p["steamid"]: p for p in players}


def get_rust_stats(key, steam_id):
    """Returns dict of raw stats, or None if profile/game details are private."""
    r = requests.get(
        f"{API}/ISteamUserStats/GetUserStatsForGame/v0002/",
        params={"key": key, "steamid": steam_id, "appid": APP_ID},
        timeout=30,
    )
    if r.status_code != 200:
        # Steam returns 500/403 for private profiles or players without Rust
        return None
    stats = r.json().get("playerstats", {}).get("stats", [])
    return {s["name"]: s["value"] for s in stats}


def get_playtime_hours(key, steam_id):
    """Total Rust hours from Steam (0 if hidden)."""
    r = requests.get(
        f"{API}/IPlayerService/GetOwnedGames/v0001/",
        params={
            "key": key,
            "steamid": steam_id,
            "include_played_free_games": 1,
            "appids_filter[0]": APP_ID,
        },
        timeout=30,
    )
    if r.status_code != 200:
        return 0
    for g in r.json().get("response", {}).get("games", []):
        if g.get("appid") == APP_ID:
            return round(g.get("playtime_forever", 0) / 60, 1)
    return 0


def main():
    key = os.environ.get("STEAM_API_KEY")
    if not key:
        sys.exit("STEAM_API_KEY env var not set")

    with open("config.json") as f:
        cfg = json.load(f)["players"]
    # dedupe by steam_id, keep order
    seen, roster = set(), []
    for p in cfg:
        if p["steam_id"] not in seen:
            seen.add(p["steam_id"])
            roster.append(p)
    steam_ids = [p["steam_id"] for p in roster]
    labels = {p["steam_id"]: p.get("label", "") for p in roster}

    summaries = get_summaries(key, steam_ids)
    out_players = []

    for sid in steam_ids:
        summary = summaries.get(sid, {})
        raw = get_rust_stats(key, sid)
        private = raw is None

        stats = {}
        if not private:
            for label, candidates in STAT_MAP.items():
                stats[label] = next((raw[k] for k in candidates if k in raw), 0)
            stats["kd"] = round(stats["kills"] / max(stats["deaths"], 1), 2)
            stats["hours"] = get_playtime_hours(key, sid)
            missing = [l for l, c in STAT_MAP.items() if not any(k in raw for k in c)]
            if missing:
                print(f"[warn] {sid}: no stat key found for {missing} - check raw dump")

        out_players.append({
            "steamid": sid,
            "label": labels.get(sid, ""),
            "name": summary.get("personaname", sid),
            "avatar": summary.get("avatarfull", ""),
            "profile_url": summary.get("profileurl", f"https://steamcommunity.com/profiles/{sid}"),
            "private": private,
            "stats": stats,
            "raw": raw or {},
        })
        print(f"[ok] {sid} ({summary.get('personaname', '?')}) private={private}")

    data = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "placeholder": False,
        "players": out_players,
    }

    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote docs/data.json ({len(out_players)} players)")


if __name__ == "__main__":
    main()
