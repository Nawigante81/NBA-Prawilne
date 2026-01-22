"""
Utility script to populate odds_snapshots from existing odds table.
This helps with line movement tracking by creating historical snapshots.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from supabase_client import create_isolated_supabase_client

def populate_odds_snapshots():
    """
    Migrate existing odds data to odds_snapshots table.
    This creates historical snapshots from current odds data.
    """
    print("🔄 Populating odds_snapshots table from odds...")
    
    supabase = create_isolated_supabase_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        return False
    
    try:
        # Fetch all odds
        response = supabase.table("odds").select("*").execute()
        odds_rows = response.data or []
        
        print(f"📊 Found {len(odds_rows)} odds records")
        
        snapshots = []
        for row in odds_rows:
            snapshot = {
                "game_id": row.get("game_id"),
                "bookmaker_key": row.get("bookmaker_key"),
                "bookmaker_title": row.get("bookmaker_title"),
                "market_type": row.get("market_type"),
                "outcome_name": row.get("outcome_name"),
                "team": row.get("team"),
                "point": row.get("point"),
                "price": row.get("price"),
                "ts": row.get("last_update") or row.get("created_at"),
            }
            snapshots.append(snapshot)
        
        if snapshots:
            # Insert in batches of 100
            batch_size = 100
            for i in range(0, len(snapshots), batch_size):
                batch = snapshots[i:i+batch_size]
                supabase.table("odds_snapshots").insert(batch).execute()
                print(f"✅ Inserted batch {i//batch_size + 1} ({len(batch)} records)")
        
        print(f"✅ Successfully populated {len(snapshots)} odds snapshots")
        return True
        
    except Exception as e:
        print(f"❌ Error populating odds snapshots: {e}")
        return False


def compute_game_results_ats_ou():
    """
    Compute ATS and O/U results for existing game_results.
    This fills in the ats_result and ou_result fields.
    """
    print("🔄 Computing ATS and O/U results for game_results...")
    
    supabase = create_isolated_supabase_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        return False
    
    try:
        # Fetch all completed game results
        response = supabase.table("game_results").select("*").not_.is_("home_score", "null").execute()
        games = response.data or []
        
        print(f"📊 Found {len(games)} completed games")
        
        updates = []
        for game in games:
            game_id = game.get("id")
            home_score = game.get("home_score")
            away_score = game.get("away_score")
            closing_spread_home = game.get("closing_spread_home")
            closing_total = game.get("closing_total")
            
            if home_score is None or away_score is None:
                continue
            
            # Calculate actual margin (home team perspective)
            actual_margin = home_score - away_score
            actual_total = home_score + away_score
            
            update_data = {"id": game_id}
            
            # ATS calculation
            if closing_spread_home is not None:
                spread_diff = actual_margin - closing_spread_home
                
                if abs(spread_diff) < 0.5:  # Push (within 0.5 points)
                    update_data["ats_result_home"] = "P"
                    update_data["ats_result_away"] = "P"
                elif spread_diff > 0:  # Home covered
                    update_data["ats_result_home"] = "W"
                    update_data["ats_result_away"] = "L"
                else:  # Away covered
                    update_data["ats_result_home"] = "L"
                    update_data["ats_result_away"] = "W"
            
            # O/U calculation
            if closing_total is not None:
                total_diff = actual_total - closing_total
                
                if abs(total_diff) < 0.5:  # Push
                    update_data["ou_result"] = "P"
                elif total_diff > 0:  # Over
                    update_data["ou_result"] = "O"
                else:  # Under
                    update_data["ou_result"] = "U"
            
            if len(update_data) > 1:  # Has updates beyond id
                updates.append(update_data)
        
        if updates:
            # Update in batches
            batch_size = 50
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i+batch_size]
                for record in batch:
                    supabase.table("game_results").update(record).eq("id", record["id"]).execute()
                print(f"✅ Updated batch {i//batch_size + 1} ({len(batch)} records)")
        
        print(f"✅ Successfully computed ATS/OU for {len(updates)} games")
        return True
        
    except Exception as e:
        print(f"❌ Error computing ATS/OU: {e}")
        return False


def main():
    print("=" * 60)
    print("🏀 NBA Betting Data Population Utility")
    print("=" * 60)
    print()
    
    # Step 1: Populate odds snapshots
    if populate_odds_snapshots():
        print("✅ Odds snapshots populated successfully")
    else:
        print("⚠️ Failed to populate odds snapshots")
    
    print()
    
    # Step 2: Compute ATS/OU results
    if compute_game_results_ats_ou():
        print("✅ ATS/OU results computed successfully")
    else:
        print("⚠️ Failed to compute ATS/OU results")
    
    print()
    print("=" * 60)
    print("🎉 Data population complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
