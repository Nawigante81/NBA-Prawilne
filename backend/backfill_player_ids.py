"""
Backfill players.player_id from player_game_stats (latest season).
Usage: python backfill_player_ids.py
"""

from pathlib import Path
from dotenv import load_dotenv
from supabase_client import create_isolated_supabase_client, get_supabase_config


def _pick_top(counts):
    if not counts:
        return None
    return max(counts.items(), key=lambda x: x[1])[0]


def main():
    root = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=root / ".env")
    config = get_supabase_config()
    if not config["available"]:
        print("Supabase config missing. Check .env.")
        return

    key = config["service_key"] or config["anon_key"]
    supabase = create_isolated_supabase_client(config["url"], key)
    if supabase is None:
        print("Supabase client unavailable.")
        return

    try:
        supabase.table("players").select("id,player_id").limit(1).execute()
    except Exception as e:
        print(f"players table check failed: {e}")
        return

    latest_resp = supabase.table("player_game_stats").select("season_year,game_date") \
        .order("game_date", desc=True).limit(1).execute()
    latest_row = (latest_resp.data or [None])[0]
    season_year = latest_row.get("season_year") if isinstance(latest_row, dict) else None
    if not season_year:
        print("No season_year found in player_game_stats.")
        return

    name_team_pid_counts = {}
    name_pid_counts = {}

    page = 0
    limit = 10000
    while True:
        start = page * limit
        end = start + limit - 1
        resp = supabase.table("player_game_stats").select(
            "player_id,player_name,team_tricode,game_id"
        ).eq("season_year", season_year).range(start, end).execute()
        rows = resp.data or []
        if not rows:
            break
        for r in rows:
            name = (r.get("player_name") or "").strip()
            pid = r.get("player_id")
            if not name or pid is None:
                continue
            try:
                pid_int = int(pid)
            except Exception:
                continue
            team_code = (r.get("team_tricode") or "").strip().upper()
            if team_code:
                key = (name, team_code)
                name_team_pid_counts.setdefault(key, {})
                name_team_pid_counts[key][pid_int] = name_team_pid_counts[key].get(pid_int, 0) + 1
            name_pid_counts.setdefault(name, {})
            name_pid_counts[name][pid_int] = name_pid_counts[name].get(pid_int, 0) + 1
        if len(rows) < limit:
            break
        page += 1

    name_team_to_pid = {k: _pick_top(v) for k, v in name_team_pid_counts.items() if _pick_top(v) is not None}
    name_to_pid = {k: _pick_top(v) for k, v in name_pid_counts.items() if _pick_top(v) is not None}

    updates = []
    updated = 0
    skipped = 0

    page = 0
    while True:
        start = page * limit
        end = start + limit - 1
        resp = supabase.table("players").select("id,name,team_abbreviation,player_id") \
            .range(start, end).execute()
        rows = resp.data or []
        if not rows:
            break
        for p in rows:
            if p.get("player_id") is not None:
                skipped += 1
                continue
            name = (p.get("name") or "").strip()
            team_code = (p.get("team_abbreviation") or "").strip().upper()
            if not name:
                skipped += 1
                continue
            pid_pick = name_team_to_pid.get((name, team_code)) or name_to_pid.get(name)
            if pid_pick is None:
                skipped += 1
                continue
            updates.append({"id": p.get("id"), "player_id": pid_pick})
        if len(rows) < limit:
            break
        page += 1

    batch_size = 500
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]
        supabase.table("players").upsert(batch, on_conflict="id").execute()
        updated += len(batch)

    print(f"Backfill complete. season_year={season_year}")
    print(f"Updated players: {updated}")
    print(f"Skipped players: {skipped}")


if __name__ == "__main__":
    main()
