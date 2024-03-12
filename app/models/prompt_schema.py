"""Module defining schemas for handling prompt payloads."""

from __future__ import annotations

from pydantic import BaseModel


class PromptPayload(BaseModel):
    """Represents the payload for processing a prompt with a specified GPT model."""

    prompt: str
    gpt_model: str | None = "gpt-3.5-turbo"
