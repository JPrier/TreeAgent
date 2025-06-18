from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.task import Task
from dataBuilders.prompt_builder import PromptBuilder

class AgentNode:
    def __init__(self, agent_id: str, accessor: BaseModelAccessor):
        self.agent_id = agent_id
        self.accessor = accessor
        self.prompt_builder = PromptBuilder()

    def __repr__(self):
        return f"AgentNode(id={self.agent_id})"
    
    def execute_task(self, task: Task):
        """
        Execute a task using the injected model accessor.
        The accessor handles whether the model supports direct MCP execution or needs simulation.
        """
        system_prompt = self.prompt_builder.build_system_prompt(task)
        user_prompt = self.prompt_builder.build(task)
        
        # Always use execute_task_with_tools - the accessor handles MCP abstraction
        return self.accessor.execute_task_with_tools(
            model=task.model.name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tools=task.tools
        )
    
    # def handle_response(self, task: Task, response):
    #     """
    #     Handles the model response based on the task type and updates the task status accordingly.
    #     """
    #     match response.response_type:
    #         case ModelResponseType.DECOMPOSED:
    #             task.status = TaskStatus.PENDING_VALIDATION
    #             # Process subtasks
    #             for subtask in response.subtasks:
    #                 subtask.task_id = f"{task.task_id}-{subtask.task_type}"
    #                 # Here you would typically add the subtask to a queue or process it immediately
    #         case ModelResponseType.IMPLEMENTED:
    #             task.status = TaskStatus.COMPLETED
    #             # Handle implementation summary
    #         case ModelResponseType.FAILED:
    #             task.status = TaskStatus.FAILED if not response.retryable else TaskStatus.PENDING
    #             # Log error message
    #     return task