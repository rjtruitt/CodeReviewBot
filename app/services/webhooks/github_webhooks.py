from fastapi import HTTPException, Body
import logging
from app.models.github_webhook_schema import GitHubWebhookPayload
from app.services.pr_processing import PRProcessor

logger = logging.getLogger(__name__)


async def handle_github_webhook(payload: GitHubWebhookPayload):
    pr_number = payload.pull_request.get("number")
    repository_full_name = payload.repository.get("full_name", "")
    user_login = payload.sender.get("login", "")

    processor = PRProcessor(user_login=user_login, repo_full_name=repository_full_name, gpt_model="your-gpt-model")

    await processor.review_pull_request(pr_number, process_diffs_only=False)

    return {"message": "Pull request processed successfully"}
