from .modelAccessors.openai_accessor import OpenAIAccessor
from .dataModel.task import TaskModel

class AgentNode:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.accessor = OpenAIAccessor()

    def __repr__(self):
        return f"AgentNode(id={self.agent_id})"
    
    def complete_task(self, task: TaskModel):
        messages = [
            {"role": "system", "content": task.agent_description},
            {"role": "user", "content": task.prompt}
        ]
        return self.accessor.prompt_model(task.model, messages)