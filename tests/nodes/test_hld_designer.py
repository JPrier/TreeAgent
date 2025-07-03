import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from agentNodes.hld_designer import HLDDesigner
from dataModel.task import Task, TaskType
from dataModel.model_response import DecomposedResponse, ImplementedResponse

import litellm

litellm.with_structured_output = lambda *a, **k: (lambda x: x)


def test_hld_designer_decomposes():
    node = HLDDesigner()
    task = Task(id="h1", description="HLD", type=TaskType.HLD, complexity=3)
    state = {"task_queue": [task]}
    res = node(state, {})
    parsed = HLDDesigner.SCHEMA.model_validate(res)
    assert isinstance(parsed, DecomposedResponse)
    assert len(parsed.subtasks) == 3
    assert all(st.type == TaskType.HLD for st in parsed.subtasks)


def test_hld_designer_implemented():
    node = HLDDesigner()
    task = Task(id="h1", description="HLD", type=TaskType.HLD, complexity=1)
    state = {"task_queue": [task]}
    res = node(state, {})
    parsed = HLDDesigner.SCHEMA.model_validate(res)
    assert isinstance(parsed, ImplementedResponse)
