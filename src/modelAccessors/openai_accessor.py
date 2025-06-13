from os import environ
from openai import OpenAI

class OpenAIAccessor:
    def __init__(self):
        self.client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))

    def prompt_model(self, model, messages):
        """
        Sends a prompt to the specified OpenAI model and returns the response.

        :param model: The model to use for generating the response.
        :param messages: A list of messages to send to the model.
        :return: The response from the model.
        """
        response = self.client.chat.completions.create(
        model=model,
        messages=messages
        )
        return response.choices[0].message.content
