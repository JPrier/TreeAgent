from os import environ
from typing import Any
from openai import OpenAI
from pydantic import TypeAdapter
from src.dataModel.model_response import ModelResponse

class OpenAIAccessor:
    def __init__(self):
        self.client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str) -> ModelResponse:
        """
        Sends a prompt to the specified OpenAI model and returns the response.

        :param model: The model to use for generating the response.
        :param messages: A list of messages to send to the model.
        :return: The response from the model.
        """
        response: dict[Any, Any] = openai.ChatCompletion.create(
            model=model,  # or any that support structured outputs
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={
                "json_schema": TypeAdapter(ModelResponse).json_schema(),
                "strict": True
            }
        )
        return ModelResponse.model_validate_json(response.choices[0].message.content)
