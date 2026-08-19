from spec_tagger.spec_review import git_context
from spec_tagger.spec_review.coverage_filter import CoverageFilter
from spec_tagger.tag_test.spec_test_data import Invalidities
from enum import Enum
from spec_tagger.spec_review.solution import Solution


class ProblemType(Enum):
    INVALID_TAG = "Invalid Tag has been found"
    TEST_FAILURE = "This test has failed"
    TEST_ERROR = "This test has error-ed out"
    MISSED_FILE = "The file has been missed"
    MISSED_TEST = "The test has been missed"
    PASSED_BUT_CHANGED = "The test has passed but the file has changed"
    IMPLEMENTATION_CHANGE_NOT_COVERED = "A change in the implementation code is present but it is either partially covered or not covered at all by the spec or tests, this requires review to understand how the spec and tests can stay consistent with the behaviour of the implementation code."


class SolutionMessages(Enum):
    DUPLICATE_SPEC_TAG = "Check all duplicate spec items and identify which tag fits the spec item the best, that tag will stay the same while all others should be re-named to something new."
    NO_TEST_TAG_FOR_SPEC_TAG = (
        "Make sure that the spec tag has test tags assigned to it and tests that pass."
    )
    NO_FUNCTION_FOR_TEST_TAG = "Double check that the test tag has been placed in the right location, either remove it, relocate it, or write a new test to fit the test tag and spec tag items."
    NO_SPEC_TAG_FOR_TEST_TAG = "Enure that the tests written have a respective spec tag and portion of the spec dedicated to the test."
    TAG_REVISION_MISMATCH = "Take a look at the older/lower revision numbers to see if anything in their content needs to be updated according to how the tag content with the latest revision number looks. If not, just bump the revision numbe rup to the latest, or adjust the content if so."
    UNCOVERED_FILE = "Read through the file contents to understand where in the spec they adhere to in terms of functionality, then either apply pre-existing spec tags to the tests in the file one-by-one, or write new entries for the specification to describe the behaviour that is being tested in the test file."
    UNCOVERED_TEST = "Read through the test contents to see what part of the spec it might belong to, either apply a pre-existing tag to the test or write a new entry into the spec with a new tag which you can then apply to the test."
    FAILED_TEST = "Take a look at the test output of the failing test to make sure that the behaviour it tests is correct in accordance to the spec item, also take a look at recently changed portions of the implementation code to figure out if anything might be incorrect, or not implemented yet."
    ERROR_TEST = "The test has returned an error instead of being able to finish and provide a result, make sure to take a look at the error output and the test function block to be sure there are no errors in your test code, then look at the implementation code to see if any errors are apparent there as well."
    PASSED_BUT_CHANGED = "Everything in terms of test-results appears to be running correctly, although it seems that the files that are connected to the spec, test, or implementation code have changed substantially, make sure to check these diffs in the code and evaluate if behaviourally they are all consistent with eachother."
    UNCOVERED_IMPLEMENTATION_CHANGE = "There is either partial or no coverage for these files at all, you need to read through and figure out how these changes need to be incorporated into the specification to allow for the the spec to stay up-to-date with the implementation code as well, also look into and express the types of linked tests that are required."


class ResultTriage:
    def __init__(
        self,
        context_data: dict,
        src_dir: str,
        ai_enabled: bool = False,
        semantic_drift_included: bool = True,
        failure_diagnostic_included: bool = True,
        tag_suggestion_included: bool = True,
        invalid_tags_included: bool = True,
        entire_diff_included: bool = False,
    ):
        self.context_data = context_data
        self.ai_enabled = ai_enabled
        context_data["git_context"]["changed_files"] = set(
            context_data["git_context"]["changed_files"]
        )
        self.git_context = context_data["git_context"]
        self.invalid_tags = context_data["report"]["invalid_tags"]
        self.uncovered_tests_and_files = context_data["report"]["coverage_data"][
            "tag_coverage"
        ]
        self.test_coverage = context_data["report"]["coverage_data"]["test_coverage"]
        self.test_failures = []
        self.test_passes = []
        for tag, info in context_data["report"]["test_results"].items():
            failure_presence = False
            for result in info["results"]:
                if result["outcome"] == "failed":
                    failure_presence = True
                    break
            if failure_presence:
                self.test_failures.append({"tag": tag, "result": info})
            else:
                self.test_passes.append({"tag": tag, "result": info})

        # self._print_keys(self.git_context, "Git Context", True)
        self._print_keys(self.invalid_tags, "Invalid Tags")
        self._print_keys(
            self.uncovered_tests_and_files, "Un-Covered Tests and Files", True
        )
        self._print_keys(self.test_coverage, "Test Coverage")

        self.solutions = []
        self.semantic_drift_included = semantic_drift_included
        self.failure_diagnostic_included = failure_diagnostic_included
        self.tag_suggestion_included = tag_suggestion_included
        self.invalid_tags_included = invalid_tags_included
        self.entire_diff_included = entire_diff_included
        self.src_dir = src_dir

    def _print_keys(self, data_dict: dict, name: str, value_also: bool = False):

        print(f"----------------- {name} -----------------")
        if data_dict:
            for key, value in data_dict.items():
                print(key)
                if value_also:
                    print(f"\n{value}")

    def filter_results(self):
        # Invalid Tags
        if self.invalid_tags_included:
            self._triage_invalid_tags()
        # Missed Tests and Files
        if self.tag_suggestion_included:
            self._triage_missed_tests_and_files()
        # Failed Tests
        if self.failure_diagnostic_included:
            self._triage_failed_tests()
        # Passed Tests
        if self.semantic_drift_included:
            self._triage_passed_but_changed_tests()

        self._triage_uncovered_implementation_changes()

        return self.solutions

    def _triage_uncovered_implementation_changes(self):
        if self.entire_diff_included:
            solution = Solution(
                related_tag=None,
                location=None,
                item=None,
                git_commit_messages=self.git_context["commit_messages"],
                git_diff=self.git_context["diff"],
                test_coverage=None,
                problem_type=ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED,
                problem_statement=[ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED.value],
                solution_statement=[
                    SolutionMessages.UNCOVERED_IMPLEMENTATION_CHANGE.value
                ],
                ai_enabled=self.ai_enabled,
                ai_usage_recommended=True,
            )
            self.solutions.append(solution)
        else:
            uncovered_implementation_files = self._get_uncovered_implementation_files()
            for file in uncovered_implementation_files:
                solution = Solution(
                    related_tag=None,
                    location=f"{file}",
                    item=None,
                    git_commit_messages=git_context.commits_for_file(
                        file,
                        self.git_context["base"],
                        self.git_context["head"],
                    ),
                    git_diff=git_context.diff_for_file(
                        file,
                        self.git_context["base"],
                        self.git_context["head"],
                    ),
                    test_coverage=None,
                    problem_type=ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED,
                    problem_statement=[
                        ProblemType.IMPLEMENTATION_CHANGE_NOT_COVERED.value
                    ],
                    solution_statement=[
                        SolutionMessages.UNCOVERED_IMPLEMENTATION_CHANGE.value
                    ],
                    ai_enabled=self.ai_enabled,
                    ai_usage_recommended=True,
                )
                self.solutions.append(solution)

    def _get_uncovered_implementation_files(self):
        uncovered_files = set()
        coverage_filter = CoverageFilter(self.test_coverage)
        changed_files = self.context_data["git_context"]["changed_files"]
        covered_files = coverage_filter.file_to_covered_lines.keys()
        print(f"COVERED FILES: {covered_files}")
        print(f"CHANGED FILES: {changed_files}")
        diff_file_to_lines = git_context.changed_lines_from_diff(
            self.git_context["base"], self.git_context["head"]
        )
        for changed_file in changed_files:
            if changed_file in covered_files and changed_file.startswith(self.src_dir):
                if changed_file in coverage_filter.file_to_covered_lines:
                    line_diff = (
                        diff_file_to_lines[changed_file]
                        - coverage_filter.file_to_covered_lines[changed_file]
                    )
                    print(f"LINE DIFF FOUND for file {changed_file}: {line_diff}")
            if changed_file not in covered_files and changed_file.startswith(
                self.src_dir
            ):
                uncovered_files.add(changed_file)

        return list(uncovered_files)

    def _triage_invalid_tags(self):
        if self.invalid_tags:
            for invalid in self.invalid_tags:
                solution = Solution(
                    related_tag=invalid["full_tag"],
                    location=f"{invalid['filename']}:{invalid['line']}",
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
                    self.solutions.append(solution)
        else:
            print("No invalid tags found during triage")

    def _triage_missed_tests_and_files(self):
        if self.uncovered_tests_and_files["files"]:
            for file in self.uncovered_tests_and_files["files"]:
                solution = Solution(
                    related_tag=None,
                    location=file,
                    item=None,
                    git_commit_messages=git_context.commits_for_file(
                        file, self.git_context["base"], self.git_context["head"]
                    ),
                    git_diff=git_context.diff_for_file(
                        file, self.git_context["base"], self.git_context["head"]
                    ),
                    test_coverage=None,
                    problem_type=ProblemType.MISSED_FILE,
                    problem_statement=[ProblemType.MISSED_FILE.value],
                    solution_statement=[SolutionMessages.UNCOVERED_FILE.value],
                    ai_enabled=self.ai_enabled,
                    ai_usage_recommended=True,
                )
                self.solutions.append(solution)
        if self.uncovered_tests_and_files["tests"]:
            for test, info in self.uncovered_tests_and_files["tests"].items():
                solution = Solution(
                    related_tag=None,
                    location=f"{info['file']}:{info['line']}",
                    item=test,
                    git_commit_messages=git_context.commits_for_file(
                        info["file"], self.git_context["base"], self.git_context["head"]
                    ),
                    git_diff=git_context.diff_for_file(
                        info["file"], self.git_context["base"], self.git_context["head"]
                    ),
                    test_coverage=None,
                    problem_type=ProblemType.MISSED_TEST,
                    problem_statement=[ProblemType.MISSED_TEST.value],
                    solution_statement=[SolutionMessages.UNCOVERED_TEST.value],
                    ai_enabled=self.ai_enabled,
                    ai_usage_recommended=True,
                )
                self.solutions.append(solution)

    def _triage_failed_tests(self):
        if self.test_failures:
            for test_fail in self.test_failures:
                (
                    result_diff_string,
                    result_commit_messages,
                    related_files,
                    item_content,
                ) = self._collect_test_data_from_spec_and_test_tags(test_fail)
                test_coverage = None
                if test_fail["tag"] in self.test_coverage:
                    test_coverage = self.test_coverage[test_fail["tag"]]
                if test_fail["result"]["error"]:
                    solution = Solution(
                        related_tag=test_fail["tag"],
                        location=related_files,
                        item=item_content,
                        git_commit_messages=result_commit_messages,
                        git_diff=result_diff_string,
                        test_coverage=test_coverage,
                        problem_type=ProblemType.TEST_ERROR,
                        problem_statement=[ProblemType.TEST_ERROR.value],
                        solution_statement=[SolutionMessages.ERROR_TEST.value],
                        ai_enabled=self.ai_enabled,
                        ai_usage_recommended=True,
                        stdout=test_fail["result"]["error"],
                    )
                    self.solutions.append(solution)
                else:
                    solution = Solution(
                        related_tag=test_fail["tag"],
                        location=related_files,
                        item=item_content,
                        git_commit_messages=result_commit_messages,
                        git_diff=result_diff_string,
                        test_coverage=test_coverage,
                        problem_type=ProblemType.TEST_FAILURE,
                        problem_statement=[ProblemType.TEST_FAILURE.value],
                        solution_statement=[SolutionMessages.FAILED_TEST.value],
                        ai_enabled=self.ai_enabled,
                        ai_usage_recommended=True,
                        stdout=test_fail["result"]["output"],
                    )
                    self.solutions.append(solution)

    def _triage_passed_but_changed_tests(self):
        for test_pass in self.test_passes:
            check_results = self._passed_test_check(test_pass["result"])
            if check_results:
                (
                    result_diff_string,
                    result_commit_messages,
                    related_files,
                    item_content,
                ) = check_results
                test_coverage = None
                if test_pass["tag"] in self.test_coverage:
                    test_coverage = self.test_coverage[test_pass["tag"]]

                solution = Solution(
                    related_tag=test_pass["tag"],
                    location=related_files,
                    item=item_content,
                    git_commit_messages=result_commit_messages,
                    git_diff=result_diff_string,
                    test_coverage=test_coverage,
                    problem_type=ProblemType.PASSED_BUT_CHANGED,
                    problem_statement=[ProblemType.PASSED_BUT_CHANGED.value],
                    solution_statement=[SolutionMessages.PASSED_BUT_CHANGED.value],
                    ai_enabled=self.ai_enabled,
                    ai_usage_recommended=True,
                    stdout=None,
                )
                self.solutions.append(solution)

    def _passed_test_check(self, test_result) -> tuple[str, list[str], str, str] | None:
        # Get the related files for the tests and spec, if any of them show up in the changed files
        file_to_tag = {test_result["spec_tag"]["filename"]: test_result["spec_tag"]}
        for test_tag in test_result["test_tags"]:
            file_to_tag[test_tag["filename"]] = test_tag
        files = set(file_to_tag.keys())
        relevant_files = files.intersection(self.git_context["changed_files"])
        if len(relevant_files) > 0:
            spec_content = test_result["spec_tag"]["content"]
            diff_string = "Diffs for Connected Files:\n"
            commit_messages = []
            item_contents = f"Spec Item Content: {spec_content}\n"
            file_locations = "File Locations:\n"
            for file in relevant_files:
                tag = file_to_tag[file]
                tag_line = tag["line"]
                commit_messages.append(
                    f"File commit_messages: {tag['full_tag']}\n {git_context.commits_for_file(file, self.git_context['base'], self.git_context['head'])}\n"
                )
                diff_string += f"Related Diff to Tag: {tag['full_tag']}\n {git_context.diff_for_file(file, self.git_context['base'], self.git_context['head'])}\n"
                item_contents += f"Tag Item Contents: {tag['content']}"
                file_locations += f"{file}:{tag_line}\n"
            return diff_string, commit_messages, file_locations, item_contents
        else:
            return None

    def _collect_test_data_from_spec_and_test_tags(
        self, test_result
    ) -> tuple[str, list[str], str, str]:
        spec_file = test_result["result"]["spec_tag"]["filename"]
        spec_line = test_result["result"]["spec_tag"]["line"]
        spec_content = test_result["result"]["spec_tag"]["content"]
        diff_string = f"Spec File Diff:\n {git_context.diff_for_file(spec_file, self.git_context['base'], self.git_context['head'])}\n"
        commit_messages = [
            f"Spec File Commit Messages if any:\n {git_context.commits_for_file(spec_file, self.git_context['base'], self.git_context['head'])}\n"
        ]
        related_files = f"Spec File: {spec_file}:{spec_line} \nTest Files:\n"
        item_contents = f"Spec Item Content: {spec_content}\n"
        for test_tag in test_result["result"]["test_tags"]:
            test_file = test_tag["filename"]
            test_line = test_tag["line"]
            diff_string += f"Test Function: {test_tag['test_function']}\n {git_context.diff_for_file(test_file, self.git_context['base'], self.git_context['head'])}\n"
            commit_messages.append(
                f"Test File commit_messages: {test_tag['test_function']}\n {git_context.commits_for_file(test_file, self.git_context['base'], self.git_context['head'])}\n"
            )
            related_files += f"{test_file}:{test_line}\n"
            item_contents += f"Test Function: {test_tag['test_function']} Contents: \n {test_tag['content']}\n"
        return diff_string, commit_messages, related_files, item_contents

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
