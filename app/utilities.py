import json
import logging
from fastapi import HTTPException, Body

from app.config_loader import get_config
from app.dependencies import get_github_integration, get_openai_integration
from app.models.github_webhook_schema import GitHubWebhookPayload, GithubComment, FullRepoReview
from app.models.prompt_schema import PromptPayload

logger = logging.getLogger(__name__)
config = get_config()


async def review_all_open_pull_requests(payload: FullRepoReview):
    gh_client = get_github_integration(payload.user_login, payload.repository_name)

    pull_requests = gh_client.fetch_open_pull_requests()

    for pr in pull_requests:
        files = gh_client.fetch_files_from_pr(pr)
        for file in files:
            await process_file(file, gh_client, payload.repository_name, pr.number, payload.gpt_model,
                               payload.process_diffs_only)

    return 'OK'


async def process_file(file, gh_client, repository_name, pr_number, model: None, process_diffs_only: bool = False):
    openai_integration = get_openai_integration(model=model)

    filename = file['filename']
    content = file['content']
    patch = file.get('patch', '')
    language = file.get('language', 'Plain text')
    current_model = model or config['openai']['default_model']

    summarize_code = f'Filename: {filename}\nLanguage: {language}\nGPT_Model: {current_model}\nCode:\n{content}'

    summary_response = openai_integration.summarize_text(summarize_code)
    summary = summary_response['choices'][0]['message']['content']

    code_to_review = patch if process_diffs_only else content
    review_response = openai_integration.review_code(code_to_review, language, process_diffs_only)
    review = review_response['choices'][0]['message']['content']

    # Combine summary and review into a single comment
    comment_to_post = f'{summary}\n\nCode Review (diff={process_diffs_only}):\n{review}'
    gh_client.post_comment_on_pr(repository_name, pr_number, comment_to_post)


async def add_comment_to_github_pr(payload: GithubComment):
    gh_client = get_github_integration('test', 'test')
    return gh_client.post_comment_on_pr(payload.repository, payload.pr_num, payload.comment)


# also using this for testing, just passing prompts to make sure the openai integration works
async def process_prompt(payload: PromptPayload = Body(...)):
    """
    Processes a prompt by generating a summary or response using the OpenAI API.

    Args:
        payload (PromptPayload): The payload containing the prompt to process.

    Returns:
        dict: A dictionary containing the processed prompt result.
    """
    logger.debug("Received prompt request: %s", payload.prompt)
    openai_integration = get_openai_integration()
    summary = openai_integration.summarize_text(payload.prompt)

    return {"summary": summary}


async def handle_github_webhook(payload: GitHubWebhookPayload = Body(...)):
    """
    Handles GitHub webhook payload to process pull request files and generate feedback.

    Args:
        payload (GitHubWebhookPayload): GitHub webhook payload containing pull request information.

    Returns:
        dict: A dictionary containing the response message and feedback.
    """
    repository_full_name = payload.repository.get("full_name", "")
    user_login = payload.sender.get("login", "")

    if not repository_full_name:
        logger.error("Repository full name not found in payload")
        raise HTTPException(status_code=400, detail="Repository full name not found in payload.")

    pr_number = payload.pull_request.get("number")
    if not pr_number:
        logger.error("Pull request number not found in payload")
        raise HTTPException(status_code=400, detail="Pull request number not found in payload.")

    gh_client = get_github_integration(user_login, repository_full_name)

    pr = gh_client.fetch_pull_request(repository_full_name, pr_number)
    file_details = gh_client.fetch_files_from_pr(pr, payload.repository)

    feedback_messages = []
    for filename, content, language in file_details:
        if language == "Unknown":
            feedback_messages.append(f"Skipping unknown or unsupported file type: {filename}")
            continue

        # TODO: add the code review part, prompts and parsing, breaking apart code into processable chunks using
        # code_parser.py

    logger.info("Webhook processed successfully")
    response = {"message": "Webhook processed successfully", "feedback": feedback_messages}
    logger.debug("Webhook response: %s", json.dumps(response, indent=2))
    return {"message": "Webhook processed successfully"}
