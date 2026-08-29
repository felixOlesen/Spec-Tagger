from pathlib import Path
import spec_tagger
import spec_tagger.spec_review.git_context as git_context
import json


class ContextAggregator:
    def __init__(self, report_path: str, base, head) -> None:
        self.report_path = report_path
        self.report_data = None
        self.git_context_data = None
        self.git_base = base
        self.git_head = head

    def _retrieve_report_data(self):
        path = Path(self.report_path)
        if path.is_file():
            self.report_data = json.loads(path.read_text())
        else:
            print(
                f"Warning, context_aggregator found report_path '{path}' to not be a valid file"
            )

    def _collect_git_context(self):
        self.git_context_data = git_context.collect_context(
            self.git_base, self.git_head
        )

    def get_all_context(self) -> dict:
        self._retrieve_report_data()
        if not self.report_data:
            print("Warning, no report data was found")

        self._collect_git_context()
        if not self.git_context_data:
            print("Warning, no git context data was found")

        if self.report_data:
            for key, _ in self.report_data.items():
                print(key)

        if self.git_context_data:
            for key, _ in self.git_context_data.items():
                print(key)

        return {"report": self.report_data, "git_context": self.git_context_data}
