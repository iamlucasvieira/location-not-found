"""Streamlit dashboard for GeoGuessr leaderboard - 404 Location Not Found."""

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from location_not_found.analytics import ScoreAnalyzer
from location_not_found.data_loader import DataLoadError, GoogleSheetsLoader, load_config_from_env


def configure_page() -> None:
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="404 Location Not Found",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def display_header() -> None:
    """Display the dashboard header."""
    st.title("🌍 404 Location Not Found")
    st.markdown("**GeoGuessr Leaderboard & Analytics Dashboard**")
    st.markdown("---")


def display_error(error: Exception) -> None:
    """Display error message to user.

    Args:
        error: Exception to display
    """
    st.error(f"❌ Error: {error}")
    st.info(
        """
        **Setup Instructions:**
        1. Ensure your Google Sheets has columns: `player`, `date`, `score`
        2. Configure `credentials.json` with your service account
        3. Set up `.streamlit/secrets.toml` with your spreadsheet ID
        """
    )


def display_summary_metrics(analyzer: ScoreAnalyzer) -> None:
    """Display summary metrics in columns.

    Args:
        analyzer: ScoreAnalyzer instance
    """
    summary = analyzer.get_summary_stats()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Games", summary["total_games"])

    with col2:
        st.metric("Total Players", summary["total_players"])

    with col3:
        st.metric("Average Score", f"{summary['average_score']:,.0f}")

    with col4:
        st.metric("Highest Score", f"{summary['highest_score']:,}")

    with col5:
        st.metric("Perfect Games", summary["perfect_games"])


def display_leaderboard(analyzer: ScoreAnalyzer) -> None:
    """Display the main leaderboard.

    Args:
        analyzer: ScoreAnalyzer instance
    """
    st.subheader("🏆 Leaderboard")

    _col1, col2 = st.columns([3, 1])

    with col2:
        metric = st.selectbox(
            "Rank by",
            ["average_score", "total_score", "best_score", "total_games"],
            format_func=lambda x: x.replace("_", " ").title(),
        )
        top_n = st.slider("Show top", 5, 20, 10)

    leaderboard_df = analyzer.get_leaderboard(n=top_n, metric=metric)

    if not leaderboard_df.empty:
        # Format for display
        display_df = leaderboard_df.copy()
        display_df.index = display_df.index + 1  # Start ranking from 1

        # Add emoji medals for top 3
        display_df.insert(0, "Rank", ["🥇", "🥈", "🥉"] + [""] * (len(display_df) - 3))

        # Format numeric columns
        display_df["average_score"] = display_df["average_score"].apply(lambda x: f"{x:,.0f}")
        display_df["best_score"] = display_df["best_score"].apply(lambda x: f"{x:,}")
        display_df["worst_score"] = display_df["worst_score"].apply(lambda x: f"{x:,}")
        display_df["total_score"] = display_df["total_score"].apply(lambda x: f"{x:,}")

        # Trend indicator
        display_df["recent_trend"] = display_df["recent_trend"].apply(
            lambda x: f"📈 +{x:,.0f}" if x > 0 else (f"📉 {x:,.0f}" if x < 0 else "➡️ 0")
        )

        # Rename columns
        display_df = display_df.rename(
            columns={
                "player": "Player",
                "total_games": "Games",
                "average_score": "Avg Score",
                "best_score": "Best",
                "worst_score": "Worst",
                "total_score": "Total",
                "perfect_games": "Perfect",
                "recent_trend": "Trend",
            }
        )

        st.dataframe(display_df, use_container_width=True, hide_index=True)


def display_score_distribution(analyzer: ScoreAnalyzer) -> None:
    """Display score distribution chart.

    Args:
        analyzer: ScoreAnalyzer instance
    """
    st.subheader("📊 Score Distribution")

    dist_df = analyzer.get_score_distribution()

    if not dist_df.empty:
        fig = px.bar(
            dist_df,
            x="score_range",
            y="count",
            title="Distribution of Scores",
            labels={"score_range": "Score Range", "count": "Number of Games"},
            color="count",
            color_continuous_scale="viridis",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def display_player_trends(analyzer: ScoreAnalyzer, df: pd.DataFrame) -> None:
    """Display player performance trends over time.

    Args:
        analyzer: ScoreAnalyzer instance
        df: DataFrame with game data
    """
    st.subheader("📈 Player Performance Trends")

    players = sorted(df["player"].unique().tolist())
    selected_players = st.multiselect("Select players to compare", players, default=players[:3])

    if selected_players:
        fig = go.Figure()

        for player in selected_players:
            player_df = analyzer.get_player_history(player)
            if not player_df.empty:
                player_df = player_df.sort_values("date")
                fig.add_trace(
                    go.Scatter(
                        x=player_df["date"],
                        y=player_df["score"],
                        mode="lines+markers",
                        name=player,
                        hovertemplate="<b>%{fullData.name}</b><br>"
                        + "Date: %{x|%Y-%m-%d}<br>"
                        + "Score: %{y:,}<br>"
                        + "<extra></extra>",
                    )
                )

        fig.update_layout(
            title="Score Trends Over Time",
            xaxis_title="Date",
            yaxis_title="Score",
            hovermode="x unified",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        )

        st.plotly_chart(fig, use_container_width=True)


def display_recent_games(analyzer: ScoreAnalyzer) -> None:
    """Display recent games table.

    Args:
        analyzer: ScoreAnalyzer instance
    """
    st.subheader("🕐 Recent Games")

    n_games = st.slider("Number of games to show", 5, 50, 10, key="recent_games")
    recent_df = analyzer.get_recent_games(n=n_games)

    if not recent_df.empty:
        display_df = recent_df.copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        display_df["score"] = display_df["score"].apply(lambda x: f"{x:,}")

        # Add indicator for perfect scores
        display_df["indicator"] = display_df["score"].apply(lambda x: "⭐" if "25,000" in str(x) else "")

        display_df = display_df.rename(columns={"player": "Player", "date": "Date", "score": "Score", "indicator": ""})

        st.dataframe(display_df, use_container_width=True, hide_index=True)


def display_player_comparison(analyzer: ScoreAnalyzer, df: pd.DataFrame) -> None:
    """Display head-to-head player comparison.

    Args:
        analyzer: ScoreAnalyzer instance
        df: DataFrame with game data
    """
    st.subheader("⚔️ Player Comparison")

    players = sorted(df["player"].unique().tolist())

    col1, col2 = st.columns(2)

    with col1:
        player1 = st.selectbox("Player 1", players, key="p1")

    with col2:
        # Default to second player if available
        default_idx = 1 if len(players) > 1 else 0
        player2 = st.selectbox("Player 2", players, index=default_idx, key="p2")

    if player1 and player2 and player1 != player2:
        comparison = analyzer.get_head_to_head(player1, player2)

        if comparison:
            col1, col2, col3 = st.columns([1, 1, 1])

            p1_stats = comparison["player1"]
            p2_stats = comparison["player2"]

            with col1:
                st.markdown(f"### {player1}")
                st.metric("Average Score", f"{p1_stats['average_score']:,.0f}")
                st.metric("Best Score", f"{p1_stats['best_score']:,}")
                st.metric("Total Games", p1_stats["total_games"])
                st.metric("Perfect Games", p1_stats["perfect_games"])

            with col2:
                st.markdown("### VS")
                diff = comparison["avg_score_diff"]
                if abs(diff) < 10:
                    st.info("🤝 Very close match!")
                elif diff > 0:
                    st.success(f"👈 {player1} leads by {abs(diff):,.0f} points avg")
                else:
                    st.success(f"{player2} leads by {abs(diff):,.0f} points avg 👉")

            with col3:
                st.markdown(f"### {player2}")
                st.metric("Average Score", f"{p2_stats['average_score']:,.0f}")
                st.metric("Best Score", f"{p2_stats['best_score']:,}")
                st.metric("Total Games", p2_stats["total_games"])
                st.metric("Perfect Games", p2_stats["perfect_games"])

    elif player1 == player2:
        st.warning("Please select two different players to compare.")


def display_sidebar_filters(df: pd.DataFrame) -> tuple[date | None, date | None]:
    """Display sidebar filters.

    Args:
        df: DataFrame with game data

    Returns:
        Tuple of (start_date, end_date) or (None, None) if no filter
    """
    st.sidebar.header("🔍 Filters")

    use_date_filter = st.sidebar.checkbox("Filter by date range")

    if use_date_filter and not df.empty:
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()

        col1, col2 = st.sidebar.columns(2)

        with col1:
            start_date = st.date_input("Start date", min_date, min_value=min_date, max_value=max_date, key="start_date")

        with col2:
            end_date = st.date_input("End date", max_date, min_value=min_date, max_value=max_date, key="end_date")

        return start_date, end_date

    return None, None


def display_sidebar_info() -> None:
    """Display sidebar information."""
    st.sidebar.header("\u2139\ufe0f About")
    st.sidebar.markdown(
        """
        **404 Location Not Found** is a GeoGuessr leaderboard
        tracking player scores and performance.

        ### Features
        - 🏆 Real-time leaderboard
        - 📊 Score analytics
        - 📈 Performance trends
        - ⚔️ Player comparison
        - 🕐 Recent games

        ### Data Source
        Data is loaded from Google Sheets and
        cached for performance.
        """
    )

    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()


def main() -> None:
    """Main dashboard application."""
    configure_page()
    display_header()

    try:
        # Load configuration
        config = load_config_from_env()

        # Initialize loader and load data
        loader = GoogleSheetsLoader(config)
        scores = loader.load_data()

        if not scores:
            st.warning("No data found in the spreadsheet.")
            return

        # Convert to DataFrame
        df = loader.to_dataframe(scores)

        # Display sidebar
        display_sidebar_info()
        start_date, end_date = display_sidebar_filters(df)

        # Apply date filter if specified
        if start_date and end_date:
            df = df[(df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)]
            if df.empty:
                st.warning("No data found for the selected date range.")
                return

        # Initialize analyzer
        analyzer = ScoreAnalyzer(df)

        # Display dashboard sections
        display_summary_metrics(analyzer)
        st.markdown("---")

        display_leaderboard(analyzer)
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            display_score_distribution(analyzer)

        with col2:
            display_recent_games(analyzer)

        st.markdown("---")

        display_player_trends(analyzer, df)
        st.markdown("---")

        display_player_comparison(analyzer, df)

    except DataLoadError as e:
        display_error(e)
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()
