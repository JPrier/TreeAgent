from src.modelAccessors.base_accessor import BaseModelAccessor
from src.dataModel.task import Task, TaskType
from dataBuilders.prompt_builder import PromptBuilder
from src.dataModel.model_response import ModelResponse

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

        # TODO:
        #   * Set which TaskTypes should NOT go to LLM - ex: code validation
        #     * Add an accessor to run for each
        #   * Decide which tasks should have tools and which should just use chat - ex: Decomposition could use no tools but would need context

        if Task.task_type == TaskType.VALIDATE_CODE:
            return self.run_code_validation(task)
        
        if not task.tools or len(task.tools) == 0:
            return self.run_llm_chat(task)

        return self.run_llm_agent(task)
    
    def run_code_validation(self, task: Task) -> ModelResponse:
        pass

    def run_llm_agent(self, task: Task) -> ModelResponse:
        system_prompt = self.prompt_builder.build_system_prompt(task)
        user_prompt = self.prompt_builder.build(task)
        
        # Always use execute_task_with_tools - the accessor handles MCP abstraction
        return self.accessor.execute_task_with_tools(
            model=task.model.name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tools=task.tools
        )
    
    def run_llm_chat(self, task: Task) -> ModelResponse:
        system_prompt = self.prompt_builder.build_system_prompt(task)
        user_prompt = self.prompt_builder.build(task)
        
        # Always use execute_task_with_tools - the accessor handles MCP abstraction
        return self.accessor.prompt_model(
            model=task.model.name,
            system_prompt=system_prompt,
            user_prompt=user_prompt
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