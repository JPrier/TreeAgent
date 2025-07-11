from __future__ import annotations

from typing import Optional, TypedDict, Dict, Callable, Any

from langgraph.graph import StateGraph, END
from pydantic import TypeAdapter

from .dataModel.task import Task, TaskType
from .dataModel.model_response import ModelResponse
from .agentNodes.clarifier import Clarifier
from .agentNodes.researcher import Researcher
from .agentNodes.hld_designer import HLDDesigner
from .agentNodes.implementer import Implementer
from .agentNodes.reviewer import Reviewer
from .agentNodes.tester import Tester
from .agentNodes.deployer import Deployer
from .modelAccessors.mock_accessor import MockAccessor


class OrchestratorState(TypedDict):
    root_task: Task
    task_queue: list[Task]
    last_response: Optional[ModelResponse]


class AgentOrchestrator:
    """Simple orchestrator built using LangGraph."""

    def __init__(self) -> None:
        accessor = MockAccessor()
        self._nodes: Dict[TaskType, Callable[[dict, Any], dict]] = {
            TaskType.REQUIREMENTS: Clarifier(accessor),
            TaskType.RESEARCH: Researcher(accessor),
            TaskType.HLD: HLDDesigner(accessor),
            TaskType.IMPLEMENT: Implementer(),
            TaskType.REVIEW: Reviewer(),
            TaskType.TEST: Tester(),
            TaskType.DEPLOY: Deployer(),
        }
        self._adapter = TypeAdapter(ModelResponse)

    def _process_task(self, state: OrchestratorState) -> dict:
        if not state["task_queue"]:
            return {}
        task = state["task_queue"].pop(0)
        node = self._nodes.get(task.type)
        if node is None:
            raise ValueError(f"No node for task type {task.type}")
        result = node(state)
        state["last_response"] = self._adapter.validate_python(result)
        return {"task_queue": state["task_queue"], "last_response": state["last_response"]}

    def _queue_check(self, state: dict) -> str:
        return "continue" if state["task_queue"] else "end"

    def implement_project(self, project_prompt: str) -> OrchestratorState:
        tasks = [
            Task(id="root", description=project_prompt, type=TaskType.REQUIREMENTS),
            Task(id="research", description="Gather information", type=TaskType.RESEARCH),
            Task(id="design", description="Create high level design", type=TaskType.HLD, complexity=1),
            Task(id="implement", description="Implement features", type=TaskType.IMPLEMENT),
            Task(id="review", description="Review code", type=TaskType.REVIEW),
            Task(id="test", description="Test code", type=TaskType.TEST),
            Task(id="deploy", description="Deploy application", type=TaskType.DEPLOY),
        ]
        state: OrchestratorState = {
            "root_task": tasks[0],
            "task_queue": tasks,
            "last_response": None,
        }

        graph_builder = StateGraph(OrchestratorState)
        graph_builder.add_node("step", self._process_task)
        graph_builder.add_node("check", lambda s: s)
        graph_builder.add_edge("step", "check")
        graph_builder.add_conditional_edges("check", self._queue_check, {"continue": "step", "end": END})
        graph_builder.set_entry_point("step")
        graph = graph_builder.compile()
        final_state = graph.invoke(state)
        return final_state


if __name__ == "__main__":  # pragma: no cover
    orchestrator = AgentOrchestrator()
    result = orchestrator.implement_project("Build a web app")
    print(result)
