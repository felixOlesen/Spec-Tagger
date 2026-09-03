import json
import os
import importlib.resources as pkg_resources
from pathlib import Path


class Generator:
    """Report Generator
    We want the user to be able to generate a report of their tests after running spec tagger.
    """

    def __init__(
        self,
        report_output_dir: str,
        report_type: str,
        test_output: dict | None,
        invalid_tags: list | None,
        successful_links: dict | None,
        one_by_one: bool,
        tag_coverage_data: dict[str, set],
        test_coverage_location: str,
        test_coverage_library: str,
        verbose: bool,
        coverage_container_root: str | None = None,
    ):
        self.report_output_dir = report_output_dir
        self.report_type = report_type
        self.test_output = test_output
        self.invalid_tags = invalid_tags
        self.successful_links = successful_links
        self.one_by_one = one_by_one
        self.verbose = verbose
        self.output_object = {}
        self.report_name = "report.json"
        self.tag_coverage_data = tag_coverage_data
        self.test_coverage_location = test_coverage_location
        self.test_coverage_data = None
        self.test_coverage_library = test_coverage_library
        self.coverage_container_root = coverage_container_root
        self.repo_root = os.getcwd()

    def generate_report(self):
        self._construct_report_object()
        match self.report_type:
            case "json":
                self._generate_json()
            case "html":
                self._generate_html()
            case "stdout":
                self._generate_stdout()
            case _:
                print("Invalid report type given.")

    def _construct_report_object(self):
        """Object Strucutre

        Test Results

            Spec item
                Line Number
                Spec snapshot
                Test Coverage
                Execution Time
                Passes
                    Coverage
                Failures
                    Output
                Error
                    Output

        Invalid Tags
            Tag
                Reason

        """
        if not self.successful_links:
            print("Warning tag links found to be null on report generation.")
            return

        if not self.test_output:
            print("Warning test_output found to be null on test generation")
            return

        if self.test_coverage_location:
            match self.test_coverage_library:
                case "python.coverage":
                    self.test_coverage_data = self.parse_coveragepy_json()
                case "ruby.simplecov":
                    self.test_coverage_data = self.parse_simplecov_json()

        self.output_object["one_by_one"] = self.one_by_one
        self.output_object["test_results"] = self.test_output
        self.output_object["invalid_tags"] = self.invalid_tags
        self.output_object["coverage_data"] = {}
        self.output_object["coverage_data"]["test_coverage"] = self.test_coverage_data
        self.output_object["coverage_data"]["tag_coverage"] = self.tag_coverage_data

        for _, links in self.successful_links.items():
            full_tag = links["spec_tag"]["full_tag"]
            if full_tag in self.output_object["test_results"]:
                self.output_object["test_results"][full_tag]["spec_tag"] = links[
                    "spec_tag"
                ]
                self.output_object["test_results"][full_tag]["test_tags"] = links[
                    "test_tags"
                ]
            else:
                print("Warning, links found with no connected test results.")

        if self.verbose:
            print("Constructed Report Object:")
            print(self.output_object)

    def _generate_json(self):
        location = os.path.join(self.report_output_dir, self.report_name)
        with open(location, "w") as f:
            json.dump(self.output_object, f)

    def _generate_html(self):
        os.makedirs(self.report_output_dir, exist_ok=True)

        location = os.path.join(self.report_output_dir, "data.js")
        with open(location, "w") as f:
            f.write(f"window.REPORT_DATA = {json.dumps(self.output_object)};")

        self._copy_template_file("index.html")
        self._copy_template_file("style.css")
        self._copy_template_file("script.js")

        print(f"Report successfully saved to {os.path.abspath(self.report_output_dir)}")

    def _generate_stdout(self):
        GREEN = "\033[92m"
        RED = "\033[91m"
        YELLOW = "\033[93m"
        RESET = "\033[00m"

        print("\n---------- Test Results ----------")
        for _, data in self.output_object["test_results"].items():
            spec_tag = data["spec_tag"]
            test_count = data["test_count"]
            pass_count = data["pass_count"]
            fail_count = data["fail_count"]
            if test_count == 0:
                status = f"{YELLOW}UNTESTED{RESET}"
            elif pass_count == test_count:
                status = f"{GREEN}PASSED{RESET}"
            else:
                status = f"{RED}FAILED{RESET}"

            print(f"\n{spec_tag['full_tag']}: {status}")
            print(f"Spec File: {spec_tag['filename']}")
            print(f"Line Number: {spec_tag['line']}")
            print(f"Execution Time: {data['exec_time']}")
            print(f"Test Count: {test_count}")
            print(f"Overall: {pass_count}/{fail_count + pass_count} passed")

            print("Linked Tests:")
            if "test_tags" in data and data["test_tags"]:
                for test_tag in data["test_tags"]:
                    print(f"- {test_tag['filename']} : {test_tag['test_function']}")

            if data["results"]:
                print("Results:")
                for result in data["results"]:
                    color = GREEN if result["outcome"] == "passed" else RED
                    print(
                        f"  {color}{result['outcome'].upper()}{RESET}: {result['cmd']}"
                    )
                    if result["error"]:
                        print(f"    Error: {result['error']}")

        print("\n---------- Coverage ----------")
        if (
            self.output_object["coverage_data"]
            and self.output_object["coverage_data"]["test_coverage"]
        ):
            for tag, data in self.output_object["coverage_data"][
                "test_coverage"
            ].items():
                print(f"\nCoverage for Tag {tag}")
                for file, file_cov_data in data.items():
                    print(f"Coverage for {file}")
                    print(f"Lines Covered: {len(file_cov_data['covered_lines'])}")
                    print(f"Missing Lines: {len(file_cov_data['missing_lines'])}")
                    print(f"Percent Covered: {file_cov_data['coverage']}\n")

        print("\n---------- Missed Files/Tests ----------")
        if (
            self.output_object["coverage_data"]
            and self.output_object["coverage_data"]["tag_coverage"]
        ):
            for file in enumerate(
                self.output_object["coverage_data"]["tag_coverage"]["files"]
            ):
                print(f"File {file} missing any tags and coverage.")
            for test in self.output_object["coverage_data"]["tag_coverage"][
                "tests"
            ].items():
                print(
                    f"Test {test} found untagged, ensure it is tagges and documented in the spec."
                )

        print("\n---------- Invalid Tags ----------")
        for tag in self.output_object["invalid_tags"]:
            print(f"\nTag: {tag['full_tag']}")
            print(f"Reason: {tag['validity']['reasons']}")

        print("\n")

    def parse_coveragepy_json(self) -> dict[str, dict]:
        path = self.test_coverage_location
        test_coverage_data = {}
        tag_to_implementation_coverage = {}
        if os.path.isdir(path):
            # Walk through the directory to load each report file into memory:
            for root, _, files in os.walk(self.test_coverage_location):
                for file in files:
                    if file.endswith(".json"):
                        file_components = file.split("_cov.json")
                        full_tag = file_components[0]
                        if self.verbose:
                            print(f"json report found: {file}")

                        data = json.loads(Path(root, file).read_text())
                        if full_tag not in test_coverage_data:
                            test_coverage_data[full_tag] = []
                        test_coverage_data[full_tag].append(data["files"])

            for tag, test_coverage in test_coverage_data.items():
                tag_to_implementation_coverage[tag] = {}
                for file_data in test_coverage:
                    for covered_file, coverage_data in file_data.items():
                        if covered_file not in tag_to_implementation_coverage[tag]:
                            tag_to_implementation_coverage[tag][covered_file] = {}
                        tag_to_implementation_coverage[tag][covered_file][
                            "coverage"
                        ] = coverage_data["summary"]["percent_covered"]
                        tag_to_implementation_coverage[tag][covered_file][
                            "missing_lines"
                        ] = coverage_data["missing_lines"]
                        tag_to_implementation_coverage[tag][covered_file][
                            "covered_lines"
                        ] = coverage_data["executed_lines"]

        return tag_to_implementation_coverage

    def parse_simplecov_json(self) -> dict[str, dict]:
        """Parse SimpleCov reports into the same shape as parse_coveragepy_json."""
        tag_to_implementation_coverage = {}
        path = self.test_coverage_location
        if not os.path.isdir(path):
            return tag_to_implementation_coverage

        for root, _, files in os.walk(path):
            for file in files:
                if not file.endswith(".json"):
                    continue
                full_tag = file.split("_cov.json")[0]
                print(f"json report found: {file}")

                data = json.loads(Path(root, file).read_text())

                # Two possible shapes:
                #   coverage.json    (simplecov_json_formatter) -> {"meta":…, "coverage": {...}}
                #   .resultset.json  (raw SimpleCov)            -> {"<CommandName>": {"coverage": {...}}}
                if "coverage" in data and "meta" in data:
                    file_maps = [data["coverage"]]
                else:
                    file_maps = [
                        v["coverage"]
                        for v in data.values()
                        if isinstance(v, dict) and "coverage" in v
                    ]

                merged = tag_to_implementation_coverage.setdefault(full_tag, {})

                for file_map in file_maps:
                    for abs_path, entry in file_map.items():
                        # Newer SimpleCov nests under "lines"; older is a bare array.
                        lines = entry["lines"] if isinstance(entry, dict) else entry

                        covered, missing = [], []
                        for idx, hits in enumerate(lines):
                            if hits is None:  # not executable
                                continue
                            (covered if hits > 0 else missing).append(idx + 1)

                        # SimpleCov writes ABSOLUTE paths; normalise so they match
                        # the relative paths git and coverage.py use. When coverage
                        # ran inside a container whose mount point differs from
                        # where spectagger runs (self.repo_root), relpath-ing
                        # against repo_root walks up to "/" and back down,
                        # producing a deeply nested "../../.." path - so prefer
                        # stripping the known container root instead.
                        if self.coverage_container_root and abs_path.startswith(
                            self.coverage_container_root
                        ):
                            rel = os.path.relpath(
                                abs_path, self.coverage_container_root
                            )
                        else:
                            rel = os.path.relpath(abs_path, self.repo_root)

                        relevant = len(covered) + len(missing)
                        merged[rel] = {
                            "coverage": (100.0 * len(covered) / relevant)
                            if relevant
                            else 0.0,
                            "missing_lines": missing,
                            "covered_lines": covered,
                        }

        return tag_to_implementation_coverage

    def _copy_template_file(self, file_name):
        template_content = (
            pkg_resources.files("spec_tagger.tag_test.templates")
            .joinpath(file_name)
            .read_text()
        )

        destination = os.path.join(self.report_output_dir, file_name)
        with open(destination, "w", encoding="utf-8") as f:
            f.write(template_content)
