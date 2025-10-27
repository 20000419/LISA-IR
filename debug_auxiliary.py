#!/usr/bin/env python3
"""
Debug script to test the auxiliary layer comment extraction.
"""

import re
from auxiliary_layer import AuxiliaryLayer

def debug_comment_extraction(c_code):
    """Debug the comment extraction logic."""
    print("=== DEBUG: Comment Extraction ===")
    print("Input code:")
    print(c_code)
    print("\n" + "="*50 + "\n")

    # Test the regex patterns
    comment_pattern = r'/\*(.*?)\*/'
    function_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_\s\*]*?)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:;|\{)'

    lines = c_code.split('\n')
    current_comment = ""
    in_function = False

    for i, line in enumerate(lines):
        print(f"Line {i}: {repr(line)}")

        # Check for multiline comments
        comment_match = re.search(comment_pattern, line, re.DOTALL)
        if comment_match:
            current_comment = comment_match.group(1).strip()
            print(f"  -> Found comment: {repr(current_comment)}")

        # Check for function definition
        function_match = re.match(function_pattern, line)
        if function_match:
            func_name = function_match.group(2)
            print(f"  -> Found function: {func_name}")
            print(f"  -> Current comment: {repr(current_comment)}")
            print(f"  -> Comment length: {len(current_comment.strip())}")
            print(f"  -> Should process: {bool(current_comment and len(current_comment.strip()) >= 10)}")

        print()

if __name__ == "__main__":
    # Test with our simple example
    with open("simple_ai_test.c", "r") as f:
        code = f.read()

    debug_comment_extraction(code)