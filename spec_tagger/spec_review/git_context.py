import json
import os
import subprocess
from pathlib import Path


def _git(*args: str) -> str:
    """Run a git command, returning the stdout of the command. Empty string returned on failure."""
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def _event_payload() -> dict:
    """The full webhook event that triggered the workflow.
    Actions writes it to a file and puts the path in GITHUB_EVENT_PATH. This is
    where the PR title/body/author are located.
    """
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text())


def collect_context(base: str | None = None, head: str | None = None):
    """Collect diff, commit messages, and PR metadata.
    works in CI and locally (falls back to git alone when not running in CI pipeline).
    """
    event = _event_payload()
    pr = event.get("pull_request", {})
    if not base:
        base = (
            pr.get("base", {}).get("sha")
            or os.environ.get("GITHUB_BASE_REF")
            or "origin/main"
        )
    if not head:
        head = pr.get("head", {}).get("sha") or os.environ.get("GITHUB_SHA") or "HEAD"

    diff_range = f"{base}...{head}"

    return {
        "base": base,
        "head": head,
        "diff": _git("diff", diff_range),
        "changed_files": _git("diff", "--name-only", diff_range).splitlines(),
        "commit_messages": _git("log", "--format=%s%n%n%b%x00", diff_range).split(
            "\x00"
        ),
        "pr_title": pr.get("title"),
        "pr_description": pr.get("body"),
        "pr_number": pr.get("number"),
        "author": pr.get("user", {}).get("login") or _git("log", "-1", "--format=%an"),
        "branch": os.environ.get("GITHUB_HEAD_REF")
        or _git("rev-parse", "--abbrev-ref", "HEAD"),
        "repo": os.environ.get("GITHUB_REPOSITORY"),
    }


def diff_for_file(path: str, base: str, head: str) -> str:
    """Diff for a specific file, saves sending an entire diff for smaller errors."""
    return _git("diff", f"{base}...{head}", "--", path)


def commits_for_file(path: str, base: str, head: str) -> list[str]:
    """Commit messages that touched `path` in the given range."""
    out = _git("log", f"{base}...{head}", "--format=%s%n%n%b%x00", "--", path)
    return [m.strip() for m in out.split("\x00") if m.strip()]
