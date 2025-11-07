"""Pydantic models for data validation."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class GameScore(BaseModel):
    """Model representing a single game score entry."""

    player: str = Field(..., description="Player name", min_length=1)
    game_date: date = Field(..., description="Date of the game")
    score: int = Field(..., description="Score achieved", ge=0, le=25000)

    @field_validator("player")
    @classmethod
    def normalize_player_name(cls, v: str) -> str:
        """Normalize player name by stripping whitespace and title-casing."""
        return v.strip().title()

    @field_validator("game_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date:
        """Parse date from various formats."""
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            # Try multiple date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(v.strip(), fmt).date()
                except ValueError:
                    continue
            msg = f"Date format not recognized: {v}"
            raise ValueError(msg)
        msg = f"Invalid date type: {type(v)}"
        raise TypeError(msg)


class PlayerStats(BaseModel):
    """Model representing aggregated player statistics."""

    player: str = Field(..., description="Player name")
    total_games: int = Field(..., description="Total number of games played", ge=0)
    average_score: float = Field(..., description="Average score across all games", ge=0.0)
    best_score: int = Field(..., description="Best score achieved", ge=0)
    worst_score: int = Field(..., description="Worst score achieved", ge=0)
    total_score: int = Field(..., description="Sum of all scores", ge=0)
    perfect_games: int = Field(default=0, description="Number of perfect 25000 scores", ge=0)
    recent_trend: float = Field(
        default=0.0, description="Trend indicator: positive means improving, negative means declining"
    )

    class Config:
        """Pydantic config."""

        frozen = False


class DashboardConfig(BaseModel):
    """Model for dashboard configuration."""

    spreadsheet_id: str = Field(..., description="Google Sheets spreadsheet ID")
    sheet_name: str = Field(default="Sheet1", description="Name of the sheet to read from")
    credentials_path: str = Field(default="credentials.json", description="Path to Google service account credentials")
    cache_ttl: int = Field(default=300, description="Cache time-to-live in seconds", ge=0)
    max_score: int = Field(default=25000, description="Maximum possible score", ge=1)

    class Config:
        """Pydantic config."""

        frozen = True
