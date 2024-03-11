from fastapi import HTTPException
from app.models.prompt_schema import PromptPayload
from app.utilities.openai_integration import OpenAIIntegration


async def process_prompt(payload: PromptPayload):
    """
    Processes a prompt by generating a summary or response using the OpenAI API.

    Args:
        payload (PromptPayload): The payload containing the prompt to process.

    Returns:
        dict: A dictionary containing the processed prompt result.
    """
    try:
        openai_integration = OpenAIIntegration(model=payload.gpt_model)
        return openai_integration.gpt_prompt(payload.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
