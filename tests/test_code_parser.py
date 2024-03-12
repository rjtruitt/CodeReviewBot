from __future__ import annotations

import pytest

from app.code_parser import JavascriptParser, PythonParser


class TestParsers:
    @pytest.fixture
    def python_parser(self):
        return PythonParser()

    @pytest.fixture
    def javascript_parser(self):
        return JavascriptParser()

    def test_python_parser_minify_code(self, python_parser):
        content = "def add(x, y): return x + y"
        minified_code = python_parser.minify_code(content)

        assert minified_code == "def add(x,y):return x+y"

    def test_python_parser_parse_functions(self, python_parser):
        test_code = """
def test_function():
    print("Hello, world!")

async def async_test_function():
    await some_task()
"""

        snippets = python_parser.parse_functions(test_code)
        assert len(snippets) == 2
        assert snippets[0] == "def test_function():\n    print('Hello, world!')"

    def test_javascript_parser_minify_code(self, javascript_parser):
        content = "function add(x, y) { return x + y; }"
        minified_code = javascript_parser.minify_code(content)
        assert minified_code == "function add(x,y){return x+y;}"

    # Add more tests as needed
