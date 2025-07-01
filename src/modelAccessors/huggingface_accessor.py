from os import environ
from typing import Any, Dict, List, Optional
from pydantic import TypeAdapter
import json
import requests
from .base_accessor import BaseModelAccessor, Tool
from ..dataModel.model_response import ModelResponse

class HuggingFaceAccessor(BaseModelAccessor):
    def __init__(self):
        self.api_key = environ.get("HF_API_KEY")
        self.api_url = "https://api-inference.huggingface.co/models/"
        # HF models generally don't support tools natively
        self.tool_supported_models = []
        
    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        """Basic text prompting for Hugging Face models"""
        # Format depends on model type - this is simplified
        prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = requests.post(
            f"{self.api_url}{model}",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"inputs": prompt},
            timeout=30
        )
        
        if response.status_code != 200:
            raise ValueError(f"Error from Hugging Face API: {response.text}")
            
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            content = result[0].get("generated_text", "")
        else:
            content = str(result)
        
        # Try to parse as JSON, fall back to text wrapping if needed
        try:
            json_content = json.loads(content)
        except json.JSONDecodeError:
            json_content = {"text": content}
            
        return TypeAdapter(ModelResponse).validate_python(json_content)
        
    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, 
                               tools: Optional[List[Tool]] = None) -> ModelResponse:
        """Execute task with tools - for HF we use prompt-based approach"""
        return self.prompt_model(model, system_prompt, user_prompt)
    
    def supports_tools(self, model: str) -> bool:
        return False
