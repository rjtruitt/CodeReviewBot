import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
import yaml


class OpenAIIntegration:
    def __init__(self, api_key, model):
        """
        Initialize the OpenAIIntegration class.

        Args:
            api_key (str): OpenAI API key.
            model (str): Name of the language model to use.
        """
        self.api_key = api_key
        self.openai_client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.language_config = self.load_language_specific_config()

    def load_language_specific_config(self):
        """Load language prompts from the config file."""
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        return config.get("languages", {})

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(1))
    def summarize_text(self, text, temperature=0.7, max_tokens=1024):
        """
        Generate a summary for the given text.

        Args:
            text (str): The text to be summarized.
            temperature (float): Controls the randomness of the generated text.
            max_tokens (int): Maximum number of tokens in the generated text.

        Returns:
            dict: A dictionary containing the summary response.
        """
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
            ]
        )

        response_dict = {
            "id": response.id,
            "created": response.created,
            "model": response.model,
            "object": response.object,
            "system_fingerprint": response.system_fingerprint,
            "usage": {
                "completion_tokens": response.usage.completion_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "choices": [
                {
                    "finish_reason": choice.finish_reason,
                    "index": choice.index,
                    "message": {
                        "content": choice.message.content,
                        "role": choice.message.role,
                    }
                } for choice in response.choices
            ]
        }

        return response_dict

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(1))
    def review_code(self, code, language="Python", temperature=0.7, max_tokens=2048):
        """
        Generate a review for the given code snippet.

        Args:
            code (str): The code snippet to be reviewed.
            language (str): The programming language of the code snippet.
            temperature (float): Controls the randomness of the generated text.
            max_tokens (int): Maximum number of tokens in the generated text.

        Returns:
            str: The review feedback for the code snippet.
        """
        prompt_template = self.language_config.get(language, {}).get("prompt_template")

        if prompt_template is None:
            prompt_template = (
                "Here is a snippet of {language} code. Please review it for readability, "
                "maintainability, security, and adherence to best practices. Highlight any areas that "
                "could be improved or might contain potential bugs, and suggest specific improvements "
                "or alternatives. Avoid deep technical explanations and focus on practical, actionable "
                "advice."
            )

        prompt = prompt_template.format(language=language, code=code)

        response = self.openai_client.completions.create(
            model=self.model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=["\n\n", "END"]
        )
        return response.choices[0].text.strip()
