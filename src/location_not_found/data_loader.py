"""Google Sheets data loader with caching functionality."""

import logging
from pathlib import Path
from typing import ClassVar

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from pydantic import ValidationError

from location_not_found.models import DashboardConfig, GameScore

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Exception raised when data loading fails."""


class GoogleSheetsLoader:
    """Loader for Google Sheets data with caching and validation."""

    SCOPES: ClassVar[list[str]] = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    def __init__(self, config: DashboardConfig) -> None:
        """Initialize the Google Sheets loader.

        Args:
            config: Dashboard configuration containing credentials and sheet info
        """
        self.config = config
        self._client: gspread.Client | None = None

    @property
    def client(self) -> gspread.Client:
        """Get or create the gspread client."""
        if self._client is None:
            try:
                credentials = self._load_credentials()
                self._client = gspread.authorize(credentials)
            except Exception as e:
                msg = f"Failed to authenticate with Google Sheets: {e}"
                raise DataLoadError(msg) from e
        return self._client

    def _load_credentials(self) -> Credentials:
        """Load Google service account credentials.

        Returns:
            Service account credentials

        Raises:
            DataLoadError: If credentials file is not found or invalid
        """
        creds_path = Path(self.config.credentials_path)
        if not creds_path.exists():
            msg = f"Credentials file not found: {creds_path}"
            raise DataLoadError(msg)

        try:
            return Credentials.from_service_account_file(str(creds_path), scopes=self.SCOPES)
        except Exception as e:
            msg = f"Failed to load credentials from {creds_path}: {e}"
            raise DataLoadError(msg) from e

    @st.cache_data(ttl=300, show_spinner="Loading data from Google Sheets...")
    def load_data(_self) -> list[GameScore]:
        """Load and validate data from Google Sheets.

        Returns:
            List of validated GameScore objects

        Raises:
            DataLoadError: If data loading or validation fails
        """
        try:
            # Open spreadsheet and worksheet
            spreadsheet = _self.client.open_by_key(_self.config.spreadsheet_id)
            worksheet = spreadsheet.worksheet(_self.config.sheet_name)

            # Get all records as dictionaries
            records = worksheet.get_all_records()

            if not records:
                logger.warning("No data found in spreadsheet")
                return []

            # Validate and convert to GameScore objects
            validated_scores: list[GameScore] = []
            errors: list[tuple[int, str]] = []

            for idx, record in enumerate(records, start=2):  # Start at 2 (header is row 1)
                try:
                    # Normalize column names (case-insensitive)
                    normalized_record = {k.lower().strip(): v for k, v in record.items()}

                    # Map to expected field names
                    game_data = {
                        "player": normalized_record.get("player", ""),
                        "date": normalized_record.get("date", ""),
                        "score": normalized_record.get("score", 0),
                    }

                    score = GameScore(**game_data)
                    validated_scores.append(score)
                except ValidationError as e:
                    error_msg = _self._format_validation_error(e)
                    errors.append((idx, error_msg))
                    logger.warning(f"Row {idx} validation failed: {error_msg}")
                except Exception as e:
                    errors.append((idx, str(e)))
                    logger.warning(f"Row {idx} processing failed: {e}")

            # Log summary
            logger.info(f"Loaded {len(validated_scores)} valid records, {len(errors)} errors")

            if errors and len(errors) < 10:  # Only show errors if not too many
                for row_num, error in errors:
                    st.warning(f"Row {row_num}: {error}")
            else:
                return validated_scores

        except gspread.SpreadsheetNotFound:
            msg = f"Spreadsheet not found: {_self.config.spreadsheet_id}"
            raise DataLoadError(msg) from None
        except gspread.WorksheetNotFound:
            msg = f"Worksheet '{_self.config.sheet_name}' not found"
            raise DataLoadError(msg) from None
        except Exception as e:
            msg = f"Failed to load data: {e}"
            raise DataLoadError(msg) from e

    @staticmethod
    def _format_validation_error(error: ValidationError) -> str:
        """Format Pydantic validation error for display.

        Args:
            error: Pydantic validation error

        Returns:
            Formatted error message
        """
        errors = []
        for err in error.errors():
            field = ".".join(str(x) for x in err["loc"])
            msg = err["msg"]
            errors.append(f"{field}: {msg}")
        return "; ".join(errors)

    def to_dataframe(self, scores: list[GameScore]) -> pd.DataFrame:
        """Convert GameScore list to pandas DataFrame.

        Args:
            scores: List of GameScore objects

        Returns:
            DataFrame with game scores
        """
        if not scores:
            return pd.DataFrame(columns=["player", "date", "score"])

        data = [score.model_dump() for score in scores]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date", ascending=False).reset_index(drop=True)


def load_config_from_env() -> DashboardConfig:
    """Load dashboard configuration from Streamlit secrets or environment.

    Returns:
        Dashboard configuration

    Raises:
        DataLoadError: If required configuration is missing
    """
    try:
        # Try to load from Streamlit secrets first
        if "gsheets" in st.secrets:
            return DashboardConfig(
                spreadsheet_id=st.secrets["gsheets"]["spreadsheet_id"],
                sheet_name=st.secrets["gsheets"].get("sheet_name", "Sheet1"),
                credentials_path=st.secrets["gsheets"].get("credentials_path", "credentials.json"),
                cache_ttl=st.secrets["gsheets"].get("cache_ttl", 300),
            )

        # Fallback to environment variables
        import os

        from dotenv import load_dotenv

        load_dotenv()

        spreadsheet_id = os.getenv("SPREADSHEET_ID")

        def _raise_missing_id() -> None:
            msg = "SPREADSHEET_ID not found in secrets or environment"
            raise DataLoadError(msg)  # noqa: TRY301

        if not spreadsheet_id:
            _raise_missing_id()

        return DashboardConfig(
            spreadsheet_id=spreadsheet_id,
            sheet_name=os.getenv("SHEET_NAME", "Sheet1"),
            credentials_path=os.getenv("CREDENTIALS_PATH", "credentials.json"),
            cache_ttl=int(os.getenv("CACHE_TTL", "300")),
        )
    except Exception as e:
        msg = f"Failed to load configuration: {e}"
        raise DataLoadError(msg) from e
