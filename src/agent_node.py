from dataBuilders.prompt_builder import PromptBuilder
from src.modelAccessors.openai_accessor import OpenAIAccessor
from src.dataModel.task import Task, TaskStatus
from src.dataModel.model_response import ModelResponse, ModelResponseType

class AgentNode:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.accessor = OpenAIAccessor()
        self.prompt_builder = PromptBuilder()

    def __repr__(self):
        return f"AgentNode(id={self.agent_id})"
    
    def execute_task(self, task: Task):
        system_prompt = self.prompt_builder.build_system_prompt(task)
        user_prompt = self.prompt_builder.build(task)

        return self.accessor.prompt_model(task.model, system_prompt, user_prompt)
    
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