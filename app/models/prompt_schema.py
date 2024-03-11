from typing import Optional

from pydantic import BaseModel


class PromptPayload(BaseModel):
    prompt: str
    gpt_model: Optional[str] = "gpt-3.5-turbo"