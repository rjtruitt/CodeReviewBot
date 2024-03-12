"""This module defines the routing for the API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Body

from app.models.github_webhook_schema import (FullRepoReview, GithubComment,
                                              GitHubWebhookPayload)
from app.models.prompt_schema import PromptPayload
from app.services.gpt.gpt_requests import process_prompt
from app.services.pr_processing import PRProcessor
from app.services.webhooks.github_webhooks import handle_github_webhook

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status/")
def get_status() -> dict:
    """Get the status of the service.

    Returns:
        dict: A dictionary containing the service status, indicating it is running.
    """
    return {"status": "Service is up and running"}


@router.post("/prompt/")
def process_prompt_endpoint(payload: PromptPayload) -> dict:
    """Processes a given prompt using GPT and returns the response.

    Args:
        payload (PromptPayload): The payload containing the prompt.

    Returns:
        dict: The processed prompt response.
    """
    return process_prompt(payload)


@router.post("/github-webhook/", response_model=dict)
def github_webhook_endpoint(payload: GitHubWebhookPayload) -> dict:
    """Endpoint for processing GitHub webhook payloads.

    Args:
        payload (GitHubWebhookPayload): The GitHub webhook payload.

    Returns:
        dict: A dictionary indicating the webhook was processed successfully.
    """
    return handle_github_webhook(payload)


@router.post("/review_all_open_PRs/")
def review_all_open_pull_requests_endpoint(payload: FullRepoReview = Body(...)) -> dict:
    """Reviews all open pull requests for the specified repository.

    Args:
        payload (FullRepoReview): Information about the repository and user.

    Returns:
        dict: A summary of the review process.
    """
    processor = PRProcessor(
        user_login=payload.user_login,
        repo_full_name=payload.repository_name,
        gpt_model=payload.gpt_model,
    )
    return processor.review_all_open_pull_requests(payload.process_diffs_only)


@router.post("/generate_PR_summary/")
def generate_pr_summary_endpoint(payload: FullRepoReview = Body(...)) -> dict:
    """Generates a summary for all pull requests in the specified repository.

    Args:
        payload (FullRepoReview): Information about the repository and user.

    Returns:
        dict: A dictionary containing summaries for all PRs.
    """
    processor = PRProcessor(
        user_login=payload.user_login,
        repo_full_name=payload.repository_name,
        gpt_model=payload.gpt_model,
    )
    return processor.generate_all_prs_summary(payload.process_diffs_only)


@router.post("/add_github_comment/")
def add_github_comment(payload: GithubComment = Body(...)) -> dict:
    """Adds a comment to a GitHub pull request.

    Args:
        payload (GithubComment): The payload containing the PR number and comment.

    Returns:
        dict: A message indicating the comment was added successfully.
    """
    processor = PRProcessor(
        user_login=payload.user_login,
        repo_full_name=payload.repository_name,
        gpt_model="",
    )
    processor.gh_client.post_comment_on_pr(payload.pr_num, payload.comment)
    return {"message": "Comment added successfully."}
