from pydantic import BaseModel
from typing import Dict, Optional


class GitHubWebhookPayload(BaseModel):
    repository: Dict[str, str]
    sender: Dict[str, str]
    pull_request: Dict[str, int]

class GithubComment(BaseModel):
    repository: str
    pr_num: int
    comment: str

class FullRepoReview(BaseModel):
    repository_name: str
    gpt_model: Optional[str] = "gpt-3.5-turbo"
    user_login: Optional[str] = None
    process_diffs_only: Optional[bool] = False