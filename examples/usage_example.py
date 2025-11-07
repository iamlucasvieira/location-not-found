"""Example usage of the location-not-found library programmatically.

This demonstrates how to use the core components without running the Streamlit dashboard.
"""

from location_not_found import DashboardConfig, GoogleSheetsLoader, ScoreAnalyzer


def main() -> None:
    """Demonstrate programmatic usage of the library."""
    # Create configuration
    config = DashboardConfig(
        spreadsheet="your_spreadsheet_id_here",
        worksheet="Sheet1",
        cache_ttl=300,
    )

    # Initialize loader
    loader = GoogleSheetsLoader(config)

    # Load data
    print("Loading data from Google Sheets...")
    scores = loader.load_data()
    print(f"Loaded {len(scores)} game scores")

    # Convert to DataFrame
    df = loader.to_dataframe(scores)
    print(f"\nDataFrame shape: {df.shape}")
    print(f"\nFirst few rows:\n{df.head()}")

    # Initialize analyzer
    analyzer = ScoreAnalyzer(df)

    # Get summary statistics
    summary = analyzer.get_summary_stats()
    print("\n=== Summary Statistics ===")
    print(f"Total Games: {summary['total_games']}")
    print(f"Total Players: {summary['total_players']}")
    print(f"Average Score: {summary['average_score']:.2f}")
    print(f"Highest Score: {summary['highest_score']}")
    print(f"Perfect Games: {summary['perfect_games']}")

    # Get player statistics
    print("\n=== Player Statistics ===")
    player_stats = analyzer.get_player_stats()
    for stat in player_stats:
        print(f"\n{stat.player}:")
        print(f"  Games Played: {stat.total_games}")
        print(f"  Average Score: {stat.average_score:.2f}")
        print(f"  Best Score: {stat.best_score}")
        print(f"  Perfect Games: {stat.perfect_games}")
        trend_indicator = "📈" if stat.recent_trend > 0 else ("📉" if stat.recent_trend < 0 else "➡️")
        print(f"  Recent Trend: {trend_indicator} {stat.recent_trend:+.0f}")

    # Get leaderboard
    print("\n=== Top 5 Leaderboard ===")
    leaderboard = analyzer.get_leaderboard(n=5, metric="average_score")
    for idx, row in leaderboard.iterrows():
        rank = int(idx) + 1
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")
        print(f"{medal} {row['player']}: {row['average_score']:.0f} avg ({row['total_games']} games)")

    # Get recent games
    print("\n=== Recent Games ===")
    recent = analyzer.get_recent_games(n=5)
    for _, game in recent.iterrows():
        indicator = "⭐" if game["score"] == 25000 else ""
        print(f"{game['game_date'].strftime('%Y-%m-%d')} - {game['player']}: {game['score']:,} {indicator}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Update 'your_spreadsheet_id_here' with your actual spreadsheet ID")
        print("2. Configure Streamlit secrets with your Google Sheets credentials")
        print("3. Share the Google Sheet with your service account")
