"""
This module provides functionality to automatically fix code issues
identified by a code reliability scanner using the 'aider' tool.
"""

import json
import argparse
import os
import subprocess

def generate_fix_request(issue_type):
    """Generate a fix request message based on the issue type."""
    fix_requests = {
        "bare_except": (
            "Refactor all try-except blocks to catch specific exceptions "
            "instead of using bare except clauses. Follow PEP 8 guidelines "
            "for exception handling."
        ),
        "broad_except": (
            "Refactor all try-except blocks to catch more specific exceptions "
            "instead of broad exception types like Exception or BaseException. "
            "Follow PEP 8 guidelines for exception handling."
        ),
        "empty_except": (
            "Review and update all empty except blocks to handle exceptions "
            "appropriately. Consider logging or re-raising exceptions if necessary."
        ),
        "no_finally": (
            "Add finally clauses to try-except blocks where appropriate for "
            "cleanup operations. Follow PEP 8 guidelines for exception handling."
        ),
        "reraise_without_from": (
            "Update exception re-raising to use the 'from' keyword to preserve "
            "the original traceback. Follow PEP 8 guidelines for exception handling."
        ),
        "no_logging": (
            "Add appropriate logging to all except blocks for debugging purposes. "
            "Use the logging module and follow best practices for log levels and messages."
        ),
    }
    return fix_requests.get(
        issue_type,
        (
            f"Review and improve the code related to {issue_type}. "
            "Follow PEP 8 and best practices for Python programming."
        ),
    )
def run_aider(file_path, fix_request, repo_path):
    """
    Run the 'aider' tool to apply fixes to the specified file.

    Args:
        file_path (str): The path to the file to be fixed.
        fix_request (str): The fix request message.
        repo_path (str): The path to the repository.
    """
    aider_command = [
        'aider',
        '--message', f"Fix: {fix_request}",
        file_path
    ]
    with subprocess.Popen(
        aider_command,
        cwd=repo_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    ) as process:
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                if "?" in output:  # This is likely a question
                    user_input = input("Enter your response: ")
                    process.stdin.write(user_input + '\n')
                    process.stdin.flush()
        stderr = process.stderr.read()
        if stderr:
            print("Errors:")
            print(stderr)
        return process.returncode

def process_issues_by_file(issues_by_file, fix_request, repo_path, filename):
    """
    Process and fix issues grouped by file.

    Args:
        issues_by_file (dict): A dictionary mapping file paths to lists of issues.
        fix_request (str): The fix request message.
        repo_path (str): The path to the repository.
        filename (str): Specific filename to process, if provided.
    """
    for file_path, file_issues in issues_by_file.items():
        if filename and file_path != os.path.join(repo_path, filename):
            continue
        print(f"\nProcessing issues in {file_path}:")
        print(f"Number of occurrences: {len(file_issues)}")
        # Run aider to fix the issues
        print("Running aider to fix the issues...")
        return_code = run_aider(file_path, fix_request, repo_path)
        if return_code == 0:
            print("Aider completed successfully.")
        else:
            print(f"Aider encountered an error (return code: {return_code}).")

def main(issues_file):
    """
    Main function to process issues from a JSON file and apply fixes.

    Args:
        issues_file (str): The path to the JSON file containing the issues.
    """
    with open(issues_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        grouped_issues = data['grouped_issues']
        repo_path = data['repo_path']
        original_commit = data['original_commit']
        filename = data.get('filename')

    print(f"Original commit before fixes: {original_commit}")
    print("You can use this commit SHA to reset the repository if needed.")
    print(f"To reset, run: git reset --hard {original_commit}")

    print("\nProcessing issues:\n")
    unknown_issues = []

    for issue_type, issues in grouped_issues.items():
        print(f"\nIssue type: {issue_type}")
        print(f"Number of occurrences: {len(issues)}")
        if issue_type == "unknown":
            unknown_issues.extend(issues)
            print("Skipping unknown issue type.")
            continue

        # Generate a general fix request for the issue type
        fix_request = generate_fix_request(issue_type)

        # Group issues by file
        issues_by_file = {}
        for issue in issues:
            if issue['file'] not in issues_by_file:
                issues_by_file[issue['file']] = []
            issues_by_file[issue['file']].append(issue)

        # Process issues by file
        process_issues_by_file(issues_by_file, fix_request, repo_path, filename)

        print("------------------------")

    print("\nAll issues have been processed.")
    if unknown_issues:
        print(f"\nWARNING: {len(unknown_issues)} unknown issues were skipped:")
        for issue in unknown_issues:
            print(f"  - File: {issue['file']}, Line: {issue['line']}")
    print("\nPlease review the changes using your preferred Git tool (e.g., GitHub Desktop, git command-line).")
    print("You can then decide to keep, modify, or revert the changes as needed.")
    print("\nTo revert all changes and return to the original state, run:")
    print(f"git reset --hard {original_commit}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Auto-fix issues found by the CodeReliabilityScanner using aider"
    )
    parser.add_argument("issues_file", help="Path to the JSON file containing the issues")
    parser.add_argument("--filename", help="Specific Python file to fix (relative to repo root)")
    args = parser.parse_args()

    main(args.issues_file)
