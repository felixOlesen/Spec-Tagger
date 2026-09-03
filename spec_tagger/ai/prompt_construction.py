from spec_tagger.spec_review.solution import Solution
from spec_tagger.ai.schemas import (
    SemanticDrift,
    UncoveredChange,
)
from enum import Enum
from spec_tagger.spec_review.result_triage import ProblemType
import json


class SystemPrompt(Enum):
    BASE_PROMPT = "Please read through the instructions and provided information carefully, your over-arching goal is to ensure that the documentation provided in the specification is consistent with clear in how it describes the behaviour of the implementation. Some information may not always be available but try to make an educated guess about how the software works and be very clear when external help is needed such as a human reviewer. Your specific task will be covered here:"
    SEMANTIC_DRIFT = "With the information that is provided in this prompt, your job is to try and identify any semantic drift that might be happening between the tag-linked specification entry and the code of the tests that have changed recently, and are therefore at risk of drifting form each other."
    UNCOVERED_IMPLEMENTATION_CHANGE = "Please go through the implementation changes in the git diffs and commit messages to try and understand and produce a example specs and tests to cover these new, completely un-covered changes, it's ok if you don't generate an entirely complete solution, just point the human reviewer in the right direction."


class Prompt:
    def __init__(self, schema, system_prompt, context_evidence, problem_type):
        self.schema = schema
        self.system_prompt = system_prompt
        self.context_evidence = context_evidence
        self.problem_type = problem_type

    def pretty_print_prompt(self):
        print("------------------------------Prompt------------------------------")
        print(f"\nSchema Used:\n{self.schema}\n")
        print(f"\nSystem Prompt Used:\n{self.system_prompt}\n")
        if len(self.context_evidence) > 2500:
            print(f"\nContext Evidence:\n{self.context_evidence[:2500]}...\n")
        else:
            print(f"\nContext Evidence:\n{self.context_evidence}\n")
        print(f"\nProblem Type:\n{self.problem_type}\n")


class PromptConstructor:
    def __init__(self, solutions: list[Solution], git_global_context) -> None:
        self.solutions = solutions
        self.git_global_context = git_global_context
        self.prompts = []
        self.semantic_drift_solutions = []
        self.uncovered_implementation_solutions = []
        if self.solutions:
            for solution in self.solutions:
                match solution.problem_type:
                    case ProblemType.PASSED_BUT_CHANGED:
                        self.semantic_drift_solutions.append(solution)
                    case ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED:
                        self.uncovered_implementation_solutions.append(solution)
        else:
            print(
                "Warning, ai is enabled but no changes have been discovered under the conditons necessary for semantic drift checks or uncovered implementation review."
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
                prompt = Prompt(
                    UncoveredChange,
                    system_prompt,
                    prompt_evidence,
                    solution.problem_type,
                )
                self.prompts.append(prompt)

        if self.semantic_drift_solutions:
            for solution in self.semantic_drift_solutions:
                if not solution.ai_usage_recommended:
                    continue
                system_prompt = self._build_system_prompt(SystemPrompt.SEMANTIC_DRIFT)
                prompt_evidence = self._build_contextual_evidence(solution=solution)
                prompt = Prompt(
                    SemanticDrift, system_prompt, prompt_evidence, solution.problem_type
                )
                self.prompts.append(prompt)

        return self.prompts

    def _build_contextual_evidence(self, solution: Solution) -> str:
        tag_and_background = ""
        if solution.related_tag:
            tag_and_background += (
                f"The tag that is in question is: {solution.related_tag}."
            )
        tag_and_background += f"Here is a general statement of the problem: {solution.problem_statement}, and here is a statement describing how this problem would generally be diagnosed and solved: {solution.solution_statement}."

        git_pr_info = ""
        if self.git_global_context["pr_title"]:
            git_pr_info = f"The github PR Title: {self.git_global_context['pr_title']} and the pull-request description is: {self.git_global_context['pr_description']}"

        git_commit_and_diff = ""
        if solution.git_commit_messages:
            git_commit_and_diff += f"Here are the commit messages that cover changes made to relevant files: {solution.git_commit_messages}\n"

        if solution.git_diff:
            git_commit_and_diff = f"Here are the git diffs of the the changed files relevant to the tag: {solution.git_diff}\n"

        spec_and_test_items = ""
        if solution.item:
            spec_and_test_items = f"Here is more relevant information to this task of either a spec entry or test block for reference to the task: {solution.item}"

        stdout = ""
        if solution.stdout:
            stdout = f"Here is the stdout of the tests that have run: {solution.stdout}"

        evidence_str = f"{tag_and_background}\n{git_pr_info}\n{git_commit_and_diff}\n{spec_and_test_items}\n{stdout}"

        return evidence_str

    def _build_system_prompt(self, system_prompt: SystemPrompt) -> str:
        return f"{SystemPrompt.BASE_PROMPT.value} {system_prompt.value}"
