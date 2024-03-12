"""Module for handling Salesforce-specific operations, including language detection and code reviews."""

from __future__ import annotations

import os


def detect_salesforce_language(filepath: str) -> str | None:
    """
    Detects the Salesforce-specific programming language or file type for a given file
    based on directory structure and file extension.

    Args:
        filepath (str): Full path to the file.

    Returns:
        str | None: Detected Salesforce programming language or file type,
                    or None if not a Salesforce file.
    """
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    directory_parts = directory.split("/")  # github uses /
    # Ensure we are within a Salesforce project
    file_type = None
    if "force-app" in directory_parts:
        file_type = "Salesforce Other"
        if "__tests__" in directory_parts and filename.endswith(".js"):
            file_type = "Salesforce LWC Jest Test"
        if "lwc" in directory_parts and (
            filename.endswith(".js") or filename.endswith(".html")
        ):
            file_type = "Salesforce LWC"
        if filename.endswith(".cls") or filename.endswith(".trigger"):
            file_type = "Salesforce Apex"
        if "aura" in directory_parts and (
            filename.endswith(".cmp")
            or filename.endswith(".app")
            or filename.endswith(".evt")
            or filename.endswith(".intf")
        ):
            file_type = "Salesforce Aura Component"
        if filename.endswith(".page") or filename.endswith(".component"):
            file_type = "Salesforce Visualforce"
        if filename.endswith(".xml"):
            file_type = "Salesforce Metadata XML"
    return file_type


LWC_CODE_PROMPT = """Review the provided Salesforce LWC code for adherence to coding standards. Focus on:
Class Name & Variable Declaration: CamelCase for class name, use let or const for variable declaration.
Constants & Naming Convention: UPPERCASE with underscores for constants, verify naming conventions.
Method Declaration & Braces Style: camelCase for method names, ensure Stroustrup braces style.
Indentation & Semicolons: 4-space indentation, ensure semicolons at statement ends.
Unused Variables: Identify & remove unused variables.
Comments & Formatting: Clear, concise comments, proper code formatting.
Method Access Specifiers: Consistent method access specifiers.
Provide snippets highlighting violations with the existing code and suggest corrections for each aspect.
"""

LWC_TEST_CODE_PROMPT = """Review Salesforce LWC test code for standards adherence.  Focus on:
- File Structure: `__tests__` in root/src or alongside in force-app, exclude from `.forceignore`.
- Naming: Kebab-case tests, `.test.js` suffix.
- Test Structure: Imports order (Salesforce -> custom -> Apex), mocks after imports, `describe` starts, `afterEach` clears, separate `createElement` per scenario.
- `it` Tests: Use `async`/`await`, matching `createElement` name, avoid `@api`.
- Coverage: Target 100%.
- Exceptions: Fail by assertions only.
- Lint: No ESLint issues, justify `eslint-disable`.
- No Conditionals: Clear scenario per test.
- Emails: Use `@example.com`.
- No Magic Numbers: Use constants.
- Console: Remove `console.*` before prod.
Provide snippets highlighting violations with the existing code and suggest corrections for each aspect.
"""

APEX_CODE_PROMPT = """Review Salesforce Apex code below for standards adherence.  Focus on:
- Braces: Stroustrup style with no line breaks before the opening brace and a line break after the closing brace.
- Indentation: 4 spaces, limit to 100 columns.
- Whitespace: Around {, operators, ,.
- Naming: CamelCase for classes, lowerCamelCase for variables, UPPER_CASE for constants.
- Declarations: Use final for constants, initialize local variables when needed.
- Arrays: Prefer list initialization style.
- Docs: Javadoc comments for public items.
- Equality: Use ===.
- Column Limit: Keep lines under 100 columns where possible.
- Line Wrapping: Prefer breaking at a higher syntactic level.
- Vertical Whitespace: Use single blank lines to organize code into logical subsections.
- Horizontal Whitespace: Follow specific conventions for spacing between reserved words, operators, braces, etc.
- Horizontal Alignment: Avoid aligning tokens horizontally to prevent breaking alignment in future edits.
- Grouping Parentheses: Omit optional grouping parentheses when they don't improve readability.
- Variable Declarations: Declare one variable per declaration and initialize variables close to their first use.
- Annotations: List annotations on separate lines after the documentation block.
- Numeric Literals: Use uppercase L suffix for long-valued integer literals.
- Javadoc: Follow standard conventions for formatting Javadoc comments.
Provide snippets highlighting violations with the existing code and suggest corrections for each aspect.
"""

APEX_TEST_PROMPT = """Review Salesforce Apex test code for standards adherence. Focus on:
- Naming: CamelCase for test classes, lowerCamelCase for test methods, UPPER_CASE for constants.
- Test Structure: Arrange-Act-Assert pattern, clear setup and teardown.
- Assertions: Use System.assert methods, avoid redundant assertions.
- Coverage: Aim for 100% coverage, include edge cases and error scenarios.
- Isolation: Test each class method in isolation, mock dependencies as needed.
- Data: Use static resources or test factories, avoid hardcoding data.
- Exceptions: Ensure proper handling, assert expected behavior.
- Documentation: Provide descriptive method names and comments.
- Performance: Optimize execution time, minimize overhead.
- Dependencies: Reduce external dependencies, mock external services.
- Maintainability: Write readable and maintainable code, refactor as needed.
- Linting: Ensure code passes static analysis, address any issues.
Provide snippets highlighting violations with the existing code and suggest corrections for each aspect.
"""

SF_LANGUAGE_TO_PROMPT = {
    "Salesforce LWC": LWC_CODE_PROMPT,
    "Salesforce LWC Jest Test": LWC_TEST_CODE_PROMPT,
    "Salesforce Apex": APEX_CODE_PROMPT,
    "Salesforce Apex Test": APEX_TEST_PROMPT,
    "Salesforce Aura Component": "",
    "Salesforce Visualforce": "",
    "Salesforce Metadata XML": "",
    "Salesforce Other": "",
}
