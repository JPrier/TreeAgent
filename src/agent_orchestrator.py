from pydantic import BaseModel
from .dataModel.model_response import (
    ModelResponse,
    ModelResponseType,
)
from .agent_node import AgentNode
from .dataModel.task import Task, TaskType, TaskStatus
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
        # Create the root task
        root_task: Task = self.create_root_task(project_prompt)
        
        # Get the appropriate accessor for the root task's model
        accessor = self._get_accessor(root_task.model.accessor_type)
        
        # Create an agent node for the orchestrator with the appropriate accessor
        orchestrator_agent = AgentNode(agent_id="orchestrator", accessor=accessor)

        # Have the orchestrator agent execute the root task (Decompose)
        response: ModelResponse | None = orchestrator_agent.execute_task(root_task)
        
        if response is None:
            # Handle case where execution failed
            project = Project(
                failedTasks=[root_task],
                completedTasks=[],
                inProgressTasks=[],
                queuedTasks=[]
            )
            return project

        project = Project(
            failedTasks=[],
            completedTasks=[],
            inProgressTasks=[],
            queuedTasks=[]
        )

        # Handle the response from the agent
        match response.response_type:
            case ModelResponseType.DECOMPOSED:
                root_task.status = TaskStatus.IN_PROGRESS
                project.queuedTasks.extend(response.subtasks)
            case ModelResponseType.IMPLEMENTED:
                root_task.status = TaskStatus.COMPLETED
                project.completedTasks.append(root_task)
                return project
            case ModelResponseType.FAILED:
                if response.retryable:
                    root_task.status = TaskStatus.PENDING
                    project.queuedTasks.append(root_task)
                else:
                    root_task.status = TaskStatus.FAILED
                    project.failedTasks.append(root_task)
            
        while project.queuedTasks:
            # Pop the next task from the queue
            current_task: Task = project.queuedTasks.pop(0)
            current_task.status = TaskStatus.IN_PROGRESS
            project.inProgressTasks.append(current_task)
            
            # Get the appropriate accessor for the current task's model
            task_accessor = self._get_accessor(current_task.model.accessor_type)
            
            # Create an agent node for the current task with the appropriate accessor
            agent = AgentNode(agent_id=current_task.id, accessor=task_accessor)
            
            # Execute the task using the agent
            task_response: ModelResponse | None = agent.execute_task(current_task)
            
            # Handle the response based on its type
            project.inProgressTasks.remove(current_task)
            
            if task_response is None:
                current_task.status = TaskStatus.FAILED
                project.failedTasks.append(current_task)
                continue
                
            match task_response.response_type:
                case ModelResponseType.DECOMPOSED:
                    current_task.status = TaskStatus.IN_PROGRESS
                    project.queuedTasks.extend(task_response.subtasks)
                case ModelResponseType.IMPLEMENTED:
                    current_task.status = TaskStatus.COMPLETED
                    project.completedTasks.append(current_task)
                case ModelResponseType.FAILED:
                    if task_response.retryable:
                        current_task.status = TaskStatus.PENDING
                        project.queuedTasks.append(current_task)
                    else:
                        current_task.status = TaskStatus.FAILED
                        project.failedTasks.append(current_task)
        return project
    
    def create_root_task(self, project_prompt: str) -> Task:
        """
        Creates the root task for the project based on the initial project prompt.
        
        :param project_prompt: The initial prompt describing the project.
        :return: A Task object representing the root task.
        """
        return Task(
            id="root-task",
            type=TaskType.DECOMPOSE,
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
