import spec_tagger.ci.git_context as git_context


class ContextAggregator:
    def __init__(self, classified_results: dict):
        self.classified_results = classified_results
        self.invalid_results = classified_results["invalid"]
        self.fail_results = classified_results["failed"]
        self.untested_results = classified_results["untested"]
        self.passed_results = classified_results["pass"]

    def _collect_context_for_result(self, result: dict):
        pass

    def collect_context(self):
        if self.invalid_results:
            for invalid in self.invalid_results:
                self._collect_context_for_result(invalid)
        if self.fail_results:
            for fail in self.fail_results:
                self._collect_context_for_result(fail)
        if self.untested_results:
            for untested in self.untested_results:
                self._collect_context_for_result(untested)
        if self.passed_results:
            for pass_result in self.passed_results:
                self._collect_context_for_result(pass_result)
