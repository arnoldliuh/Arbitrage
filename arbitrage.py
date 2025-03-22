import sqlite3
import requests
import time  # Import the time module for adding delays
from datetime import datetime, timedelta

# API Configuration (Use The Odds API)
API_KEY = "0be25729d5952f68e3656998f1811026"  # Your API key
BASE_URL = "https://api.the-odds-api.com/v4"

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
        outcome TEXT,
        odds DECIMAL(5,2),
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

# Fetch odds for a specific sport
def fetch_odds(sport_key):
    url = f"{BASE_URL}/sports/{sport_key}/odds?regions=us&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch odds for {sport_key}: {response.status_code}")
        return None

# Store odds in database
def store_odds(sport_key, odds_data):
    for event in odds_data:
        event_name = event["sport_title"] + " - " + event["home_team"] + " vs " + event["away_team"]
        for bookmaker in event["bookmakers"]:
            sportsbook = bookmaker["title"]
            for market in bookmaker["markets"]:
                for outcome in market["outcomes"]:
                    cursor.execute("""
                        INSERT INTO odds (sport_key, event_name, sportsbook, outcome, odds)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sport_key, event_name, sportsbook, outcome["name"], outcome["price"]))
    conn.commit()

# Function to find arbitrage opportunities
def find_arbitrage():
    cursor.execute("""
        SELECT sport_key, event_name, outcome, sportsbook, odds 
        FROM odds
        WHERE timestamp >= datetime('now', '-1 hour')  -- Get latest odds
    """)
    data = cursor.fetchall()

    arbitrage_events = {}

    for sport_key, event, outcome, sportsbook, odds in data:
        if event not in arbitrage_events:
            arbitrage_events[event] = {}
        arbitrage_events[event][outcome] = (sportsbook, odds)

    for event, outcomes in arbitrage_events.items():
        if len(outcomes) >= 2:
            inverse_sum = sum(1 / odds[1] for odds in outcomes.values())

            if inverse_sum < 1:  # Arbitrage detected!
                print(f"\n🔥 Arbitrage Found for {event} 🔥")
                for outcome, (sportsbook, odds) in outcomes.items():
                    print(f"Bet on {outcome} at {sportsbook} (Odds: {odds})")
                print(f"🔗 Total Implied Probability: {round(inverse_sum * 100, 2)}% (should be < 100%)\n")

# Main function
def main():
    # Fetch all available sports
    sports = fetch_sports()
    if sports:
        for sport in sports:
            sport_key = sport["key"]
            print(f"Fetching odds for {sport['title']}...")
            odds_data = fetch_odds(sport_key)
            if odds_data:
                store_odds(sport_key, odds_data)
            time.sleep(1)  # Add a 1-second delay between API calls

    # Find and display arbitrage opportunities
    find_arbitrage()

    # Close DB connection
    conn.close()

if __name__ == "__main__":
    main()