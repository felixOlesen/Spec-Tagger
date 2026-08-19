class CoverageFilter:
    def __init__(self, coverage_data: dict) -> None:
        self.coverage_data = coverage_data
        self.file_to_missing_lines = {}
        self.file_to_covered_lines = {}
        self._filter_missing_and_covered_lines()

    def _filter_missing_and_covered_lines(self):
        for tag, coverage_info in self.coverage_data.items():
            for file, file_coverage_info in coverage_info.items():
                # "coverage" == Percent coverage of the file
                # "missing_lines" == list of uncovered lines in the file
                # "covered_lines" == list of covered lines in the file
                covered_lines = file_coverage_info["covered_lines"]
                missing_lines = file_coverage_info["missing_lines"]
                coverage = file_coverage_info["coverage"]
                if len(missing_lines) == 0 and len(covered_lines) == 0:
                    continue
                if file not in self.file_to_covered_lines:
                    self.file_to_covered_lines[file] = set()
                self.file_to_covered_lines[file].update(covered_lines)

                if file not in self.file_to_missing_lines:
                    self.file_to_missing_lines[file] = set()
                self.file_to_missing_lines[file].update(missing_lines)

                self.file_to_missing_lines[file] -= self.file_to_covered_lines[file]

    def is_line_covered(self, file: str, line: int):
        pass
