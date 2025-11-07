"""Analytics and data processing utilities for game scores."""

from datetime import date
from typing import Any

import pandas as pd
from pydantic import ValidationError

from location_not_found.models import PlayerStats


class ScoreAnalyzer:
    """Analyzer for game scores providing statistics and insights."""

    def __init__(self, df: pd.DataFrame) -> None:
        """Initialize the analyzer with a DataFrame.

        Args:
            df: DataFrame containing player, date, and score columns
        """
        self.df = df.copy()
        if not self.df.empty:
            self.df["game_date"] = pd.to_datetime(self.df["game_date"])

    def get_player_stats(self, player: str | None = None) -> list[PlayerStats]:
        """Calculate statistics for players.

        Args:
            player: Optional player name to filter by. If None, returns stats for all players.

        Returns:
            List of PlayerStats objects
        """
        if self.df.empty:
            return []

        df = self.df if player is None else self.df[self.df["player"] == player]

        if df.empty:
            return []

        # Group by player
        grouped = df.groupby("player").agg(
            total_games=("score", "count"),
            average_score=("score", "mean"),
            best_score=("score", "max"),
            worst_score=("score", "min"),
            total_score=("score", "sum"),
        )

        stats_list: list[PlayerStats] = []
        for player_name, row in grouped.iterrows():
            player_df = df[df["player"] == player_name]

            # Calculate perfect games (25000 score)
            perfect_games = int((player_df["score"] == 25000).sum())

            # Calculate recent trend (last 5 games vs previous 5 games)
            recent_trend = self._calculate_trend(player_df)

            try:
                stats = PlayerStats(
                    player=str(player_name),
                    total_games=int(row["total_games"]),
                    average_score=float(row["average_score"]),
                    best_score=int(row["best_score"]),
                    worst_score=int(row["worst_score"]),
                    total_score=int(row["total_score"]),
                    perfect_games=perfect_games,
                    recent_trend=recent_trend,
                )
                stats_list.append(stats)
            except ValidationError:
                continue

        # Sort by average score descending
        return sorted(stats_list, key=lambda x: x.average_score, reverse=True)

    def _calculate_trend(self, player_df: pd.DataFrame) -> float:
        """Calculate the recent performance trend for a player.

        Args:
            player_df: DataFrame filtered for a single player

        Returns:
            Trend value (positive = improving, negative = declining)
        """
        if len(player_df) < 2:
            return 0.0

        # Sort by game_date
        sorted_df = player_df.sort_values("game_date", ascending=False)

        # Take last 5 games
        recent_games = min(5, len(sorted_df))
        recent_scores = sorted_df.head(recent_games)["score"]

        # Take previous games for comparison
        if len(sorted_df) > recent_games:
            previous_scores = sorted_df.iloc[recent_games : recent_games * 2]["score"]
            if len(previous_scores) > 0:
                recent_avg = recent_scores.mean()
                previous_avg = previous_scores.mean()
                return float(recent_avg - previous_avg)

        return 0.0

    def get_leaderboard(self, n: int = 10, metric: str = "average_score") -> pd.DataFrame:
        """Get top N players by specified metric.

        Args:
            n: Number of top players to return
            metric: Metric to rank by ('average_score', 'total_score', 'best_score')

        Returns:
            DataFrame with top players
        """
        stats = self.get_player_stats()
        if not stats:
            return pd.DataFrame()

        df = pd.DataFrame([s.model_dump() for s in stats])

        if metric not in df.columns:
            metric = "average_score"

        return df.sort_values(metric, ascending=False).head(n).reset_index(drop=True)

    def get_score_distribution(self) -> pd.DataFrame:
        """Get distribution of scores in bins.

        Returns:
            DataFrame with score ranges and counts
        """
        if self.df.empty:
            return pd.DataFrame()

        bins = [0, 5000, 10000, 15000, 20000, 24999, 25000]
        labels = ["0-5K", "5K-10K", "10K-15K", "15K-20K", "20K-25K", "Perfect"]

        df = self.df.copy()
        df["score_range"] = pd.cut(df["score"], bins=bins, labels=labels, include_lowest=True)

        distribution = df["score_range"].value_counts().reset_index()
        distribution.columns = ["score_range", "count"]
        distribution = distribution.sort_values("score_range")

        return distribution

    def get_date_range_stats(self, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
        """Get statistics for a specific date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            DataFrame filtered by date range
        """
        if self.df.empty:
            return pd.DataFrame()

        df = self.df.copy()

        if start_date:
            df = df[df["game_date"] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df["game_date"] <= pd.Timestamp(end_date)]

        return df

    def get_recent_games(self, n: int = 10) -> pd.DataFrame:
        """Get N most recent games.

        Args:
            n: Number of recent games to return

        Returns:
            DataFrame with recent games
        """
        if self.df.empty:
            return pd.DataFrame()

        return self.df.nlargest(n, "game_date").reset_index(drop=True)

    def get_player_history(self, player: str) -> pd.DataFrame:
        """Get complete game history for a player.

        Args:
            player: Player name

        Returns:
            DataFrame with player's games sorted by game_date
        """
        if self.df.empty:
            return pd.DataFrame()

        player_df = self.df[self.df["player"] == player].copy()
        return player_df.sort_values("game_date", ascending=False).reset_index(drop=True)

    def get_time_series_data(self, player: str | None = None, resample: str = "D") -> pd.DataFrame:
        """Get time series data for score trends.

        Args:
            player: Optional player name to filter by
            resample: Pandas resample frequency ('D', 'W', 'M')

        Returns:
            DataFrame with time series data
        """
        if self.df.empty:
            return pd.DataFrame()

        df = self.df if player is None else self.df[self.df["player"] == player]

        if df.empty:
            return pd.DataFrame()

        # Set date as index and resample
        df = df.set_index("game_date").sort_index()
        resampled = df["score"].resample(resample).agg(["mean", "count", "max"])
        resampled = resampled.reset_index()
        resampled.columns = ["date", "average_score", "games_played", "best_score"]

        return resampled[resampled["games_played"] > 0]

    def get_head_to_head(self, player1: str, player2: str) -> dict[str, Any]:
        """Compare two players head-to-head.

        Args:
            player1: First player name
            player2: Second player name

        Returns:
            Dictionary with comparison statistics
        """
        stats = self.get_player_stats()
        stats_dict = {s.player: s for s in stats}

        p1_stats = stats_dict.get(player1)
        p2_stats = stats_dict.get(player2)

        if not p1_stats or not p2_stats:
            return {}

        return {
            "player1": p1_stats.model_dump(),
            "player2": p2_stats.model_dump(),
            "avg_score_diff": p1_stats.average_score - p2_stats.average_score,
            "total_games": p1_stats.total_games + p2_stats.total_games,
        }

    def get_summary_stats(self) -> dict[str, Any]:
        """Get overall summary statistics.

        Returns:
            Dictionary with summary statistics
        """
        if self.df.empty:
            return {
                "total_games": 0,
                "total_players": 0,
                "average_score": 0.0,
                "highest_score": 0,
                "perfect_games": 0,
            }

        return {
            "total_games": len(self.df),
            "total_players": self.df["player"].nunique(),
            "average_score": float(self.df["score"].mean()),
            "highest_score": int(self.df["score"].max()),
            "perfect_games": int((self.df["score"] == 25000).sum()),
            "date_range": {
                "start": self.df["game_date"].min().date().isoformat(),
                "end": self.df["game_date"].max().date().isoformat(),
            },
        }
