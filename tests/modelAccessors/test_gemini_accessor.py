from unittest.mock import Mock, patch
from pydantic import TypeAdapter

from src.modelAccessors.gemini_accessor import GeminiAccessor
from src.dataModel.model_response import ImplementedResponse


class MockModel:
    def __init__(self, response_text):
        self.response_text = response_text

    def generate_content(self, prompt, generation_config=None, tools=None):
        mock_response = Mock()
        mock_response.text = self.response_text
        mock_response.parts = [Mock()]
        mock_response.parts[0].function_call = None
        return mock_response


@patch('src.modelAccessors.gemini_accessor.genai.configure')
@patch('src.modelAccessors.gemini_accessor.environ.get')
def test_gemini_accessor_init(mock_env_get, mock_configure):
    """Test GeminiAccessor initialization."""
    mock_env_get.return_value = "test_api_key"
    
    accessor = GeminiAccessor()
    
    mock_env_get.assert_called_once_with("GOOGLE_API_KEY")
    mock_configure.assert_called_once_with(api_key="test_api_key")
    assert accessor.tool_supported_models == ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]


@patch('src.modelAccessors.gemini_accessor.genai.configure')
@patch('src.modelAccessors.gemini_accessor.environ.get')
@patch('src.modelAccessors.gemini_accessor.genai.GenerativeModel')
def test_call_model_without_tools(mock_generative_model, mock_env_get, mock_configure):
    """Test calling model without tools."""
    mock_env_get.return_value = "test_api_key"
    
    # Mock response
    response_text = '{"content": "test response", "artifacts": []}'
    mock_model_instance = MockModel(response_text)
    mock_generative_model.return_value = mock_model_instance
    
    accessor = GeminiAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    
    result = accessor.call_model(
        "Test prompt",
        adapter=adapter,
        schema={"type": "object"},
        model="gemini-1.5-pro"
    )
    
    assert isinstance(result, ImplementedResponse)
    assert result.content == "test response"
    assert result.artifacts == []


@patch('src.modelAccessors.gemini_accessor.genai.configure')
@patch('src.modelAccessors.gemini_accessor.environ.get')
@patch('src.modelAccessors.gemini_accessor.genai.GenerativeModel')
def test_call_model_with_tools(mock_generative_model, mock_env_get, mock_configure):
    """Test calling model with tools."""
    mock_env_get.return_value = "test_api_key"
    
    # Mock response
    response_text = '{"content": "test response with tools", "artifacts": ["tool_result"]}'
    mock_model_instance = MockModel(response_text)
    mock_generative_model.return_value = mock_model_instance
    
    accessor = GeminiAccessor()
    adapter = TypeAdapter(ImplementedResponse)
    
    mock_tool = Mock()
    mock_tool.to_gemini_tool.return_value = {"function": {"name": "test_tool"}}
    
    result = accessor.call_model(
        "Test prompt",
        adapter=adapter,
        schema={"type": "object"},
        model="gemini-1.5-pro",
        tools=[mock_tool]
    )
    
    assert isinstance(result, ImplementedResponse)
    assert result.content == "test response with tools"
    assert result.artifacts == ["tool_result"]


@patch('src.modelAccessors.gemini_accessor.genai.configure')
@patch('src.modelAccessors.gemini_accessor.environ.get')
def test_call_model_uses_default_model(mock_env_get, mock_configure):
    """Test that call_model uses default model when none specified."""
    mock_env_get.return_value = "test_api_key"
    
    with patch('src.modelAccessors.gemini_accessor.genai.GenerativeModel') as mock_gen_model:
        mock_model_instance = MockModel('{"content": "test", "artifacts": []}')
        mock_gen_model.return_value = mock_model_instance
        
        accessor = GeminiAccessor()
        adapter = TypeAdapter(ImplementedResponse)
        
        accessor.call_model(
            "Test prompt",
            adapter=adapter,
            schema={"type": "object"}
        )
        
        # Should use default model (first in tool_supported_models)
        mock_gen_model.assert_called_with("gemini-1.5-pro")