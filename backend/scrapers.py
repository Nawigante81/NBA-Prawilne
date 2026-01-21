import httpx
import os
from bs4 import BeautifulSoup
from supabase import Client
from datetime import datetime, timedelta
from datetime import date as Date
import asyncio
import anyio
import re
import logging
import calendar
import random

# Import our advanced anti-bot scraper
from anti_bot_scraper import BasketballReferenceScraper, scrape_nba_teams, scrape_bulls_players

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NBA_STATS_SCOREBOARD_URL = "https://stats.nba.com/stats/scoreboard"
NBA_STATS_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
NBA_STATS_HEADERS_BASE = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Origin": "https://stats.nba.com",
    "Referer": "https://stats.nba.com/",
}
TEAM_NAME_NORMALIZATION = {
    "LA Clippers": "Los Angeles Clippers",
    "LA Lakers": "Los Angeles Lakers",
}


def _nba_season_year_for_date(day: Date) -> int:
    """Return Basketball-Reference NBA season year for a given calendar date.

    Basketball-Reference uses the *ending* year for season pages.
    Example: Jan 2026 games live under NBA_2026.
    """
    return day.year + 1 if day.month >= 10 else day.year


def _bref_month_slug(day: Date) -> str:
    return calendar.month_name[day.month].lower()


def _normalize_team_full_name(city: str | None, name: str | None) -> str | None:
    if not city or not name:
        return None
    full = f"{city} {name}".strip()
    return TEAM_NAME_NORMALIZATION.get(full, full)


async def _fetch_nba_scoreboard(day: Date) -> list[dict]:
    """Fetch NBA scoreboard results for a given date (NBA stats)."""
    date_str = day.strftime("%m/%d/%Y")
    params = {"GameDate": date_str, "LeagueID": "00", "DayOffset": "0"}
    headers = dict(NBA_STATS_HEADERS_BASE)
    headers["User-Agent"] = random.choice(NBA_STATS_USER_AGENTS)

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(NBA_STATS_SCOREBOARD_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                result_sets = data.get("resultSets") or []
                sets_by_name = {s.get("name"): s for s in result_sets if isinstance(s, dict)}
                game_header = sets_by_name.get("GameHeader") or {}
                line_score = sets_by_name.get("LineScore") or {}

                game_headers = game_header.get("rowSet") or []
                game_header_cols = game_header.get("headers") or []
                line_scores = line_score.get("rowSet") or []
                line_score_cols = line_score.get("headers") or []

                gh_idx = {name: i for i, name in enumerate(game_header_cols)}
                ls_idx = {name: i for i, name in enumerate(line_score_cols)}

                game_map: dict[str, dict] = {}
                for row in game_headers:
                    try:
                        gid = str(row[gh_idx["GAME_ID"]])
                    except Exception:
                        continue
                    game_map[gid] = {
                        "game_id": gid,
                        "game_date": row[gh_idx.get("GAME_DATE_EST")] if "GAME_DATE_EST" in gh_idx else day.isoformat(),
                        "home_team_id": row[gh_idx.get("HOME_TEAM_ID")] if "HOME_TEAM_ID" in gh_idx else None,
                        "away_team_id": row[gh_idx.get("VISITOR_TEAM_ID")] if "VISITOR_TEAM_ID" in gh_idx else None,
                        "status_text": row[gh_idx.get("GAME_STATUS_TEXT")] if "GAME_STATUS_TEXT" in gh_idx else None,
                    }

                score_map: dict[str, dict] = {}
                for row in line_scores:
                    try:
                        gid = str(row[ls_idx["GAME_ID"]])
                    except Exception:
                        continue
                    team_id = row[ls_idx.get("TEAM_ID")] if "TEAM_ID" in ls_idx else None
                    city = row[ls_idx.get("TEAM_CITY")] if "TEAM_CITY" in ls_idx else None
                    name = row[ls_idx.get("TEAM_NAME")] if "TEAM_NAME" in ls_idx else None
                    full_name = _normalize_team_full_name(city, name)
                    pts = row[ls_idx.get("PTS")] if "PTS" in ls_idx else None
                    score_map.setdefault(gid, {})[team_id] = {
                        "team_full_name": full_name,
                        "points": pts,
                    }

                games: list[dict] = []
                for gid, g in game_map.items():
                    scores = score_map.get(gid, {})
                    home = scores.get(g.get("home_team_id"))
                    away = scores.get(g.get("away_team_id"))
                    if not home or not away:
                        continue
                    games.append(
                        {
                            "game_id": gid,
                            "game_date": g.get("game_date"),
                            "home_team": home.get("team_full_name"),
                            "away_team": away.get("team_full_name"),
                            "home_score": home.get("points"),
                            "away_score": away.get("points"),
                            "status": g.get("status_text"),
                        }
                    )
                return games
        except Exception as exc:
            logger.warning(f"NBA stats scoreboard fetch failed ({attempt + 1}/3): {exc}")
            await asyncio.sleep(1.5 * (attempt + 1))

    return []


async def scrape_recent_results(supabase: Client, days_back: int = 3):
    """Scrape recent NBA game results and store in Supabase."""
    today = Date.today()
    for offset in range(days_back + 1):
        day = today - timedelta(days=offset)
        try:
            cached = await _day_results_cached(supabase, day)
        except Exception:
            cached = False
        if cached:
            continue
        games = await _fetch_nba_scoreboard(day)
        if not games:
            continue
        records = []
        for g in games:
            if not g.get("home_team") or not g.get("away_team"):
                continue
            status_text = g.get("status") or ""
            is_final = "final" in status_text.lower()
            records.append(
                {
                    "game_id": g.get("game_id"),
                    "game_date": g.get("game_date"),
                    "home_team": g.get("home_team"),
                    "away_team": g.get("away_team"),
                    "home_score": g.get("home_score"),
                    "away_score": g.get("away_score"),
                    "status": status_text,
                    "finalized_at": datetime.now().isoformat() if is_final else None,
                    "source": "nba_stats",
                }
            )
        if records:
            try:
                await anyio.to_thread.run_sync(
                    lambda rows=records: supabase.table("game_results")
                    .upsert(rows, on_conflict="game_date,home_team,away_team")
                    .execute()
                )
            except Exception as exc:
                logger.warning(f"Saving game results failed: {exc}")
        await asyncio.sleep(0.5)


async def _day_results_cached(supabase: Client, day: Date) -> bool:
    """Return True if results for the day look complete and finalized."""
    resp = await anyio.to_thread.run_sync(
        lambda: supabase.table("game_results")
        .select("finalized_at,home_score,away_score,status")
        .eq("game_date", day.isoformat())
        .execute()
    )
    rows = resp.data or []
    if not rows:
        return False
    for r in rows:
        if r.get("home_score") is None or r.get("away_score") is None:
            return False
        status = (r.get("status") or "").lower()
        if "final" not in status and not r.get("finalized_at"):
            return False
    return True


async def get_basketball_reference_games_for_date(day: Date) -> list[dict]:
    """Fetch official schedule matchups from Basketball-Reference for a given date.

    Returns a list of {home_team, away_team}.
    If the page is unavailable/blocked, returns an empty list.
    """
    season_year = _nba_season_year_for_date(day)
    month_slug = _bref_month_slug(day)
    url = f"https://www.basketball-reference.com/leagues/NBA_{season_year}_games-{month_slug}.html"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        logger.warning(f"Basketball-Reference schedule fetch failed: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "schedule"})
    if not table:
        # Sometimes BRef nests tables in comments; keep it minimal and just fail closed.
        logger.warning("Basketball-Reference schedule table not found")
        return []

    results: list[dict] = []
    tbody = table.find("tbody")
    if not tbody:
        return []

    for row in tbody.find_all("tr"):
        # Skip header rows
        if row.get("class") and "thead" in row.get("class"):
            continue

        date_cell = row.find("th", {"data-stat": "date_game"})
        if not date_cell:
            continue

        # Prefer machine-sort key if present
        csk = date_cell.get("csk")
        row_day = None
        if csk and len(csk) >= 8 and csk[:8].isdigit():
            try:
                y = int(csk[0:4])
                m = int(csk[4:6])
                d = int(csk[6:8])
                row_day = Date(y, m, d)
            except Exception:
                row_day = None

        if row_day is None:
            # Fallback: parse visible date text (best-effort)
            text = (date_cell.get_text(" ", strip=True) or "").strip()
            # Example: "Sat, Jan 3, 2026"
            try:
                row_day = datetime.strptime(text, "%a, %b %d, %Y").date()
            except Exception:
                continue

        if row_day != day:
            continue

        away_cell = row.find("td", {"data-stat": "visitor_team_name"})
        home_cell = row.find("td", {"data-stat": "home_team_name"})
        if not away_cell or not home_cell:
            continue

        away = away_cell.get_text(" ", strip=True)
        home = home_cell.get_text(" ", strip=True)
        if away and home:
            results.append({"away_team": away, "home_team": home})

    return results


async def get_teams_data():
    """Scrape NBA teams from Basketball-Reference using anti-bot protection"""
    try:
        logger.info("Starting teams data scraping with anti-bot protection")
        teams = await scrape_nba_teams()
        logger.info(f"Successfully scraped {len(teams)} teams")
        return teams
    except Exception as e:
        logger.error(f"Failed to scrape teams data: {e}")
        return []


async def save_teams(supabase: Client, teams: list):
    """Save teams to Supabase"""
    if not teams:
        return

    for team in teams:
        try:
            await anyio.to_thread.run_sync(
                lambda t=team: supabase.table("teams").upsert(
                    [t], on_conflict="abbreviation"
                ).execute()
            )
        except Exception as e:
            print(f"Error saving team {team.get('abbreviation')}: {e}")


async def get_nba_odds():
    """Fetch NBA odds from The Odds API"""
    api_key = (
        os.getenv("ODDS_API_KEY")
        or os.getenv("VITE_ODDS_API_KEY")
        or "345c1ad37d7b391ec285a93579e7fe80"
    )

    async with httpx.AsyncClient() as client:
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
        params = {
            "apiKey": api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals"
        }

        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        # The Odds API may return a list for /events; normalize to dict for downstream code.
        if isinstance(data, list):
            return {"events": data}
        return data


async def process_odds_data(supabase: Client, odds_data: dict):
    """Process and save odds data to Supabase"""
    if isinstance(odds_data, list):
        events = odds_data
    else:
        events = odds_data.get("events", [])

    for event in events:
        try:
            game_id = event.get("id")
            home_team = event.get("home_team")
            away_team = event.get("away_team")
            commence_time = event.get("commence_time")

            game_data = {
                "id": game_id,
                "sport_key": event.get("sport_key"),
                "sport_title": event.get("sport_title"),
                "commence_time": commence_time,
                "home_team": home_team,
                "away_team": away_team,
            }

            await anyio.to_thread.run_sync(
                lambda g=game_data: supabase.table("games").upsert(
                    [g], on_conflict="id"
                ).execute()
            )

            bookmakers = event.get("bookmakers", [])
            for bookmaker in bookmakers:
                odds_records = []
                bookmaker_key = bookmaker.get("key")
                bookmaker_title = bookmaker.get("title")
                last_update = bookmaker.get("last_update")

                for market in bookmaker.get("markets", []):
                    market_key = market.get("key")
                    outcomes = market.get("outcomes", [])

                    if market_key == "h2h":
                        for outcome in outcomes:
                            odds_records.append({
                                "game_id": game_id,
                                "bookmaker_key": bookmaker_key,
                                "bookmaker_title": bookmaker_title,
                                "last_update": last_update,
                                "market_type": "h2h",
                                "team": outcome.get("name"),
                                "price": outcome.get("price"),
                            })

                    elif market_key == "spread":
                        for outcome in outcomes:
                            odds_records.append({
                                "game_id": game_id,
                                "bookmaker_key": bookmaker_key,
                                "bookmaker_title": bookmaker_title,
                                "last_update": last_update,
                                "market_type": "spread",
                                "team": outcome.get("name"),
                                "point": outcome.get("point"),
                                "price": outcome.get("price"),
                            })

                    elif market_key == "totals":
                        for outcome in outcomes:
                            odds_records.append({
                                "game_id": game_id,
                                "bookmaker_key": bookmaker_key,
                                "bookmaker_title": bookmaker_title,
                                "last_update": last_update,
                                "market_type": "totals",
                                "outcome_name": outcome.get("name"),
                                "point": outcome.get("point"),
                                "price": outcome.get("price"),
                            })

                if odds_records:
                    for record in odds_records:
                        try:
                            await anyio.to_thread.run_sync(
                                lambda r=record: supabase.table("odds").upsert(
                                    [r], on_conflict="id"
                                ).execute()
                            )
                        except Exception as e:
                            print(f"Error saving odds record: {e}")

        except Exception as e:
            print(f"Error processing event {event.get('id')}: {e}")


async def scrape_all_data(supabase: Client):
    """Main function to scrape all data"""
    try:
        print(f"[{datetime.now().isoformat()}] Starting scrape...")

        teams = await get_teams_data()
        print(f"Fetched {len(teams)} teams")
        await save_teams(supabase, teams)

        odds_data = await get_nba_odds()
        print(f"Fetched odds for {len(odds_data.get('events', []))} games")
        await process_odds_data(supabase, odds_data)

        print(f"[{datetime.now().isoformat()}] Scrape completed successfully")
    except Exception as e:
        print(f"Error during scrape: {e}")


async def get_team_roster(team_abbrev: str, season: str = "2025"):
    """Scrape team roster from Basketball-Reference"""
    async with httpx.AsyncClient() as client:
        url = f"https://www.basketball-reference.com/teams/{team_abbrev.upper()}/{season}.html"
        
        try:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"Failed to fetch roster for {team_abbrev}: {e}")
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        players = []
        
        # Find the roster table
        roster_table = soup.find("table", {"id": "roster"})
        if not roster_table:
            print(f"No roster table found for {team_abbrev}")
            return players

        for row in roster_table.find_all("tr")[1:]:  # Skip header
            cells = row.find_all(["td", "th"])
            if len(cells) < 6:
                continue
                
            try:
                # Extract player data from Basketball-Reference roster table
                player_link = cells[1].find("a")
                if not player_link:
                    continue
                    
                name = player_link.text.strip()
                basketball_reference_url = "https://www.basketball-reference.com" + player_link["href"]
                
                # Extract Basketball-Reference ID from URL (e.g., /players/j/jamesle01.html -> jamesle01)
                basketball_reference_id = player_link["href"].split("/")[-1].replace(".html", "")
                
                # Parse other data
                jersey_number = cells[0].text.strip()
                try:
                    jersey_number = int(jersey_number) if jersey_number.isdigit() else None
                except:
                    jersey_number = None
                    
                position = cells[2].text.strip() if len(cells) > 2 else ""
                height = cells[3].text.strip() if len(cells) > 3 else ""
                weight_text = cells[4].text.strip() if len(cells) > 4 else ""
                
                # Parse weight
                weight = None
                if weight_text:
                    weight_match = re.search(r'(\d+)', weight_text)
                    if weight_match:
                        weight = int(weight_match.group(1))
                
                # Birth date (if available)
                birth_date = None
                birth_text = cells[5].text.strip() if len(cells) > 5 else ""
                if birth_text and len(birth_text) > 4:
                    try:
                        # Try to parse date in format like "January 1, 1990"
                        from datetime import datetime as dt
                        birth_date = dt.strptime(birth_text, "%B %d, %Y").date().isoformat()
                    except:
                        # If parsing fails, store as text for manual review
                        pass
                
                # Experience (if available in table)
                experience = None
                if len(cells) > 7:
                    exp_text = cells[7].text.strip()
                    if exp_text.isdigit():
                        experience = int(exp_text)
                    elif exp_text == "R":  # Rookie
                        experience = 0
                
                # College (if available)
                college = ""
                if len(cells) > 6:
                    college = cells[6].text.strip()
                
                player_data = {
                    "name": name,
                    "team_abbreviation": team_abbrev.upper(),
                    "jersey_number": jersey_number,
                    "position": position,
                    "height": height,
                    "weight": weight,
                    "birth_date": birth_date,
                    "experience": experience,
                    "college": college,
                    "basketball_reference_id": basketball_reference_id,
                    "basketball_reference_url": basketball_reference_url,
                    "is_active": True,
                    "season_year": f"{int(season)-1}-{season[2:]}"  # e.g., 2024-25
                }
                
                players.append(player_data)
                
            except Exception as e:
                print(f"Error parsing player row for {team_abbrev}: {e}")
                continue
                
        print(f"Found {len(players)} players for {team_abbrev}")
        return players


async def save_players(supabase: Client, players: list):
    """Save players to Supabase database"""
    if not players:
        return
        
    success_count = 0
    error_count = 0
    
    for player in players:
        try:
            # First, get team_id from teams table
            team_result = await anyio.to_thread.run_sync(
                lambda: supabase.table("teams")
                .select("id")
                .eq("abbreviation", player["team_abbreviation"])
                .execute()
            )
            
            if team_result.data:
                player["team_id"] = team_result.data[0]["id"]
            else:
                print(f"Warning: Team {player['team_abbreviation']} not found in teams table")
                player["team_id"] = None
            
            # Upsert player data
            await anyio.to_thread.run_sync(
                lambda p=player: supabase.table("players").upsert(
                    [p], on_conflict="basketball_reference_id"
                ).execute()
            )
            success_count += 1
            
        except Exception as e:
            print(f"Error saving player {player.get('name', 'Unknown')} ({player.get('team_abbreviation')}): {e}")
            error_count += 1
            
    print(f"Players saved: {success_count} success, {error_count} errors")


async def scrape_all_team_rosters(supabase: Client, season: str = "2025"):
    """Scrape rosters for all teams"""
    try:
        print(f"[{datetime.now().isoformat()}] Starting roster scrape for season {season}...")
        
        # Get all teams from database
        teams_result = await anyio.to_thread.run_sync(
            lambda: supabase.table("teams").select("abbreviation").execute()
        )
        
        if not teams_result.data:
            print("No teams found in database. Please scrape teams first.")
            return
            
        total_teams = len(teams_result.data)
        total_players = 0
        
        def normalize_team_abbrev(abbrev: str) -> str | None:
            mapping = {
                "PHX": "PHO",
            }
            skip = {"NJN", "NOH"}
            if abbrev in skip:
                return None
            return mapping.get(abbrev, abbrev)

        for i, team in enumerate(teams_result.data, 1):
            team_abbrev = team["abbreviation"]
            scrape_abbrev = normalize_team_abbrev(team_abbrev)
            if not scrape_abbrev:
                print(f"[{i}/{total_teams}] Skipping roster scrape for {team_abbrev} (historical abbreviation)")
                continue

            print(f"[{i}/{total_teams}] Scraping roster for {team_abbrev}...")
            
            try:
                players = await get_team_roster(scrape_abbrev, season)
                if team_abbrev != scrape_abbrev:
                    for player in players:
                        player["team_abbreviation"] = team_abbrev
                await save_players(supabase, players)
                total_players += len(players)
                
                # Small delay to be respectful to Basketball-Reference
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error scraping roster for {team_abbrev}: {e}")
                continue
                
        print(f"[{datetime.now().isoformat()}] Roster scrape completed: {total_players} players from {total_teams} teams")
        
    except Exception as e:
        print(f"Error during roster scrape: {e}")


async def get_bulls_players_data():
    """Scrape Chicago Bulls players using advanced anti-bot protection"""
    try:
        logger.info("Starting Bulls players scraping with anti-bot protection")
        players = await scrape_bulls_players()
        logger.info(f"Successfully scraped {len(players)} Bulls players")
        return players
    except Exception as e:
        logger.error(f"Failed to scrape Bulls players: {e}")
        return []


async def save_bulls_players(supabase: Client, players: list):
    """Save Bulls players to Supabase"""
    if not players:
        logger.warning("No Bulls players to save")
        return
    
    try:
        for player in players:
            # Ensure team + season fields exist for DB constraints
            player['team_abbreviation'] = 'CHI'
            player.setdefault('season_year', f"{datetime.now().year-1}-{str(datetime.now().year)[2:]}")

            # Keep only columns that exist in the players table schema
            allowed_keys = {
                'name', 'jersey_number',
                'team_id', 'team_abbreviation',
                'position', 'height', 'weight', 'birth_date', 'experience', 'college',
                'basketball_reference_id', 'basketball_reference_url',
                'is_active', 'season_year',
            }
            player = {k: v for k, v in player.items() if k in allowed_keys}
            
            # Save to players table
            result = await anyio.to_thread.run_sync(
                lambda p=player: supabase.table("players").upsert(
                    [p], on_conflict="basketball_reference_id"
                ).execute()
            )
            logger.debug(f"Saved player: {player.get('name')}")
        
        logger.info(f"Successfully saved {len(players)} Bulls players to database")
    except Exception as e:
        logger.error(f"Error saving Bulls players: {e}")


async def scrape_all_data(supabase: Client, include_rosters: bool = True):
    """Main function to scrape all data including rosters"""
    try:
        print(f"[{datetime.now().isoformat()}] Starting full scrape...")

        # Scrape teams first
        teams = await get_teams_data()
        print(f"Fetched {len(teams)} teams")
        await save_teams(supabase, teams)

        # Scrape odds
        odds_data = await get_nba_odds()
        print(f"Fetched odds for {len(odds_data.get('events', []))} games")
        await process_odds_data(supabase, odds_data)

        # Scrape recent game results (NBA stats)
        await scrape_recent_results(supabase, days_back=3)
        
        # Scrape rosters if requested
        if include_rosters:
            await scrape_all_team_rosters(supabase)
        
        # Specifically scrape Bulls players with advanced anti-bot protection
        bulls_players = await get_bulls_players_data()
        if bulls_players:
            await save_bulls_players(supabase, bulls_players)

        print(f"[{datetime.now().isoformat()}] Full scrape completed successfully")
    except Exception as e:
        print(f"Error during full scrape: {e}")
