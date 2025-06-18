from pydantic import BaseModel
from dataModel.model_response import ModelResponse, ModelResponseType
from src.agent_node import AgentNode
from src.dataModel.task import Task, TaskType, TaskStatus
from src.dataModel.model import AccessorType, Model
from src.modelAccessors.base_accessor import BaseModelAccessor
from src.modelAccessors.openai_accessor import OpenAIAccessor
from src.modelAccessors.anthropic_accessor import AnthropicAccessor

class Project(BaseModel):
    failedTasks:     list[Task]
    completedTasks:  list[Task]
    inProgressTasks: list[Task]
    queuedTasks:     list[Task]

class AgentOrchestrator:
    def __init__(self):
        pass
    
    def _get_accessor(self, accessor_type: AccessorType) -> BaseModelAccessor:
        """Get the appropriate accessor for the given accessor type."""
        match accessor_type:
            case AccessorType.OPENAI:
                return OpenAIAccessor()
            case AccessorType.ANTHROPIC:
                return AnthropicAccessor()
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
        response: ModelResponse = orchestrator_agent.execute_task(root_task)

        project: Project = Project(
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
            agent = AgentNode(agent_id=current_task.task_id, accessor=task_accessor)
            
            # Execute the task using the agent
            response: ModelResponse = agent.execute_task(current_task)
            
            # Handle the response based on its type
            project.inProgressTasks.remove(current_task)
            match response.response_type:
                case ModelResponseType.DECOMPOSED:
                    current_task.status = TaskStatus.IN_PROGRESS
                    project.queuedTasks.extend(response.subtasks)
                case ModelResponseType.IMPLEMENTED:
                    current_task.status = TaskStatus.COMPLETED
                    project.completedTasks.append(current_task)
                case ModelResponseType.FAILED:
                    if response.retryable:
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
            task_id="root-task",
            task_type=TaskType.DECOMPOSE,
            prompt=project_prompt,
            model=Model()  # Use default model
        )

