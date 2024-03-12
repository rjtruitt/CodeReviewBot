"""Module providing services for processing pull requests using GitHub and OpenAI integrations."""

from __future__ import annotations

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
        self.gh_client = GitHubIntegration(
            user_login=user_login, repo_full_name=repo_full_name
        )
        self.openai_integration = OpenAIIntegration(model=gpt_model)

    # TODO: add an attribute that tries to compress the files code down instead of summary then summarize all code
    # Also try to use compressed code and structure for an architectural review as and possibly flow diagram

    def generate_pr_summary(
        self, pr_number: int, process_diffs_only: bool = False
    ) -> dict:
        """
        Generates a summary for a specified pull request.

        Args:
            pr_number (int): The number of the pull request to summarize.
            process_diffs_only (bool, optional): Whether to process diffs only. Defaults to False.

        Returns:
            Dict: A dictionary containing the PR number and its summary.
        """
        pr_summaries = self._generate_pr_summary(pr_number, process_diffs_only)
        summary_content = pr_summaries[0]["Summary"]
        self.gh_client.post_comment_on_pr(pr_number, summary_content)
        return {"PR #": pr_number, "Summary": summary_content}

    def generate_all_prs_summary(self, process_diffs_only: bool = False) -> list[dict]:
        """
        Generates summaries for all open pull requests.

        Args:
            process_diffs_only (bool, optional): Whether to process diffs only. Defaults to False.

        Returns:
            List[Dict]: A list of dictionaries, each containing a PR number and its summary.
        """
        open_prs = self.gh_client.fetch_open_pull_requests()
        all_summaries = []
        for pr in open_prs:
            summaries = self._generate_pr_summary(pr.number, process_diffs_only)
            all_summaries.extend(summaries)
            for summary in summaries:
                self.gh_client.post_comment_on_pr(pr.number, summary["Summary"])
        return all_summaries

    def _generate_pr_summary(
        self, pr_number: int, process_diffs_only: bool
    ) -> list[dict]:
        """
        Helper method to fetch files from a PR, summarize and optionally compress them.
        """
        files = self.gh_client.fetch_files_from_pr(pr_number)
        filtered_files = [
            file
            for file in files
            if (
                (process_diffs_only and file.get("patch"))
                or (not process_diffs_only and file.get("content"))
            )
        ]
        file_summaries = [
            f"Filename: {file['filename']}\n{self._summarize_file(file, process_diffs_only, True)}"
            for file in filtered_files
        ]
        combined_file_summaries = "\nNext PR File\n".join(file_summaries)
        pr_summary_content = self._create_comprehensive_summary(
            combined_file_summaries, process_diffs_only
        )
        return [{"PR #": pr_number, "Summary": pr_summary_content}]

    def _summarize_file(
        self, file, process_diffs_only: bool, pr_summary: bool = False
    ) -> str:
        """
        Asynchronously summarizes a file's content, optionally applying code minimization
        to enhance the efficiency of the summary produced by GPT.

        Args:
            file: The file object containing details like 'patch', 'content', and 'file_type'.
            process_diffs_only (bool): Flag indicating whether to summarize diff content only.
            pr_summary (bool): Flag indicating whether the summary is part of a larger PR summary,
                               which might necessitate a more condensed format.

        Returns:
            str: The summarized content as a string.
        """
        text_to_summarize = (
            file.get("patch", "") if process_diffs_only else file["content"]
        )
        diff_indicator = (
            "This is a diff so treat '+' as additions and '-' as subtractions."
            if process_diffs_only
            else "This is a full file, not a diff."
        )

        if pr_summary:
            prompt = (
                f"Summarize this file from a PR in the most condensed format that GPT can understand, "
                f"combining it into a readable format for all files in a GitHub pull request. "
                f"{diff_indicator} Use shorthand or minimize to use the least amount of tokens if necessary."
            )
            parser = get_parser_for_language(file.get("file_type", "Plain text"))
            text_to_summarize = self._minimize_content(parser, text_to_summarize)
        else:
            prompt = f"Summarize this file from a PR. {diff_indicator}"

        summary_response = self.openai_integration.summarize_text(
            text_to_summarize, prompt
        )

        return summary_response["choices"][0]["text"]

    def review_pull_request(self, pr_number: int, process_diffs_only: bool = False):
        """
        Processes a single pull request by summarizing and reviewing each file within it.

        This method fetches all files from the specified pull request, generates summaries,
        conducts code reviews, and posts the combined findings as a comment on the pull request.

        Args:
            pr_number: The number of the pull request to process.
            process_diffs_only: Indicates whether to consider only the diffs of the files for processing.
        """
        files = self.gh_client.fetch_files_from_pr(pr_number)
        for file in files:
            self.process_file(file, pr_number, process_diffs_only)

    def review_all_open_pull_requests(self, process_diffs_only: bool = False) -> str:
        """
        Processes all open pull requests in the repository by summarizing and reviewing each file within them.

        Iterates through each open pull request, applying the process_pull_request method to each,
        thereby generating summaries and reviews for posting on GitHub.

        Args:
            process_diffs_only: Indicates whether to consider only the diffs of the files for processing.

        Returns:
            A simple confirmation message indicating the completion of the operation.
        """
        open_prs = self.gh_client.fetch_open_pull_requests()
        for pr in open_prs:
            self.review_pull_request(pr.number, process_diffs_only)
        return "OK"

    def process_file(self, file, pr_number, process_diffs_only: bool = False):
        """
        Processes a single file from a pull request by generating a summary and a code review,
        then formats and posts the combined content as a comment on the pull request.

        Args:
            file: The file object containing details and content for processing.
            pr_number: The pull request number to which the file belongs.
            process_diffs_only: Indicates whether to consider only the diffs of the file for processing.
        """
        if (process_diffs_only and not file["patch"]) or not file["content"]:
            return

        summary_content = self._summarize_file(file, process_diffs_only)
        review_content = self._review_code(file, process_diffs_only)
        comment_to_post = self._format_comment(
            file, summary_content, review_content, process_diffs_only
        )
        self.gh_client.post_comment_on_pr(pr_number, comment_to_post)

    def _minimize_content(self, parser, content: str) -> str:
        """
        Attempts to minimize the given content using the specified parser.
        """
        try:
            return parser.minify_code(content)
        except NotImplementedError:
            return content

    def _create_comprehensive_summary(
        self, combined_file_summaries: str, process_diffs_only: bool
    ) -> str:
        """
        Creates a comprehensive summary from combined file summaries.
        """
        prompt = (
            "Create a comprehensive summary based on individual file summaries from this PR. "
            "Summarize the overall impact of the PR, highlighting key additions, deletions, and modifications."
        )
        summary_response = self.openai_integration.summarize_text(
            combined_file_summaries, prompt
        )
        return summary_response["choices"][0]["text"]

    def _review_code(self, file, process_diffs_only: bool) -> str:
        """
        Reviews the code of a file.
        """
        code_to_review = (
            file.get("patch", "") if process_diffs_only else file["content"]
        )
        language = file.get("file_type", "Plain text")
        review_response = self.openai_integration.review_code(
            code_to_review, language=language, is_diff=process_diffs_only
        )
        return review_response["choices"][0]["text"]

    def _format_comment(
        self, file, summary_content: str, review: str, process_diffs_only: bool
    ) -> str:
        """
        Formats the final comment to be posted on GitHub, including both summary and review.
        """
        filename = file["filename"]
        language = file.get("file_type", "Plain text")
        return (
            f"Filename: {filename}\nModel: {self.openai_integration.model}\nLanguage: {language}\n"
            f"Summary:\n{summary_content}\n\nCode Review (diff={process_diffs_only}):\n{review}"
        )
