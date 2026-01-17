from unittest.mock import MagicMock, patch

import pytest

# Mock the OpenAI client initialization before importing the module
with patch("openai.OpenAI"):
    from nearquake.open_ai_client import generate_response


@patch("nearquake.open_ai_client.client.chat.completions.create")
def test_generate_response_success(mock_create):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_create.return_value = mock_response

    # Call the function
    result = generate_response("Test prompt", "user", "gpt-4o-mini")

    # Verify the result
    assert result == "Test response"

    # Verify the function was called with the correct parameters
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]
    assert call_args["model"] == "gpt-4o-mini"
    assert call_args["messages"][0]["role"] == "user"
    assert call_args["messages"][0]["content"] == "Test prompt"


@patch("nearquake.open_ai_client.client.chat.completions.create")
def test_generate_response_with_system_role(mock_create):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "System response"
    mock_create.return_value = mock_response

    # Call the function with role="system"
    result = generate_response("System prompt", "system", "gpt-4o-mini")

    # Verify the result
    assert result == "System response"

    # Verify the function was called with the correct parameters
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]
    assert call_args["messages"][0]["role"] == "system"
    assert call_args["messages"][0]["content"] == "System prompt"


@patch("nearquake.open_ai_client.client.chat.completions.create")
def test_generate_response_with_assistant_role(mock_create):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Assistant response"
    mock_create.return_value = mock_response

    # Call the function with role="assistant"
    result = generate_response("Assistant prompt", "assistant", "gpt-4o-mini")

    # Verify the result
    assert result == "Assistant response"

    # Verify the function was called with the correct parameters
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]
    assert call_args["messages"][0]["role"] == "assistant"
    assert call_args["messages"][0]["content"] == "Assistant prompt"


def test_generate_response_invalid_role():
    # Test with an invalid role
    with pytest.raises(
        ValueError,
        match="Error: Invalid role. Please choose one of: system, user, assistant.",
    ):
        generate_response("Test prompt", "invalid_role")


@patch(
    "nearquake.open_ai_client.client.chat.completions.create",
    side_effect=Exception("API error"),
)
def test_generate_response_api_error(mock_create):
    # Test error handling
    result = generate_response("Test prompt")

    # Verify the error is handled and returned as a string
    assert "Error API error" in result
    mock_create.assert_called_once()


@patch("nearquake.open_ai_client.client.chat.completions.create")
def test_generate_response_default_parameters(mock_create):
    # Setup mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Default response"
    mock_create.return_value = mock_response

    # Call the function with default parameters
    result = generate_response("Test prompt")

    # Verify the result
    assert result == "Default response"

    # Verify the function was called with the default parameters
    mock_create.assert_called_once()
    call_args = mock_create.call_args[1]
    assert call_args["model"] == "gpt-4o-mini"  # Default model
    assert call_args["messages"][0]["role"] == "user"  # Default role
