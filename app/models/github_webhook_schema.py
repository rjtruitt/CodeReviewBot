"""Module defining Pydantic models for GitHub webhook payloads."""

from __future__ import annotations

from pydantic import BaseModel


class GitHubWebhookPayload(BaseModel):
    """Defines the structure of a GitHub webhook payload."""

    repository: dict[str, str]
    sender: dict[str, str]
    pull_request: dict[str, int]


class GithubComment(BaseModel):
    """Represents a comment on a GitHub pull request."""

    repository_name: str
    user_login: str | None = None
    pr_num: int
    comment: str


class FullRepoReview(BaseModel):
    """Represents a request for a full repository review."""

    repository_name: str
    gpt_model: str | None = "gpt-3.5-turbo"
    user_login: str | None = None
    process_diffs_only: bool | None = False
