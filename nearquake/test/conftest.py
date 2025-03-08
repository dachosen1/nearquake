from pathlib import Path
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv

# Apply patches before any modules are imported
twitter_patcher = patch("tweepy.Client", autospec=True)
twitter_patcher.start()

# Mock BlueSky client
bluesky_mock = MagicMock()
bluesky_mock.login = MagicMock()  # Mock the login method specifically
bluesky_patcher = patch("atproto.Client", return_value=bluesky_mock)
bluesky_patcher.start()


def pytest_configure(config):
    """Load test environment variables before running tests."""
    env_test_path = Path(".env.test")
    if env_test_path.exists():
        load_dotenv(env_test_path)
    else:
        print(
            "Warning: .env.test file not found. Using default test environment variables."
        )


def pytest_unconfigure(config):
    """Stop all patches when pytest exits."""
    twitter_patcher.stop()
    bluesky_patcher.stop()
