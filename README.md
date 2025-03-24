# Sports Arbitrage Detection System

A Python-based system that monitors sports odds across multiple bookmakers to identify arbitrage opportunities.

## ⚠️ Security Notice

This project uses environment variables for sensitive information. Never commit your `.env` file or expose your API keys. The `.env` file is already included in `.gitignore` to prevent accidental commits.

## Features

- Monitors odds from multiple sports leagues
- Identifies arbitrage opportunities
- Stores historical odds data in SQLite database
- Supports multiple sports including soccer, basketball, hockey, and more

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/arbitrage.git
cd arbitrage
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your The Odds API key to the `.env` file:
     ```
     ODDS_API_KEY=your_api_key_here
     ```
   - Get your API key from [The Odds API](https://the-odds-api.com/)
   - ⚠️ Never commit your `.env` file or share your API key

## Usage

Run the script:
```bash
python arbitrage.py
```

The script will:
1. Fetch current odds for all configured sports
2. Store the odds in a SQLite database
3. Analyze the odds for arbitrage opportunities
4. Display any found opportunities with implied probabilities less than 99%

## Configuration

- Modify `MAIN_SPORTS` in `arbitrage.py` to add or remove sports leagues
- Adjust `EXCLUDED_BOOKS` to filter out specific sportsbooks
- Change the arbitrage threshold in `find_implied_probabilities()` if needed

## Security Best Practices

1. Never commit your `.env` file
2. Keep your API keys secure and rotate them regularly
3. Use environment variables for all sensitive information
4. Check the `.gitignore` file to ensure sensitive files are excluded

## License

MIT License - see LICENSE file for details

## Disclaimer

This tool is for educational purposes only. Please check your local laws and regulations regarding sports betting and arbitrage. 