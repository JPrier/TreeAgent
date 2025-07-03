import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import litellm

litellm.with_structured_output = lambda *a, **k: (lambda x: x)

from agentNodes.clarifier import Clarifier
from agentNodes.researcher import Researcher
from agentNodes.hld_designer import HLDDesigner
from pydantic import TypeAdapter
from dataModel.task import Task, TaskType
from dataModel.model_response import ModelResponse, DecomposedResponse

NODE_REGISTRY = {
    "clarify": Clarifier(),
    "research": Researcher(),
    "hld": HLDDesigner(),
}

def route(task: Task, state: dict) -> dict:
    if "?" in task.description:
        return NODE_REGISTRY["clarify"](state, {})
    if task.type == TaskType.RESEARCH:
        return NODE_REGISTRY["research"](state, {})
    return NODE_REGISTRY["hld"](state, {})


def test_end_to_end_chain():
    root = Task(id="root", description="Build a web app?", type=TaskType.REQUIREMENTS)
    state = {"root_task": root, "task_queue": [root]}

    # Clarifier step
    clarifier_res = route(root, state)
    adapter = TypeAdapter(ModelResponse)
    clarifier_parsed = adapter.validate_python(clarifier_res)
    assert clarifier_parsed.response_type == "follow_up_required"

    # user provides details -> research task
    research_task = Task(id="r1", description="Gather stack", type=TaskType.RESEARCH)
    state["task_queue"] = [research_task]
    research_res = route(research_task, state)
    research_parsed = adapter.validate_python(research_res)
    assert research_parsed.response_type == "implemented"

    # design phase
    design_task = Task(id="d1", description="Design", type=TaskType.HLD, complexity=2)
    state["task_queue"] = [design_task]
    design_res = route(design_task, state)
    design_parsed = adapter.validate_python(design_res)
    assert isinstance(design_parsed, DecomposedResponse)
    assert len(design_parsed.subtasks) == 2
