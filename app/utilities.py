import json
import logging
from fastapi import HTTPException, Body

from app.config_loader import get_config
from app.dependencies import get_github_integration, get_openai_integration
from app.models.github_webhook_schema import GitHubWebhookPayload, GithubComment, FullRepoReview
from app.models.prompt_schema import PromptPayload

logger = logging.getLogger(__name__)
config = get_config()


async def generate_pr_summary(payload: FullRepoReview):
    gh_client = get_github_integration(payload.user_login, payload.repository_name)
    openai_integration = get_openai_integration(model=payload.gpt_model)

    pr_summaries = []
    for pr in gh_client.fetch_open_pull_requests():
        file_summaries = []
        for file in gh_client.fetch_files_from_pr(pr):
            text_to_summarize = file.get('patch', '') if payload.process_diffs_only else file['content']
            diff_indicator = "This is a diff so treat '+' as additions and '-' as subtractions." \
                if payload.process_diffs_only else "This is a full file, not a diff."

            prompt = (
                f"Summarize this file from a PR in the most condensed format that GPT can understand with the"
                f"understanding that it will be combined into a readable format after collecting them for all files in"
                f"a github pull request. "
                f"{diff_indicator} "
                f"Use shorthand or binary or whatever is processable but uses the least amount of tokens if necessary."
            )

            summary_response = openai_integration.summarize_text(text_to_summarize, prompt)
            summary_content = summary_response['choices'][0]['message']['content']
            print(summary_content)
            filename = file['filename']
            language = file.get('file_type', 'Plain text')
            file_summaries.append(f'Filename: {filename}\nLanguage: {language}\nSummary:\n{summary_content}')

        combined_file_summaries = "\nNext PR File\n".join(file_summaries)
        comprehensive_prompt = (
            "Create a comprehensive summary of the following PR based on individual file diffs. "
            "Summarize the overall impact of the PR, highlighting key additions, deletions, and modifications. "
            "Focus on overarching themes, major code changes, and their implications. Aim for succinctness and clarity."
        )

        pr_summary_response = openai_integration.summarize_text(combined_file_summaries, comprehensive_prompt)
        pr_summary_content = pr_summary_response['choices'][0]['message']['content']
        pr_summaries.append({'PR #': pr.number, 'Summary': pr_summary_content})

        gh_client.post_comment_on_pr(payload.repository_name, pr.number,
                                     f'PR Summary (diff={payload.process_diffs_only}):\n{pr_summary_content}')

    return pr_summaries


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
    language = file.get('file_type', 'Plain text')
    current_model = model or config['openai']['default_model']

    summary_response = openai_integration.summarize_text(content)
    summary_content = summary_response['choices'][0]['message']['content']
    summarized_response = f'Filename: {filename}\nLanguage: {language}\n' \
                          f'GPT_Model: {current_model}\nSummary:\n\n{summary_content}\n'
    code_to_review = patch if process_diffs_only else content
    review_response = openai_integration.review_code(code_to_review, language, process_diffs_only)
    review = review_response['choices'][0]['message']['content']

    comment_to_post = f'{summarized_response}\n\nCode Review (diff={process_diffs_only}):\n{review}'
    gh_client.post_comment_on_pr(repository_name, pr_number, comment_to_post)


async def add_comment_to_github_pr(payload: GithubComment):
    gh_client = get_github_integration(payload.user_login, payload.repository_name)
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
