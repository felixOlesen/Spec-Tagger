from spec_tagger.spec_review import git_context


class ResultTriage:
    def __init__(self, context_data: dict) -> None:
        self.context_data = context_data
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
        pass

    def _triage_missed_tests_and_files(self):
        pass

    def _triage_failed_tests(self):
        pass

    def _triage_passed_but_changed_tests(self):
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
