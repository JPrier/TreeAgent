"""Test OpenAI accessor structured output compatibility."""

import os
from unittest.mock import Mock, patch

from pydantic import TypeAdapter

from src.modelAccessors.openai_accessor import OpenAIAccessor
from src.dataModel.model_response import ImplementedResponse


def test_structured_output_model_classification():
    """Test that models are correctly classified for structured output support."""
    os.environ['OPENAI_API_KEY'] = 'test'
    accessor = OpenAIAccessor()
    
    # Models that should support structured outputs
    assert accessor.supports_structured_outputs("gpt-4o")
    assert accessor.supports_structured_outputs("gpt-4o-mini")
    assert accessor.supports_structured_outputs("gpt-4o-2024-08-06")
    
    # Models that should NOT support structured outputs
    assert not accessor.supports_structured_outputs("gpt-4")
    assert not accessor.supports_structured_outputs("gpt-3.5-turbo")


@patch('src.modelAccessors.openai_accessor.OpenAI')
def test_non_structured_model_uses_json_object_format(mock_openai_class):
    """Test that non-structured models use json_object format and enhanced prompts."""
    # Setup mock
    mock_client = Mock()
    mock_response = Mock()
    mock_message = Mock()
    mock_message.parsed = None
    mock_message.content = '{"type": "implemented", "content": "test", "artifacts": []}'
    mock_response.choices = [mock_message]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client
    
    os.environ['OPENAI_API_KEY'] = 'test'
    accessor = OpenAIAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    schema = adapter.json_schema()
    
    # Call with gpt-4 (non-structured model)
    accessor.call_model(
        "test prompt",
        adapter=adapter,
        schema=schema,
        model="gpt-4",
        system_prompt="You are a helpful assistant."
    )
    
    # Verify correct response format and enhanced prompt
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["response_format"]["type"] == "json_object"
    
    # Verify system prompt was enhanced with schema information
    system_message = call_args["messages"][0]["content"]
    assert "schema" in system_message
    assert "JSON" in system_message


@patch('src.modelAccessors.openai_accessor.OpenAI')
def test_structured_model_uses_json_schema_format(mock_openai_class):
    """Test that structured models use json_schema format."""
    # Setup mock
    mock_client = Mock()
    mock_response = Mock()
    mock_message = Mock()
    mock_message.parsed = {"type": "implemented", "content": "test", "artifacts": []}
    mock_response.choices = [mock_message]
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client
    
    os.environ['OPENAI_API_KEY'] = 'test'
    accessor = OpenAIAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    schema = adapter.json_schema()
    
    # Call with gpt-4o (structured model)
    accessor.call_model(
        "test prompt",
        adapter=adapter,
        schema=schema,
        model="gpt-4o"
    )
    
    # Verify json_schema response format is used
    call_args = mock_client.chat.completions.create.call_args[1]
    response_format = call_args["response_format"]
    assert response_format["type"] == "json_schema"
    assert "json_schema" in response_format
    assert response_format["json_schema"]["strict"] is True