from unittest.mock import MagicMock, patch

import pytest

# Mock the Gemini client initialization before importing the module
with patch("google.genai.Client"):
    from nearquake.gemini_client import generate_response


@patch("nearquake.gemini_client.client.models.generate_content")
def test_generate_response_success(mock_generate):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "Test response"
    mock_generate.return_value = mock_response

    # Call the function
    result = generate_response("Test prompt", "user", "gemini-2.0-flash")

    # Verify the result
    assert result == "Test response"

    # Verify the function was called with the correct parameters
    mock_generate.assert_called_once()
    call_args = mock_generate.call_args[1]
    assert call_args["model"] == "gemini-2.0-flash"


@patch("nearquake.gemini_client.client.models.generate_content")
def test_generate_response_with_model_role(mock_generate):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "Model response"
    mock_generate.return_value = mock_response

    # Call the function with role="model"
    result = generate_response("Model prompt", "model", "gemini-2.0-flash")

    # Verify the result
    assert result == "Model response"

    # Verify the function was called
    mock_generate.assert_called_once()


def test_generate_response_invalid_role():
    # Test with an invalid role
    with pytest.raises(
        ValueError,
        match="Error: Invalid role. Please choose one of: user, model.",
    ):
        generate_response("Test prompt", "invalid_role")


@patch(
    "nearquake.gemini_client.client.models.generate_content",
    side_effect=Exception("API error"),
)
def test_generate_response_api_error(mock_generate):
    # Test error handling
    result = generate_response("Test prompt")

    # Verify the error is handled and returns None
    assert result is None
    mock_generate.assert_called_once()


@patch("nearquake.gemini_client.client.models.generate_content")
def test_generate_response_default_parameters(mock_generate):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "Default response"
    mock_generate.return_value = mock_response

    # Call the function with default parameters
    result = generate_response("Test prompt")

    # Verify the result
    assert result == "Default response"

    # Verify the function was called with the default parameters
    mock_generate.assert_called_once()
    call_args = mock_generate.call_args[1]
    assert call_args["model"] == "gemini-2.0-flash"  # Default model
