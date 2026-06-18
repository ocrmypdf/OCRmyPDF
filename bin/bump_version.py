#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2017-2019 Joe Rickerby and contributors
# SPDX-License-Identifier: BSD-2-Clause

"""Bump the version number in all the right places."""

from __future__ import annotations

import glob
import os
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

import cyclopts
from packaging.version import InvalidVersion, Version

try:
    from github import Auth, Github, GithubException
except ImportError:
    Auth = None  # type: ignore
    Github = None  # type: ignore
    GithubException = Exception  # type: ignore

import ocrmypdf

config = [
    # file path, version find/replace format
    ("src/ocrmypdf/_version.py", '__version__ = "{}"'),
    ("pyproject.toml", 'version = "{}"'),
]

RED = "\u001b[31m"
GREEN = "\u001b[32m"
YELLOW = "\u001b[33m"
OFF = "\u001b[0m"

REPO_NAME = "ocrmypdf/OCRmyPDF"


def validate_release_notes(new_version: str) -> bool:
    """Check that the version appears in the release notes.

    Returns True if the version is found, False otherwise.
    """
    version_obj = Version(new_version)
    major = version_obj.major
    release_notes_path = Path(f"docs/releasenotes/version{major:02d}.md")

    if not release_notes_path.exists():
        print(f"{RED}error:{OFF} Release notes file not found: {release_notes_path}")
        return False

    content = release_notes_path.read_text(encoding="utf8")
    version_header = f"## v{new_version}"

    if version_header not in content:
        print(
            f"{RED}error:{OFF} Version v{new_version} not found in {release_notes_path}"
        )
        print(f"       Expected to find: {version_header}")
        return False

    print(f"{GREEN}Found v{new_version} in {release_notes_path}{OFF}")
    return True


def get_github_client():
    """Get an authenticated GitHub client."""
    if Github is None or Auth is None:
        print(f"{RED}error:{OFF} PyGithub is not installed")
        print("       Install with: pip install PyGithub")
        return None

    # Try GITHUB_TOKEN env var first
    token = os.environ.get("GITHUB_TOKEN")

    # Fall back to gh CLI
    if not token:
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                encoding="utf8",
                check=True,
            )
            token = result.stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            print(f"{RED}error:{OFF} No GitHub authentication found")
            print("       Set GITHUB_TOKEN env var or run: gh auth login")
            return None

    try:
        return Github(auth=Auth.Token(token))
    except GithubException as e:
        print(f"{RED}error:{OFF} Failed to authenticate with GitHub: {e}")
        return None


def wait_for_ci_completion(commit_sha: str, timeout_minutes: int = 30) -> bool:
    """Wait for CI to complete on the given commit.

    Returns True if CI passed, False otherwise.
    """
    gh = get_github_client()
    if gh is None:
        return False

    try:
        repo = gh.get_repo(REPO_NAME)
    except GithubException as e:
        print(f"{RED}error:{OFF} Failed to access repository: {e}")
        return False

    workflow_name = "Test and deploy"
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    poll_interval = 30  # seconds

    print(f"Waiting for CI workflow '{workflow_name}' on commit {commit_sha[:8]}...")

    # First, wait for the workflow run to appear
    run = None
    while time.time() - start_time < timeout_seconds:
        try:
            runs = repo.get_workflow_runs(head_sha=commit_sha)
            for r in runs:
                if r.name == workflow_name:
                    run = r
                    break
            if run:
                break
        except GithubException as e:
            print(f"{YELLOW}Warning:{OFF} Error checking workflow runs: {e}")

        elapsed = int(time.time() - start_time)
        print(f"  Waiting for workflow to start... ({elapsed}s)")
        time.sleep(poll_interval)

    if not run:
        print(
            f"{RED}error:{OFF} Workflow run not found within {timeout_minutes} minutes"
        )
        return False

    print(f"  Found workflow run #{run.run_number} (ID: {run.id})")

    # Now wait for the workflow to complete
    while time.time() - start_time < timeout_seconds:
        try:
            run = repo.get_workflow_run(run.id)  # Refresh the run
        except GithubException as e:
            print(f"{YELLOW}Warning:{OFF} Error refreshing workflow run: {e}")
            time.sleep(poll_interval)
            continue

        status = run.status
        conclusion = run.conclusion

        elapsed = int(time.time() - start_time)
        if status == "completed":
            if conclusion == "success":
                print(f"{GREEN}CI passed!{OFF} (took {elapsed}s)")
                return True
            else:
                print(f"{RED}CI failed!{OFF} Conclusion: {conclusion}")
                print(f"  View details: {run.html_url}")
                return False
        else:
            print(f"  Status: {status} ({elapsed}s elapsed)")
            time.sleep(poll_interval)

    print(f"{RED}error:{OFF} CI did not complete within {timeout_minutes} minutes")
    return False


def push_and_wait_for_ci(branch: str) -> bool:
    """Push to remote and wait for CI tests to pass."""
    print("Pushing to GitHub...")

    push_result = subprocess.run(
        ["git", "push", "origin", branch],
        capture_output=True,
        encoding="utf8",
    )

    if push_result.returncode != 0:
        print(f"{RED}error:{OFF} Failed to push: {push_result.stderr}")
        return False

    # Get the commit SHA we just pushed
    sha_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        encoding="utf8",
        check=True,
    )
    commit_sha = sha_result.stdout.strip()

    print(f"Pushed commit {commit_sha[:8]}")

    return wait_for_ci_completion(commit_sha)


def push_tag(tag: str) -> bool:
    """Push the tag to trigger release workflow."""
    print(f"Pushing tag {tag} to trigger release...")

    result = subprocess.run(
        ["git", "push", "origin", tag],
        capture_output=True,
        encoding="utf8",
    )

    if result.returncode != 0:
        print(f"{RED}error:{OFF} Failed to push tag: {result.stderr}")
        return False

    print(f"{GREEN}Tag {tag} pushed successfully!{OFF}")
    return True


def bump_version() -> None:
    """Bump the version number in all the right places."""
    current_version = ocrmypdf.__version__  # type: ignore
    try:
        commit_date_str = subprocess.run(
            [
                "git",
                "show",
                "--no-patch",
                "--pretty=format:%ci",
                f"v{current_version}^{{commit}}",
            ],
            check=True,
            capture_output=True,
            encoding="utf8",
        ).stdout
        cd_date, cd_time, cd_tz = commit_date_str.split(" ")

        url_opts = urllib.parse.urlencode(
            {"q": f"is:pr merged:>{cd_date}T{cd_time}{cd_tz}"}
        )
        url = f"https://github.com/{REPO_NAME}/pulls?{url_opts}"

        print(f"PRs merged since last release:\n  {url}")
        print()
    except subprocess.CalledProcessError as e:
        print(e)
        print("Failed to get previous version tag information.")
        print("Is the virtual environment active?")
        sys.exit(1)

    git_changes_result = subprocess.run(["git diff-index --quiet HEAD --"], shell=True)
    repo_has_uncommitted_changes = git_changes_result.returncode != 0

    if repo_has_uncommitted_changes:
        print("error: Uncommitted changes detected.")
        sys.exit(1)

    # fmt: off
    print(              'Current version:', current_version)
    new_version = input('    New version: ').strip()
    # fmt: on

    try:
        Version(new_version)
    except InvalidVersion:
        print("error: This version doesn't conform to PEP440")
        print("       https://www.python.org/dev/peps/pep-0440/")
        sys.exit(1)

    # Validate release notes contain this version
    if not validate_release_notes(new_version):
        print()
        print("Please add release notes for this version before proceeding.")
        print(f"Edit: docs/releasenotes/version{Version(new_version).major:02d}.md")
        sys.exit(1)

    actions = []

    for path_pattern, version_pattern in config:
        paths = [Path(p) for p in glob.glob(path_pattern)]

        if not paths:
            print(f"error: Pattern {path_pattern} didn't match any files")
            sys.exit(1)

        find_pattern = version_pattern.format(current_version)
        replace_pattern = version_pattern.format(new_version)
        found_at_least_one_file_needing_update = False

        for path in paths:
            contents = path.read_text(encoding="utf8")
            if find_pattern in contents:
                found_at_least_one_file_needing_update = True
                actions.append(
                    (
                        path,
                        find_pattern,
                        replace_pattern,
                    )
                )

        if not found_at_least_one_file_needing_update:
            print(
                f'''error: Didn't find any occurrences of "{find_pattern}" in "{path_pattern}"'''
            )
            sys.exit(1)

    print()
    print("Here's the plan:")
    print()

    for action in actions:
        path, find, replace = action
        print(f"{path}  {RED}{find}{OFF} → {GREEN}{replace}{OFF}")

    print(f"Then commit, and tag as v{new_version}")

    answer = input("Proceed? [y/N] ").strip()

    if answer != "y":
        print("Aborted")
        sys.exit(1)

    for path, find, replace in actions:
        contents = path.read_text(encoding="utf8")
        contents = contents.replace(find, replace)
        path.write_text(contents, encoding="utf8")

    print("Files updated.")
    print()

    while input('Type "done" to continue: ').strip().lower() != "done":
        pass

    subprocess.run(
        [
            "git",
            "commit",
            "--all",
            f"--message=Bump version: v{new_version}",
        ],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "tag",
            "--annotate",
            f"--message=v{new_version}",
            f"v{new_version}",
        ],
        check=True,
    )

    print("Commit and tag created locally.")
    print()

    # Get current branch
    branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        encoding="utf8",
        check=True,
    )
    branch = branch_result.stdout.strip()

    # Push commit and wait for CI
    if not push_and_wait_for_ci(branch):
        print()
        print(f"{RED}CI failed. The tag was NOT pushed.{OFF}")
        print("Fix the issues, then manually push the tag:")
        print(f"    git push origin v{new_version}")
        sys.exit(1)

    # Push tag to trigger release
    if not push_tag(f"v{new_version}"):
        print(f"{RED}Failed to push tag.{OFF} Push manually:")
        print(f"    git push origin v{new_version}")
        sys.exit(1)

    print()
    print(f"{GREEN}Done! Release workflow has been triggered.{OFF}")
    print()

    release_url = f"https://github.com/{REPO_NAME}/releases/tag/v{new_version}"
    print("Monitor the release at:")
    print(f"    {release_url}")


if __name__ == "__main__":
    os.chdir(Path(__file__).parent.parent.resolve())
    cyclopts.run(bump_version)
