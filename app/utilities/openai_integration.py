import openai
from tenacity import retry, stop_after_attempt, wait_random_exponential

from app.config_loader import get_config
from app.services.salesforce.salesforce_handler import sf_language_to_prompt


class OpenAIIntegration:
    def __init__(self, api_key: str = None, model: str = None):
        self.config = get_config()
        self.api_key = api_key or self.config['openai']['api_key']
        self.model = model or self.config['openai']['default_model']
        openai.api_key = self.api_key

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    def summarize_text(self, text, prompt_prefix="Summarize the following code. Not the prompt before the code."):
        """
        Generate a summary for the provided text using the OpenAI API.

        Args:
            text (str): The text to summarize.
            prompt_prefix (str): The prefix to add to the prompt for context.

        Returns:
            dict: A dictionary containing the OpenAI API response.
        """
        prompt = f"{prompt_prefix}:\n\n{text}"
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_response(response)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    def review_code(self, code, language="Python", is_diff=False, temperature=0.7, max_tokens=2048):
        """
        Generate a code review for the provided code snippet using the OpenAI API.

        Args:
            code (str): The code snippet to review.
            language (str): The programming language of the code.
            is_diff (bool): Indicates if the code snippet is a diff.
            temperature (float): Controls the randomness of the output.
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            dict: A dictionary containing the OpenAI API response.
        """
        prompt = self._generate_code_review_prompt(code, language, is_diff)
        response = self.openai_client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_response(response)

    def _generate_code_review_prompt(self, code, language, is_diff):
        """
        Generates the prompt for code review based on the provided parameters.

        Args:
            code (str): The code to review.
            language (str): The programming language of the code.
            is_diff (bool): Indicates if the code snippet is a diff.

        Returns:
            str: The generated prompt for the OpenAI API.
        """
        if language.startswith("Salesforce"):
            prompt_prefix = sf_language_to_prompt.get(language, "")
            diff_prefix = "This is a diff from GitHub with lines prefixed with + for additions and - for deletions." if is_diff else "This is a full file from a Pull Request."
            prompt = f"{diff_prefix}\n{prompt_prefix}\nCode:\n{code}"
        else:
            prompt_prefix = "This is a diff from GitHub with lines prefixed with + for additions and - for deletions." if is_diff else "This is a full file from a Pull Request."
            prompt_template = self.config.get("languages", {}).get(language, {}).get(
                "prompt_template",
                "{prompt_prefix} It is written in {language}. Review it for readability, maintainability, "
                "security, and best practices. Highlight areas for improvement or potential bugs, suggesting "
                "specific changes or alternatives. Provide practical, actionable advice, focusing on "
                "idiomatic responses and code snippets where applicable.\n\n{code}"
            )
            prompt = prompt_template.format(prompt_prefix=prompt_prefix, language=language, code=code)

        return prompt

    def _parse_response(self, response):
        """
        Parses the response from the OpenAI API into a structured dictionary.

        Args:
            response (openai.Completion): The response object from OpenAI.

        Returns:
            dict: A structured dictionary containing relevant response data.
        """
        return {
            "id": response.id,
            "created": response.created,
            "model": response.model,
            "choices": [{
                "text": choice["message"]["content"],
                "index": choice["index"],
                "finish_reason": choice.get("finish_reason", "")
            } for choice in response.choices]
        }