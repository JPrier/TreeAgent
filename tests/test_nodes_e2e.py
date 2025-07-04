from pydantic import TypeAdapter
from agentNodes.clarifier import Clarifier
from agentNodes.researcher import Researcher
from modelAccessors.base_accessor import BaseModelAccessor

from agentNodes.hld_designer import HLDDesigner
from agentNodes.implementer import Implementer
from agentNodes.reviewer import Reviewer
from agentNodes.tester import Tester
from agentNodes.deployer import Deployer
from dataModel.task import Task, TaskType
from dataModel.model_response import ModelResponse, DecomposedResponse, ImplementedResponse


class _StubAccessor(BaseModelAccessor):
    def __init__(self, callback):
        self._callback = callback

    def call_model(self, prompt: str, schema):
        return self._callback(prompt, schema)

    def prompt_model(self, model: str, system_prompt: str, user_prompt: str):
        raise NotImplementedError()

    def execute_task_with_tools(self, model: str, system_prompt: str, user_prompt: str, tools=None):
        raise NotImplementedError()

def _hld_call_model(prompt: str, schema):
    if "Complexity: 2" in prompt:
        subtasks = [
            Task(id="d1-1", description="sub", type=TaskType.HLD),
            Task(id="d1-2", description="sub", type=TaskType.HLD),
        ]
        return DecomposedResponse(subtasks=subtasks)
    return ImplementedResponse(content="outline")

NODE_REGISTRY = {
    "clarify": Clarifier(),
    "research": Researcher(),
    "hld": HLDDesigner(_StubAccessor(_hld_call_model)),
    "implement": Implementer(),
    "review": Reviewer(),
    "test": Tester(),
    "deploy": Deployer(),
}

def route(task: Task, state: dict) -> dict:
    if "?" in task.description:
        return NODE_REGISTRY["clarify"](state, {})
    if task.type == TaskType.RESEARCH:
        return NODE_REGISTRY["research"](state, {})
    if task.type == TaskType.IMPLEMENT:
        return NODE_REGISTRY["implement"](state, {})
    if task.type == TaskType.REVIEW:
        return NODE_REGISTRY["review"](state, {})
    if task.type == TaskType.TEST:
        return NODE_REGISTRY["test"](state, {})
    if task.type == TaskType.DEPLOY:
        return NODE_REGISTRY["deploy"](state, {})
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

    # implementation phase
    implement_task = Task(id="i1", description="Implement", type=TaskType.IMPLEMENT)
    state["task_queue"] = [implement_task]
    implement_res = route(implement_task, state)
    implement_parsed = adapter.validate_python(implement_res)
    assert implement_parsed.response_type == "implemented"
    state["last_response"] = implement_parsed

    # review phase
    review_task = Task(id="v1", description="Review", type=TaskType.REVIEW)
    state["task_queue"] = [review_task]
    review_res = route(review_task, state)
    review_parsed = adapter.validate_python(review_res)
    assert review_parsed.response_type == "implemented"
    state["last_response"] = review_parsed

    # test phase
    test_task = Task(id="t1", description="Test", type=TaskType.TEST)
    state["task_queue"] = [test_task]
    test_res = route(test_task, state)
    test_parsed = adapter.validate_python(test_res)
    assert test_parsed.response_type == "implemented"

    # deploy phase
    deploy_task = Task(id="dpl1", description="Deploy", type=TaskType.DEPLOY)
    state["task_queue"] = [deploy_task]
    deploy_res = route(deploy_task, state)
    deploy_parsed = adapter.validate_python(deploy_res)
    assert deploy_parsed.response_type == "implemented"
    assert deploy_parsed.content == "deployed"
    assert deploy_parsed.artifacts == ["foo.py"]
