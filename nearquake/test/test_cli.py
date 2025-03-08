from unittest.mock import patch

from nearquake.cli import parse_arguments


@patch("argparse.ArgumentParser.parse_args")
def test_parse_arguments_default(mock_parse_args):
    """Test parse_arguments with default arguments."""
    # Setup mock to return default values
    mock_args = type(
        "Args",
        (),
        {
            "daily": False,
            "live": False,
            "initialize": False,
            "weekly": False,
            "monthly": False,
            "fun": False,
            "backfill": False,
        },
    )()
    mock_parse_args.return_value = mock_args

    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is False
    assert args.live is False
    assert args.initialize is False
    assert args.weekly is False
    assert args.monthly is False
    assert args.fun is False
    assert args.backfill is False

    # Verify the function was called
    mock_parse_args.assert_called_once()


@patch("sys.argv", ["program", "-d"])
def test_parse_arguments_daily():
    """Test parse_arguments with daily flag."""
    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is True
    assert args.live is False
    assert args.initialize is False
    assert args.weekly is False
    assert args.monthly is False
    assert args.fun is False
    assert args.backfill is False


@patch("sys.argv", ["program", "-l"])
def test_parse_arguments_live():
    """Test parse_arguments with live flag."""
    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is False
    assert args.live is True
    assert args.initialize is False
    assert args.weekly is False
    assert args.monthly is False
    assert args.fun is False
    assert args.backfill is False


@patch("sys.argv", ["program", "-i"])
def test_parse_arguments_initialize():
    """Test parse_arguments with initialize flag."""
    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is False
    assert args.live is False
    assert args.initialize is True
    assert args.weekly is False
    assert args.monthly is False
    assert args.fun is False
    assert args.backfill is False


@patch("sys.argv", ["program", "-w"])
def test_parse_arguments_weekly():
    """Test parse_arguments with weekly flag."""
    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is False
    assert args.live is False
    assert args.initialize is False
    assert args.weekly is True
    assert args.monthly is False
    assert args.fun is False
    assert args.backfill is False


@patch("sys.argv", ["program", "-m"])
def test_parse_arguments_monthly():
    """Test parse_arguments with monthly flag."""
    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is False
    assert args.live is False
    assert args.initialize is False
    assert args.weekly is False
    assert args.monthly is True
    assert args.fun is False
    assert args.backfill is False


@patch("sys.argv", ["program", "-f"])
def test_parse_arguments_fun():
    """Test parse_arguments with fun flag."""
    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is False
    assert args.live is False
    assert args.initialize is False
    assert args.weekly is False
    assert args.monthly is False
    assert args.fun is True
    assert args.backfill is False


@patch("sys.argv", ["program", "-b"])
def test_parse_arguments_backfill():
    """Test parse_arguments with backfill flag."""
    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is False
    assert args.live is False
    assert args.initialize is False
    assert args.weekly is False
    assert args.monthly is False
    assert args.fun is False
    assert args.backfill is True


@patch("sys.argv", ["program", "-d", "-l", "-i", "-w", "-m", "-f", "-b"])
def test_parse_arguments_all():
    """Test parse_arguments with all flags."""
    # Call the function
    args = parse_arguments()

    # Verify the result
    assert args.daily is True
    assert args.live is True
    assert args.initialize is True
    assert args.weekly is True
    assert args.monthly is True
    assert args.fun is True
    assert args.backfill is True
