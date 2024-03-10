import ast
import jsmin
from app.config_loader import get_config
from python_minifier import minify


class BaseParser:
    def __init__(self):
        self.config = get_config()

    def minify_code(self, content):
        raise NotImplementedError(
            "This method should be implemented by subclasses or is not available currently for this language.")

    def parse_functions(self, content):
        raise NotImplementedError(
            "This method should be implemented by subclasses or is not available currently for this language.")


class PythonParser(BaseParser):
    def parse_functions(self, content):
        root = ast.parse(content)
        return [ast.unparse(node) for node in ast.walk(root) if
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

    def minify_code(self, content):
        return minify(content, remove_literal_statements=True, combine_imports=True)


class JavascriptParser(BaseParser):
    def minify_code(self, content):
        return jsmin.jsmin(content)


def get_parser_for_language(language):
    parsers = {
        'Python': PythonParser(),
        'JavaScript': JavascriptParser()
    }
    return parsers.get(language, BaseParser())
