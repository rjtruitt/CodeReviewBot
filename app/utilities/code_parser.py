import ast
import jsmin
from app.config_loader import get_config
from python_minifier import minify


class BaseParser:
    """
    A base class for language-specific parsers. It provides the structure for minimizing code
    and parsing functions within a given code content. Subclasses are expected to implement
    these functionalities for specific languages.
    """

    def __init__(self):
        """
        Initializes the BaseParser instance by loading the application configuration.
        """
        self.config = get_config()

    def minify_code(self, content: str) -> str:
        """
        Minifies the provided code content. This method should be implemented by subclasses.

        Args:
            content (str): The code content to be minified.

        Returns:
            str: The minified code content.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Minify method is not implemented for this language.")

    def parse_functions(self, content: str) -> list:
        """
        Parses the functions from the provided code content. This method should be implemented by subclasses.

        Args:
            content (str): The code content from which to parse functions.

        Returns:
            list: A list of parsed functions.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Parse functions method is not implemented for this language.")


class PythonParser(BaseParser):
    """
    A parser class for Python that extends BaseParser to provide Python-specific parsing
    and code minimization functionalities.
    """

    def parse_functions(self, content: str) -> list:
        """
        Parses functions from the provided Python code content using the `ast` module.

        Args:
            content (str): The Python code content from which to parse functions.

        Returns:
            list: A list of strings representing the parsed functions.
        """
        root = ast.parse(content)
        return [ast.unparse(node) for node in ast.walk(root) if
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

    def minify_code(self, content: str) -> str:
        """
        Minifies the provided Python code content using the `python_minifier` package.

        Args:
            content (str): The Python code content to be minified.

        Returns:
            str: The minified Python code content.
        """
        return minify(content, remove_literal_statements=True, combine_imports=True)


class JavascriptParser(BaseParser):
    """
    A parser class for JavaScript that extends BaseParser to provide JavaScript-specific
    code minimization functionality.
    """

    def minify_code(self, content: str) -> str:
        """
        Minifies the provided JavaScript code content using the `jsmin` package.

        Args:
            content (str): The JavaScript code content to be minified.

        Returns:
            str: The minified JavaScript code content.
        """
        return jsmin.jsmin(content)


def get_parser_for_language(language: str) -> BaseParser:
    """
    Returns an instance of a parser class for the specified language.

    Args:
        language (str): The programming language for which to get a parser.

    Returns:
        BaseParser: An instance of the appropriate parser class for the specified language.
    """
    parsers = {
        'Python': PythonParser(),
        'JavaScript': JavascriptParser(),
    }
    return parsers.get(language, BaseParser())
