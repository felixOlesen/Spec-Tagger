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
        stdout: str | None = None,
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
        self.stdout = stdout

    def construct_non_ai_response(self):
        problem_found = f"###{self.problem_type} has been found."
        problems = ""
        for problem in self.problem_statement:
            problems += f"\n- {problem}"

        solutions = ""
        for solution in self.solution_statement:
            solutions += f"\n- {solution}"

        solution_problem_descr = f"Here is the description of the problem/s: {problems}.\n\nHere is also a suggested general solution for problems of this type: {solutions}."
        tag = ""
        if self.related_tag:
            tag = f"The problem adheres to this relevant tag: {self.related_tag}"
        item = ""
        if self.item:
            item = "Here is a list of the relevant item/s related to your problem: \n"
            item += "```"
            for content in self.item:
                item += content
            item += "```"

        return f"\n{problem_found}\n\n{tag}\n\n{solution_problem_descr}\n\n{item}"

    def display_data(self):
        print("\n---------------------Next test---------------------")
        print(f"related_tag: {self.related_tag}")
        print(f"location: {self.location}")
        print(f"git_commit_messages: {self.git_commit_messages}")
        print(f"git_diff: {self.git_diff}")
        print(f"problem_type: {self.problem_type}")
        print(f"problem_statement: {self.problem_statement}")
        print(f"solution_statement: {self.solution_statement}")
