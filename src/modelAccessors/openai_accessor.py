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
        Prepare schema for OpenAI's structured output requirements with minimal changes.
        
        Instead of aggressively flattening all unions, this applies targeted fixes:
        1. Only flatten problematic union structures
        2. Keep oneOf/anyOf that can work with proper branch structure
        3. Clean nullable fields (anyOf with null)
        4. Ensure all objects have additionalProperties: false
        5. Clean $ref objects with extra keywords
        6. Handle empty objects explicitly
        
        This preserves the original schema design while ensuring OpenAI compliance.
        """
        import copy
        
        # Always start with a deep copy to avoid modifying the original
        result_schema = copy.deepcopy(schema)
        
        # Clean only problematic anyOf/oneOf structures
        # Keep discriminated unions if they're properly structured
        if self._has_problematic_unions(result_schema):
            result_schema = self._clean_problematic_unions(result_schema)
        else:
            # Even if we're not flattening, we need to ensure each branch is OpenAI compliant
            self._make_union_branches_compliant(result_schema)
        
        # Clean nullable fields (anyOf with null) - these are always problematic for OpenAI
        result_schema = self._clean_oneof_anyof_recursive(result_schema)
        
        # Apply targeted OpenAI compliance fixes without breaking conditional logic
        self._fix_required_fields_recursive(result_schema)
        
        return result_schema
    
    def _has_problematic_unions(self, schema: dict) -> bool:
        """
        Check if the schema has union structures that need flattening.
        
        Try to preserve oneOf/anyOf if possible. Only flatten if the branches
        can't be made OpenAI-compliant as-is.
        """
        if "oneOf" in schema:
            # Check if all branches can be made OpenAI compliant
            one_of = schema["oneOf"]
            for branch in one_of:
                if "$ref" in branch:
                    # $ref branches should be fine if the referenced schema is compliant
                    continue
                elif isinstance(branch, dict):
                    # Check if this branch can be made compliant
                    if branch.get("type") == "object" or "properties" in branch:
                        # This should be fixable - don't flatten
                        continue
                    else:
                        # Complex branch that might need flattening
                        return True
            
            # All branches look fine, don't flatten
            return False
            
        # Root-level anyOf might need flattening if it's not just nullable
        if "anyOf" in schema:
            any_of = schema["anyOf"]
            # Check if it's just a nullable pattern
            if len(any_of) == 2:
                types = []
                for item in any_of:
                    if isinstance(item, dict) and "type" in item:
                        types.append(item["type"])
                if "null" in types:
                    # This is just a nullable field, don't flatten at root
                    return False
            # Other anyOf patterns might need flattening
            return True
            
        return False
    
    def _make_union_branches_compliant(self, schema: dict):
        """
        Make each branch of a oneOf/anyOf union OpenAI compliant without flattening.
        
        This preserves union semantics while ensuring compliance.
        """
        if "oneOf" in schema:
            for branch in schema["oneOf"]:
                if isinstance(branch, dict) and "$ref" not in branch:
                    self._make_object_compliant(branch)
                    
        if "anyOf" in schema:
            for branch in schema["anyOf"]:
                if isinstance(branch, dict) and "$ref" not in branch:
                    self._make_object_compliant(branch)
        
        # Also recursively fix any nested $defs
        for defs_key in ["$defs", "definitions"]:
            if defs_key in schema and isinstance(schema[defs_key], dict):
                for def_schema in schema[defs_key].values():
                    self._fix_required_fields_recursive(def_schema)
    
    def _make_object_compliant(self, obj: dict):
        """Make a single object OpenAI compliant."""
        if obj.get("type") == "object" or "properties" in obj:
            obj["additionalProperties"] = False
            # Ensure required array exists but don't force all properties
            obj.setdefault("required", [])
    
    def _make_object_compliant(self, obj: dict):
        """Make a single object OpenAI compliant."""
        if obj.get("type") == "object" or "properties" in obj:
            obj["additionalProperties"] = False
            # Ensure required array exists but don't force all properties
            obj.setdefault("required", [])
    
    def _clean_problematic_unions(self, schema: dict) -> dict:
        """
        Clean only the problematic union structures, preserving good ones.
        """
        if "oneOf" in schema or "anyOf" in schema:
            return self._flatten_discriminated_union(schema)
        return schema
    
    def _fix_required_fields_recursive(self, schema):
        """
        Recursively ensure all objects in the schema are OpenAI-compliant.
        
        Instead of forcing all properties to be required, this applies targeted fixes:
        1. Add additionalProperties: false to all objects
        2. Extend (don't overwrite) existing required arrays only when needed
        3. Handle empty objects explicitly
        4. Clean problematic $ref objects
        
        This preserves the original schema structure while ensuring OpenAI compliance.
        """
        if not isinstance(schema, dict):
            return
            
        # If this is an object type, ensure additionalProperties is false
        if schema.get("type") == "object":
            schema["additionalProperties"] = False
            
        # Handle objects with properties
        if "properties" in schema and isinstance(schema["properties"], dict):
            properties = schema["properties"]
            
            # Ensure additionalProperties is false for objects with properties
            schema["additionalProperties"] = False
            
            # Handle empty objects explicitly (OpenAI requirement)
            if not properties:
                schema.setdefault("required", [])
            else:
                # Ensure required key exists (OpenAI requirement)
                schema.setdefault("required", [])
                
                # Only extend required array if it's missing properties that should be required
                # Don't force ALL properties to be required - preserve conditional logic
                existing_required = set(schema.get("required", []))
                
                # For discriminated unions, only the discriminator should be universally required
                # Other fields remain conditional based on the original schema design
                pass  # Let the original schema determine what should be required
                
        # Handle empty objects without properties (must be explicit)
        elif schema.get("type") == "object" and "properties" not in schema:
            schema["properties"] = {}
            schema["required"] = []
            schema["additionalProperties"] = False
        
        # Recursively fix objects in $defs and definitions
        for defs_key in ["$defs", "definitions"]:
            if defs_key in schema and isinstance(schema[defs_key], dict):
                for def_schema in schema[defs_key].values():
                    self._fix_required_fields_recursive(def_schema)
        
        # Recursively fix nested objects in properties
        if "properties" in schema and isinstance(schema["properties"], dict):
            for prop_schema in schema["properties"].values():
                self._fix_required_fields_recursive(prop_schema)
        
        # Fix $ref objects that have additional keywords (OpenAI doesn't allow this)
        self._clean_ref_objects_recursive(schema)
        
        # Recursively fix array item schemas
        if "items" in schema and isinstance(schema["items"], dict):
            self._fix_required_fields_recursive(schema["items"])

    def _clean_ref_objects_recursive(self, schema):
        """
        Recursively clean $ref objects that have additional keywords.
        
        OpenAI's strict validation doesn't allow $ref to be combined with other keywords
        like 'default', 'title', etc. This removes such keywords from $ref objects.
        """
        if not isinstance(schema, dict):
            return
            
        # If this object has $ref, remove all other keywords except $ref
        if "$ref" in schema:
            ref_value = schema["$ref"]
            schema.clear()
            schema["$ref"] = ref_value
            return  # Don't recurse into a pure $ref object
        
        # Recursively clean nested structures
        for key, value in list(schema.items()):
            if isinstance(value, dict):
                self._clean_ref_objects_recursive(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._clean_ref_objects_recursive(item)

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
                        
                        # If the field had a null default but is now non-nullable, remove the default
                        # This prevents invalid schemas where required string fields have null defaults
                        if cleaned.get("default") is None and cleaned.get("type") != "null":
                            # Remove null default for non-nullable required fields
                            cleaned.pop("default", None)
                        
                        return self._clean_oneof_anyof_recursive(cleaned)
            
            # Handle oneOf - only remove if it's problematic
            if "oneOf" in obj:
                # Don't automatically remove oneOf at root level
                # Only clean nested oneOf that might be problematic
                # Skip root-level oneOf that we want to preserve
                pass  
            
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
            "required": list(required_fields),  # Only require discriminator and truly required fields
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
