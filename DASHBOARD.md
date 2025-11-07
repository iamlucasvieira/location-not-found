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
- A Google Sheet with your game data

### 2. Installation

Install the package with dependencies:

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```

### 3. Google Sheets Setup (Easy!)

#### Step 1: Prepare Your Google Sheet

Create a Google Sheet with the following structure:

| player | date       | score |
|--------|------------|-------|
| Alice  | 2024-01-15 | 24500 |
| Bob    | 2024-01-15 | 18900 |
| Alice  | 2024-01-16 | 23100 |

**Column Requirements:**
- `player`: Player name (text)
- `date`: Game date (formats: YYYY-MM-DD, DD/MM/YYYY, or MM/DD/YYYY)
- `score`: Score from 0 to 25,000 (number)

#### Step 2: Enable Link Sharing

1. Click the **Share** button in your Google Sheet
2. Change access to **"Anyone with the link"** → **"Viewer"**
3. Click **Copy link**

That's it! No service accounts, no JSON credentials needed! 🎉

### 4. Configuration

Create `.streamlit/secrets.toml` in your project root:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit#gid=0"
type = "gsheets"

# Optional settings
[gsheets]
worksheet = "Sheet1"
ttl = 300
```

**Note:** Replace the URL with your Google Sheet's link. You can use the example file as a template:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your Google Sheet URL
```

### 5. Run the Dashboard

```bash
streamlit run src/location_not_found/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501` 🚀

## Data Schema

### Required Columns

Your Google Sheet must have these three columns (case-insensitive):

- **player** (string): Player name
- **date** (string/date): Game date
- **score** (number): Score between 0 and 25,000

### Supported Date Formats

- `YYYY-MM-DD` (e.g., 2024-01-15)
- `DD/MM/YYYY` (e.g., 15/01/2024)
- `MM/DD/YYYY` (e.g., 01/15/2024)
- `DD-MM-YYYY` (e.g., 15-01-2024)

### Data Validation

The dashboard uses Pydantic for robust data validation:
- Player names are automatically normalized (title case, trimmed whitespace)
- Dates are parsed from multiple formats automatically
- Scores must be between 0 and 25,000
- Invalid rows are logged with helpful error messages (shown in the UI)

## Architecture

### Project Structure

```
src/location_not_found/
├── models.py          # Pydantic models for data validation
├── data_loader.py     # Google Sheets integration with st.connection
├── analytics.py       # Statistics and data analysis
└── dashboard.py       # Streamlit UI and visualizations

examples/
├── sample_data.csv    # Sample dataset for testing
└── usage_example.py   # Programmatic usage example

.streamlit/
└── secrets.toml.example  # Configuration template

DASHBOARD.md           # This guide
```

### Key Technologies

- **Streamlit**: Web framework and UI
- **st-gsheets-connection**: Official Google Sheets connector
- **Pydantic**: Data validation with type safety
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations

### Design Patterns

- **Type Safety**: Full type hints throughout the codebase
- **Data Validation**: Automatic validation with Pydantic models
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

Automatically identifies and counts perfect 25,000 point scores with ⭐ indicator.

## Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub (without `secrets.toml`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Create a new app pointing to your repository
4. In app settings, add your secrets:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit#gid=0"
type = "gsheets"
```

5. Deploy!

**Important**: Never commit `secrets.toml` to version control!

### Docker

```bash
docker build -t location-not-found .
docker run -p 8501:8501 \
  -e STREAMLIT_SECRETS='[connections.gsheets]
spreadsheet="YOUR_SHEET_URL"
type="gsheets"' \
  location-not-found
```

## Configuration Options

### Cache Settings

Adjust cache TTL in `secrets.toml`:

```toml
[gsheets]
ttl = 600  # Cache for 10 minutes
```

Set to `0` to disable caching (not recommended for production).

### Worksheet Selection

If your data is in a different tab/worksheet:

```toml
[gsheets]
worksheet = "GameScores"  # Change from default "Sheet1"
```

## Troubleshooting

### "Failed to load data from Google Sheets"

**Solutions:**
- Verify your Google Sheet has link sharing enabled ("Anyone with the link")
- Check that the URL in `secrets.toml` is correct
- Ensure your sheet has the required columns: `player`, `date`, `score`
- Try refreshing the dashboard with the 🔄 button in the sidebar

### "No data found in spreadsheet"

**Solutions:**
- Verify there's data below the header row
- Check column names match: `player`, `date`, `score` (case-insensitive)
- Ensure the worksheet name in config matches your sheet

### Data validation errors

**Solutions:**
- Check date format matches one of the supported formats
- Ensure scores are numbers between 0 and 25,000
- Verify player names are not empty
- Look at the warning messages in the UI for specific row errors

### Connection timeout or quota exceeded

**Solutions:**
- Google Sheets API has usage limits
- Increase cache TTL to reduce API calls
- Consider copying data to a separate sheet if the source is very large

## Sample Data

Use the included `examples/sample_data.csv` to test the dashboard:

1. Create a new Google Sheet
2. Copy the sample data into it
3. Enable link sharing
4. Update your `secrets.toml` with the sheet URL
5. Run the dashboard!

## Development

### Code Quality

The project follows high Python standards:

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Run tests
uv run pytest
```

### Adding New Features

1. **Models**: Add new Pydantic models in `models.py`
2. **Analytics**: Extend `ScoreAnalyzer` in `analytics.py`
3. **Visualizations**: Add new display functions in `dashboard.py`

Example - Adding win streaks:

```python
# In analytics.py
def get_win_streaks(self, player: str) -> int:
    """Calculate longest win streak for a player."""
    # Implementation

# In dashboard.py
def display_win_streaks(analyzer: ScoreAnalyzer):
    """Display win streak statistics."""
    # Implementation
```

## Performance

- **Caching**: Data is cached for 5 minutes by default (configurable)
- **Lazy Loading**: Data is only fetched when needed
- **Efficient Queries**: Uses pandas for fast data manipulation
- **Connection Pooling**: Streamlit connections handle connection reuse

## Security

- **No Credentials Needed**: Uses public link sharing (simpler and safer)
- **Read-only Access**: Dashboard only reads data, never writes
- **Secrets Management**: Streamlit secrets are never exposed in code
- **Link Sharing**: While convenient, anyone with the link can view data
  - For private data, consider using service account authentication

## Why This Approach?

**Advantages of Public Sheet + Link Sharing:**
- ✅ No complex service account setup
- ✅ No credential files to manage
- ✅ Works with personal Google accounts
- ✅ Easy to update and maintain
- ✅ Perfect for team dashboards

**When to Use Service Accounts Instead:**
- Highly sensitive data
- Need write access
- Enterprise security requirements
- Automated data pipelines

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

See [LICENSE](LICENSE) for details.

## Support

For issues and questions:
- GitHub Issues: [location-not-found/issues](https://github.com/iamlucasvieira/location-not-found/issues)
- Documentation: [location-not-found docs](https://iamlucasvieira.github.io/location-not-found/)

## Acknowledgments

Built with ❤️ using:
- [Streamlit](https://streamlit.io/)
- [Streamlit GSheetsConnection](https://github.com/streamlit/gsheets-connection)
- [Pydantic](https://docs.pydantic.dev/)
- [Plotly](https://plotly.com/)
