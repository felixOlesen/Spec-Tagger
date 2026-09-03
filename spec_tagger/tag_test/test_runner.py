import subprocess
import shlex
import shutil
import time
import datetime
import json
from pathlib import Path
from tqdm import tqdm


class Runner:
    """The runner class provides functionality for running the tests connected to tags.
    The tests are run spec tag-by-spec tag."""

    SIMPLECOV_DIR = "coverage"  # SimpleCov's default coverage_dir

    def __init__(
        self,
        test_run_command: str,
        test_format: str,
        test_join: str,
        linked_tags: dict | None,
        one_by_one: bool,
        test_coverage_location: str,
        coverage_library: str,
        verbose: bool,
    ):
        self.test_run_command = test_run_command
        self.test_format = test_format
        self.linked_tags = linked_tags
        self.test_join = test_join
        self.one_by_one = one_by_one
        self.test_coverage_location = test_coverage_location
        self.coverage_library = coverage_library
        self.verbose = verbose

    def format_target(self, tag: dict) -> str:
        """Formats a test target to be injected into the test_command provided in the main.py args."""
        if "test_function" not in tag:
            return tag["filename"]
        return self.test_format.format(
            file=tag["filename"], name=tag["test_function"], line=tag["item_start_line"]
        )

    def build_targets_for_link(self, link: dict) -> list:
        """Joins the test targets together to be injected into the test_command arg in main.py"""
        # De-dupe and prune within this one spec tag's tests.
        targets = []
        seen = set()
        file_level = set()

        for test_tag in link["test_tags"]:
            if "test_function" not in test_tag:
                file_level.add(test_tag["filename"])

        for test_tag in link["test_tags"]:
            is_file_target = test_tag.get("test_function") is None
            if not is_file_target and test_tag["filename"] in file_level:
                continue

            target = self.format_target(test_tag)
            if target not in seen:
                seen.add(target)
                targets.append(target)

        if self.test_join is not None and targets:
            targets = [self.test_join.join(targets)]
        return targets

    def build_command_for_targets(self, targets: list) -> list:
        """Constructs the command that will be run during testing, allows for
        running of test targets one_by_one or multiple in a sinlge command"""
        cmd = []
        for part in shlex.split(self.test_run_command):
            if part == "{tests}" or part == "{files}":
                for target in targets:
                    cmd.extend(shlex.split(target))
            else:
                cmd.append(part)
        return cmd

    def _reset_simplecov_dir(self) -> None:
        shutil.rmtree(self.SIMPLECOV_DIR, ignore_errors=True)
        Path(self.SIMPLECOV_DIR).mkdir(parents=True, exist_ok=True)

    def _read_simplecov_result(self) -> dict[str, list]:
        """Parses simplecov coverage report"""
        result_path = Path(self.SIMPLECOV_DIR, ".resultset.json")
        if not result_path.exists():
            result_path = Path(self.SIMPLECOV_DIR, "coverage.json")
        if not result_path.exists():
            return {}

        data = json.loads(result_path.read_text())

        if "coverage" in data and "meta" in data:
            file_maps = [data["coverage"]]
        else:
            file_maps = [
                v["coverage"]
                for v in data.values()
                if isinstance(v, dict) and "coverage" in v
            ]

        file_lines = {}
        for file_map in file_maps:
            for path, entry in file_map.items():
                # Newer SimpleCov nests under "lines"; older is a bare array.
                file_lines[path] = entry["lines"] if isinstance(entry, dict) else entry
        return file_lines

    def _merge_simplecov_result(self, accumulator: dict[str, list]):
        """Merges simplecov coverage reports into a single location between runs"""
        # Boot file has SimpleCov.use_merging false, so each run's result file is
        # only that run's data.
        for path, lines in self._read_simplecov_result().items():
            if path not in accumulator:
                accumulator[path] = list(lines)
                continue
            existing = accumulator[path]
            for idx, hits in enumerate(lines):
                if hits is None or existing[idx] is None:
                    continue
                existing[idx] = max(existing[idx], hits)

    def run_tests(self, dry_run: bool = False) -> dict | None:
        """Main entrypoint for tag_test/orchestrator.py controls the flow of constructing
        and running test commands and compiling the test results"""
        results = {}  # tag_str -> 'passed' | 'failed' | 'untested'

        if not self.linked_tags:
            print("Warning linked tags found to be null on run, exiting.")
            return
        if self.coverage_library:
            subprocess.run(["mkdir", self.test_coverage_location])

        loading_bar = tqdm(self.linked_tags.items())
        if self.verbose:
            loading_bar = self.linked_tags.items()

        for _, link in loading_bar:
            if link["test_tags"]:
                targets = self.build_targets_for_link(link)
            else:
                targets = None

            tag_str = link["spec_tag"]["full_tag"]
            if not self.verbose:
                loading_bar.set_description(f"Running {tag_str}")

            if not targets:
                spec = link["spec_tag"]
                if self.verbose:
                    print(
                        f"Warning: {tag_str} ({spec['filename']}:{spec['line']}) "
                        f"has no linked tests."
                    )
                results[tag_str] = {
                    "test_date": str(datetime.datetime.now()),
                    "results": [],
                    "test_count": 0,
                    "exec_time": "0.000000 Seconds",
                    "pass_count": 0,
                    "fail_count": 0,
                }
                continue
            command_list = []
            if self.one_by_one:
                for target in targets:
                    command_list.append(self.build_command_for_targets([target]))
            else:
                command_list.append(self.build_command_for_targets(targets))
            if dry_run:
                print(f"{tag_str}:")
                for target in targets:
                    print(f"  : {target}")
                    for command in command_list:
                        print("  Command:", " ".join(shlex.quote(p) for p in command))
                continue

            if self.coverage_library == "python.coverage":
                subprocess.run(["coverage", "erase"])
            elif self.coverage_library == "ruby.simplecov":
                self._reset_simplecov_dir()
            if self.verbose:
                print(f"Running tests for {tag_str} ...")
            start_time = time.perf_counter()
            res = []
            simplecov_accumulator = {}

            for index, command in enumerate(command_list):
                res.append(subprocess.run(command, capture_output=True, text=True))
                if self.coverage_library == "ruby.simplecov":
                    self._merge_simplecov_result(simplecov_accumulator)
            end_time = time.perf_counter()
            if self.coverage_library == "python.coverage":
                subprocess.run(
                    [
                        "coverage",
                        "json",
                        "-o",
                        f"{self.test_coverage_location}/{tag_str}_cov.json",
                    ],
                    capture_output=True,
                )
            elif self.coverage_library == "ruby.simplecov":
                coverage_payload = {
                    "meta": {"spectagger_merged": True},
                    "coverage": {
                        path: {"lines": lines}
                        for path, lines in simplecov_accumulator.items()
                    },
                }
                with open(
                    f"{self.test_coverage_location}/{tag_str}_cov.json", "w"
                ) as f:
                    json.dump(coverage_payload, f)

            results[tag_str] = {
                "test_date": str(datetime.datetime.now()),
                "results": [],
                "test_count": len(targets),
                "exec_time": f"{(end_time - start_time):.6f} Seconds",
            }

            for index, result in enumerate(res):
                cmd_string = " ".join(command_list[index])
                outcome = None
                output = None
                error = None

                if result.returncode == 0:
                    outcome = "passed"
                else:
                    outcome = "failed"
                    if result.stdout:
                        output = result.stdout
                        if self.verbose:
                            print(result.stdout)
                    if result.stderr and self.verbose:
                        error = result.stderr
                        if self.verbose:
                            print(result.stderr)
                results[tag_str]["results"].append(
                    {
                        "outcome": outcome,
                        "output": output,
                        "error": error,
                        "cmd": cmd_string,
                    }
                )

        if dry_run:
            return {}

        # Summary: the traceability report.
        print("\n===== Spec tag results =====")
        for tag_str, outcome in results.items():
            pass_count = 0
            fail_count = 0
            if not outcome["results"]:
                print(f"  {tag_str}: ", "\033[93m UNTESTED\033[00m")
            for result in outcome["results"]:
                if result["outcome"] == "failed":
                    fail_count += 1
                    print(
                        f"  {tag_str}: ",
                        "\033[91m {}\033[00m".format(result["outcome"].upper()),
                    )
                elif result["outcome"] == "passed":
                    pass_count += 1
                    print(
                        f"  {tag_str}: ",
                        "\033[92m {}\033[00m".format(result["outcome"].upper()),
                    )
            print(f" Test Count: {outcome['test_count']}")
            print(f" Overall: {pass_count}/{pass_count + fail_count} passed. \n")
            results[tag_str]["pass_count"] = pass_count
            results[tag_str]["fail_count"] = fail_count
        return results
