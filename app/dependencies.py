from app.config_loader import get_config
from app.github_integration import GitHubIntegration
from app.openai_integration import OpenAIIntegration
import logging

logger = logging.getLogger(__name__)

config = get_config()


def get_openai_integration(api_key=config['openai']['api_key'], model=config['openai']['default_model']):
    """
    Get an instance of OpenAIIntegration.

    Returns:
        OpenAIIntegration: An instance of the OpenAIIntegration class.
    """
    logger.info("Initializing OpenAI integration")
    return OpenAIIntegration(api_key, model)


def get_github_integration(user_login: str, repo_full_name: str):
    """
    Get an instance of GitHubIntegration configured with the appropriate GitHub API key.

    Args:
        user_login (str): User login name to potentially fetch a user-specific API key.
        repo_full_name (str): Full name of the repository to potentially fetch a repository-specific API key.

    Returns:
        GitHubIntegration: An instance of the GitHubIntegration class configured with the appropriate API key.
    """
    logger.info("Initializing GitHub integration")

    # Attempt to retrieve a user-specific API key
    github_api_key = (
            config.get('user_keys', {}).get(user_login, {}).get('api_key') or
            config.get('repo_owner_keys', {}).get(repo_full_name.split('/')[0], {}).get('api_key') or
            config.get('github', {}).get('default_api_key')
    )

    if not github_api_key:
        logger.error("No GitHub API key found for integration")
        raise Exception("No GitHub API key found for integration")

    return GitHubIntegration(github_token=github_api_key)
