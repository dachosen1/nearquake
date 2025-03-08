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
# or
make test
```

To run a specific test file:

```bash
python -m pytest nearquake/test/test_command_handlers.py
```

To run tests with verbose output:

```bash
python -m pytest -v
```

## Test Coverage

The test suite includes coverage reporting to measure how much of the codebase is tested. The current overall coverage is 84%.

### Coverage by Module

| Module                        | Coverage |
|-------------------------------|----------|
| nearquake/__init__.py         | 100%     |
| nearquake/app/__init__.py     | 100%     |
| nearquake/app/db.py           | 80%      |
| nearquake/cli/__init__.py     | 18%      |
| nearquake/cli/command_handlers.py | 99%  |
| nearquake/config/__init__.py  | 100%     |
| nearquake/data_processor.py   | 77%      |
| nearquake/open_ai_client.py   | 35%      |
| nearquake/post_manager.py     | 49%      |
| nearquake/utils/__init__.py   | 49%      |
| nearquake/utils/db_sessions.py| 81%      |

### Running Coverage Tests

To run tests with coverage reporting:

```bash
# Terminal output
python -m pytest --cov=nearquake --cov-report=term

# HTML report
python -m pytest --cov=nearquake --cov-report=html

# Using Makefile
make coverage
```

The HTML report will be generated in the `htmlcov` directory at the root of the project. Open `htmlcov/index.html` in a browser to view the detailed coverage report, or use:

```bash
make coverage-report
```

### Updating Coverage Information

The coverage information in this README is manually updated based on the output of the coverage tests. When you run the coverage tests, you should update the coverage percentages in this README if they have changed significantly.

### Coverage Report

![Coverage Report](../htmlcov/index.html)

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
6. Run coverage tests to ensure your tests adequately cover the code 