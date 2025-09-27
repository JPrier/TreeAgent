import pytest
from unittest.mock import Mock, patch
from pydantic import TypeAdapter

from src.modelAccessors.anthropic_accessor import AnthropicAccessor
from src.dataModel.model_response import ImplementedResponse


@patch('src.modelAccessors.anthropic_accessor.Anthropic')
@patch('src.modelAccessors.anthropic_accessor.environ.get')
def test_anthropic_accessor_init(mock_env_get, mock_anthropic):
    """Test AnthropicAccessor initialization."""
    mock_env_get.return_value = "test_api_key"
    mock_client = Mock()
    mock_anthropic.return_value = mock_client
    
    accessor = AnthropicAccessor()
    
    mock_env_get.assert_called_once_with("ANTHROPIC_API_KEY")
    mock_anthropic.assert_called_once_with(api_key="test_api_key")
    assert accessor.client == mock_client
    assert accessor.tool_supported_models == [
        "claude-3-opus-20240229", 
        "claude-3-sonnet-20240229", 
        "claude-3-5-sonnet-20240620"
    ]


@patch('src.modelAccessors.anthropic_accessor.Anthropic')
@patch('src.modelAccessors.anthropic_accessor.environ.get')
def test_call_model_without_tools(mock_env_get, mock_anthropic):
    """Test calling model without tools."""
    mock_env_get.return_value = "test_api_key"
    
    # Mock client and response
    mock_client = Mock()
    mock_anthropic.return_value = mock_client
    
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = '{"content": "test response", "artifacts": []}'
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    
    accessor = AnthropicAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    
    result = accessor.call_model(
        "Test prompt",
        adapter=adapter,
        schema={"type": "object"},
        model="claude-3-sonnet-20240229"
    )
    
    assert isinstance(result, ImplementedResponse)
    assert result.content == "test response"
    assert result.artifacts == []


@patch('src.modelAccessors.anthropic_accessor.Anthropic')
@patch('src.modelAccessors.anthropic_accessor.environ.get')
def test_call_model_with_tools(mock_env_get, mock_anthropic):
    """Test calling model with tools."""
    mock_env_get.return_value = "test_api_key"
    
    # Mock client and response
    mock_client = Mock()
    mock_anthropic.return_value = mock_client
    
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = '{"content": "test response with tools", "artifacts": ["tool_result"]}'
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    
    accessor = AnthropicAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    
    mock_tool = Mock()
    mock_tool.to_anthropic_tool.return_value = {"name": "test_tool", "input_schema": {}}
    
    result = accessor.call_model(
        "Test prompt",
        adapter=adapter,
        schema={"type": "object"},
        model="claude-3-sonnet-20240229",
        tools=[mock_tool]
    )
    
    assert isinstance(result, ImplementedResponse)
    assert result.content == "test response with tools"
    assert result.artifacts == ["tool_result"]


@patch('src.modelAccessors.anthropic_accessor.Anthropic')
@patch('src.modelAccessors.anthropic_accessor.environ.get')
def test_call_model_uses_default_model(mock_env_get, mock_anthropic):
    """Test that call_model uses default model when none specified."""
    mock_env_get.return_value = "test_api_key"
    
    # Mock client and response
    mock_client = Mock()
    mock_anthropic.return_value = mock_client
    
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = '{"content": "test", "artifacts": []}'
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    
    accessor = AnthropicAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    
    accessor.call_model(
        "Test prompt",
        adapter=adapter,
        schema={"type": "object"}
    )
    
    # Should call messages.create with default model
    mock_client.messages.create.assert_called_once()
    call_args = mock_client.messages.create.call_args
    assert call_args[1]['model'] == "claude-3-opus-20240229"  # First in tool_supported_models


@patch('src.modelAccessors.anthropic_accessor.Anthropic')
@patch('src.modelAccessors.anthropic_accessor.environ.get')
def test_call_model_handles_json_parsing_error(mock_env_get, mock_anthropic):
    """Test that call_model handles JSON parsing errors gracefully."""
    mock_env_get.return_value = "test_api_key"
    
    # Mock client and response with invalid JSON
    mock_client = Mock()
    mock_anthropic.return_value = mock_client
    
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = 'invalid json response'
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    
    accessor = AnthropicAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    
    # Should handle the JSON parsing error appropriately
    with pytest.raises(Exception):  # The exact exception depends on implementation
        accessor.call_model(
            "Test prompt",
            adapter=adapter,
            schema={"type": "object"}
        )