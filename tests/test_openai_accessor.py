"""Test OpenAI accessor model validation and structured output support."""

import os
from unittest.mock import Mock, patch

from pydantic import TypeAdapter

from src.modelAccessors.openai_accessor import OpenAIAccessor
from src.dataModel.model_response import ImplementedResponse


def test_supported_model_validation():
    """Test that only supported models are accepted."""
    os.environ['OPENAI_API_KEY'] = 'test'
    accessor = OpenAIAccessor()
    
    # Supported models should pass validation
    assert "gpt-4o" in accessor.supported_models
    assert "gpt-4o-mini" in accessor.supported_models
    assert "gpt-5-mini" in accessor.supported_models
    assert "gpt-5-nano" in accessor.supported_models
    
    # Unsupported models should not be in the list
    assert "gpt-4" not in accessor.supported_models
    assert "gpt-3.5-turbo" not in accessor.supported_models


@patch('src.modelAccessors.openai_accessor.OpenAI')
def test_unsupported_model_raises_error(mock_openai_class):
    """Test that unsupported models raise validation error."""
    mock_client = Mock()
    mock_openai_class.return_value = mock_client
    
    os.environ['OPENAI_API_KEY'] = 'test'
    accessor = OpenAIAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    schema = adapter.json_schema()
    
    # Should raise ValueError for unsupported model
    try:
        accessor.call_model(
            "test prompt",
            adapter=adapter,
            schema=schema,
            model="gpt-4"  # This model is not supported
        )
        assert False, "Expected ValueError to be raised"
    except ValueError as e:
        assert "Unsupported model 'gpt-4'" in str(e)
    except Exception as e:
        assert False, f"Expected ValueError, got {type(e).__name__}: {e}"


@patch('src.modelAccessors.openai_accessor.OpenAI')
def test_supported_model_uses_json_schema_format(mock_openai_class):
    """Test that supported models use json_schema format."""
    # Use a custom class instead of Mock to avoid the parsed attribute issue
    class MockMessage:
        def __init__(self, content):
            self.content = content
            # Don't create a parsed attribute

    class MockChoice:
        def __init__(self, message):
            self.message = message
    
    mock_client = Mock()
    mock_response = Mock()
    mock_message = MockMessage('{"type": "implemented", "content": "test", "artifacts": []}')
    mock_choice = MockChoice(mock_message)
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client
    
    os.environ['OPENAI_API_KEY'] = 'test'
    accessor = OpenAIAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    schema = adapter.json_schema()
    
    # Call with supported model  
    response = accessor.call_model(
        "test prompt",
        adapter=adapter,
        schema=schema,
        model="gpt-5-nano"  # This model is supported
    )
    
    # Verify json_schema response format is used
    call_args = mock_client.chat.completions.create.call_args[1]
    response_format = call_args["response_format"]
    assert response_format["type"] == "json_schema"
    assert "json_schema" in response_format
    assert response_format["json_schema"]["strict"] is True
    
    # Verify the response is properly parsed
    assert response.type == "implemented"
    assert response.content == "test"


def test_default_model_is_supported():
    """Test that the default model is in the supported list."""
    os.environ['OPENAI_API_KEY'] = 'test'
    accessor = OpenAIAccessor()
    
    # The default model should be supported
    assert "gpt-5-nano" in accessor.supported_models


def test_tool_support():
    """Test that tool support works for supported models."""
    os.environ['OPENAI_API_KEY'] = 'test'
    accessor = OpenAIAccessor()
    
    # Test tool support
    assert accessor.supports_tools("gpt-4o")
    assert accessor.supports_tools("gpt-4o-mini")
    assert accessor.supports_tools("gpt-5-mini")
    assert accessor.supports_tools("gpt-5-nano")
    
    # Old models shouldn't be in tool support either
    assert not accessor.supports_tools("gpt-4")