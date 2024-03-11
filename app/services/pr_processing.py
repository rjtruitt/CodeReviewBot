from typing import List, Dict

from app.code_parser import get_parser_for_language
from app.utilities.github_integration import GitHubIntegration
from app.utilities.openai_integration import OpenAIIntegration


class PRProcessor:
    """
    Processes pull requests to generate summaries and review code,
    utilizing OpenAI and custom parsers for code minimization.
    """

    def __init__(self, user_login: str, repo_full_name: str, gpt_model: str):
        """
        Initializes the PRProcessor with necessary integrations.

        Args:
            user_login (str): GitHub user login for API interaction.
            repo_full_name (str): Full repository name (e.g., 'user/repo').
            gpt_model (str): Model name for OpenAI GPT summarization.
        """
        self.gh_client = GitHubIntegration(user_login=user_login, repo_full_name=repo_full_name)
        self.openai_integration = OpenAIIntegration(model=gpt_model)

    async def generate_pr_summary(self, pr_number: int, process_diffs_only: bool = False) -> Dict:
        """
        Generates a summary for a specified pull request.

        Args:
            pr_number (int): The number of the pull request to summarize.
            process_diffs_only (bool, optional): Whether to process diffs only. Defaults to False.

        Returns:
            Dict: A dictionary containing the PR number and its summary.
        """
        pr_summaries = await self._generate_pr_summary(pr_number, process_diffs_only)
        summary_content = pr_summaries[0]['Summary']
        await self.gh_client.post_comment_on_pr(pr_number, summary_content)
        return {"PR #": pr_number, "Summary": summary_content}

    async def generate_all_prs_summary(self, process_diffs_only: bool = False) -> List[Dict]:
        """
        Generates summaries for all open pull requests.

        Args:
            process_diffs_only (bool, optional): Whether to process diffs only. Defaults to False.

        Returns:
            List[Dict]: A list of dictionaries, each containing a PR number and its summary.
        """
        open_prs = await self.gh_client.fetch_open_pull_requests()
        all_summaries = []
        for pr in open_prs:
            summaries = await self._generate_pr_summary(pr.number, process_diffs_only)
            all_summaries.extend(summaries)
            for summary in summaries:
                await self.gh_client.post_comment_on_pr(pr.number, summary['Summary'])
        return all_summaries

    async def _generate_pr_summary(self, pr_number: int, process_diffs_only: bool) -> List[Dict]:
        """
        Helper method to fetch files from a PR, summarize and optionally compress them.
        """
        files = await self.gh_client.fetch_files_from_pr(pr_number)
        file_summaries = [await self._summarize_file(file, process_diffs_only, True) for file in files]
        combined_file_summaries = "\nNext PR File\n".join(file_summaries)
        pr_summary_content = await self._create_comprehensive_summary(combined_file_summaries, process_diffs_only)
        return [{'PR #': pr_number, 'Summary': pr_summary_content}]

    async def _summarize_file(self, file, process_diffs_only: bool, compress_response: bool = False) -> str:
        """
        Summarizes a file's content, with optional code minimization.
        """
        text_to_summarize = file.get('patch', '') if process_diffs_only else file['content']
        if compress_response:
            parser = get_parser_for_language(file.get('file_type', 'Plain text'))
            text_to_summarize = self._minimize_content(parser, text_to_summarize)
        prompt = f"Summarize this file from a PR. {'Compress if possible.' if compress_response else ''}"
        summary_response = await self.openai_integration.summarize_text(text_to_summarize, prompt)
        return summary_response['choices'][0]['message']['content']

    async def review_pull_request(self, pr_number: int, process_diffs_only: bool = False):
        """
        Processes a single pull request by summarizing and reviewing each file within it.

        This method fetches all files from the specified pull request, generates summaries,
        conducts code reviews, and posts the combined findings as a comment on the pull request.

        Args:
            pr_number: The number of the pull request to process.
            process_diffs_only: Indicates whether to consider only the diffs of the files for processing.
        """
        files = await self.gh_client.fetch_files_from_pr(pr_number)
        for file in files:
            await self.process_file(file, pr_number, process_diffs_only)

    async def review_all_open_pull_requests(self, process_diffs_only: bool = False) -> str:
        """
        Processes all open pull requests in the repository by summarizing and reviewing each file within them.

        Iterates through each open pull request, applying the process_pull_request method to each,
        thereby generating summaries and reviews for posting on GitHub.

        Args:
            process_diffs_only: Indicates whether to consider only the diffs of the files for processing.

        Returns:
            A simple confirmation message indicating the completion of the operation.
        """
        open_prs = await self.gh_client.fetch_open_pull_requests()
        for pr in open_prs:
            await self.review_pull_request(pr.number, process_diffs_only)
        return 'OK'

    async def process_file(self, file, pr_number, process_diffs_only: bool = False):
        """
        Processes a single file from a pull request by generating a summary and a code review,
        then formats and posts the combined content as a comment on the pull request.

        Args:
            file: The file object containing details and content for processing.
            pr_number: The pull request number to which the file belongs.
            process_diffs_only: Indicates whether to consider only the diffs of the file for processing.
        """
        summary_content = await self._summarize_file(file, process_diffs_only)
        review_content = await self._review_code(file, process_diffs_only)
        comment_to_post = self._format_comment(file, summary_content, review_content, process_diffs_only)
        await self.gh_client.post_comment_on_pr(pr_number, comment_to_post)

    def _minimize_content(self, parser, content: str) -> str:
        """
        Attempts to minimize the given content using the specified parser.
        """
        try:
            return parser.minify_code(content)
        except NotImplementedError:
            return content

    async def _create_comprehensive_summary(self, combined_file_summaries: str, process_diffs_only: bool) -> str:
        """
        Creates a comprehensive summary from combined file summaries.
        """
        prompt = (
            "Create a comprehensive summary based on individual file summaries from this PR. "
            "Summarize the overall impact of the PR, highlighting key additions, deletions, and modifications."
        )
        summary_response = await self.openai_integration.summarize_text(combined_file_summaries, prompt)
        return summary_response['choices'][0]['message']['content']

    async def _review_code(self, file, process_diffs_only: bool) -> str:
        """
        Reviews the code of a file.
        """
        code_to_review = file.get('patch', '') if process_diffs_only else file['content']
        language = file.get('file_type', 'Plain text')
        review_response = await self.openai_integration.review_code(code_to_review, language, process_diffs_only)
        return review_response['choices'][0]['message']['content']

    def _format_comment(self, file, summary_content: str, review: str, process_diffs_only: bool) -> str:
        """
        Formats the final comment to be posted on GitHub, including both summary and review.
        """
        filename = file['filename']
        language = file.get('file_type', 'Plain text')
        return f'Filename: {filename}\nLanguage: {language}\nSummary:\n{summary_content}\n\nCode Review (diff={process_diffs_only}):\n{review}'
