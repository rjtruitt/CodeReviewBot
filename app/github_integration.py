import os

from fastapi import HTTPException
from github import Github, GithubException, UnknownObjectException
import logging
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound
from unidiff import PatchSet
from base64 import b64decode

from app.salesforce_handler import detect_salesforce_language

logger = logging.getLogger(__name__)


def detect_language(filepath):
    """
    Detect the programming language of a file, integrating Salesforce-specific handling.

    Args:
        filepath (str): Full path or name of the file.

    Returns:
        str: Detected programming language.
    """
    logger.debug("Detecting language of file: %s", filepath)
    filename = os.path.basename(filepath)

    # Try Salesforce-specific detection first
    sf_language = detect_salesforce_language(filepath)
    if sf_language:
        return sf_language

    # General language detection
    try:
        lexer = guess_lexer_for_filename(filename, "")
        return lexer.name
    except ClassNotFound:
        return "Unknown"


class GitHubIntegration:
    def __init__(self, github_token, repository_name=None, base_url=None):
        """
        Initialize the GitHubIntegration class.

        Args:
            github_token (str): GitHub API token.
            base_url (str, optional): Base URL of the GitHub instance for GitHub Enterprise.
        """
        try:
            if base_url:
                self.github = Github(base_url=base_url, login_or_token=github_token)
            else:
                self.github = Github(login_or_token=github_token)

            self.repository = self.github.get_repo(repository_name)

        except UnknownObjectException:
            raise HTTPException(status_code=404, detail=f"{repository_name}: Repository not found")
        except GithubException as e:
            raise HTTPException(status_code=500, detail="GitHub API error")

    def fetch_open_pull_requests(self):
        """
        Fetch all open pull requests from a GitHub repository.

        Returns:
            list: A list of open pull requests
        """
        logger.info("Fetching open pull requests from GitHub repository: %s", self.repository.full_name)
        return self.repository.get_pulls(state='open')

    def fetch_pull_request(self, repo_name, pr_number):
        """
        Fetch a specific pull request from GitHub.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").
            pr_number (int): Number of the pull request.

        Returns:
            github.PullRequest: A GitHub PullRequest object.
        """
        logger.info("Fetching pull request from GitHub")
        return self.repository.get_pull(pr_number)

    def fetch_commit(self, repo_name, commit_sha):
        """
        Fetch a specific commit from GitHub.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").
            commit_sha (str): SHA of the commit.

        Returns:
            github.Commit.Commit: A GitHub Commit object.
        """
        logger.info("Fetching commit from GitHub")
        return self.repository.get_commit(commit_sha)

    def fetch_files_from_pr(self, pr):
        """
        Fetch files from a given pull request and detect their language.

        Args:
            pr (github.PullRequest): GitHub PullRequest object.

        Returns:
            list: A list of tuples containing file details (filename, patch content, language).
        """
        logger.info("Fetching files from pull request")
        files = pr.get_files()
        file_details = []
        for file in files:
            file_content = self.repository.get_contents(file.filename, ref=pr.base.sha).content
            decoded_content = b64decode(file_content).decode('utf-8')  # Decode from Base64 and convert bytes to string

            file_details.append({'filename': file.filename,
                                 'content': decoded_content,
                                 'patch': file.patch,
                                 'file_type': detect_language(file.filename),
                                 'additions': file.additions,
                                 'deletions': file.deletions,
                                 'changed': file.changes,
                                 'status': file.status,
                                 'url': file.contents_url
                                 })

        return file_details

    def fetch_repo_info(self, repo_name):
        """
        Fetch information about a GitHub repository.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").

        Returns:
            dict: Dictionary containing repository information.
        """
        logger.info("Fetching repository information for: %s", repo_name)
        return {
            "full_name": self.repository.full_name,
            "description": self.repository.description,
            "html_url": self.repository.html_url,
            "created_at": self.repository.created_at.isoformat(),
            "updated_at": self.repository.updated_at.isoformat(),
            "default_branch": self.repository.default_branch,
            "fork": self.repository.fork,
            "forks_count": self.repository.forks_count,
            "open_issues_count": self.repository.open_issues_count,
            "watchers_count": self.repository.watchers_count,
            "language": self.repository.language,
        }

    def fetch_files_in_folder(self, repo_name, folder_path):
        """
        Fetch all files in a specific folder of a repository.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").
            folder_path (str): Path to the folder in the repository.

        Returns:
            list: A list of tuples containing file details (filename, content).
        """
        logger.info("Fetching files from folder: %s", folder_path)
        contents = self.repository.get_contents(folder_path)
        file_details = []
        for content in contents:
            if content.type == "file":
                file_details.append((content.name, content.decoded_content.decode()))
        return file_details

    def post_comment_on_pr(self, repo_name, pr_number, comment):
        """
        Post a comment on a pull request.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").
            pr_number (int): Number of the pull request.
            comment (str): The comment text to post.
        """
        logger.info("Posting comment on pull request #%d in repository: %s", pr_number, repo_name)
        pull_request = self.repository.get_pull(pr_number)
        pull_request.create_issue_comment(comment)

    def post_comment_on_commit(self, repo_name, commit_sha, path, position, body):
        """
        Post a comment on a specific line of a file in a commit, often used in the context of a review in a pull request.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").
            commit_sha (str): SHA of the commit where the comment should be posted.
            path (str): The file path relative to the repository root.
            position (int): The line index in the diff where the comment should be placed.
            body (str): The comment text to post.
        """
        logger.info("Posting comment on file '%s' at position %d in commit %s of repository: %s", path, position,
                    commit_sha, repo_name)
        commit = self.repository.get_commit(commit_sha)
        commit.create_comment(body, path, position)

    def get_pr_diffs(self, repo_name, pr_number):
        """
        Fetch diff data for all files in a pull request and parse the diffs to extract changed lines.

        Args:
            repo_name (str): Full name of the repository (e.g., "owner/repo").
            pr_number (int): Number of the pull request.

        Returns:
            list: A list of dictionaries, each representing a file with changes. Each dictionary includes
                  the filename and lists of added or modified lines.
        """
        logger.info("Fetching diff for pull request #%d from repository: %s", pr_number, repo_name)
        pr = self.repository.get_pull(pr_number)
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
