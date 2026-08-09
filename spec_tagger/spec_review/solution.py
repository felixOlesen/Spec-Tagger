from enum import Enum


class Solution:
    def __init__(
        self,
        related_tag: str | None,
        location: str | None,
        item: str | None,
        git_commit_messages: list[str] | None,
        git_diff: str | None,
        test_coverage: dict | None,
        problem_type: Enum | None,
        solution_statement: list[str],
        problem_statement: list[str],
        tag_coverage: dict | None = None,
        ai_enabled: bool = False,
        ai_usage_recommended: bool = False,
    ):
        self.related_tag = related_tag
        self.location = location
        self.problem_type = problem_type
        self.item = item
        self.solution_statement = solution_statement
        self.problem_statement = problem_statement
        self.git_commit_messages = git_commit_messages
        self.git_diff = git_diff
        self.test_coverage = test_coverage
        self.tag_coverage = tag_coverage
        self.ai_enabled = ai_enabled
        self.ai_response_text = None
        self.ai_usage_recommended = ai_usage_recommended
