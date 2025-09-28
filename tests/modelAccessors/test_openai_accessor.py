"""Test OpenAI accessor model validation and structured output support."""

import json
import os
from typing import cast
from unittest.mock import Mock, patch

from pydantic import TypeAdapter

from src.modelAccessors.openai_accessor import OpenAIAccessor
from src.dataModel.model_response import ClarifierResponse, ImplementedResponse, ModelResponse


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


def test_prepare_schema_for_openai():
    """Test that discriminated union schemas are properly flattened for OpenAI compatibility."""
    # Test with discriminated union (should be flattened)
    adapter = cast(TypeAdapter[ModelResponse], TypeAdapter(ClarifierResponse))
    union_schema = adapter.json_schema()
    
    # Create accessor without initializing the client
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()
    
    # Test union schema flattening
    fixed_schema = accessor._prepare_schema_for_openai(union_schema)
    assert fixed_schema["type"] == "object"
    assert "properties" in fixed_schema
    assert "oneOf" not in fixed_schema
    assert "anyOf" not in fixed_schema
    # OpenAI requires all properties to be in the required array
    expected_props = ["type", "content", "artifacts", "follow_up_ask"]
    assert set(fixed_schema["required"]) == set(expected_props)
    assert fixed_schema["additionalProperties"] is False
    
    # Should have properties from both FollowUpResponse and ImplementedResponse
    properties = fixed_schema["properties"]
    assert "type" in properties
    assert "content" in properties  # Common field
    assert "artifacts" in properties  # Common field
    assert "follow_up_ask" in properties  # FollowUpResponse field
    
    # Type field should have correct enum values
    type_prop = properties["type"]
    assert type_prop["type"] == "string"
    assert set(type_prop["enum"]) == {"follow_up_required", "implemented"}
    
    # Test object schema (should not be changed)
    object_schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
        "required": ["test"]
    }
    unchanged_schema = accessor._prepare_schema_for_openai(object_schema)
    assert unchanged_schema == object_schema


def test_extract_response_from_openai_format():
    """Test that responses are properly extracted from OpenAI format."""
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()
    
    # Test with discriminated union schema (should be returned as-is)
    adapter = cast(TypeAdapter[ModelResponse], TypeAdapter(ClarifierResponse))
    union_schema = adapter.json_schema()
    
    response = {"type": "implemented", "content": "test"}
    extracted = accessor._extract_response_from_openai_format(response, union_schema)
    assert extracted == {"type": "implemented", "content": "test"}
    
    # Test with object schema (should be returned as-is)
    object_schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
        "required": ["test"]
    }
    object_response = {"test": "value"}
    unchanged = accessor._extract_response_from_openai_format(object_response, object_schema)
    assert unchanged == {"test": "value"}


def test_response_unwrapping_integration():
    """Test that flattened responses are properly handled in the full call flow."""
    # Mock the OpenAI client and response
    with patch('src.modelAccessors.openai_accessor.OpenAI') as mock_openai:
        accessor = OpenAIAccessor()
        mock_client = Mock()
        mock_openai.return_value = mock_client
        accessor.client = mock_client
        
        # Create mock response with flattened data (no wrapping)
        mock_message = Mock()
        mock_message.parsed = {"type": "implemented", "content": "test"}
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
        
        # Verify the response was handled correctly
        assert hasattr(result, 'type')
        assert result.type == "implemented"


def test_json_fallback_unwrapping_integration():
    """Test that JSON fallback also handles flattened responses correctly."""
    with patch('src.modelAccessors.openai_accessor.OpenAI') as mock_openai:
        accessor = OpenAIAccessor()
        mock_client = Mock()
        mock_openai.return_value = mock_client
        accessor.client = mock_client
        
        # Create mock response with JSON content (no parsed attribute)
        mock_message = Mock()
        mock_message.parsed = None
        mock_message.content = json.dumps({"type": "implemented", "content": "test"})
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
        
        # Verify the response was handled correctly
        assert hasattr(result, 'type')
        assert result.type == "implemented"

def test_full_modelresponse_compatibility():
    """Test that the full ModelResponse schema is OpenAI compatible after flattening."""
    # This tests the exact scenario from the GitHub issue
    adapter = TypeAdapter(ModelResponse)
    schema = adapter.json_schema()
    
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()
    
    # The original schema has oneOf which OpenAI doesn't support
    assert "oneOf" in schema
    
    # After preparation, should be fully OpenAI compatible
    openai_schema = accessor._prepare_schema_for_openai(schema)
    assert openai_schema["type"] == "object"
    assert "oneOf" not in str(openai_schema)
    assert "anyOf" not in str(openai_schema)
    # OpenAI requires all properties to be in the required array
    expected_props = ["type", "content", "artifacts", "subtasks", "follow_up_ask", "error_message", "retryable"]
    assert set(openai_schema["required"]) == set(expected_props)
    
    # Should have all possible properties from all union members
    properties = openai_schema["properties"]
    expected_props = ["type", "content", "artifacts", "subtasks", "follow_up_ask", "error_message", "retryable"]
    for prop in expected_props:
        assert prop in properties, f"Missing property: {prop}"
    
    # Type field should have all discriminator values
    type_prop = properties["type"]
    assert type_prop["type"] == "string"
    expected_types = {"decomposed", "implemented", "follow_up_required", "failed"}
    assert set(type_prop["enum"]) == expected_types
    
    # Should preserve complex type references
    # Use robust key checking due to potential encoding issues
    has_defs = any(key.endswith("defs") for key in openai_schema.keys())
    assert has_defs
    defs_key = next(key for key in openai_schema.keys() if key.endswith("defs"))
    assert "Task" in openai_schema[defs_key]


def test_openai_required_array_compliance():
    """Test that all properties are included in required array for OpenAI compliance."""
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()

    # Test case 1: Object schema missing some required properties
    incomplete_schema = {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["test"]},
            "content": {"type": "string"},
            "optional_field": {"type": "string", "default": "default"}
        },
        "required": ["type"],  # Missing content and optional_field
        "additionalProperties": False
    }

    fixed_schema = accessor._prepare_schema_for_openai(incomplete_schema)
    
    # All properties should now be in required array
    properties = set(fixed_schema["properties"].keys())
    required = set(fixed_schema["required"])
    assert properties == required, f"Properties {properties} != Required {required}"
    assert "content" in fixed_schema["required"], "content should be in required array"

    # Test case 2: Empty required array  
    empty_required_schema = {
        "type": "object",
        "properties": {
            "field1": {"type": "string"},
            "field2": {"type": "number"}
        },
        "required": [],
        "additionalProperties": False
    }

    fixed_empty = accessor._prepare_schema_for_openai(empty_required_schema)
    
    # All properties should be added to required
    assert len(fixed_empty["required"]) == len(fixed_empty["properties"])
    assert set(fixed_empty["required"]) == set(fixed_empty["properties"].keys())

    # Test case 3: Schema that already has all properties in required (should be unchanged)
    complete_schema = {
        "type": "object", 
        "properties": {
            "prop1": {"type": "string"},
            "prop2": {"type": "boolean"}
        },
        "required": ["prop1", "prop2"],
        "additionalProperties": False
    }

    unchanged_schema = accessor._prepare_schema_for_openai(complete_schema)
    
    # Should be identical (except potentially reordered)
    assert set(unchanged_schema["required"]) == {"prop1", "prop2"}
    assert unchanged_schema["properties"] == complete_schema["properties"]


def test_recursive_required_array_fix():
    """Test that nested objects in $defs also get complete required arrays."""
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()

    # Create a schema with nested objects that have incomplete required arrays
    schema_with_nested_issues = {
        "type": "object",
        "properties": {
            "main_field": {"type": "string"}
        },
        "required": ["main_field"],
        "$defs": {
            "IncompleteObject": {
                "type": "object",
                "properties": {
                    "prop1": {"type": "string"},
                    "prop2": {"type": "number"},
                    "prop3": {"type": "boolean"}
                },
                "required": ["prop1"]  # Missing prop2 and prop3
            },
            "EmptyRequiredObject": {
                "type": "object", 
                "properties": {
                    "field_a": {"type": "string"},
                    "field_b": {"type": "array"}
                }
                # No required array at all
            }
        }
    }

    fixed_schema = accessor._prepare_schema_for_openai(schema_with_nested_issues)
    
    # Check that nested objects now have complete required arrays
    incomplete_obj = fixed_schema["$defs"]["IncompleteObject"]
    assert set(incomplete_obj["required"]) == {"prop1", "prop2", "prop3"}
    
    empty_req_obj = fixed_schema["$defs"]["EmptyRequiredObject"] 
    assert set(empty_req_obj["required"]) == {"field_a", "field_b"}
    
    # Verify top level is still correct
    assert set(fixed_schema["required"]) == {"main_field"}
