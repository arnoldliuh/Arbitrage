import sqlite3
import requests
import time
from datetime import datetime, timedelta

# API Configuration
API_KEY = "1b688ed00b4b57a9b35b15d17426fc84"  # The Odds API key
BASE_URL = "https://api.the-odds-api.com/v4"

# Excluded sportsbooks
EXCLUDED_BOOKS = []

# Main sports to include
MAIN_SPORTS = {
    # Basketball 
    "basketball_ncaab": "NCAAB",  
    "basketball_nbl": "NBL (Australia)",  
    
    # Boxing
    "boxing_boxing": "Boxing",
    
    # Ice Hockey 
    "icehockey_ahl": "AHL",  
    "icehockey_liiga": "Finnish Liiga",  
    "icehockey_mestis": "Finnish Mestis",  
    "icehockey_sweden_hockey_league": "SHL",  
    "icehockey_sweden_allsvenskan": "HockeyAllsvenskan",  
    
    # MMA
    "mma_mixed_martial_arts": "MMA",  # Year-round
    
    # Rugby
    "rugbyleague_nrl": "NRL",  
    
    # Soccer (Currently Active Leagues)
    "soccer_argentina_primera_division": "Argentina Primera",  
    "soccer_australia_aleague": "A-League",  
    "soccer_austria_bundesliga": "Austrian Bundesliga",  
    "soccer_belgium_first_div": "Belgium First Division",  
    "soccer_brazil_campeonato": "Brazil Serie A",  
    "soccer_brazil_serie_b": "Brazil Serie B",  
    "soccer_chile_campeonato": "Chile Primera",  
    "soccer_china_superleague": "China Super League",  
    "soccer_denmark_superliga": "Denmark Superliga",  
    "soccer_england_efl_cup": "EFL Cup",  
    "soccer_england_league1": "League 1",  
    "soccer_england_league2": "League 2",   
    "soccer_finland_veikkausliiga": "Veikkausliiga",  
    "soccer_france_ligue_one": "Ligue 1",  
    "soccer_france_ligue_two": "Ligue 2",  
    "soccer_germany_bundesliga": "Bundesliga",  
    "soccer_germany_bundesliga2": "Bundesliga 2",  
    "soccer_germany_liga3": "3. Liga",  
    "soccer_greece_super_league": "Greek Super League",  
    "soccer_italy_serie_a": "Serie A",  
    "soccer_italy_serie_b": "Serie B",  
    "soccer_japan_j_league": "J League",  
    "soccer_korea_kleague1": "K League 1",  
    "soccer_league_of_ireland": "League of Ireland",  
    "soccer_mexico_ligamx": "Liga MX",  
    "soccer_netherlands_eredivisie": "Eredivisie",  
    "soccer_norway_eliteserien": "Eliteserien",  
    "soccer_poland_ekstraklasa": "Ekstraklasa",  
    "soccer_portugal_primeira_liga": "Primeira Liga",  
    "soccer_spain_la_liga": "La Liga",  
    "soccer_spain_segunda_division": "La Liga 2",  
    "soccer_spl": "Scottish Premiership",  
    "soccer_sweden_allsvenskan": "Allsvenskan",  
    "soccer_sweden_superettan": "Superettan",  
    "soccer_switzerland_superleague": "Swiss Super League",  
    "soccer_turkey_super_league": "Turkish Super League",  
    
    # Australian Rules
    "aussierules_afl": "AFL"  
}

# Markets to include
MARKETS = ["h2h"]  # Only moneyline bets

# Connect to SQLite database
conn = sqlite3.connect("sports_odds.db")
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS odds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sport_key TEXT,
        event_name TEXT,
        sportsbook TEXT,
        market TEXT,
        outcome TEXT,
        odds DECIMAL(5,2),
        point_spread DECIMAL(5,2),
        total_points DECIMAL(5,2),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Fetch odds from API
def fetch_odds(sport_key):
    markets_param = ','.join(MARKETS)
    url = f"{BASE_URL}/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=us&markets={markets_param}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch odds for {sport_key}: {response.status_code}")
        return None

# Store odds in database
def store_odds(sport_key, odds_data):
    if not odds_data:
        return

    # Prepare batch insert data
    batch_data = []
    for event in odds_data:
        # Skip events without home_team and away_team (e.g., futures)
        if "home_team" not in event or "away_team" not in event:
            continue

        event_name = f"{event['sport_title']} - {event['home_team']} vs {event['away_team']}"
        
        for bookmaker in event["bookmakers"]:
            # Skip excluded sportsbooks
            if bookmaker["title"] in EXCLUDED_BOOKS:
                continue
                
            for market in bookmaker["markets"]:
                if market["key"] in MARKETS:  # Process all markets
                    for outcome in market["outcomes"]:
                        point_spread = outcome.get("point", None)  # Get the point spread (only for spreads)
                        total_points = outcome.get("point", None)  # Get the total points (only for totals)
                        batch_data.append((
                            sport_key, event_name, bookmaker["title"],
                            market["key"], outcome["name"], outcome["price"],
                            point_spread, total_points
                        ))

    # Batch insert
    if batch_data:
        cursor.executemany("""
            INSERT INTO odds (sport_key, event_name, sportsbook, market, outcome, odds, point_spread, total_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)
        conn.commit()

# Function to find and print implied probabilities for all events
def find_implied_probabilities():
    cursor.execute("""
        SELECT sport_key, event_name, market, outcome, sportsbook, odds, point_spread, total_points 
        FROM odds
        WHERE timestamp >= datetime('now', '-1 hour')  -- Get latest odds
    """)
    data = cursor.fetchall()

    arbitrage_events = {}

    # Group odds by event and outcome
    for sport_key, event, market, outcome, sportsbook, odds, point_spread, total_points in data:
        if event not in arbitrage_events:
            arbitrage_events[event] = {}
        if market not in arbitrage_events[event]:
            arbitrage_events[event][market] = {}
        if outcome not in arbitrage_events[event][market]:
            arbitrage_events[event][market][outcome] = []
        arbitrage_events[event][market][outcome].append((sportsbook, odds, total_points))

    # Check for arbitrage opportunities
    for event, markets in arbitrage_events.items():
        # Process moneyline bets
        if "h2h" in markets:
            outcomes = markets["h2h"]
            if len(outcomes) >= 2:  # Need both home and away outcomes
                # Find the best odds for each outcome
                best_odds = {}
                for outcome, sportsbook_odds in outcomes.items():
                    best_odds[outcome] = max(sportsbook_odds, key=lambda x: x[1])  # Max odds for each outcome

                # Calculate total implied probability
                inverse_sum = sum(1 / odds[1] for odds in best_odds.values())
                total_prob = round(inverse_sum * 100, 2)

                # Only print if total probability is less than 99%
                if total_prob < 99:
                    print(f"\n📊 Event: {event}")
                    print("    Moneyline Bets:")
                    for outcome, (sportsbook, odds, _) in best_odds.items():
                        print(f"    - Bet on {outcome} at {sportsbook} (Odds: {odds})")
                    print(f"    🔗 Total Implied Probability: {total_prob}%")
                    print("    🔥 ARBITRAGE OPPORTUNITY FOUND! 🔥")

# Main function
def main():
    # Process each sport
    for sport_key in MAIN_SPORTS:
        sport_name = MAIN_SPORTS[sport_key]
        print(f"\nFetching odds for {sport_name}...")
        odds_data = fetch_odds(sport_key)
        if odds_data:
            store_odds(sport_key, odds_data)

    # Find and display implied probabilities for all events
    find_implied_probabilities()

    # Close DB connection
    conn.close()

if __name__ == "__main__":
    main()