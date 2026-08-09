from spec_tagger.spec_review.result_triage import ProblemType


class Solution:
    def __init__(
        self,
        related_tag: str,
        tag_location: str,
        item: str,
        git_commit_messages: list[str],
        git_diff: str,
        test_coverage,
        problem_type: ProblemType,
        solution_statement: list[str],
        problem_statement: list[str],
        tag_coverage=None,
        ai_enabled: bool = False,
        ai_usage_recommended: bool = False,
    ):
        self.related_tag = related_tag
        self.tag_location = tag_location
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
