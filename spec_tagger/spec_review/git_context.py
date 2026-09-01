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


def collect_context(base: str | None = None, head: str | None = None) -> dict:
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


def changed_lines_from_diff(base: str, head: str) -> dict[str, set[int]]:
    """file -> set of line numbers changed on the NEW side."""

    import re

    HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    diff_text = _git("diff", "-U0", f"{base}...{head}")
    out, current, new_line = {}, None, 0
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            out.setdefault(current, set())
        elif m := HUNK.match(line):
            new_line = int(m.group(1))
        elif current and line.startswith("+") and not line.startswith("+++"):
            out[current].add(new_line)
            new_line += 1
        elif current and not line.startswith("-"):
            new_line += 1
    return out


def get_git_log_for_list_of_lines(
    file: str, lines: set[int], base: str, head: str, message_only: bool = False
) -> list:
    runs = _get_contiguous_runs(lines)
    if not runs:
        return []

    args = []
    if message_only:
        for start, end in runs:
            args += ["-s", f"{start},{end}:{file}"]
    else:
        for start, end in runs:
            args += ["-L", f"{start},{end}:{file}"]

    out = _git("log", f"{base}...{head}", *args, "--format=%s%n%n%b%x00")

    return [m.strip() for m in out.split("\x00") if m.strip()]


def _get_contiguous_runs(lines: set[int], tolerance: int = 2) -> list[tuple[int, int]]:
    """Group line numbers into (start, end) runs.
    `tolerance` merges runs separated by small gaps — a 1-2 line gap is usually
    an unchanged brace or blank line inside one logical change, and merging
    avoids emitting dozens of single-line ranges."""
    if not lines:
        return []
    ordered = sorted(lines)
    runs, start, prev = [], ordered[0], ordered[0]
    for n in ordered[1:]:
        if n - prev <= tolerance + 1:
            prev = n
        else:
            runs.append((start, prev))
            start = prev = n
    runs.append((start, prev))
    return runs
