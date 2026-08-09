from spec_tagger.spec_review import git_context
from spec_tagger.tag_test.spec_test_linker import Invalidities
from enum import Enum
from spec_tagger.spec_review.solution import Solution


class ProblemType(Enum):
    INVALID_TAG = 1
    TEST_FAILURE = 2
    MISSED_TEST_OR_FILE = 3
    PASSED_BUT_CHANGED = 4


class SolutionMessages(Enum):
    DUPLICATE_SPEC_TAG = "Check all duplicate spec items and identify which tag fits the spec item the best, that tag will stay the same while all others should be re-named to something new."
    NO_TEST_TAG_FOR_SPEC_TAG = (
        "Make sure that the spec tag has test tags assigned to it and tests that pass."
    )
    NO_FUNCTION_FOR_TEST_TAG = "Double check that the test tag has been placed in the right location, either remove it, relocate it, or write a new test to fit the test tag and spec tag items."
    NO_SPEC_TAG_FOR_TEST_TAG = "Enure that the tests written have a respective spec tag and portion of the spec dedicated to the test."
    TAG_REVISION_MISMATCH = "Take a look at the older/lower revision numbers to see if anything in their content needs to be updated according to how the tag content with the latest revision number looks. If not, just bump the revision numbe rup to the latest, or adjust the content if so."


class ResultTriage:
    def __init__(self, context_data: dict, ai_enabled: bool = False) -> None:
        self.context_data = context_data
        self.ai_enabled = ai_enabled
        self.git_context = context_data["git_context"]
        self.invalid_tags = context_data["report"]["invalid_tags"]
        self.uncovered_tests_and_files = context_data["report"]["coverage_data"][
            "tag_coverage"
        ]
        self.test_coverage = context_data["report"]["coverage_data"]["test_coverage"]
        self.test_failures = context_data["report"]["test_results"]

        self._print_keys(self.git_context, "Git Context", True)
        self._print_keys(self.invalid_tags, "Invalid Tags")
        self._print_keys(
            self.uncovered_tests_and_files, "Un-Covered Tests and Files", True
        )
        self._print_keys(self.test_coverage, "Test Coverage")
        self._print_keys(self.test_failures, "Test Failures")

        self.solutions = []

    def _print_keys(self, data_dict: dict, name: str, value_also: bool = False):

        print(f"----------------- {name} -----------------")
        if data_dict:
            for key, value in data_dict.items():
                print(key)
                if value_also:
                    print(f"\n{value}")

    def filter_results(self):
        # Invalid Tags
        self._triage_invalid_tags()
        # Missed Tests and Files
        self._triage_missed_tests_and_files()
        # Failed Tests
        self._triage_failed_tests()
        # Passed Tests
        self._triage_passed_but_changed_tests()

    def _triage_invalid_tags(self):
        if self.invalid_tags:
            for invalid in self.invalid_tags:
                solution = Solution(
                    related_tag=invalid["full_tag"],
                    tag_location=f"{invalid['filename']}:{invalid['line']}",
                    item=invalid["content"],
                    git_commit_messages=git_context.commits_for_file(
                        invalid["filename"],
                        self.git_context["base"],
                        self.git_context["head"],
                    ),
                    git_diff=git_context.diff_for_file(
                        invalid["filename"],
                        self.git_context["base"],
                        self.git_context["head"],
                    ),
                    test_coverage=self.test_coverage[invalid["full_tag"]],
                    problem_type=ProblemType.INVALID_TAG,
                    problem_statement=[],
                    solution_statement=[],
                    ai_enabled=self.ai_enabled,
                    ai_usage_recommended=False,
                )
                for reason in invalid["validity"]["reasons"]:
                    solution.problem_statement.append(reason.value)
                    match reason:
                        case Invalidities.DUPLICATE_SPEC_TAG:
                            solution.solution_statement.append(
                                SolutionMessages.DUPLICATE_SPEC_TAG.value
                            )
                        case Invalidities.NO_FUNCTION_FOR_TEST_TAG:
                            solution.solution_statement.append(
                                SolutionMessages.NO_FUNCTION_FOR_TEST_TAG.value
                            )
                        case Invalidities.NO_SPEC_TAG_FOR_TEST_TAG:
                            solution.solution_statement.append(
                                SolutionMessages.NO_SPEC_TAG_FOR_TEST_TAG.value
                            )
                        case Invalidities.NO_TEST_TAG_FOR_SPEC_TAG:
                            solution.solution_statement.append(
                                SolutionMessages.NO_TEST_TAG_FOR_SPEC_TAG.value
                            )
                        case Invalidities.TAG_REVISION_MISMATCH:
                            solution.solution_statement.append(
                                SolutionMessages.TAG_REVISION_MISMATCH.value
                            )
        else:
            print("No invalid tags found during triage")

    def _triage_missed_tests_and_files(self):
        pass

    def _triage_failed_tests(self):
        pass

    def _triage_passed_but_changed_tests(self):
        pass

    def _register_non_ai_entry(self):
        pass

    def _register_ai_recommended_entry(self):
        pass

    # Invalid Tag Handling
    # - All that's needed is the tag data and the item

    # Missing File / Test Handling
    # - All that's needed is the file names and test function names

    # Test Error/Failure Handling
    # - Get the output of the test
    # - Get the content of the test data
    # - Get the content of the spec item
    # - Get the diff of the related file

    # Change Analysis:
    #
    #
    #
    # Compare Changed files to their respective passing tests.
    # if a test has passed, BUT any of the respecitve files in the spec or test files have changed
    #   - Push it through to an AI check
    #
    #
    # Has a spec file changed?
    #
    #
    #
    # Has a test file changed?
    #
    #
    #
    #
    # Has a code file changed and do the tests cover it?
