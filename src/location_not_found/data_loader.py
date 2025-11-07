"""Google Sheets data loader using Streamlit's connection interface."""

import logging

import pandas as pd
import streamlit as st
from pydantic import ValidationError
from streamlit_gsheets import GSheetsConnection

from location_not_found.models import DashboardConfig, GameScore

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Exception raised when data loading fails."""


class GoogleSheetsLoader:
    """Loader for Google Sheets data using Streamlit's connection interface."""

    def __init__(self, config: DashboardConfig | None = None) -> None:
        """Initialize the Google Sheets loader.

        Args:
            config: Optional dashboard configuration. If not provided, uses Streamlit secrets.
        """
        self.config = config

    @st.cache_data(ttl=300, show_spinner="Loading data from Google Sheets...")
    def load_data(_self, worksheet: str | None = None) -> list[GameScore]:
        """Load and validate data from Google Sheets.

        Args:
            worksheet: Optional worksheet name to override config

        Returns:
            List of validated GameScore objects

        Raises:
            DataLoadError: If data loading or validation fails
        """
        try:
            # Create connection
            conn = st.connection("gsheets", type=GSheetsConnection)

            # Determine which worksheet to read
            sheet_name = worksheet
            if sheet_name is None and _self.config:
                sheet_name = _self.config.worksheet

            # Read data from Google Sheets
            # If config specifies a spreadsheet, use it; otherwise use default from secrets
            if _self.config and _self.config.spreadsheet:
                df = conn.read(spreadsheet=_self.config.spreadsheet, worksheet=sheet_name, ttl=_self.config.cache_ttl)
            else:
                df = conn.read(worksheet=sheet_name, ttl=300)

            if df.empty:
                logger.warning("No data found in spreadsheet")
                return []

            # Validate and convert to GameScore objects
            validated_scores: list[GameScore] = []
            errors: list[tuple[int, str]] = []

            for idx, row in df.iterrows():
                try:
                    # Normalize column names (case-insensitive)
                    row_dict = {k.lower().strip(): v for k, v in row.to_dict().items()}

                    # Map to expected field names
                    game_data = {
                        "player": row_dict.get("player", ""),
                        "date": row_dict.get("date", ""),
                        "score": row_dict.get("score", 0),
                    }

                    score = GameScore(**game_data)
                    validated_scores.append(score)
                except ValidationError as e:
                    error_msg = _self._format_validation_error(e)
                    errors.append((idx + 2, error_msg))  # +2 because pandas is 0-indexed and row 1 is header
                    logger.warning(f"Row {idx + 2} validation failed: {error_msg}")
                except Exception as e:
                    errors.append((idx + 2, str(e)))
                    logger.warning(f"Row {idx + 2} processing failed: {e}")

            # Log summary
            logger.info(f"Loaded {len(validated_scores)} valid records, {len(errors)} errors")

            # Show errors to user if not too many
            if errors and len(errors) < 10:
                for row_num, error in errors:
                    st.warning(f"Row {row_num}: {error}")

            return validated_scores  # noqa: TRY300

        except Exception as e:
            msg = f"Failed to load data from Google Sheets: {e}"
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


def load_config_from_secrets() -> DashboardConfig | None:
    """Load dashboard configuration from Streamlit secrets.

    Returns:
        Dashboard configuration or None if not configured

    Raises:
        DataLoadError: If configuration is invalid
    """
    try:
        # Check if gsheets config exists in secrets
        if "gsheets" in st.secrets:
            gsheets_config = st.secrets["gsheets"]
            return DashboardConfig(
                spreadsheet=gsheets_config.get("spreadsheet", ""),
                worksheet=gsheets_config.get("worksheet", "Sheet1"),
                cache_ttl=gsheets_config.get("ttl", 300),
            )

<<<<<<< HEAD
        # Fallback to environment variables
        load_dotenv()

        spreadsheet_id = os.getenv("SPREADSHEET_ID", "")

        def _raise_missing_id() -> NoReturn:
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
=======
        # If no specific config, return None and let st.connection use default from secrets
        return None

>>>>>>> c44de4d (Simplify Google Sheets integration using st.connection)
    except Exception as e:
        msg = f"Failed to load configuration from secrets: {e}"
        raise DataLoadError(msg) from e
