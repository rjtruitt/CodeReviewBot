import os


def detect_salesforce_language(filepath):
    """
    Detects the Salesforce-specific programming language or file type for a given file
    based on directory structure and file extension.

    Args:
        filepath (str): Full path to the file.

    Returns:
        str: Detected Salesforce programming language or file type, or None if not a Salesforce file.
    """
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    directory_parts = directory.split(os.sep)

    # Ensure we are within a Salesforce project
    if 'force-app' in directory_parts:
        # Salesforce LWC Jest Test
        if '__tests__' in directory_parts and filename.endswith('.js'):
            return "Salesforce LWC Jest Test"
        # Salesforce LWC
        elif 'lwc' in directory_parts and (filename.endswith('.js') or filename.endswith('.html')):
            return "Salesforce LWC"
        # Salesforce Apex
        elif filename.endswith('.cls') or filename.endswith('.trigger'):
            return "Salesforce Apex"
        # Salesforce Aura Components
        elif 'aura' in directory_parts and (filename.endswith('.cmp') or filename.endswith('.app') or filename.endswith(
                '.evt') or filename.endswith('.intf')):
            return "Salesforce Aura Component"
        # Salesforce Visualforce
        elif filename.endswith('.page') or filename.endswith('.component'):
            return "Salesforce Visualforce"
        # Salesforce Metadata XML
        elif filename.endswith('.xml'):
            return "Salesforce Metadata XML"
        # Other Salesforce-related files (static resources, labels, etc.)
        else:
            return "Salesforce Other"
    return None


lwc_code_prompt = """Review the Salesforce LWC code below for standards adherence. Highlight violations with existing 
code snippets and provide suggested corrections. Focus on:
- Braces: Stroustrup style.
- Indentation: 4 spaces, limit to 100 columns.
- Whitespace: Around {{, operators, ,.
- Naming: CamelCase for classes, lowerCamelCase for methods/vars, UPPER_CASE for constants.
- Declarations: Use const/let.
- Arrays: Prefer list initialization style.
- Docs: Java block comments for public items.
- Equality: Use ===.
- HTML & External: Adhere to accessibility and copyright.
"""

lwc_test_code_prompt = """Review Salesforce LWC test code for standards adherence. Highlight violations with existing 
code snippets and provide suggested corrections. Focus on:
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
"""

apex_code_prompt = """Review Salesforce Apex code below for standards adherence. Highlight violations with existing code snippets and provide suggested corrections. Focus on:
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
"""

apex_test_prompt = """Review Salesforce Apex test code for standards adherence. Focus on:
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
"""

sf_language_to_prompt = {
    "Salesforce LWC": lwc_code_prompt,
    "Salesforce LWC Jest Test": lwc_test_code_prompt,
    "Salesforce Apex": apex_code_prompt,
    "Salesforce Apex Test": apex_test_prompt,
    "Salesforce Aura Component": "",
    "Salesforce Visualforce": "",
    "Salesforce Metadata XML": "",
    "Salesforce Other": ""
}
