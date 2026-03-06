from unittest.mock import MagicMock, patch

import pytest

# Mock the Gemini client initialization before importing the module
with patch("google.genai.Client"):
    from nearquake.gemini_client import generate_response


@patch("nearquake.gemini_client.client.models.generate_content")
def test_generate_response_success(mock_generate):
    mock_response = MagicMock()
    mock_response.text = "Test response"
    mock_generate.return_value = mock_response

    result = generate_response("Test prompt", "user", "gemini-2.0-flash")

    assert result == "Test response"

    mock_generate.assert_called_once()
    call_args = mock_generate.call_args
    assert call_args[1]["model"] == "gemini-2.0-flash"


@patch("nearquake.gemini_client.client.models.generate_content")
def test_generate_response_with_system_role(mock_generate):
    mock_response = MagicMock()
    mock_response.text = "System response"
    mock_generate.return_value = mock_response

    result = generate_response("System prompt", "system", "gemini-2.0-flash")

    assert result == "System response"
    mock_generate.assert_called_once()


@patch("nearquake.gemini_client.client.models.generate_content")
def test_generate_response_with_assistant_role(mock_generate):
    mock_response = MagicMock()
    mock_response.text = "Assistant response"
    mock_generate.return_value = mock_response

    result = generate_response("Assistant prompt", "assistant", "gemini-2.0-flash")

    assert result == "Assistant response"
    mock_generate.assert_called_once()


def test_generate_response_invalid_role():
    with pytest.raises(
        ValueError,
        match="Error: Invalid role. Please choose one of: system, user, assistant.",
    ):
        generate_response("Test prompt", "invalid_role")


@patch(
    "nearquake.gemini_client.client.models.generate_content",
    side_effect=Exception("API error"),
)
def test_generate_response_api_error(mock_generate):
    result = generate_response("Test prompt")

    assert result is None
    mock_generate.assert_called_once()


@patch("nearquake.gemini_client.client.models.generate_content")
def test_generate_response_default_parameters(mock_generate):
    mock_response = MagicMock()
    mock_response.text = "Default response"
    mock_generate.return_value = mock_response

    result = generate_response("Test prompt")

    assert result == "Default response"

    mock_generate.assert_called_once()
    call_args = mock_generate.call_args
    assert call_args[1]["model"] == "gemini-2.0-flash"
