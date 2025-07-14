from pydantic import BaseModel
from .dataModel.task import Task, TaskType
from .dataModel.model import AccessorType, Model
from .modelAccessors.base_accessor import BaseModelAccessor
from .modelAccessors.openai_accessor import OpenAIAccessor
from .modelAccessors.anthropic_accessor import AnthropicAccessor
from .modelAccessors.mock_accessor import MockAccessor

class Project(BaseModel):
    failedTasks:     list[Task]
    completedTasks:  list[Task]
    inProgressTasks: list[Task]
    queuedTasks:     list[Task]

class AgentOrchestrator:
    def __init__(self):
        # Initialize the orchestrator - no setup needed currently
        pass
    
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

    def implement_project(self, project_prompt: str) -> Project:
        """
        Orchestrates the implementation of a project by decomposing it into tasks,
        assigning them to agents, and collecting their responses.
        
        :param project_prompt: The initial prompt describing the project.
        :return: Summary of the implemented project.
        """
        # Create the root task and mark it completed.
        root_task: Task = self.create_root_task(project_prompt)

        project = Project(
            failedTasks=[],
            completedTasks=[root_task],
            inProgressTasks=[],
            queuedTasks=[],
        )

        return project
    
    def create_root_task(self, project_prompt: str) -> Task:
        """
        Creates the root task for the project based on the initial project prompt.
        
        :param project_prompt: The initial prompt describing the project.
        :return: A Task object representing the root task.
        """
        return Task(
            id="root-task",
            type=TaskType.HLD,
            description=project_prompt,
            model=Model(),  # Use default model
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
