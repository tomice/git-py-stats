"""
General git operation functions
"""

import subprocess
from typing import List, Optional


def run_git_command(cmd: List[str]) -> Optional[str]:
    """
    Runs a git command and returns the output.

    Args:
        cmd List[str]: A list of strings representing the git command and its arguments.

    Returns:
        The standard output from the git command if successful, None otherwise.
    """
    if not cmd:
        print("Error: Command list is empty!")
        return None
    try:
        # We enforce utf-8 encoding and use surrogateescape to handle non-ascii characters
        # that may be present in git history (e.g. in author names or commit messages)
        # as recommended by PEP 383 for system interfaces.
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
            errors="surrogateescape",
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None
    # Grab any other possible exception
    except Exception as e:
        print(f"Unexpected error running command: {e}")
        return None


def check_git_repository() -> bool:
    """
    Checks if the current directory is within a git repository.

    Args:
        None

    Returns:
        True if inside a git repository, False otherwise.
    """
    cmd = ["git", "rev-parse", "--is-inside-work-tree"]
    result = run_git_command(cmd)
    if result == "true":
        return True
    else:
        print("This script must be run inside a git repository.")
        return False
