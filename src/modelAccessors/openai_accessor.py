import json
from os import environ
from typing import Any, Optional

from openai import OpenAI
from pydantic import TypeAdapter

from .base_accessor import BaseModelAccessor, Tool
from src.dataModel.model_response import ModelResponse

class OpenAIAccessor(BaseModelAccessor):
    def __init__(self):
        self.client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))
        # Models that support structured outputs (json_schema response format)
        # Based on https://platform.openai.com/docs/guides/structured-outputs
        self.supported_models = [
            "gpt-4o", 
            "gpt-4o-mini", 
            "gpt-4o-2024-05-13", 
            "gpt-4o-2024-08-06",
            "gpt-4o-2024-11-20", 
            "gpt-4o-mini-2024-07-18",
            "gpt-5-mini",
            "gpt-5-nano"
        ]
        # Models that support function calling/tools (subset of supported models)
        self.tool_supported_models = ["gpt-4o", "gpt-4o-mini", "gpt-5-mini", "gpt-5-nano"]

    def call_model(
        self,
        prompt: str,
        *,
        adapter: TypeAdapter[ModelResponse],
        schema: dict,
        model: str = "gpt-5-nano",
        system_prompt: str = "",
        tools: Optional[list[Tool]] = None,
    ) -> ModelResponse:
        # Validate that the model is supported
        if model not in self.supported_models:
            supported_models_str = ", ".join(self.supported_models)
            raise ValueError(
                f"Unsupported model '{model}'. OpenAI accessor only supports models with structured outputs: {supported_models_str}"
            )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        
        # Ensure the schema is compatible with OpenAI's requirements
        openai_schema = self._prepare_schema_for_openai(schema)
        
        kwargs = {
            "model": model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": openai_schema, "strict": True},
            },
        }
        
        if tools and self.supports_tools(model):
            kwargs["tools"] = self._convert_to_openai_tools(tools)
            
        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        # Use parsed response when available
        parsed = getattr(message, "parsed", None)
        if parsed is not None:
            return adapter.validate_python(self._extract_response_from_openai_format(parsed, schema))
            
        # Fallback to JSON parsing if parsed is not available
        raw = message.content
        if not raw:
            raise ValueError("No content in response")
        
        # Parse and extract response
        parsed_json = json.loads(raw)
        extracted_response = self._extract_response_from_openai_format(parsed_json, schema)
        return adapter.validate_json(json.dumps(extracted_response))
    
    def supports_tools(self, model: str) -> bool:
        """Check if model supports native tools/function calling"""
        return model in self.tool_supported_models
    
    def _prepare_schema_for_openai(self, schema: dict) -> dict:
        """
        Prepare schema for OpenAI's structured output requirements.
        
        OpenAI requires the root schema to have 'type': 'object' and does not support
        oneOf/anyOf anywhere in the schema. Pydantic's discriminated unions generate 
        schemas with oneOf at the root level, and nullable fields use anyOf, so we 
        need to flatten and clean them.
        """
        # Check if the schema already has a root type of "object" and no oneOf/anyOf
        if schema.get("type") == "object" and not self._contains_oneof_anyof(schema):
            # Even for simple object schemas, ensure OpenAI compliance
            result_schema = schema.copy()
        else:
            # If it's a oneOf/anyOf schema (discriminated union), flatten it
            if "oneOf" in schema or "anyOf" in schema:
                flattened = self._flatten_discriminated_union(schema)
            else:
                flattened = schema
                
            # Clean any remaining oneOf/anyOf structures (like nullable fields)
            result_schema = self._clean_oneof_anyof_recursive(flattened)
        
        # Ensure OpenAI's requirement: all properties must be in required array
        # This prevents the "Missing 'content'" error by guaranteeing compliance
        if result_schema.get("type") == "object" and "properties" in result_schema:
            properties = result_schema["properties"]
            required = result_schema.get("required", [])
            
            # Add any missing properties to required array
            all_prop_names = list(properties.keys())
            missing_required = [prop for prop in all_prop_names if prop not in required]
            
            if missing_required:
                result_schema["required"] = required + missing_required
        
        return result_schema

    def _contains_oneof_anyof(self, obj) -> bool:
        """Recursively check if an object contains oneOf or anyOf."""
        if isinstance(obj, dict):
            if "oneOf" in obj or "anyOf" in obj:
                return True
            for value in obj.values():
                if isinstance(value, (dict, list)) and self._contains_oneof_anyof(value):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)) and self._contains_oneof_anyof(item):
                    return True
        return False

    def _clean_oneof_anyof_recursive(self, obj):
        """Recursively clean oneOf/anyOf structures from a schema."""
        if isinstance(obj, dict):
            # Handle nullable fields (anyOf with null)
            if "anyOf" in obj:
                any_of = obj["anyOf"]
                # Check if this is a nullable field pattern: [{"type": "string"}, {"type": "null"}]
                if len(any_of) == 2:
                    types = []
                    for item in any_of:
                        if isinstance(item, dict) and "type" in item:
                            types.append(item["type"])
                    if "null" in types:
                        # Convert to OpenAI-compatible nullable field
                        non_null_type = [t for t in types if t != "null"][0]
                        other_schema = next(item for item in any_of if item.get("type") == non_null_type)
                        # Create a new dict without anyOf
                        cleaned = {k: v for k, v in obj.items() if k != "anyOf"}
                        cleaned.update(other_schema)
                        # Make it nullable by not including it in required fields
                        return self._clean_oneof_anyof_recursive(cleaned)
            
            # Handle oneOf (shouldn't happen after flattening, but just in case)
            if "oneOf" in obj:
                # This is a complex case - for now, take the first option
                # In practice, this shouldn't happen after proper flattening
                one_of = obj["oneOf"]
                if one_of:
                    cleaned = {k: v for k, v in obj.items() if k != "oneOf"}
                    cleaned.update(one_of[0])
                    return self._clean_oneof_anyof_recursive(cleaned)
            
            # Recursively clean all nested objects
            return {k: self._clean_oneof_anyof_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_oneof_anyof_recursive(item) for item in obj]
        else:
            return obj

    def _flatten_discriminated_union(self, schema: dict) -> dict:
        """
        Flatten a discriminated union schema to be compatible with OpenAI's structured outputs.
        
        This converts a oneOf schema into a single object schema with all possible properties
        from all union members, making conditional fields optional.
        """
        # Get the oneOf alternatives
        one_of_schemas = schema.get("oneOf", schema.get("anyOf", []))
        if not one_of_schemas:
            return schema
            
        # Get definitions from the original schema
        # Use a more robust way to find definitions in case of encoding issues
        definitions = {}
        for key, value in schema.items():
            if key.endswith("defs") and isinstance(value, dict):
                definitions = value
                break
        
        # Collect all properties and required fields from all alternatives
        all_properties = {}
        required_fields = set()
        
        # The discriminator field (usually 'type') is required
        discriminator_info = schema.get("discriminator", {})
        discriminator_field = discriminator_info.get("propertyName")
        
        if discriminator_field:
            required_fields.add(discriminator_field)
            # Create an enum for all possible discriminator values
            possible_values = []
            for alt_schema in one_of_schemas:
                # Resolve $ref if present
                resolved_schema = self._resolve_schema_ref(alt_schema, definitions)
                properties = resolved_schema.get("properties", {})
                if discriminator_field in properties:
                    disc_prop = properties[discriminator_field]
                    if "const" in disc_prop:
                        possible_values.append(disc_prop["const"])
                    elif "enum" in disc_prop:
                        possible_values.extend(disc_prop["enum"])
            
            all_properties[discriminator_field] = {
                "type": "string",
                "enum": possible_values
            }
        
        # Merge properties from all alternatives
        for alt_schema in one_of_schemas:
            resolved_schema = self._resolve_schema_ref(alt_schema, definitions)
            properties = resolved_schema.get("properties", {})
            
            for prop_name, prop_schema in properties.items():
                if prop_name not in all_properties:
                    all_properties[prop_name] = prop_schema
                # Note: We don't make alternative-specific fields required in the flattened schema
                # because they're only required conditionally based on the discriminator value
        
        flattened = {
            "type": "object",
            "properties": all_properties,
            "required": list(all_properties.keys()),  # OpenAI requires all properties to be in required
            "additionalProperties": False
        }
        
        # Include definitions if they exist and are referenced
        if definitions:
            flattened["$defs"] = definitions
        
        return flattened

    def _resolve_schema_ref(self, schema: dict, definitions: dict) -> dict:
        """Resolve a $ref reference to get the actual schema definition."""
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/$defs/"):
                def_name = ref_path.replace("#/$defs/", "")
                return definitions.get(def_name, schema)
        return schema
    
    def _extract_response_from_openai_format(self, response_data: Any, original_schema: dict) -> Any:
        """
        Extract the actual response from OpenAI's format.
        
        Since we now flatten discriminated unions instead of wrapping them,
        we can return the response data as-is.
        """
        return response_data
        
    def _convert_to_openai_tools(self, tools: list[Tool]) -> list[dict[str, Any]]:
        """Convert our Tool objects to OpenAI's tool format"""
        openai_tools: list[dict[str, Any]] = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": []  # Could be enhanced with required params
                    }
                }
            })
        return openai_tools
