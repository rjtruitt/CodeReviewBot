import json
import logging
from fastapi import HTTPException, Body
from app.dependencies import get_github_integration, get_openai_integration
from app.models.github_webhook_schema import GitHubWebhookPayload
from app.models.prompt_schema import PromptPayload

logger = logging.getLogger(__name__)

# Only for testing, remove after getting the github integration all squared away
async def test_github():
    gh_client = get_github_integration('test', 'test')
    return gh_client.fetch_files_from_pr(gh_client.fetch_pull_request('rjtruitt/CodeReviewBot', 1))

#also using this for testing, just passing prompts to make sure the openai integration works
async def process_prompt(payload: PromptPayload = Body(...)):
    """
    Processes a prompt by generating a summary or response using the OpenAI API.

    Args:
        payload (PromptPayload): The payload containing the prompt to process.

    Returns:
        dict: A dictionary containing the processed prompt result.
    """
    logger.debug("Received prompt request: %s", payload.prompt)
    # Assuming get_openai_integration() provides an instance of OpenAIIntegration with a summarize_text method
    openai_integration = get_openai_integration()
    summary = await openai_integration.summarize_text(payload.prompt)

    return {"summary": summary}


async def handle_github_webhook(payload: GitHubWebhookPayload = Body(...)):
    """
    Handles GitHub webhook payload to process pull request files and generate feedback.

    Args:
        payload (GitHubWebhookPayload): GitHub webhook payload containing pull request information.

    Returns:
        dict: A dictionary containing the response message and feedback.
    """
    repository_full_name = payload.repository.get("full_name", "")
    user_login = payload.sender.get("login", "")

    if not repository_full_name:
        logger.error("Repository full name not found in payload")
        raise HTTPException(status_code=400, detail="Repository full name not found in payload.")

    pr_number = payload.pull_request.get("number")
    if not pr_number:
        logger.error("Pull request number not found in payload")
        raise HTTPException(status_code=400, detail="Pull request number not found in payload.")

    gh_client = get_github_integration(user_login, repository_full_name)

    pr = gh_client.fetch_pull_request(repository_full_name, pr_number)
    file_details = gh_client.fetch_files_from_pr(pr)

    feedback_messages = []
    for filename, content, language in file_details:
        if language == "Unknown":
            feedback_messages.append(f"Skipping unknown or unsupported file type: {filename}")
            continue

        # TODO: add the code review part, prompts and parsing, breaking apart code into processable chunks using
        # code_parser.py

    logger.info("Webhook processed successfully")
    response = {"message": "Webhook processed successfully", "feedback": feedback_messages}
    logger.debug("Webhook response: %s", json.dumps(response, indent=2))
    return {"message": "Webhook processed successfully"}
