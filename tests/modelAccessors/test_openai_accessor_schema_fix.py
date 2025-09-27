import json
from typing import cast
from unittest.mock import Mock, patch

from pydantic import TypeAdapter

from src.modelAccessors.openai_accessor import OpenAIAccessor
from src.dataModel.model_response import ClarifierResponse, ModelResponse


def test_ensure_openai_compatible_schema():
    """Test that discriminated union schemas are properly wrapped for OpenAI compatibility."""
    # Test with discriminated union (should be wrapped)
    adapter = cast(TypeAdapter[ModelResponse], TypeAdapter(ClarifierResponse))
    union_schema = adapter.json_schema()
    
    # Create accessor without initializing the client
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()
    
    # Test union schema wrapping
    fixed_schema, was_wrapped = accessor._ensure_openai_compatible_schema(union_schema)
    assert was_wrapped is True
    assert fixed_schema["type"] == "object"
    assert "properties" in fixed_schema
    assert "response" in fixed_schema["properties"]
    assert fixed_schema["required"] == ["response"]
    assert fixed_schema["additionalProperties"] is False
    assert fixed_schema["properties"]["response"] == union_schema
    
    # Test object schema (should not be wrapped)
    object_schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
        "required": ["test"]
    }
    unchanged_schema, was_wrapped = accessor._ensure_openai_compatible_schema(object_schema)
    assert was_wrapped is False
    assert unchanged_schema == object_schema


def test_response_unwrapping():
    """Test that wrapped responses are properly unwrapped."""
    # Mock the OpenAI client and response
    with patch('src.modelAccessors.openai_accessor.OpenAI') as mock_openai:
        accessor = OpenAIAccessor()
        mock_client = Mock()
        mock_openai.return_value = mock_client
        accessor.client = mock_client
        
        # Create mock response with wrapped data
        mock_message = Mock()
        mock_message.parsed = {"response": {"type": "implemented", "content": "test"}}
        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the call
        adapter = cast(TypeAdapter[ModelResponse], TypeAdapter(ClarifierResponse))
        schema = adapter.json_schema()
        
        result = accessor.call_model(
            prompt="test",
            adapter=adapter,
            schema=schema
        )
        
        # Verify the response was unwrapped correctly
        assert hasattr(result, 'type')
        assert result.type == "implemented"


def test_json_fallback_unwrapping():
    """Test that JSON fallback also unwraps responses correctly."""
    with patch('src.modelAccessors.openai_accessor.OpenAI') as mock_openai:
        accessor = OpenAIAccessor()
        mock_client = Mock()
        mock_openai.return_value = mock_client
        accessor.client = mock_client
        
        # Create mock response with JSON content (no parsed attribute)
        mock_message = Mock()
        mock_message.parsed = None
        mock_message.content = json.dumps({"response": {"type": "implemented", "content": "test"}})
        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the call
        adapter = cast(TypeAdapter[ModelResponse], TypeAdapter(ClarifierResponse))
        schema = adapter.json_schema()
        
        result = accessor.call_model(
            prompt="test",
            adapter=adapter,
            schema=schema
        )
        
        # Verify the response was unwrapped correctly
        assert hasattr(result, 'type')
        assert result.type == "implemented"


if __name__ == "__main__":
    test_ensure_openai_compatible_schema()
    test_response_unwrapping() 
    test_json_fallback_unwrapping()
    print("All tests passed!")