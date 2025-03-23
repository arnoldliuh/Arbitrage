import sqlite3
import requests
import time
from datetime import datetime

# API Configuration (Use The Odds API)
API_KEY = "0be25729d5952f68e3656998f1811026"  # Your API key
BASE_URL = "https://api.the-odds-api.com/v4"

# Main sports to include (NBA, NCAAB, NHL)
MAIN_SPORTS = {
    "basketball_nba": "NBA",      # NBA
    "basketball_ncaab": "NCAAB",  # NCAA Basketball
    "icehockey_nhl": "NHL"        # NHL Hockey
}

# Market to include (totals only)
MARKET = ["totals"]

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
        market TEXT,  -- Market type (e.g., totals)
        outcome TEXT,
        odds DECIMAL(5,2),
        point_spread DECIMAL(5,2),  -- The line (e.g., 220.5 for basketball, 5.5 for hockey)
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Fetch all available sports
def fetch_sports():
    url = f"{BASE_URL}/sports?apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch sports: {response.status_code}")
        return None

# Fetch odds for a specific sport (totals only)
def fetch_odds(sport_key):
    url = f"{BASE_URL}/sports/{sport_key}/odds?regions=us&markets={','.join(MARKET)}&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 422:
        try:
            return response.json()
        except:
            return None
    else:
        print(f"Failed to fetch odds for {sport_key}: {response.status_code}")
        return None

# Store odds in database
def store_odds(sport_key, odds_data):
    for event in odds_data:
        # Skip events without home_team and away_team
        if "home_team" not in event or "away_team" not in event:
            continue

        event_name = event["sport_title"] + " - " + event["home_team"] + " vs " + event["away_team"]
        for bookmaker in event["bookmakers"]:
            sportsbook = bookmaker["title"]
            for market in bookmaker["markets"]:
                if market["key"] in MARKET:  # Only process totals
                    for outcome in market["outcomes"]:
                        point_spread = outcome.get("point", None)
                        cursor.execute("""
                            INSERT INTO odds (sport_key, event_name, sportsbook, market, outcome, odds, point_spread)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (sport_key, event_name, sportsbook, market["key"], outcome["name"], outcome["price"], point_spread))
    conn.commit()

# Function to find and print implied probabilities
def find_implied_probabilities():
    cursor.execute("""
        SELECT sport_key, event_name, market, outcome, sportsbook, odds, point_spread 
        FROM odds
        WHERE timestamp >= datetime('now', '-1 hour')
    """)
    data = cursor.fetchall()

    arbitrage_events = {}

    # Group odds by event and line
    for sport_key, event, market, outcome, sportsbook, odds, point_spread in data:
        if event not in arbitrage_events:
            arbitrage_events[event] = {}
        if point_spread not in arbitrage_events[event]:
            arbitrage_events[event][point_spread] = {}
        if outcome not in arbitrage_events[event][point_spread]:
            arbitrage_events[event][point_spread][outcome] = []
        arbitrage_events[event][point_spread][outcome].append((sportsbook, odds))

    # Check for arbitrage opportunities
    for event, lines in arbitrage_events.items():
        print(f"\n📊 Event: {event}")
        for line, outcomes in lines.items():
            print(f"  Line: {line}")
            if len(outcomes) >= 2:  # Need Over and Under
                best_odds = {}
                for outcome, sportsbook_odds in outcomes.items():
                    best_odds[outcome] = max(sportsbook_odds, key=lambda x: x[1])

                inverse_sum = sum(1 / odds[1] for odds in best_odds.values())

                for outcome, (sportsbook, odds) in best_odds.items():
                    print(f"    - Bet on {outcome} {line} at {sportsbook} (Odds: {odds})")
                print(f"    🔗 Total Implied Probability: {round(inverse_sum * 100, 2)}%")

                if inverse_sum < 0.99:
                    print("    🔥 ARBITRAGE OPPORTUNITY FOUND! 🔥")

# Main function
def main():
    sports = fetch_sports()
    if sports:
        for sport in sports:
            sport_key = sport["key"]
            if sport_key in MAIN_SPORTS:
                sport_name = MAIN_SPORTS[sport_key]
                print(f"Fetching odds for {sport_name}...")
                odds_data = fetch_odds(sport_key)
                if odds_data:
                    store_odds(sport_key, odds_data)
                time.sleep(1)

    find_implied_probabilities()
    conn.close()

if __name__ == "__main__":
    main()