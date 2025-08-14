from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.logging_utils import init_logger

from pydantic import TypeAdapter

from src.dataModel.task import Task, TaskType, TaskStatus
from src.dataModel.model import AccessorType, Model
from src.dataModel.model_response import (
    ModelResponse,
    ModelResponseType,
    DecomposedResponse,
    ImplementedResponse,
    FollowUpResponse,
    FailedResponse,
)
from src.dataModel.project import Project
from src.dataManagement.project_manager import (
    save_project_state,
    load_project_state,
    latest_snapshot_path,
)
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.modelAccessors.openai_accessor import OpenAIAccessor
from src.modelAccessors.anthropic_accessor import AnthropicAccessor
from src.modelAccessors.mock_accessor import MockAccessor
from src.agentNodes.clarifier import Clarifier
from src.agentNodes.hld_designer import HLDDesigner
from src.agentNodes.lld_designer import LLDDesigner
from src.agentNodes.researcher import Researcher
from src.agentNodes.implementer import Implementer
from src.agentNodes.reviewer import Reviewer
from src.agentNodes.tester import Tester
from src.agentNodes.deployer import Deployer
from src.agentNodes.jury import Jury


NODE_FACTORY: dict[TaskType, Callable[[BaseModelAccessor], Any]] = {
    TaskType.REQUIREMENTS: lambda acc: Clarifier(acc),
    TaskType.RESEARCH: lambda acc: Researcher(acc),
    TaskType.HLD: lambda acc: HLDDesigner(acc),
    TaskType.LLD: lambda acc: LLDDesigner(acc),
    TaskType.IMPLEMENT: lambda acc: Implementer(acc),
    TaskType.REVIEW: lambda acc: Reviewer(),
    TaskType.TEST: lambda acc: Tester(acc),
    TaskType.JURY: lambda acc: Jury(acc),
    TaskType.DEPLOY: lambda acc: Deployer(),
}


class AgentOrchestrator:
    def __init__(
        self,
        config_path: str | None = None,
        *,
        verbose: bool = False,
        logger: logging.Logger | None = None,
        default_accessor_type: AccessorType | None = None,
    ) -> None:
        """Load spawn rules and prepare orchestrator."""
        self.verbose = verbose
        self.logger = logger or init_logger(self.__class__.__name__, verbose)
        self.default_accessor_type = default_accessor_type

        cfg_path: Path | None
        if config_path:
            cfg_path = Path(config_path)
        else:
            cfg_path = self._search_rules_file()
        if cfg_path and cfg_path.exists():
            with open(cfg_path, "r") as fh:
                self.spawn_rules: dict[str, dict[str, Any]] = json.load(fh)
        else:
            self.spawn_rules = {}

    @staticmethod
    def _search_rules_file() -> Path | None:
        """Search parent directories for ``spawn_rules.json``."""
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "config" / "spawn_rules.json"
            if candidate.exists():
                return candidate
            candidate = parent / "spawn_rules.json"
            if candidate.exists():
                return candidate
        return None

    def _enqueue_subtasks(
        self, parent: Task, subtasks: list[Task]
    ) -> list[Task]:
        """Filter subtasks based on spawn rules and return the allowed ones."""
        rules = self.spawn_rules.get(parent.type.name, {})
        allowed = rules.get("can_spawn", {})
        allow_self = rules.get("self_spawn", True)
        spawned_count: dict[str, int] = {}
        out: list[Task] = []
        for sub in subtasks:
            if not allow_self and sub.type == parent.type:
                continue
            limit = allowed.get(sub.type.name)
            if limit is None:
                continue
            spawned_count[sub.type.name] = spawned_count.get(sub.type.name, 0) + 1
            if spawned_count[sub.type.name] > limit:
                continue
            if (
                self.default_accessor_type
                and sub.model.accessor_type == AccessorType.MOCK
            ):
                sub.model = Model(accessor_type=self.default_accessor_type)
            sub.parent_id = parent.id
            sub.status = TaskStatus.PENDING
            out.append(sub)
        return out
    
    def _get_accessor(self, accessor_type: AccessorType) -> BaseModelAccessor:
        """Get the appropriate accessor for the given accessor type."""
        match accessor_type:
            case AccessorType.OPENAI:
                return OpenAIAccessor()
            case AccessorType.ANTHROPIC:
                return AnthropicAccessor()
            case AccessorType.MOCK:
                return MockAccessor()
            case _:
                raise ValueError(f"Unknown accessor type: {accessor_type}")

    def implement_project(self, project_prompt: str, checkpoint_dir: str = "checkpoints") -> Project:
        """
        Orchestrates the implementation of a project by decomposing it into tasks,
        assigning them to agents, and collecting their responses.
        
        :param project_prompt: The initial prompt describing the project.
        :return: Summary of the implemented project.
        """
        root_task: Task = self.create_root_task(project_prompt)
        project = Project(
            rootTask=root_task,
            failedTasks=[],
            completedTasks=[],
            inProgressTasks=[],
            queuedTasks=[root_task],
        )

        base = Path(checkpoint_dir)
        run_dir = base / datetime.now().strftime("%Y%m%d%H%M%S")

        return self._run_loop(project, run_dir)

    def resume_project(self, checkpoint_dir: str) -> Project:
        """Resume an existing project from ``checkpoint_dir``."""
        snapshot = latest_snapshot_path(checkpoint_dir)
        project = load_project_state(snapshot)
        return self._run_loop(project, Path(checkpoint_dir))

    def _run_loop(self, project: Project, checkpoint_dir: Path) -> Project:
        """Execute tasks sequentially until the queue is empty."""
        adapter = TypeAdapter(ModelResponse)

        while project.queuedTasks:
            current_task = project.queuedTasks.pop(0)
            current_task.status = TaskStatus.IN_PROGRESS
            project.inProgressTasks.append(current_task)

            self.logger.info(
                "Executing %s (%s) using %s",
                current_task.id,
                current_task.type.name,
                current_task.model.accessor_type.value,
            )
            self.logger.debug("Description: %s", current_task.description)

            accessor = self._get_accessor(current_task.model.accessor_type)
            factory = NODE_FACTORY.get(current_task.type)
            if not factory:
                current_task.status = TaskStatus.FAILED
                failure = FailedResponse(error_message=f"No node for {current_task.type}")
                project.inProgressTasks.remove(current_task)
                project.failedTasks.append(current_task)
                project.taskResults[current_task.id] = failure
                project.latestResponse = failure
                save_project_state(project, checkpoint_dir)
                continue

            node = factory(accessor)

            try:
                response_dict = node(current_task)
                self.logger.debug("Raw response dict: %s", response_dict)
                response = adapter.validate_python(response_dict)
            except Exception as exc:  # noqa: BLE001
                current_task.status = TaskStatus.FAILED
                failure = FailedResponse(error_message=str(exc))
                project.inProgressTasks.remove(current_task)
                project.failedTasks.append(current_task)
                project.taskResults[current_task.id] = failure
                project.latestResponse = failure
                save_project_state(project, checkpoint_dir)
                self.logger.error("Task %s failed: %s", current_task.id, str(exc))
                continue

            project.taskResults[current_task.id] = response
            project.latestResponse = response

            match response.response_type:
                case ModelResponseType.DECOMPOSED:
                    assert isinstance(response, DecomposedResponse)
                    new_tasks = self._enqueue_subtasks(current_task, response.subtasks)
                    project.queuedTasks.extend(new_tasks)
                    current_task.status = TaskStatus.COMPLETED
                    project.inProgressTasks.remove(current_task)
                    project.completedTasks.append(current_task)
                    self.logger.info(
                        "%s task completed: produced %d subtasks",
                        current_task.type.name,
                        len(response.subtasks),
                    )
                case ModelResponseType.IMPLEMENTED:
                    assert isinstance(response, ImplementedResponse)
                    if current_task.type is TaskType.REQUIREMENTS:
                        hld = Task(
                            id=f"{current_task.id}-hld",
                            description=current_task.description,
                            type=TaskType.HLD,
                            model=Model(accessor_type=self.default_accessor_type)
                            if self.default_accessor_type
                            else Model(),
                        )
                        new_tasks = self._enqueue_subtasks(current_task, [hld])
                        project.queuedTasks.extend(new_tasks)
                    current_task.status = TaskStatus.COMPLETED
                    project.inProgressTasks.remove(current_task)
                    project.completedTasks.append(current_task)
                    self.logger.info(
                        "%s task completed: artifacts %s",
                        current_task.type.name,
                        ", ".join(response.artifacts) if response.artifacts else "none",
                    )
                case ModelResponseType.FOLLOW_UP_REQUIRED:
                    assert isinstance(response, FollowUpResponse)
                    if current_task.type is TaskType.REQUIREMENTS:
                        question = response.follow_up_ask.description
                        answer = input(question + " ")
                        desc = f"{current_task.description}\n{answer}".strip()
                        hld = Task(
                            id=f"{current_task.id}-hld",
                            description=desc,
                            type=TaskType.HLD,
                            model=Model(accessor_type=self.default_accessor_type)
                            if self.default_accessor_type
                            else Model(),
                        )
                        new_tasks = self._enqueue_subtasks(current_task, [hld])
                        project.queuedTasks.extend(new_tasks)
                        current_task.status = TaskStatus.COMPLETED
                        project.inProgressTasks.remove(current_task)
                        project.completedTasks.append(current_task)
                    else:
                        current_task.status = TaskStatus.BLOCKED
                        project.inProgressTasks.remove(current_task)
                        project.failedTasks.append(current_task)
                    self.logger.info("%s task requires follow up", current_task.type.name)
                case ModelResponseType.FAILED:
                    assert isinstance(response, FailedResponse)
                    current_task.status = TaskStatus.FAILED
                    project.inProgressTasks.remove(current_task)
                    project.failedTasks.append(current_task)
                    self.logger.error("Task %s failed: %s", current_task.id, response.error_message)

            save_project_state(project, checkpoint_dir)

        save_project_state(project, checkpoint_dir)

        return project
    
    def create_root_task(self, project_prompt: str) -> Task:
        """
        Creates the root task for the project based on the initial project prompt.
        
        :param project_prompt: The initial prompt describing the project.
        :return: A Task object representing the root task.
        """
        return Task(
            id="root-task",
            type=TaskType.REQUIREMENTS,
            description=project_prompt,
            model=Model(accessor_type=self.default_accessor_type)
            if self.default_accessor_type
            else Model(),
        )

if __name__ == "__main__":
    orchestrator = AgentOrchestrator()
    example_prompt = "Build a simple web application with user authentication and a dashboard."
    result_project = orchestrator.implement_project(example_prompt)
    
    print("Project Summary:")
    print(f"Completed Tasks: {len(result_project.completedTasks)}")
    print(f"In Progress Tasks: {len(result_project.inProgressTasks)}")
    print(f"Failed Tasks: {len(result_project.failedTasks)}")
    print(f"Queued Tasks: {len(result_project.queuedTasks)}")
