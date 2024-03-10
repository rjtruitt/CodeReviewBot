from pydantic import BaseModel
from typing import Dict


class GitHubWebhookPayload(BaseModel):
    repository: Dict[str, str]
    sender: Dict[str, str]
    pull_request: Dict[str, int]

class GithubComment(BaseModel):
    repository: str
    pr_num: int
    comment: str
