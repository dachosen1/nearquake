# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Nearquake** ([@quakebot_](https://twitter.com/quakebot_)) is a Twitter/BlueSky bot that tweets earthquakes greater than magnitude 4.5 around the world, provides historical snapshots, and shares earthquake safety tips and fun facts. Data is sourced from the USGS Earthquake API.

## Development Commands

### Environment Setup
```bash
# Uses uv for dependency management
uv sync                    # Install dependencies
```

### Testing
```bash
make test                  # Run all tests with pytest
make coverage              # Run tests with coverage report
make coverage-report       # Open HTML coverage report
pytest -m "not integration"  # Skip integration tests
```

### Code Quality
```bash
make linter               # Format code with black and isort
make lint                 # Check code formatting (CI mode)
make format               # Format code (alias for linter)
```

### Running the Application Locally
```bash
make live                 # Monitor earthquakes in real-time (hourly check)
make daily                # Post daily earthquake summary
make weekly               # Post weekly earthquake summary
make monthly              # Post monthly earthquake summary
uv run main.py -f         # Post fun fact about earthquakes
uv run main.py -i         # Initialize database schemas
uv run main.py -b         # Backfill historical earthquake data (interactive)
```

### AWS Infrastructure & Deployment
```bash
make validate             # Validate CloudFormation template
make deploy-infra         # Deploy infrastructure (validates, builds, pushes, deploys)
make build-and-push       # Build Docker image and push to ECR
make stack-status         # Show CloudFormation stack status
make stack-outputs        # Show stack outputs
make clean                # Delete CloudFormation stack (interactive)
```

### Monitoring & Debugging
```bash
make logs-live            # Tail logs for live job
make logs-daily           # Tail logs for daily job
make logs-weekly          # Tail logs for weekly job
make logs-monthly         # Tail logs for monthly job
make logs-fun             # Tail logs for fun fact job
make batch-jobs           # List all batch jobs
make batch-describe-job JOB_ID=<id>  # Describe specific job
make batch-cancel-job JOB_ID=<id>    # Cancel specific job
```

## Architecture

### Command Pattern
The application uses a command handler pattern with a factory for extensibility:
- **main.py**: Entry point that parses CLI arguments and delegates to command handlers
- **CommandHandlerFactory** (nearquake/cli/command_handlers.py): Registers and creates handlers
- **CommandHandler** (abstract base): Each command (live, daily, weekly, monthly, fun, backfill, initialize) has its own handler class

### Core Components

#### Data Pipeline (nearquake/data_processor.py)
- **UploadEarthQuakeEvents**: Fetches earthquake data from USGS API and stores in database
  - Deduplicates events by checking existing `id_event` in database
  - Extracts event details (magnitude, timestamp, location coordinates, etc.)
  - Supports both real-time uploads and historical backfills
- **UploadEarthQuakeLocation**: Enriches events with reverse geocoding data
  - Uses external geocoding API to get continent, country, city details
  - Only processes events missing location data (left outer join)
- **TweetEarthquakeEvents**: Identifies and posts recent significant earthquakes
  - Filters: magnitude > 4.5, occurred within last 2 hours, not yet tweeted
  - Fetches shakemap images from USGS and attaches to tweets
  - Posts to both Twitter and BlueSky platforms

#### Database Layer (nearquake/app/db.py)
- **EventDetails** (earthquake.fct__event_details): Main earthquake event data
- **LocationDetails** (earthquake.dim__location_details): Geocoded location information
- **Post** (tweet.fct__post): Tweet history to prevent duplicate posts
- Uses SQLAlchemy ORM with PostgreSQL backend
- Alembic for database migrations (alembic/ directory)

#### Database Session Management (nearquake/utils/db_sessions.py)
- **DbSessionManager**: Context manager for database connections
  - Automatically commits on success, rolls back on exceptions
  - Provides `insert()`, `insert_many()`, `fetch_single()`, `fetch_many()` methods
  - Always use as context manager: `with DbSessionManager(url) as conn:`

#### Social Media Integration (nearquake/post_manager.py)
- **PlatformPoster** (abstract base): Common interface for posting platforms
- **TwitterPost**: Posts to Twitter using Tweepy (v2 API for tweets, v1.1 for media uploads)
- **BlueSkyPost**: Posts to BlueSky using atproto client
- **post_and_save_tweet()**: Posts to all platforms and saves to database
- Supports media attachments (shakemap images for earthquake tweets)

#### Configuration (nearquake/config/__init__.py)
- **Secrets Management**: Uses AWS Secrets Manager for credentials
  - `get_postgres_secret()`: Database credentials
  - `get_nearquake_secret()`: API keys (Twitter, BlueSky, geocoding)
- **Constants**:
  - `EARTHQUAKE_POST_THRESHOLD = 4.5`: Minimum magnitude to tweet
  - `REPORTED_SINCE_THRESHOLD = 7200`: Tweet earthquakes within 2 hours
- **URL Generators**:
  - `generate_time_period_url()`: USGS API URLs for hour/day/week/month
  - `generate_time_range_url()`: USGS API URLs for custom date ranges
  - `generate_event_detail_url()`: USGS event detail API
  - `generate_coordinate_lookup_detail_url()`: Reverse geocoding API

#### Utilities (nearquake/utils/)
- **format_earthquake_alert()**: Formats tweet text for events or facts
- **fetch_json_data_from_url()**: HTTP client with error handling
- **get_earthquake_image_url()**: Extracts shakemap image URL from USGS event data
- **extract_url_content()**: Downloads image data from URL
- **convert_timestamp_to_utc()**: Converts UNIX timestamps to UTC datetime
- **backfill_valid_date_range()**: Generates date ranges for backfill operations
- **logging_utils.py**: Structured logging with color-coded levels

### AWS Infrastructure
- **Deployment**: AWS Batch jobs on Fargate Spot instances
- **Scheduling**: EventBridge cron rules trigger different job types
- **Container**: Multi-stage Docker build with uv package manager
- **Database**: RDS PostgreSQL with SSL required
- **Secrets**: AWS Secrets Manager for credentials

### Testing
- **Unit tests**: nearquake/test/test_*.py
- **Integration tests**: Marked with `@pytest.mark.integration`
- **Test fixtures**: nearquake/test/conftest.py
- **Test environment**: Uses .env.test for configuration

## Important Patterns

### Adding a New Command
1. Create a new handler class inheriting from `CommandHandler` in nearquake/cli/command_handlers.py
2. Implement the `execute(self, db_session)` method
3. Register the handler in main.py: `factory.register("command_name", CommandHandlerClass)`
4. Add CLI argument in nearquake/cli/__init__.py: `parser.add_argument(...)`

### Database Operations
Always use `DbSessionManager` as a context manager to ensure proper transaction handling:
```python
from nearquake.config import POSTGRES_CONNECTION_URL
from nearquake.utils.db_sessions import DbSessionManager

with DbSessionManager(url=POSTGRES_CONNECTION_URL) as conn:
    # Database operations here
    conn.insert(model_instance)
```

### Posting to Social Media
Use the unified interface to post to all platforms and save to database:
```python
from nearquake.post_manager import post_and_save_tweet

tweet_data = {
    "post": "Tweet text here",
    "id_event": event_id,  # Optional, for earthquake events
    "post_type": "event",  # or "fact"
}
post_and_save_tweet(tweet_data, db_session, media_data=image_bytes)
```

### Fetching Earthquake Data
The USGS API returns GeoJSON with this structure:
```json
{
  "features": [
    {
      "id": "event_id",
      "properties": {"mag": 5.2, "place": "Location", ...},
      "geometry": {"coordinates": [lon, lat, depth]}
    }
  ]
}
```

### Shakemap Image Handling
Shakemap images are fetched from USGS event details and attached to tweets:
1. Fetch event details using `generate_event_detail_url(event_id)`
2. Extract shakemap URL using `get_earthquake_image_url(event_details)`
3. Download image data using `extract_url_content(image_url)`
4. Pass image bytes to `post_and_save_tweet()` via `media_data` parameter

## Development Notes

### Local Development
- Uses Docker Compose for local PostgreSQL database: `make up`
- Initialize database schemas before first run: `uv run main.py -i`
- Set up secrets locally or use .env file (not committed to git)

### Deployment Pipeline
GitHub Actions workflows (.github/workflows/):
- **deploy-ecr.yml**: Builds and pushes Docker image to ECR on push to master
- **workflow.yml**: Runs tests and deploys infrastructure
- CloudFormation template (aws-infrastructure.yml) defines all AWS resources

### Database Migrations
- Use Alembic for schema changes: `alembic revision -m "description"`
- Apply migrations: `alembic upgrade head`
- Configuration: alembic.ini and alembic/env.py

### Secrets Management
Required secrets in AWS Secrets Manager:
- **postgres-nearquake**: Database credentials (username, password, host, port, dbname, engine)
- **nearquake-secrets**: API keys (CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BEARER_TOKEN, BLUESKY_USER_NAME, BLUESKY_PASSWORD, GEO_API_KEY, GEO_REVERSE_LOOKUP_BASE_URL)
