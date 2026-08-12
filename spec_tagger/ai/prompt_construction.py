from spec_tagger.spec_review.solution import Solution
from spec_tagger.ai.schemas import (
    FailureDiagnostic,
    SemanticDrift,
    TagSuggestion,
    UncoveredChange,
)
from enum import Enum
from spec_tagger.spec_review.result_triage import ProblemType
import json


class SystemPrompt(Enum):
    BASE_PROMPT = "Please read through the instructions and provided information carefully, your over-arching goal is to ensure that the documentation provided in the specification is consistent with clear in how it describes the behaviour of the implementation. Some information may not always be available but try to make an educated guess about how the software works and be very clear when external help is needed such as a human reviewer. Your specific task will be covered here:"
    SEMANTIC_DRIFT = "With the information that is provided in this prompt, your job is to try and identify any semantic drift that might be happening between the tag-linked specification entry and the code of the tests that have changed recently, and are therefore at risk of drifting form each other."
    FAILURE_DIAGNOSTIC = "With the information provided to you in this promp, try to figure out what has gone wrong and caused the test to fail or error out."
    TAG_SUGGESTION = "In this case, your goal is to try and provide suggestions for how new un-tagged tests and files can be tagged and maybe a short description or snapshot of what the spec entry could look like if one doesn't already exist."
    INVALID_TAG = "Invalid Tag system prompt"
    UNCOVERED_IMPLEMENTATION_CHANGE = "Please go through the implementation changes in the git diffs and commit messages to try and understand and produce a example specs and tests to cover these new, completely un-covered changes, it's ok if you don't generate an entirely complete solution, just point the human reviewer in the right direction."


class Prompt:
    def __init__(self, schema, system_prompt, context_evidence):
        self.schema = schema
        self.system_prompt = system_prompt
        self.context_evidence = context_evidence


class PromptConstructor:
    def __init__(self, solutions: list[Solution], git_global_context) -> None:
        self.solutions = solutions
        self.git_global_context = git_global_context
        self.prompts = []
        self.semantic_drift_solutions = []
        self.failure_diagnostic_solutions = []
        self.tag_suggestion_solutions = []
        self.invalid_tag_solutions = []
        self.uncovered_implementation_solutions = []
        if self.solutions:
            for solution in self.solutions:
                match solution.problem_type:
                    case ProblemType.PASSED_BUT_CHANGED:
                        self.semantic_drift_solutions.append(solution)
                    case ProblemType.TEST_FAILURE:
                        self.failure_diagnostic_solutions.append(solution)
                    case ProblemType.TEST_ERROR:
                        self.failure_diagnostic_solutions.append(solution)
                    case ProblemType.MISSED_TEST:
                        self.tag_suggestion_solutions.append(solution)
                    case ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED:
                        self.uncovered_implementation_solutions.append(solution)
        else:
            print(
                "Warning, no tag suggestions given on prompt constructor initialisation"
            )

    def construct_prompt_list(self) -> list[Prompt]:
        if self.uncovered_implementation_solutions:
            for solution in self.uncovered_implementation_solutions:
                if not solution.ai_usage_recommended:
                    continue
                system_prompt = self._build_system_prompt(
                    SystemPrompt.UNCOVERED_IMPLEMENTATION_CHANGE
                )
                prompt_evidence = self._build_contextual_evidence(solution=solution)
                prompt = Prompt(UncoveredChange, system_prompt, prompt_evidence)
                self.prompts.append(prompt)

        if self.semantic_drift_solutions:
            for solution in self.semantic_drift_solutions:
                if not solution.ai_usage_recommended:
                    continue
                system_prompt = self._build_system_prompt(SystemPrompt.SEMANTIC_DRIFT)
                prompt_evidence = self._build_contextual_evidence(solution=solution)
                prompt = Prompt(SemanticDrift, system_prompt, prompt_evidence)
                self.prompts.append(prompt)
        if self.failure_diagnostic_solutions:
            for solution in self.failure_diagnostic_solutions:
                if not solution.ai_usage_recommended:
                    continue
                system_prompt = self._build_system_prompt(
                    SystemPrompt.FAILURE_DIAGNOSTIC
                )
                prompt_evidence = self._build_contextual_evidence(solution=solution)
                prompt = Prompt(FailureDiagnostic, system_prompt, prompt_evidence)
                self.prompts.append(prompt)
        if self.tag_suggestion_solutions:
            for solution in self.tag_suggestion_solutions:
                if not solution.ai_usage_recommended:
                    continue
                system_prompt = self._build_system_prompt(SystemPrompt.TAG_SUGGESTION)
                prompt_evidence = self._build_contextual_evidence(solution=solution)
                prompt = Prompt(TagSuggestion, system_prompt, prompt_evidence)
                self.prompts.append(prompt)

        return self.prompts

    def _build_contextual_evidence(self, solution: Solution) -> str:
        tag_and_background = f"The tag that is in question is: {solution.related_tag}. Here is a general statement of the problem: {solution.problem_statement}, and here is a statement describing how this problem would generally be diagnosed and solved: {solution.solution_statement}."
        git_pr_info = ""
        if self.git_global_context["pr_title"]:
            git_pr_info = f"The github PR Title: {self.git_global_context['pr_title']} and the pull-request description is: {self.git_global_context['pr_description']}"
        git_commit_and_diff = f"Here are the commit messages that cover changes made to relevant files: {solution.git_commit_messages}\n Here are the git diffs of the the changed files relevant to the tag: {solution.git_diff}\n"
        coverage_info = ""
        if solution.test_coverage:
            coverage_info = f"Here is the test coverage information relevant to the tag to understand what files in the implementation code have been covered by the connected test code: {json.dumps(solution.test_coverage)}"
        stdout = ""
        if solution.stdout:
            stdout = f"Here is the stdout of the tests that have run: {solution.stdout}"
        evidence_str = f"{tag_and_background}\n{git_pr_info}\n{git_commit_and_diff}\n{coverage_info}\n{stdout}"
        return evidence_str

    def _build_system_prompt(self, system_prompt: SystemPrompt) -> str:
        return f"{SystemPrompt.BASE_PROMPT.value} {system_prompt.value}"
