# Nearquake Test Suite

This directory contains the test suite for the Nearquake application. The tests are organized by module and functionality.

## Test Files

- `test_command_handlers.py`: Unit tests for the command handlers in the CLI module
- `test_data_processor.py`: Tests for the data processing functionality
- `utils_test.py`: Tests for utility functions
- `integration_test.py`: Integration tests for the application
- `test_db_sessions.py`: Tests for database session management
- `config_test.py`: Tests for configuration management
- `db_test.py`: Tests for database operations

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run a specific test file:

```bash
python -m pytest nearquake/test/test_command_handlers.py
```

To run tests with verbose output:

```bash
python -m pytest -v
```

## Test Configuration

The test suite uses the configuration in `pytest.ini` and environment variables from `.env.test`. Make sure these files are properly configured before running tests.

## Mocking

The test suite uses mocking to isolate components and avoid external dependencies:

- Twitter API is mocked using `unittest.mock.patch`
- BlueSky client is mocked
- OpenAI client is mocked to avoid API key requirements

## Adding New Tests

When adding new tests:

1. Create a new test file or add to an existing one based on the module being tested
2. Follow the existing patterns for test organization
3. Use appropriate mocking to isolate the component being tested
4. Ensure tests are independent and don't rely on external services
5. Add documentation for new test files in this README 