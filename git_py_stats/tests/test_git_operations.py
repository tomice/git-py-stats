import unittest
from unittest.mock import patch, MagicMock
import subprocess

from git_py_stats.git_operations import run_git_command, check_git_repository


class TestGitOperations(unittest.TestCase):
    """
    Unit test class for testing git_operations.
    """

    @patch("subprocess.run")
    def test_run_git_command_success(self, mock_subprocess_run):
        """
        Test run_git_command with a successful git command.
        """
        # Mock the subprocess.run to return a successful result
        mock_result = MagicMock()
        mock_result.stdout = "git version 2.30.0\n"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        output = run_git_command(["git", "--version"])
        self.assertEqual(output, "git version 2.30.0")

        mock_subprocess_run.assert_called_once_with(
            ["git", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
            errors="surrogateescape",
        )

    @patch("subprocess.run")
    def test_run_git_command_failure(self, mock_subprocess_run):
        """
        Test run_git_command with a failing git command.
        """
        # Mock the subprocess.run to raise a CalledProcessError
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["git", "invalidcommand"],
            stderr="git: 'invalidcommand' is not a git command.",
        )

        output = run_git_command(["git", "invalidcommand"])
        self.assertIsNone(output)

        mock_subprocess_run.assert_called_once_with(
            ["git", "invalidcommand"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
            errors="surrogateescape",
        )

    @patch("subprocess.run")
    def test_run_git_command_no_output(self, mock_subprocess_run):
        """
        Test run_git_command with a command that produces no output.
        """
        # Mock the subprocess.run to return empty stdout
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        output = run_git_command(["git", "status"])
        self.assertEqual(output, "")

        mock_subprocess_run.assert_called_once_with(
            ["git", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
            errors="surrogateescape",
        )

    @patch("subprocess.run")
    def test_run_git_command_exception(self, mock_subprocess_run):
        """
        Test run_git_command when subprocess.run raises an exception.
        """
        # Mock the subprocess.run to raise an OSError
        mock_subprocess_run.side_effect = OSError("No such file or directory")

        output = run_git_command(["git", "status"])
        self.assertIsNone(output)

        mock_subprocess_run.assert_called_once_with(
            ["git", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            encoding="utf-8",
            errors="surrogateescape",
        )

    def test_run_git_command_empty_command(self):
        """
        Test run_git_command with an empty command list.
        """
        output = run_git_command([])
        self.assertIsNone(output)

    @patch("git_py_stats.git_operations.run_git_command")
    def test_check_git_repository_true(self, mock_run_git_command):
        """
        Test check_git_repository when inside a git repository.
        """
        mock_run_git_command.return_value = "true"

        result = check_git_repository()
        self.assertTrue(result)

        mock_run_git_command.assert_called_once_with(["git", "rev-parse", "--is-inside-work-tree"])

    @patch("git_py_stats.git_operations.run_git_command")
    def test_check_git_repository_false(self, mock_run_git_command):
        """
        Test check_git_repository when not inside a git repository.
        """
        mock_run_git_command.return_value = "false"

        result = check_git_repository()
        self.assertFalse(result)

        mock_run_git_command.assert_called_once_with(["git", "rev-parse", "--is-inside-work-tree"])

    @patch("git_py_stats.git_operations.run_git_command")
    def test_check_git_repository_none(self, mock_run_git_command):
        """
        Test check_git_repository when run_git_command returns None.
        """
        mock_run_git_command.return_value = None

        result = check_git_repository()
        self.assertFalse(result)

        mock_run_git_command.assert_called_once_with(["git", "rev-parse", "--is-inside-work-tree"])

    @patch("git_py_stats.git_operations.run_git_command")
    def test_check_git_repository_unexpected_output(self, mock_run_git_command):
        """
        Test check_git_repository with unexpected output from run_git_command.
        """
        mock_run_git_command.return_value = "unexpected"

        result = check_git_repository()
        self.assertFalse(result)

        mock_run_git_command.assert_called_once_with(["git", "rev-parse", "--is-inside-work-tree"])

    @patch("git_py_stats.git_operations.run_git_command")
    def test_check_git_repository_error_message(self, mock_run_git_command):
        """
        Test that check_git_repository prints error message when not in a git repo.
        """
        mock_run_git_command.return_value = "false"

        with patch("builtins.print") as mock_print:
            result = check_git_repository()
            self.assertFalse(result)
            mock_print.assert_called_once_with("This script must be run inside a git repository.")

    @patch("git_py_stats.git_operations.run_git_command")
    def test_check_git_repository_no_output(self, mock_run_git_command):
        """
        Test check_git_repository when run_git_command returns empty string.
        """
        mock_run_git_command.return_value = ""

        result = check_git_repository()
        self.assertFalse(result)

        mock_run_git_command.assert_called_once_with(["git", "rev-parse", "--is-inside-work-tree"])


if __name__ == "__main__":
    unittest.main()
