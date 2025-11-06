"""Script to load sample data into Google Sheets for testing.

Usage:
    python examples/load_sample_data.py
"""

import csv
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials


def load_sample_data_to_sheet(
    credentials_path: str = "credentials.json",
    spreadsheet_id: str | None = None,
    sheet_name: str = "Sheet1",
) -> None:
    """Load sample data from CSV to Google Sheets.

    Args:
        credentials_path: Path to service account credentials
        spreadsheet_id: Google Sheets spreadsheet ID
        sheet_name: Name of the sheet to write to
    """
    # Load credentials
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    client = gspread.authorize(credentials)

    # Open spreadsheet
    if spreadsheet_id:
        spreadsheet = client.open_by_key(spreadsheet_id)
    else:
        # Create a new spreadsheet
        spreadsheet = client.create("GeoGuessr Leaderboard - Sample Data")
        print(f"Created new spreadsheet: {spreadsheet.url}")
        print(f"Spreadsheet ID: {spreadsheet.id}")

    # Get or create worksheet
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        worksheet.clear()  # Clear existing data
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=10)

    # Load sample data from CSV
    csv_path = Path(__file__).parent / "sample_data.csv"

    with csv_path.open() as f:
        reader = csv.reader(f)
        data = list(reader)

    # Write data to sheet
    worksheet.update(range_name="A1", values=data)

    print(f"\n✅ Successfully loaded {len(data) - 1} rows of sample data!")
    print(f"📊 Spreadsheet URL: {spreadsheet.url}")
    print(f"\n💡 Next steps:")
    print(f"1. Copy the spreadsheet ID: {spreadsheet.id}")
    print(f"2. Add it to your .streamlit/secrets.toml or .env file")
    print(f"3. Run the dashboard: streamlit run src/location_not_found/dashboard.py")


if __name__ == "__main__":
    import os
    import sys

    from dotenv import load_dotenv

    load_dotenv()

    # Get configuration from environment or prompts
    creds_path = os.getenv("CREDENTIALS_PATH", "credentials.json")

    if not Path(creds_path).exists():
        print(f"❌ Credentials file not found: {creds_path}")
        print("Please create a service account and download credentials.json")
        sys.exit(1)

    spreadsheet_id = os.getenv("SPREADSHEET_ID")

    if not spreadsheet_id:
        print("No SPREADSHEET_ID found in environment.")
        print("A new spreadsheet will be created.")

    try:
        load_sample_data_to_sheet(
            credentials_path=creds_path,
            spreadsheet_id=spreadsheet_id,
            sheet_name=os.getenv("SHEET_NAME", "Sheet1"),
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
