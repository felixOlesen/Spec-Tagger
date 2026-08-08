from pathlib import Path
import spec_tagger
import spec_tagger.spec_review.git_context as git_context
import json


class ContextAggregator:
    def __init__(self, report_path: str) -> None:
        self.report_path = report_path
        self.report_data = None
        self.git_context_data = None

    def _retrieve_report_data(self):
        path = Path(self.report_path)
        if path.is_file():
            self.report_data = json.loads(path.read_text())
        else:
            print(
                f"Warning, context_aggregator found report_path '{path}' to not be a valid file"
            )

    # I also want to collect git context data

    def _collect_git_context(self):
        self.git_context_data = git_context.collect_context()

    def get_all_context(self) -> dict:
        self._retrieve_report_data()
        if not self.report_data:
            print("Warning, no report data was found")

        self._collect_git_context()
        if not self.git_context_data:
            print("Warning, no git context data was found")

        print(
            git_context.diff_for_file(
                path="spec_tagger/spec_review/context_aggregator.py",
                base="origin/main",
                head="HEAD",
            )
        )

        return {"report": self.report_data, "git_context": self.git_context_data}
