from pydantic import BaseModel


class PromptPayload(BaseModel):
    prompt: str
