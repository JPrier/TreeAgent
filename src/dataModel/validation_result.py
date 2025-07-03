from pydantic import BaseModel
from typing import Optional, List, Any

class ValidationResult(BaseModel):
    is_valid: bool
    errors: Optional[List[Any]]

    def __init__(self, **data):
        super().__init__(**data)
        if self.is_valid and self.errors and len(self.errors) > 0:
            raise ValueError("Cannot have both is_valid=True and an error_message.")
        if not self.is_valid and (not self.errors or len(self.errors) == 0):
            raise ValueError("Must provide an error_message when is_valid=False.")
