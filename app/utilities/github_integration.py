import os
import logging
from base64 import b64decode

from fastapi import HTTPException
from github import Github, GithubException, UnknownObjectException
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound
from unidiff import PatchSet

from app.config_loader import get_config
from app.services.salesforce.salesforce_handler import detect_salesforce_language

logger = logging.getLogger(__name__)


def detect_language(filepath):
    """
    Detect the programming language of a file, with special handling for Salesforce.

    Args:
        filepath (str): Path or name of the file.

    Returns:
        str: Detected programming language, or 'Unknown' if detection fails.
    """
    logger.debug("Detecting language for: %s", filepath)
    filename = os.path.basename(filepath)

    sf_language = detect_salesforce_language(filepath)
    if sf_language:
        return sf_language

    try:
        lexer = guess_lexer_for_filename(filename, "")
        return lexer.name
    except ClassNotFound:
        return "Unknown"


class GitHubIntegration:
    def __init__(self, user_login: str, repo_full_name: str, base_url: str = None):
        self.config = get_config()
        self.github_api_key = self._get_github_api_key(user_login, repo_full_name)
        try:
            if base_url:
                self.github = Github(base_url=base_url, login_or_token=self.github_api_key)
            else:
                self.github = Github(login_or_token=self.github_api_key)
            self.repository = self.github.get_repo(repo_full_name)
        except UnknownObjectException:
            raise HTTPException(status_code=404, detail=f"Repository {repo_full_name} not found")
        except GithubException as e:
            raise HTTPException(status_code=e.status, detail=str(e))

    def _get_github_api_key(self, user_login: str, repo_full_name: str) -> str:
        # Logic to get the GitHub API key
        api_key = (self.config.get('user_keys', {}).get(user_login, {}).get('api_key') or
                   self.config.get('repo_owner_keys', {}).get(repo_full_name.split('/')[0], {}).get('api_key') or
                   self.config['github']['default_api_key'])
        if not api_key:
            raise ValueError("No GitHub API key found for integration")
        return api_key

    def fetch_open_pull_requests(self):
        """
        Fetch open pull requests from the repository.

        Returns:
            List of open pull requests.
        """
        logger.info("Fetching open PRs from: %s", self.repository.full_name)
        return self.repository.get_pulls(state='open')

    def fetch_pull_request(self, pr_number):
        """
        Fetch a specific pull request.

        Args:
            pr_number (int): Pull request number.

        Returns:
            PullRequest object.
        """
        logger.info("Fetching PR #%d", pr_number)
        return self.repository.get_pull(pr_number)

    def fetch_commit(self, commit_sha):
        """
        Fetch a specific commit.

        Args:
            commit_sha (str): Commit SHA.

        Returns:
            Commit object.
        """
        logger.info("Fetching commit: %s", commit_sha)
        return self.repository.get_commit(commit_sha)

    def fetch_files_from_pr(self, pr_number):
        """
        Fetch files from a pull request and detect their language.

        Args:
            pr_number (int): Pull request number.

        Returns:
            List of file details including language.
        """
        logger.info("Fetching files from PR #%d", pr_number)
        pr = self.fetch_pull_request(pr_number)
        files = pr.get_files()

        file_details = [{
            'filename': file.filename,
            'patch': file.patch,
            'language': detect_language(file.filename),
            'additions': file.additions,
            'deletions': file.deletions,
            'changes': file.changes,
            'status': file.status,
            'url': file.contents_url
        } for file in files]

        return file_details

    def post_comment_on_pr(self, pr_number, comment):
        """
        Post a comment on a pull request.

        Args:
            pr_number (int): Pull request number.
            comment (str): Comment text.
        """
        logger.info("Posting comment on PR #%d", pr_number)
        pr = self.fetch_pull_request(pr_number)
        pr.create_issue_comment(comment)

    def post_comment_on_commit(self, commit_sha, path, position, body):
        """
        Post a comment on a specific line of a file in a commit, useful in pull request reviews.

        Args:
            commit_sha (str): SHA of the commit.
            path (str): File path relative to the repository root.
            position (int): Line index in the diff for the comment.
            body (str): Comment text.
        """
        logger.info("Posting comment on commit: %s, file: %s", commit_sha, path)
        commit = self.fetch_commit(commit_sha)
        commit.create_comment(body, path, position)

    def get_pr_diffs(self, pr_number):
        """
        Fetch diff data for all files in a pull request, extracting changed lines.

        Args:
            pr_number (int): Pull request number.

        Returns:
            List of dictionaries representing file changes.
        """
        logger.info("Fetching diffs for PR #%d", pr_number)
        pr = self.fetch_pull_request(pr_number)
        diffs = pr.get_files()

        changed_files = []
        for diff in diffs:
            patch_set = PatchSet(diff.patch)
            for patched_file in patch_set:
                file_changes = {
                    'filename': patched_file.path,
                    'added_lines': [line.value for hunk in patched_file for line in hunk if line.is_added],
                    'modified_lines': [line.value for hunk in patched_file for line in hunk if line.is_modified]
                }
                changed_files.append(file_changes)

        return changed_files

    def fetch_files_in_folder(self, folder_path):
        """
        Fetch all files in a specific folder of the repository.

        Args:
            folder_path (str): Path to the folder in the repository.

        Returns:
            List of file details (name, content).
        """
        logger.info("Fetching files from folder: %s", folder_path)
        contents = self.repository.get_contents(folder_path)
        file_details = []
        for content in contents:
            if content.type == "file":
                file_content = b64decode(content.content).decode('utf-8')
                file_details.append({
                    'name': content.name,
                    'content': file_content
                })
        return file_details

    def fetch_repo_info(self):
        """
        Fetch information about the GitHub repository.

        Returns:
            Dictionary containing repository information.
        """
        repo = self.repository
        logger.info("Fetching info for repository: %s", repo.full_name)
        return {
            "full_name": repo.full_name,
            "description": repo.description,
            "html_url": repo.html_url,
            "created_at": repo.created_at.isoformat(),
            "updated_at": repo.updated_at.isoformat(),
            "default_branch": repo.default_branch,
            "fork": repo.fork,
            "forks_count": repo.forks_count,
            "open_issues_count": repo.open_issues_count,
            "watchers_count": repo.watchers_count,
            "language": repo.language,
        }
