from typing import assert_never
from spec_tagger.ai.prompt_construction import PromptConstructor, Prompt
from spec_tagger.spec_review.solution import Solution
from spec_tagger.spec_review.result_triage import ProblemType, SolutionMessages


def test_prompt_creation():
    solution = Solution(
        related_tag=None,
        location=None,
        item=None,
        git_commit_messages=None,
        git_diff=None,
        test_coverage=None,
        problem_type=ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED,
        solution_statement=[SolutionMessages.UNCOVERED_IMPLEMENTATION_CHANGE.value],
        problem_statement=[ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED.value],
        tag_coverage=None,
        ai_enabled=True,
        ai_usage_recommended=True,
        stdout=None,
    )
    solutions = [solution]
    constructor = PromptConstructor(
        solutions=solutions, git_global_context={"pr_title": ""}
    )
    prompts = constructor.construct_prompt_list()
    prompts[0].pretty_print_prompt()

    assert len(prompts) == 1
