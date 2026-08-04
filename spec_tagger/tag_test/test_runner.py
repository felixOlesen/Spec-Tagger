import subprocess
import shlex
import time
import datetime


class Runner:
    def __init__(
        self,
        test_run_command: str,
        test_format: str,
        test_join: str,
        linked_tags: dict | None,
        one_by_one: bool,
        verbose: bool,
    ):
        self.test_run_command = test_run_command
        self.test_format = test_format
        self.linked_tags = linked_tags
        self.test_join = test_join
        self.one_by_one = one_by_one
        self.verbose = verbose

    def format_target(self, tag: dict):
        if "test_function" not in tag:
            return tag["filename"]
        return self.test_format.format(
            file=tag["filename"], name=tag["test_function"], line=tag["item_start_line"]
        )

    def build_targets_for_link(self, link: dict) -> list:
        # Dedupe and prune within this one spec tag's tests.
        targets = []
        seen = set()
        file_level = set()

        for test_tag in link["test_tags"]:
            if "test_function" not in test_tag:
                file_level.add(test_tag["filename"])

        for test_tag in link["test_tags"]:
            # Prune using the tag's own data — no string parsing.
            is_file_target = test_tag.get("test_function") is None
            if not is_file_target and test_tag["filename"] in file_level:
                continue  # whole file already runs, skip

            target = self.format_target(test_tag)
            if target not in seen:
                seen.add(target)
                targets.append(target)

        if self.test_join is not None and targets:
            targets = [self.test_join.join(targets)]
        return targets

    def build_command_for_targets(self, targets: list) -> list:
        cmd = []
        for part in shlex.split(self.test_run_command):
            if part == "{tests}" or part == "{files}":
                for target in targets:
                    cmd.extend(shlex.split(target))
            else:
                cmd.append(part)
        return cmd

    def run_tests(self, dry_run: bool = False) -> dict | None:
        results = {}  # tag_str -> 'passed' | 'failed' | 'untested'

        if not self.linked_tags:
            print("Warning linked tags found to be null on run, exiting.")
            return

        for _, link in self.linked_tags.items():
            if link["test_tags"]:
                targets = self.build_targets_for_link(link)
            else:
                targets = None
            tag_str = link["spec_tag"]["full_tag"]
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

            print(f"Running tests for {tag_str} ...")
            start_time = time.perf_counter()
            res = []

            for command in command_list:
                res.append(subprocess.run(command, capture_output=True, text=True))
            end_time = time.perf_counter()

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
