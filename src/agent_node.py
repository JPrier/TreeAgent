from .modelAccessors.base_accessor import BaseModelAccessor
from .dataModel.task import Task, TaskType, TaskStatus
from dataBuilders.prompt_builder import PromptBuilder
from .dataModel.model_response import ModelResponse
from .validators.python_code_validator import PythonCodeValidator

class AgentNode:
    def __init__(self, agent_id: str, accessor: BaseModelAccessor):
        self.agent_id = agent_id
        self.accessor = accessor
        self.prompt_builder = PromptBuilder()
        self.code_validator = PythonCodeValidator()

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
        
        if Task.task_type == TaskType.DECOMPOSE:
            return self.run_llm_chat(task)

        if not task.tools or len(task.tools) == 0:
            return self.run_llm_chat(task)

        return self.run_llm_agent(task)
    
    def run_code_validation(self, task: Task):
        validation_results = self.code_validator.validate_code() # need a way to pass the code to validate (ideally the entire project)
        if validation_results.is_valid:
            task.status = TaskStatus.COMPLETED
        else:
            task.status = TaskStatus.FAILED
            task.result = validation_results.errors

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
    
    def handle_response(self, task: Task, response: ModelResponse) -> Task:
        """
        Handles the model response based on the task type and updates the task status accordingly.
        """
        match response.response_type:
            case ModelResponseType.DECOMPOSED:
                task.status = TaskStatus.PENDING_VALIDATION
                if not response.subtasks:
                    task.status = TaskStatus.FAILED
                    return task
                for subtask in response.subtasks:
                    subtask.task_id = f"{task.task_id}-{subtask.task_type}"
                    # TODO: Add subtask to project queue or execute immediately
            case ModelResponseType.IMPLEMENTED:
                task.status = TaskStatus.COMPLETED
                # TODO: If parent requested details share summary -- does this condition matter here? 
            case ModelResponseType.FAILED:
                task.status = TaskStatus.FAILED if not response.retryable else TaskStatus.PENDING
            case _:
                task.status = TaskStatus.FAILED
        return task