"""
Functions related to the 'List' section.
"""

import collections
import re
from datetime import datetime, timezone
from typing import Dict, Optional

from git_py_stats.git_operations import run_git_command


def branch_tree() -> None:
    """
    Displays a visual graph of recent commits across all branches.
    """

    # Since can be hardcoded for now. It'll be based on the earliest commit
    # in the repo
    earliest_commit_date = run_git_command(['git', 'log', '--reverse', '--format=%ad'])
    if earliest_commit_date:
        # Take the first line as the earliest commit date
        first_commit_date = earliest_commit_date.split('\n')[0]
        since = f"--since='{first_commit_date}'"
    else:
        # If no commits, set since to an empty string
        since = ''

    # Until will be current system's date and time
    now = datetime.now(timezone.utc).astimezone()
    until_formatted = now.strftime('%a, %d %b %Y %H:%M:%S %Z')
    until = f"--until='{until_formatted}'"
    
    # Empty log options for now
    log_options = ''

    # Hardcoded limit
    limit=10

    # Format string for git --format so it gets interpreted correctly
    format_str = "--format=--+ Commit:  %h%n  | Date:    %aD (%ar)%n  | Message: %s %d%n  + Author:  %aN %n"

    # Perform final git command
    cmd = [
        'git', '-c', 'log.showSignature=false', 'log',
        '--use-mailmap',
        '--graph',
        '--abbrev-commit',
        since,
        until,
        '--decorate',
        format_str,
        '--all'
    ]

    output = run_git_command(cmd)

    # handle the head -n $((_limit*5)) portion
    if output:
        print('Branching tree view:\n')
        lines = output.split('\n')
        total_lines = limit * 5
        limited_lines = lines[:total_lines]

        for line in limited_lines:
            print(f"{line}")

        commit_count = sum(1 for line in limited_lines if line.strip().startswith('--+ Commit:'))
    else:
        print('No data available.')


def branches_by_date() -> None:
    """
    Lists branches sorted by the latest commit date.
    """

    # Original command:
    # git for-each-ref --sort=committerdate refs/heads/ \
    #     --format='[%(authordate:relative)] %(authorname) %(refname:short)' | cat -n
    # TODO: Wouldn't git log --pretty=format:'%ad' --date=short be better here?
    #       Then we could pipe it through sort, uniq -c, sort -nr, etc.
    #       Possibly feed back into the parent project
    format_str = "[%(authordate:relative)] %(authorname) %(refname:short)"
    cmd = ['git', 'for-each-ref', '--sort=committerdate', 'refs/heads/', f'--format={format_str}']

    output = run_git_command(cmd)
    if output:
        # Split the output into lines
        lines = output.split('\n')

        # Number the lines similar to 'cat -n'
        numbered_lines = [f"{idx + 1}  {line}" for idx, line in enumerate(lines)]

        # Output numbered lines
        print('All branches (sorted by most recent commit):\n')
        for line in numbered_lines:
            print(f'\t{line}')
    else:
        print('No commits found.')


def contributors() -> None:
    """
    Lists all contributors alphabetically.
    """

    # Hardcode variables
    # TODO: Make these configurable by the user
    earliest_commit_date = run_git_command(['git', 'log', '--reverse', '--format=%ad'])
    if earliest_commit_date:
        # Take the first line as the earliest commit date
        first_commit_date = earliest_commit_date.split('\n')[0]
        since = f"--since='{first_commit_date}'"
    else:
        # If no commits, set since to an empty string
        since = ''


    now = datetime.now(timezone.utc).astimezone()
    until_formatted = now.strftime('%a, %d %b %Y %H:%M:%S %Z')
    until = f"--until={until_formatted}"

    pathspec = ""  # No pathspec filtering

    merges = "--no-merges"
    limit = 50
    log_options = ""

    # Original command
    #     git -c log.showSignature=false log --use-mailmap $_merges "$_since" "$_until" \
    #         --format='%aN' $_log_options $_pathspec | sort -u | cat -n
    cmd = [
        'git',
        '-c', 'log.showSignature=false',
        'log',
        '--use-mailmap',
        merges,
        since,
        until,
        '--format=%aN',
        log_options
    ]

    # Append pathspec only if it's not empty. Currently hardcoded
    if pathspec:
        cmd.append(pathspec)

    # Remove any empty strings from the command to prevent Git misinterpretation
    # Breaks without this
    cmd = [arg for arg in cmd if arg]

    # Execute the Git command
    output = run_git_command(cmd)
    if output:
        print('All contributors (sorted by name):\n')
        # Split the output into individual author names
        authors = [line.strip() for line in output.split('\n') if line.strip()]

        # Remove duplicates by converting the list to a set
        unique_authors = set(authors)

        # Sort the unique authors alphabetically
        sorted_authors = sorted(unique_authors)

        # Apply the limit
        limited_authors = sorted_authors[:limit]

        # Number the authors similar to 'cat -n' and print
        numbered_authors = [f"{idx + 1}  {author}" for idx, author in enumerate(limited_authors)]
        for author in numbered_authors:
            print(f'\t{author}')
    else:
        print('No contributors found.')

def new_contributors(new_date: str) -> None:
    """
    Lists all new contributors to a repo since the specified date.

    Args:
        new_date (str): Cutoff date for being considered "new" in 'YYYY-MM-DD' format.

    Returns:
        None
    """

    # Attempt to handle date in YYYY-MM-DD format
    try:
        new_date_dt = datetime.strptime(new_date, '%Y-%m-%d')
        new_date_ts = int(new_date_dt.timestamp())
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return

    # User adjustable vars
    # TODO: Fix these later on
    merges = "--no-merges"
    since = ""  # Include the world for now
    until = ""
    log_options = ""
    pathspec = ""

    # Original command:
    # git -c log.showSignature=false log --use-mailmap $_merges \
    #     "$_since" "$_until" --format='%aE' $_log_options \
    #     $_pathspec | sort -u
    cmd = [
        'git',
        '-c', 'log.showSignature=false',
        'log',
        '--use-mailmap',
        merges,
        since,
        until,
        '--format=%aE|%at',
        log_options,
        pathspec
    ]

    # Remove any empty strings from the command to prevent Git misinterpretation
    # Needed when we start messing with datetime stuff
    cmd = [arg for arg in cmd if arg]

    output = run_git_command(cmd)
    if output:
        # Dictionary to store the earliest commit timestamp for each contributor
        contributors_dict = {}

        # Process each line of the Git output
        for line in output.split('\n'):
            try:
                email, timestamp = line.split('|')
                timestamp = int(timestamp)
                # If the contributor is not in the dictionary or the current timestamp is earlier
                if email not in contributors_dict or timestamp < contributors_dict[email]:
                    contributors_dict[email] = timestamp
            except ValueError:
                continue  # Skip lines that don't match format

        # List to hold new contributors
        new_contributors_list = []

        # Iterate over contributors to find those who are new since 'new_date'
        for email, first_commit_ts in contributors_dict.items():
            if first_commit_ts >= new_date_ts:
                # Retrieve the contributor's name
                # Original command:
                # git -c log.showSignature=false log --author="$c" \
                #     --reverse --use-mailmap $_merges "$_since" "$_until" \
                #     --format='%at' $_log_options $_pathspec | head -n 1
                name_cmd = [
                    'git',
                    '-c', 'log.showSignature=false',
                    'log',
                    '--use-mailmap',
                    '--format=%aN',
                    '--author=' + email,
                    '-n', '1'
                ]

                # Grab name + email if we can. Otherwise, just grab email
                name = run_git_command(name_cmd)
                if name:
                    new_contributors_list.append((name, email))
                else:
                    new_contributors_list.append(("", email))

        # Sort the list alphabetically by name to match the original
        # and print all of this out
        if new_contributors_list:
            print(f"New contributors since {new_date}:\n")
            sorted_new_contributors = sorted(new_contributors_list, key=lambda x: (x[0], x[1]))
            for idx, (name, email) in enumerate(sorted_new_contributors, 1):
                if name:
                    print(f"{name} <{email}>")
                else:
                    print(f"<{email}>")
        else:
            print("No new contributors found since the specified date.")
    else:
        print('No contributors found.')


def git_commits_per_author() -> None:
    """
    Shows the number of commits per author.
    """
    
    # Original authors command:
    # git -c log.showSignature=false log --use-mailmap \
    #     $_merges "$_since" "$_until" $_log_options \
    #     | grep -i Author: | cut -c9-

    # Original co-authors command:
    # git -c log.showSignature=false log --author="$c" \
    #     --reverse --use-mailmap $_merges "$_since" "$_until" \
    #     --format='%at' $_log_options $_pathspec | head -n 1
    cmd = [
        'git',
        '-c', 'log.showSignature=false',
        'log',
        '--use-mailmap',
        '--no-merges',
        '--pretty=format:Author:%aN <%aE>%n%b'
    ]

    output = run_git_command(cmd)
    if not output:
        print('No commits found.')
        return

    # Initialize commit count dictionary
    commit_counts = {}

    # Total commits (including co-authored commits)
    total_commits = 0

    # Regular expressions for parsing the author(s)
    author_regex = re.compile(r'^Author:\s*(.+)$', re.IGNORECASE)
    coauthor_regex = re.compile(r'^Co-Authored-by:\s*(.+)$', re.IGNORECASE)

    # Process each line of the git output
    for line in output.split('\n'):
        author_match = author_regex.match(line)
        coauthor_match = coauthor_regex.match(line)

        # Handle author
        if author_match:
            author_info = author_match.group(1).strip()
            author_name = extract_name(author_info)
            if author_name:
                commit_counts[author_name] = commit_counts.get(author_name, 0) + 1
                total_commits += 1

        # Handle co-author
        elif coauthor_match:
            coauthor_info = coauthor_match.group(1).strip()
            coauthor_name = extract_name(coauthor_info)
            if coauthor_name:
                commit_counts[coauthor_name] = commit_counts.get(coauthor_name, 0) + 1
                total_commits += 1

    # Handle case if nothing is found
    if total_commits == 0:
        print("No commits found.")
        return

    # Prepare a list of contributors with counts and percentages
    contributors_list = []
    for author, count in commit_counts.items():
        percentage = (count / total_commits) * 100
        contributors_list.append((count, author, percentage))

    # Sort the list by commit count in descending order
    contributors_list.sort(key=lambda x: x[0], reverse=True)

    # Fancy stuff for making the commit count alignment kosher
    max_count = contributors_list[0][0]
    count_width = len(str(max_count)) + 1  # Extra space for alignment

    # Print all the fun stuff. Finally...
    print('Git commits per author:\n')
    for count, author, percentage in contributors_list:
        print(f"\t{count:<{count_width}} {author:<30} {percentage:5.1f}%")


def extract_name(author_info: str) -> Optional[str]:
    """
    Extracts the author's name from the author information string.

    Args:
        author_info (str): The author information string (e.g., "Name <email@example.com>").

    Returns:
        Optional[str]: The extracted author name, or None if extraction fails.
    """

    # Use regex to extract the name before the email
    # Mostly a helper function for commits
    # NOTE: Should we move this into a separate file with other helper funcs?
    match = re.match(r'^([^<]+)', author_info)
    if match:
        return match.group(1).strip()
    else:
        return None


def git_commits_per_date() -> None:
    """
    Displays commits grouped by date.
    """
    
    # Customizable vars in the future
    mailmap = "--use-mailmap"
    merges = "--no-merges"
    #log_options
    #pathspec
    
    # Since can be hardcoded for now. It'll be based on the earliest commit
    # in the repo
    earliest_commit_date = run_git_command(['git', 'log', '--reverse', '--format=%ad'])
    if earliest_commit_date:
        # Take the first line as the earliest commit date
        first_commit_date = earliest_commit_date.split('\n')[0]
        since = f"--since='{first_commit_date}'"
    else:
        # If no commits, set since to an empty string
        since = ''

    # Until will be current system's date and time
    now = datetime.now(timezone.utc).astimezone()
    until_formatted = now.strftime('%a, %d %b %Y %H:%M:%S %Z')
    until = f"--until='{until_formatted}'"

    # Original command
    #  git -c log.showSignature=false log --use-mailmap $_merges "$_since" "$_until" \
    #      --date=short --format='%ad' $_log_options $_pathspec | sort | uniq -c
    cmd = ['git', '-c', 'log.showSignature=false', 'log', mailmap, merges,
           since, until, '--date=short', '--pretty=format:%ad']
    
    # Print out the commit count and date in YYYY-MM-DD format
    output = run_git_command(cmd)
    if output:
        dates = output.split('\n')
        counter = collections.Counter(dates)
        print("Git commits per date:\n")

        # Need to figure out the max count for width alignment purposes
        max_count = max(counter.values())
        count_width = len(str(max_count))

        # Can now display this to the terminal
        for date, count in sorted(counter.items()):
            print(f"\t{count:>{count_width}} {date}")
    else:
        print('No commits found.')


def git_commits_per_month() -> None:
    """
    Displays commits grouped by month.
    """
    
    cmd = ['git', 'log', '--date=format:%Y-%m', '--pretty=format:%cd']
    output = run_git_command(cmd)
    if output:
        months = output.split('\n')
        counter = collections.Counter(months)
        print("Git commits per month:")
        for month, count in sorted(counter.items()):
            print(f"{month} {count} commits")
    else:
        print('No commits found.')


def git_commits_per_year() -> None:
    """
    Displays commits grouped by year.
    """
    
    cmd = ['git', 'log', '--date=format:%Y', '--pretty=format:%cd']
    output = run_git_command(cmd)
    if output:
        years = output.split('\n')
        counter = collections.Counter(years)
        print("Git commits per year:")
        for year, count in sorted(counter.items()):
            print(f"{year}: {count} commits")
    else:
        print('No commits found.')


def git_commits_per_weekday(author: Optional[str] = None) -> None:
    """
    Shows commits grouped by weekday. If an author is provided, it shows
    commits grouped by weekday for that specific author.

    Args:
        author (Optional[str]): The author you want to show the commits grouped by.
                                If None, show for all authors.
    """
    
    # Build git cmd based on whether or not we have an author provided
    if author:
        cmd = ['git', 'log', '--author', author, '--pretty=format:%cd', '--date=raw']
    else:
        cmd = ['git', 'log', '--pretty=format:%cd', '--date=raw']

    # Run the git command and capture the output
    output = run_git_command(cmd)

    if output:
        try:
            timestamps = [int(line.split()[0]) for line in output.split('\n')]
            weekdays = [datetime.datetime.fromtimestamp(ts).strftime('%A') for ts in timestamps]
            counter = collections.Counter(weekdays)

            # Display commits per weekday
            if author:
                print(f"Git commits per weekday for author '{author}':")
            else:
                print("Git commits per weekday:")

            for day, count in counter.most_common():
                print(f"  {day}: {count} commits")

        except (ValueError, IndexError):
            print("Failed to parse timestamps.")
    else:
        if author:
            print(f'No commits found for author: {author}')
        else:
            print('No commits found.')


def git_commits_per_hour(author: Optional[str] = None) -> None:
    """
    Shows commits grouped by hour of the day. If an author is provided, 
    it shows commits grouped by hour for that specific author.

    Args:
        author (Optional[str]): The author to show the commits grouped by. 
                                If None, show for all authors.
    """
    
    # Build git cmd based on whether or not we have an author provided
    if author:
        cmd = ['git', 'log', '--author', author, '--pretty=format:%cd', '--date=raw']
    else:
        cmd = ['git', 'log', '--pretty=format:%cd', '--date=raw']

    # Run the git command and capture the output
    output = run_git_command(cmd)

    if output:
        try:
            timestamps = [int(line.split()[0]) for line in output.split('\n')]
            hours = [datetime.datetime.fromtimestamp(ts).hour for ts in timestamps]
            counter = collections.Counter(hours)

            # Display commits per hour
            if author:
                print(f"Git commits per hour for author '{author}':")
            else:
                print("Git commits per hour:")

            for hour, count in sorted(counter.items()):
                print(f"  {hour:02d}:00 - {count} commits")

        except (ValueError, IndexError):
            print("Failed to parse timestamps.")
    else:
        if author:
            print(f'No commits found for author: {author}')
        else:
            print('No commits found.')


def git_commits_per_timezone(author: Optional[str] = None) -> None:
    """
    Displays commits grouped by timezone. If an author is provided, it shows
    commits grouped by timezone for that specific author.

    Args:
        author (Optional[str]): The author to show the commits grouped by.
                                If None, show for all authors.
    """
    
    # Build git cmd based on whether or not we have an author provided
    if author:
        cmd = ['git', 'log', '--author', author, '--pretty=format:%cd', '--date=raw']
    else:
        cmd = ['git', 'log', '--pretty=format:%cd', '--date=raw']

    # Run the git command and capture the output
    output = run_git_command(cmd)

    if output:
        try:
            timezones = []
            for line in output.split('\n'):
                parts = line.split()
                if len(parts) == 2:  # Check if we have the format: "timestamp timezone"
                    _, timezone = parts
                    # Check if the second part is a valid timezone offset
                    if timezone.startswith(('+', '-')):
                        timezones.append(timezone)

            if timezones:
                counter = collections.Counter(timezones)
                if author:
                    print(f"Git commits per timezone for author '{author}':")
                else:
                    print("Git commits per timezone:")
                
                for tz, count in counter.most_common():
                    print(f"  {tz}: {count} commits")
            else:
                if author:
                    print(f"No valid timezones found for author: {author}")
                else:
                    print("No valid timezones found in commits.")
                    
        except IndexError:
            print("Failed to parse timezones.")
    else:
        if author:
            print(f'No commits found for author: {author}')
        else:
            print('No commits found.')
