"""
Import historical NBA box score data from CSV files to Supabase
Usage: python import_historical_data.py
"""

import os
import pandas as pd
from dotenv import load_dotenv
from supabase_client import create_isolated_supabase_client, get_supabase_config
from datetime import datetime
import time

# Load environment variables
load_dotenv()

def convert_minutes_to_seconds(minutes_str):
    """Convert minutes string (MM:SS) to total seconds"""
    if pd.isna(minutes_str) or minutes_str == '' or minutes_str == '0':
        return None
    try:
        parts = str(minutes_str).split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return None
    except:
        return None

def clean_dataframe(df):
    """Clean and prepare dataframe for database insertion"""
    # Rename columns to match database schema (snake_case)
    column_mapping = {
        'season_year': 'season_year',
        'game_date': 'game_date',
        'gameId': 'game_id',
        'matchup': 'matchup',
        'teamId': 'team_id',
        'teamCity': 'team_city',
        'teamName': 'team_name',
        'teamTricode': 'team_tricode',
        'teamSlug': 'team_slug',
        'personId': 'player_id',
        'personName': 'player_name',
        'position': 'position',
        'comment': 'comment',
        'jerseyNum': 'jersey_num',
        'minutes': 'minutes',
        'fieldGoalsMade': 'field_goals_made',
        'fieldGoalsAttempted': 'field_goals_attempted',
        'fieldGoalsPercentage': 'field_goals_percentage',
        'threePointersMade': 'three_pointers_made',
        'threePointersAttempted': 'three_pointers_attempted',
        'threePointersPercentage': 'three_pointers_percentage',
        'freeThrowsMade': 'free_throws_made',
        'freeThrowsAttempted': 'free_throws_attempted',
        'freeThrowsPercentage': 'free_throws_percentage',
        'reboundsOffensive': 'rebounds_offensive',
        'reboundsDefensive': 'rebounds_defensive',
        'reboundsTotal': 'rebounds_total',
        'assists': 'assists',
        'steals': 'steals',
        'blocks': 'blocks',
        'turnovers': 'turnovers',
        'foulsPersonal': 'fouls_personal',
        'points': 'points',
        'plusMinusPoints': 'plus_minus_points'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Convert game_date to ISO string to avoid JSON serialization issues
    df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df['game_date'] = df['game_date'].where(pd.notna(df['game_date']), None)
    
    # Convert game_id to string (stored as text in database)
    df['game_id'] = df['game_id'].astype(str)
    
    # Handle NaN values
    df['position'] = df['position'].fillna('')
    df['comment'] = df['comment'].fillna('')
    df['jersey_num'] = df['jersey_num'].fillna(0).astype(int)
    df['jersey_num'] = df['jersey_num'].replace(0, None)
    
    # Replace NaN percentages with None (NULL in database)
    percentage_cols = ['field_goals_percentage', 'three_pointers_percentage', 'free_throws_percentage']
    for col in percentage_cols:
        df[col] = df[col].where(pd.notna(df[col]), None)
    
    # Replace NaN integers with 0
    int_cols = [
        'field_goals_made', 'field_goals_attempted',
        'three_pointers_made', 'three_pointers_attempted',
        'free_throws_made', 'free_throws_attempted',
        'rebounds_offensive', 'rebounds_defensive', 'rebounds_total',
        'assists', 'steals', 'blocks', 'turnovers', 'fouls_personal', 'points'
    ]
    for col in int_cols:
        df[col] = df[col].fillna(0).astype(int)
    
    # Handle plus_minus (can be negative or None)
    df['plus_minus_points'] = df['plus_minus_points'].where(pd.notna(df['plus_minus_points']), None)

    # Replace any remaining NaN/NaT with None for JSON serialization
    df = df.where(pd.notna(df), None)

    return df

def import_csv_to_supabase(csv_path, supabase_client, batch_size=1000):
    """Import CSV file to Supabase in batches"""
    print(f"\n📂 Wczytywanie pliku: {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    total_rows = len(df)
    print(f"   Znaleziono {total_rows:,} wierszy")
    
    # Clean dataframe
    df = clean_dataframe(df)
    
    # Convert to list of dictionaries
    records = df.to_dict('records')
    
    # Import in batches
    total_batches = (total_rows + batch_size - 1) // batch_size
    success_count = 0
    error_count = 0
    
    for i in range(0, total_rows, batch_size):
        batch = records[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        try:
            # Upsert batch to avoid duplicates (requires unique index on game_id, player_id)
            result = supabase_client.table('player_game_stats').upsert(
                batch,
                on_conflict='game_id,player_id'
            ).execute()
            success_count += len(batch)
            print(f"   ✅ Batch {batch_num}/{total_batches}: {len(batch)} wierszy zaimportowano")
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            error_count += len(batch)
            print(f"   ❌ Batch {batch_num}/{total_batches}: Błąd - {str(e)[:100]}")
    
    return success_count, error_count

def main():
    """Main import function"""
    print("=" * 70)
    print("🏀 IMPORT DANYCH HISTORYCZNYCH NBA DO SUPABASE")
    print("=" * 70)
    
    # Get Supabase configuration
    config = get_supabase_config()
    
    if not config['available']:
        print("❌ Błąd: Brak konfiguracji Supabase!")
        print("   Sprawdź zmienne środowiskowe w pliku .env:")
        print("   - VITE_SUPABASE_URL")
        print("   - SUPABASE_SERVICE_KEY (lub VITE_SUPABASE_ANON_KEY)")
        return
    
    # Create Supabase client (use service key for elevated privileges)
    service_key = config['service_key'] or config['anon_key']
    supabase = create_isolated_supabase_client(config['url'], service_key)
    
    print(f"\n✅ Połączono z Supabase: {config['url']}")
    
    # Check if table exists
    try:
        test_query = supabase.table('player_game_stats').select('id').limit(1).execute()
        print("✅ Tabela player_game_stats istnieje")
    except Exception as e:
        print(f"\n❌ BŁĄD: Tabela player_game_stats nie istnieje!")
        print("   Najpierw uruchom migrację:")
        print("   1. Otwórz plik: supabase/migrations/20251231141500_005_create_player_game_stats_table.sql")
        print("   2. Skopiuj zawartość")
        print("   3. Wklej do SQL Editor w Supabase Dashboard")
        print("   4. Uruchom SQL")
        print(f"\n   Szczegóły błędu: {str(e)[:200]}")
        return
    
    # Find CSV files
    csv_files = [
        'nba historia/regular_season_box_scores_2010_2024_part_1.csv',
        'nba historia/regular_season_box_scores_2010_2024_part_2.csv',
        'nba historia/regular_season_box_scores_2010_2024_part_3.csv'
    ]
    
    # Check if files exist
    existing_files = [f for f in csv_files if os.path.exists(f)]
    
    if not existing_files:
        print("\n❌ Nie znaleziono plików CSV!")
        print("   Oczekiwane pliki w folderze 'nba historia/':")
        for f in csv_files:
            print(f"   - {f}")
        return
    
    print(f"\n📊 Znaleziono {len(existing_files)} plików CSV")
    
    # Import each file
    total_success = 0
    total_errors = 0
    start_time = time.time()
    
    for csv_file in existing_files:
        success, errors = import_csv_to_supabase(csv_file, supabase, batch_size=1000)
        total_success += success
        total_errors += errors
    
    elapsed_time = time.time() - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 PODSUMOWANIE IMPORTU")
    print("=" * 70)
    print(f"✅ Zaimportowano pomyślnie: {total_success:,} wierszy")
    if total_errors > 0:
        print(f"❌ Błędy: {total_errors:,} wierszy")
    print(f"⏱️  Czas importu: {elapsed_time:.1f} sekund")
    print(f"🚀 Średnia prędkość: {total_success / elapsed_time:.0f} wierszy/sekundę")
    print("\n✅ Import zakończony!")
    print("\nMożesz teraz używać danych historycznych w aplikacji.")
    print("Przykładowe zapytania:")
    print("  - Statystyki gracza: SELECT * FROM player_game_stats WHERE player_name = 'LeBron James' ORDER BY game_date DESC LIMIT 10")
    print("  - Statystyki Bulls: SELECT * FROM player_game_stats WHERE team_tricode = 'CHI' AND season_year = '2023-24'")

if __name__ == '__main__':
    main()
