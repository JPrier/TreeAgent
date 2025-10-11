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
    """Test that discriminated union schemas are made OpenAI-compliant while preserving structure."""
    # Test with discriminated union (should preserve oneOf structure, not flatten)
    adapter = cast(TypeAdapter[ModelResponse], TypeAdapter(ClarifierResponse))
    union_schema = adapter.json_schema()
    
    # Create accessor without initializing the client
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()
    
    # Test union schema - should preserve oneOf but make it compliant
    fixed_schema = accessor._prepare_schema_for_openai(union_schema)
    
    # Should preserve oneOf structure (better than flattening)
    assert "oneOf" in fixed_schema, "Should preserve oneOf structure"
    
    # Should have proper $defs with compliance
    assert "$defs" in fixed_schema
    
    # Check that $defs objects are compliant
    for def_name, def_obj in fixed_schema["$defs"].items():
        if "properties" in def_obj:
            assert def_obj.get("additionalProperties") is False, f"{def_name} should have additionalProperties: false"
    
    # Should preserve original required array logic (not force all properties required)
    follow_up_def = fixed_schema["$defs"]["FollowUpResponse"]
    impl_def = fixed_schema["$defs"]["ImplementedResponse"]
    
    # FollowUpResponse should still only require follow_up_ask (preserve original logic)
    assert follow_up_def.get("required") == ["follow_up_ask"], "Should preserve original required logic"
    
    # ImplementedResponse should have no required fields (preserve original logic)  
    assert impl_def.get("required") == [], "Should preserve original required logic"

    # Test with object schema (should add additionalProperties: false)
    object_schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
        "required": ["test"]
    }
    fixed_object = accessor._prepare_schema_for_openai(object_schema)
    
    # Should add additionalProperties: false
    expected_schema = {
        "type": "object",
        "properties": {"test": {"type": "string"}},
        "required": ["test"],
        "additionalProperties": False
    }
    assert fixed_object == expected_schema


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


def test_ref_objects_cleaning():
    """Test that $ref objects with additional keywords are cleaned for OpenAI compliance."""
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()

    # Create a schema with problematic $ref objects
    schema_with_problematic_refs = {
        "type": "object",
        "properties": {
            "field_with_ref": {
                "$ref": "#/$defs/SomeType",
                "default": "some_default",
                "title": "Some Title"
            },
            "normal_field": {"type": "string"}
        },
        "required": ["field_with_ref", "normal_field"],
        "$defs": {
            "SomeType": {
                "type": "string",
                "enum": ["value1", "value2"]
            },
            "AnotherType": {
                "properties": {
                    "nested_ref": {
                        "$ref": "#/$defs/SomeType", 
                        "description": "This should be cleaned"
                    }
                }
            }
        }
    }

    fixed_schema = accessor._prepare_schema_for_openai(schema_with_problematic_refs)
    
    # Function to find $ref objects with extra keywords
    def find_problematic_refs(obj, path=""):
        issues = []
        if isinstance(obj, dict):
            if "$ref" in obj and len(obj) > 1:
                other_keys = [k for k in obj.keys() if k != "$ref"]
                issues.append(f"{path}: $ref with extra keys {other_keys}")
            
            for key, value in obj.items():
                if isinstance(value, dict):
                    issues.extend(find_problematic_refs(value, f"{path}.{key}"))
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            issues.extend(find_problematic_refs(item, f"{path}.{key}[{i}]"))
        return issues
    
    issues = find_problematic_refs(fixed_schema)
    assert len(issues) == 0, f"Found problematic $ref objects: {issues}"
    
    # Verify that $ref objects are now clean
    field_with_ref = fixed_schema["properties"]["field_with_ref"]
    assert field_with_ref == {"$ref": "#/$defs/SomeType"}, f"Expected clean $ref, got {field_with_ref}"
    
    nested_ref = fixed_schema["$defs"]["AnotherType"]["properties"]["nested_ref"]
    assert nested_ref == {"$ref": "#/$defs/SomeType"}, f"Expected clean nested $ref, got {nested_ref}"


def test_additional_properties_recursive_fix():
    """Test that all objects in schema get additionalProperties: false."""
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()

    # Create a schema with nested objects missing additionalProperties
    schema_missing_additional_props = {
        "type": "object",
        "properties": {
            "main_field": {"type": "string"}
        },
        "required": ["main_field"],
        "$defs": {
            "ObjectWithoutAdditionalProps": {
                "type": "object",
                "properties": {
                    "prop1": {"type": "string"},
                    "nested_object": {
                        "type": "object",
                        "properties": {
                            "nested_prop": {"type": "number"}
                        }
                    }
                },
                "required": ["prop1"]
            },
            "AnotherObject": {
                "properties": {
                    "field_a": {"type": "string"}
                }
                # No type specified, but has properties
            }
        }
    }

    fixed_schema = accessor._prepare_schema_for_openai(schema_missing_additional_props)
    
    # Function to recursively check all objects have additionalProperties: false
    def check_additional_properties(obj, path=""):
        issues = []
        if isinstance(obj, dict):
            # Check if this should have additionalProperties
            if obj.get("type") == "object" or "properties" in obj:
                if obj.get("additionalProperties") is not False:
                    issues.append(f"{path}: missing or incorrect additionalProperties")
            
            # Recurse into nested structures
            for key, value in obj.items():
                if key in ["$defs", "definitions"] and isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        issues.extend(check_additional_properties(sub_value, f"{path}.{key}.{sub_key}"))
                elif key == "properties" and isinstance(value, dict):
                    for prop_key, prop_value in value.items():
                        issues.extend(check_additional_properties(prop_value, f"{path}.{key}.{prop_key}"))
                elif key == "items" and isinstance(value, dict):
                    issues.extend(check_additional_properties(value, f"{path}.{key}"))
        
        return issues
    
    issues = check_additional_properties(fixed_schema, "root")
    assert len(issues) == 0, f"Found additionalProperties issues: {issues}"
    
    # Verify specific objects
    assert fixed_schema["additionalProperties"] is False, "Root should have additionalProperties: false"
    
    obj1 = fixed_schema["$defs"]["ObjectWithoutAdditionalProps"]
    assert obj1["additionalProperties"] is False, "ObjectWithoutAdditionalProps should have additionalProperties: false"
    
    nested_obj = obj1["properties"]["nested_object"]
    assert nested_obj["additionalProperties"] is False, "Nested object should have additionalProperties: false"
    
    obj2 = fixed_schema["$defs"]["AnotherObject"]  
    assert obj2["additionalProperties"] is False, "AnotherObject should have additionalProperties: false"


def test_recursive_required_array_fix():
    """Test that nested objects in $defs get proper OpenAI compliance without breaking schema design."""
    with patch('src.modelAccessors.openai_accessor.OpenAI'):
        accessor = OpenAIAccessor()

    # Create a schema with nested objects that need OpenAI compliance
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
                "required": ["prop1"]  # Should preserve original design, just add additionalProperties
            },
            "EmptyRequiredObject": {
                "type": "object", 
                "properties": {
                    "field_a": {"type": "string"},
                    "field_b": {"type": "array"}
                }
                # No required array - should add empty one, not force all props required
            }
        }
    }

    fixed_schema = accessor._prepare_schema_for_openai(schema_with_nested_issues)
    
    # Check that nested objects are now OpenAI compliant but preserve original design
    incomplete_obj = fixed_schema["$defs"]["IncompleteObject"]
    assert incomplete_obj.get("additionalProperties") is False, "Should have additionalProperties: false"
    assert incomplete_obj["required"] == ["prop1"], "Should preserve original required array"
    
    empty_req_obj = fixed_schema["$defs"]["EmptyRequiredObject"] 
    assert empty_req_obj.get("additionalProperties") is False, "Should have additionalProperties: false"
    assert "required" in empty_req_obj, "Should have required array"
    assert empty_req_obj["required"] == [], "Should have empty required array, not force all props"
    
    # Verify top level is still correct
    assert set(fixed_schema["required"]) == {"main_field"}
