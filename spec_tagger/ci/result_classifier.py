from enum import Enum
from pathlib import Path


class ResultClass(Enum):
    TEST_FAIL = 1
    TEST_ERROR = 2
    INVALID_TAG = 3
    TEST_PASS = 4
    UNTESTED = 5


class ResultClassifier:
    def __init__(self, results_path: Path) -> None:
        self.results_path = results_path

    def load_results(self):
        pass

    def classify_results(self):
        pass
