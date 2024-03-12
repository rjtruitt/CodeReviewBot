"""Module for parsing and minifying code across different programming languages."""

from __future__ import annotations

import ast

import jsmin
from python_minifier import minify

from app.config_loader import get_config


class BaseParser:
    """Base class for language-specific parsers. Defines common interfaces for parsing
    and minifying code."""

    def __init__(self):
        """Initializes the parser with configuration settings."""
        self.config = get_config()

    def minify_code(self, content: str) -> str:
        """Minifies the provided code content.

        Args:
            content (str): The code content to minify.

        Raises:
            NotImplementedError: If the subclass does not implement this method.

        Returns:
            str: The minified code.
        """
        raise NotImplementedError("Minify method is not implemented for this language.")

    def parse_functions(self, content: str) -> list:
        """Parses the provided code content and extracts functions.

        Args:
            content (str): The code content to parse.

        Raises:
            NotImplementedError: If the subclass does not implement this method.

        Returns:
            list: A list of parsed functions.
        """
        raise NotImplementedError("Parsing is not implemented for this language.")


class PythonParser(BaseParser):
    """Parser for Python code. Extends BaseParser to parse and minify Python code."""

    def parse_functions(self, content: str) -> list:
        """Parses Python code to extract function definitions.

        Args:
            content (str): Python code content.

        Returns:
            list: A list of string representations of function definitions.
        """
        root = ast.parse(content)
        return [
            ast.unparse(node)
            for node in ast.walk(root)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    def minify_code(self, content: str) -> str:
        """Minifies Python code using python-minifier.

        Args:
            content (str): Python code content.

        Returns:
            str: Minified Python code.
        """
        return minify(content, remove_literal_statements=True, combine_imports=True)


class JavascriptParser(BaseParser):
    """Parser for JavaScript code. Extends BaseParser to minify JavaScript code."""

    def parse_functions(self, content: str) -> list:
        """Placeholder method for JavaScript function parsing.

        Args:
            content (str): JavaScript code content.

        Returns:
            list: An empty list, as parsing is not implemented.
        """
        # Placeholder implementation, trying to find appropriate library.
        raise NotImplementedError("Parsing is not implemented for this language")

    def minify_code(self, content: str) -> str:
        """Minifies JavaScript code using jsmin.

        Args:
            content (str): JavaScript code content.

        Returns:
            str: Minified JavaScript code.
        """
        return jsmin.jsmin(content)


def get_parser_for_language(language: str) -> BaseParser:
    """Factory function to get a parser instance for the given language.

    Args:
        language (str): The programming language of the parser.

    Returns:
        BaseParser: An instance of a parser for the specified language.
    """
    parsers = {
        "Python": PythonParser(),
        "JavaScript": JavascriptParser(),
    }
    return parsers.get(language, BaseParser())
