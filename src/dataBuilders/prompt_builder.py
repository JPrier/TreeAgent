import json
from typing import Any
from pydantic import TypeAdapter
from src.dataModel.model_response import ModelResponse
from src.dataModel.task import Task, TaskType

class PromptBuilder:
    def __init__(self):
        # Pre-compute JSON schema once
        self.schema = TypeAdapter(ModelResponse).json_schema()

        # Example templates for each response type
        self.example_decomposed: dict[str, Any] = {
            "response_type": "decomposed",
            "subtasks": [
                {
                    "task_id": "t1",
                    "task_type": "implement",
                    "agent_description": "You are a senior engineer...",
                    "prompt": "Write a function to add two numbers"
                }
            ]
        }
        self.example_implemented: dict[str, Any] = {
            "response_type": "implemented",
            "summary": "Function add(a, b) implemented with docstring and tests."
        }
        self.example_failed: dict[str, Any] = {
            "response_type": "failed",
            "error_message": "Task too vague to implement.",
            "retryable": False
        }

    def build(self, task: Task) -> str:
        match task.task_type:
            case TaskType.IMPLEMENT:
                return self._build_implement_prompt(task)
            case TaskType.DESIGN:
                return self._build_design_prompt(task)
            case TaskType.DECOMPOSE:
                return self._build_decompose_prompt(task)
            case TaskType.RESEARCH:
                return self._build_research_prompt(task)
            case TaskType.VALIDATE:
                return self._build_validate_prompt(task)
            case TaskType.DOCUMENT:
                return self._build_document_prompt(task)
            case _:
                raise ValueError(f"Unhandled TaskType: {task.task_type}")
            
    def build_system_prompt(self, task: Task) -> str:
        base = {
            TaskType.IMPLEMENT: "You are a senior software engineer. Write clean, efficient, and testable code.",
            TaskType.DESIGN: "You are a software architect. Design robust, scalable solutions with clear justifications.",
            TaskType.DECOMPOSE: (
                "You are a technical planner. Evaluate whether the input task is complex enough to require decomposition. "
                "If yes, break it into smaller subtasks with types; otherwise return implemented or failed."
            ),
            TaskType.RESEARCH: "You are a researcher. Gather accurate, recent info and cite sources.",
            TaskType.VALIDATE: "You are a code reviewer. Analyze output, flag issues, suggest improvements.",
            TaskType.DOCUMENT: "You are a documentation expert. Write clear, developer-friendly documentation.",
        }.get(task.task_type, "You are an expert assistant.")

        schema_str = json.dumps(self.schema, indent=2)
        return (
            f"{base}\n"
            "Respond strictly with a single JSON object matching the provided schema below (no extra text):\n"
            f"{schema_str}"
        )

    def _with_example(self, prompt_body: str, example: dict[str, Any]) -> str:
        return (
            f"{prompt_body}\n\n"
            "Here’s an example of a valid response:\n"
            f"{json.dumps(example, indent=2)}\n\n"
            "Now respond with the correct JSON."
        )

    def _build_implement_prompt(self, task: Task) -> str:
        body = f"Implement the following request:\n{task.prompt}"
        return self._with_example(body, self.example_implemented)

    def _build_design_prompt(self, task: Task) -> str:
        body = f"Design a solution for:\n{task.prompt}"
        return self._with_example(body, self.example_implemented)

    def _build_decompose_prompt(self, task: Task) -> str:
        body = (
            f"Consider task:\n{task.prompt}\n\n"
            "If complex, decompose it; if simple, implement or fail as appropriate."
        )
        return self._with_example(body, self.example_decomposed)

    def _build_research_prompt(self, task: Task) -> str:
        body = f"Conduct research on:\n{task.prompt}"
        return self._with_example(body, self.example_implemented)

    def _build_validate_prompt(self, task: Task) -> str:
        body = f"Validate the following:\n{task.prompt}"
        return self._with_example(body, self.example_implemented)

    def _build_document_prompt(self, task: Task) -> str:
        body = f"Write documentation for:\n{task.prompt}"
        return self._with_example(body, self.example_implemented)
