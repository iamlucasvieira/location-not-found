# 🌍 404 Location Not Found - Dashboard Guide

A comprehensive GeoGuessr leaderboard dashboard built with Streamlit, featuring real-time statistics, player analytics, and performance tracking.

## Features

- 🏆 **Real-time Leaderboard** - Rank players by average score, total score, or best performance
- 📊 **Score Distribution** - Visualize score ranges and performance patterns
- 📈 **Performance Trends** - Track player improvement over time
- ⚔️ **Player Comparison** - Head-to-head statistics between players
- 🕐 **Recent Games** - View the latest game results
- 🎯 **Smart Analytics** - Automatic trend detection and insights
- 💾 **Caching** - Fast data loading with configurable cache

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Google account with access to Google Sheets
- Service account credentials for Google Sheets API

### 2. Installation

Install the package with dependencies:

```bash
uv sync
```

Or install manually:

```bash
pip install -e .
```

### 3. Google Sheets Setup

#### Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google Sheets API** and **Google Drive API**
4. Create a service account:
   - Navigate to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Give it a name (e.g., "streamlit-dashboard")
   - Click "Create and Continue"
   - Grant role: "Editor" (or more restrictive if preferred)
   - Click "Done"
5. Create and download credentials:
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create New Key"
   - Choose JSON format
   - Save the file as `credentials.json` in the project root

#### Prepare Your Google Sheet

1. Create a Google Sheet with the following structure:

| player | date       | score |
|--------|------------|-------|
| Alice  | 2024-01-15 | 24500 |
| Bob    | 2024-01-15 | 18900 |
| Alice  | 2024-01-16 | 23100 |

2. Share the sheet with your service account email (found in `credentials.json` as `client_email`)
   - Grant "Viewer" or "Editor" access

### 4. Configuration

#### Option A: Using Streamlit Secrets (Recommended for Production)

Create `.streamlit/secrets.toml`:

```toml
[gsheets]
spreadsheet_id = "your_spreadsheet_id_here"
sheet_name = "Sheet1"
credentials_path = "credentials.json"
cache_ttl = 300
```

#### Option B: Using Environment Variables (Local Development)

Create `.env`:

```bash
SPREADSHEET_ID=your_spreadsheet_id_here
SHEET_NAME=Sheet1
CREDENTIALS_PATH=credentials.json
CACHE_TTL=300
```

**Finding your Spreadsheet ID:**
From the Google Sheets URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

### 5. Run the Dashboard

```bash
streamlit run src/location_not_found/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Data Schema

### Required Columns

Your Google Sheet must have these columns (case-insensitive):

- **player** (string): Player name
- **date** (string/date): Game date in format YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY
- **score** (number): Score between 0 and 25,000

### Data Validation

The dashboard uses Pydantic for robust data validation:

- Player names are automatically normalized (title case, trimmed whitespace)
- Dates are parsed from multiple formats
- Scores must be between 0 and 25,000
- Invalid rows are logged with helpful error messages

## Architecture

### Components

```
src/location_not_found/
├── models.py          # Pydantic models for data validation
├── data_loader.py     # Google Sheets integration with caching
├── analytics.py       # Statistics and data analysis
└── dashboard.py       # Streamlit UI and visualizations
```

### Key Design Patterns

- **Type Safety**: Full type hints with Pydantic models
- **Data Validation**: Automatic validation with helpful error messages
- **Caching**: Streamlit's `@st.cache_data` for performance
- **Separation of Concerns**: Clean separation between data, logic, and UI
- **Error Handling**: Graceful error handling with user-friendly messages

## Advanced Features

### Custom Metrics

The dashboard supports ranking by:
- **Average Score**: Mean score across all games
- **Total Score**: Sum of all scores
- **Best Score**: Highest single game score
- **Total Games**: Number of games played

### Trend Detection

Automatically calculates performance trends by comparing:
- Recent 5 games average
- Previous 5 games average
- Displays 📈 for improvement, 📉 for decline

### Date Range Filtering

Filter all statistics and visualizations by custom date ranges through the sidebar.

### Perfect Games Tracking

Automatically identifies and counts perfect 25,000 point scores.

## Deployment

### Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Create a new app
4. Add secrets in app settings (same format as `secrets.toml`)
5. Deploy!

**Important**: Don't commit `credentials.json` or `secrets.toml` to version control!

### Docker

A Dockerfile is provided for containerized deployment:

```bash
docker build -t location-not-found .
docker run -p 8501:8501 -v $(pwd)/credentials.json:/app/credentials.json location-not-found
```

## Troubleshooting

### "Spreadsheet not found"
- Verify the spreadsheet ID is correct
- Ensure the service account has access to the sheet

### "Credentials file not found"
- Check that `credentials.json` exists in the specified path
- Verify the path in your configuration

### "No data found"
- Ensure your sheet has the required columns: player, date, score
- Check that column names match (case-insensitive)
- Verify there's data below the header row

### Data validation errors
- Check date format matches one of: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY
- Ensure scores are numbers between 0 and 25,000
- Verify player names are not empty

## Development

### Code Quality

The project follows high Python standards:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Run tests
uv run pytest

# Type checking (if using mypy)
mypy src/
```

### Adding New Features

1. **Models**: Add new Pydantic models in `models.py`
2. **Analytics**: Extend `ScoreAnalyzer` in `analytics.py`
3. **Visualizations**: Add new display functions in `dashboard.py`

Example - Adding a new metric:

```python
# In analytics.py
def get_consistency_score(self, player: str) -> float:
    """Calculate player consistency (lower std dev = more consistent)."""
    player_df = self.df[self.df["player"] == player]
    return float(player_df["score"].std())

# In dashboard.py
def display_consistency_chart(analyzer: ScoreAnalyzer, df: pd.DataFrame):
    """Display player consistency rankings."""
    # Implementation here
```

## Performance

- **Caching**: Data is cached for 5 minutes by default (configurable via `cache_ttl`)
- **Lazy Loading**: Data is only fetched when needed
- **Efficient Queries**: Uses pandas for fast data manipulation

## Security

- Never commit credentials files
- Use environment-specific secrets management
- Restrict service account permissions to minimum required
- Regularly rotate service account keys

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

See [LICENSE](LICENSE) for details.

## Support

For issues and questions:
- GitHub Issues: [location-not-found/issues](https://github.com/iamlucasvieira/location-not-found/issues)
- Documentation: [location-not-found docs](https://iamlucasvieira.github.io/location-not-found/)
