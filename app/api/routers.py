from fastapi import APIRouter, Body
import logging

from app.models.github_webhook_schema import GithubComment, GitHubWebhookPayload, FullRepoReview
from app.models.prompt_schema import PromptPayload
from app.services.gpt.gpt_requests import process_prompt
from app.services.pr_processing import PRProcessor
from app.services.webhooks.github_webhooks import handle_github_webhook

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status/")
def get_status():
    """
    Get the status of the service.
    Returns:
        dict: A dictionary containing the service status.
    """
    return {"status": "Service is up and running"}


@router.post("/prompt/")
async def process_prompt_endpoint(payload: PromptPayload):
    return await process_prompt(payload)


@router.post("/github-webhook/", response_model=dict)
async def github_webhook_endpoint(payload: GitHubWebhookPayload):
    return await handle_github_webhook(payload)


@router.post("/review_all_open_PRs/")
async def review_all_open_pull_requests_endpoint(payload: FullRepoReview = Body(...)):
    processor = PRProcessor(user_login=payload.user_login, repo_full_name=payload.repository_name,
                            gpt_model=payload.gpt_model)
    return await processor.review_all_open_pull_requests(payload.process_diffs_only)


@router.post("/generate_PR_summary/")
async def generate_pr_summary_endpoint(payload: FullRepoReview = Body(...)):
    processor = PRProcessor(user_login=payload.user_login, repo_full_name=payload.repository_name,
                            gpt_model=payload.gpt_model)
    return await processor.generate_pr_summary(payload.pr_num)


@router.post("/add_github_comment/")
async def add_github_comment(payload: GithubComment = Body(...)):
    processor = PRProcessor(user_login=payload.user_login, repo_full_name=payload.repository_name, gpt_model="")
    await processor.gh_client.post_comment_on_pr(payload.pr_num, payload.comment)
    return {"message": "Comment added successfully."}