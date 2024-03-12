"""Module for handling GitHub webhook events.

This module processes incoming webhook payloads from GitHub, specifically handling
pull request events to trigger further actions like pull request reviews.
"""

from __future__ import annotations

import logging

from app.models.github_webhook_schema import GitHubWebhookPayload
from app.services.pr_processing import PRProcessor

logger = logging.getLogger(__name__)


async def handle_github_webhook(payload: GitHubWebhookPayload):
    """
    Processes a GitHub webhook payload related to pull requests.

    This function extracts necessary information from the webhook payload to initiate
    a review process on the pull request using the PRProcessor class.

    Args:
        payload (GitHubWebhookPayload): The payload data received from a GitHub webhook event.

    Returns:
        dict: A dictionary message indicating the pull request processing status.
    """
    pr_number = payload.pull_request.get("number")
    repository_full_name = payload.repository.get("full_name", "")
    user_login = payload.sender.get("login", "")

    processor = PRProcessor(
        user_login=user_login,
        repo_full_name=repository_full_name,
        gpt_model="your-gpt-model",  # Ensure you replace "your-gpt-model" with an actual model identifier if needed.
    )

    await processor.review_pull_request(pr_number, process_diffs_only=False)

    return {"message": "Pull request processed successfully"}
