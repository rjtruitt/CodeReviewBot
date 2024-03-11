from pydantic import BaseModel
from typing import Dict, Optional


class GitHubWebhookPayload(BaseModel):
    repository: Dict[str, str]
    sender: Dict[str, str]
    pull_request: Dict[str, int]


class GithubComment(BaseModel):
    repository_name: str
    user_login: Optional[str] = None
    pr_num: int
    comment: str


class FullRepoReview(BaseModel):
    """
    Represents a full repository review.

    - repository_name: Name of the repository.
    - gpt_model: The GPT model used for analysis. Defaults to "gpt-3.5-turbo".
    - user_login: Optional GitHub user login for user-specific analysis.
    - process_diffs_only: Whether to process diffs only. Defaults to False.
    """
    repository_name: str
    gpt_model: Optional[str] = "gpt-3.5-turbo"
    user_login: Optional[str] = None
    process_diffs_only: Optional[bool] = False
