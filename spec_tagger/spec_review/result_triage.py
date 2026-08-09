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

        self._print_keys(self.git_context, "Git Context")
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

    # Extract Invalid Tags
    def _extract_invalid_tags(self):
        pass

    # Extract Test Failures
    def _extract_test_failures(self):
        pass

    # Un-covered tests and test files
    def _extract_uncovered_tests_and_files(self):
        pass

    # Change Analysis:
    #
    #
    #
    # Compare Changed files to their respective passing tests.
    #   - Figure this out from line numbers
    #
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
