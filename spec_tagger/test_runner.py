import subprocess
import shlex


class Runner:
    def __init__(
        self,
        test_run_command: str,
        test_format: str,
        test_join: str,
        linked_tags: dict,
        verbose: bool,
    ):
        self.test_run_command = test_run_command
        self.test_format = test_format
        self.linked_tags = linked_tags
        self.test_join = test_join
        self.verbose = verbose

    def format_target(self, tag: dict):
        if "test_function" not in tag:
            return tag["filename"]
        return self.test_format.format(file=tag["filename"], name=tag["test_function"])

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
                    cmd.append(target)
            else:
                cmd.append(part)
        return cmd

    def run_tests(self, dry_run: bool = False) -> int:
        results = {}  # tag_str -> 'passed' | 'failed' | 'untested'
        for _, link in self.linked_tags.items():
            targets = self.build_targets_for_link(link)
            tag_str = link["spec_tag"]["full_tag"]
            if not targets:
                spec = link["spec_tag"]
                if self.verbose:
                    print(
                        f"Warning: {tag_str} ({spec['file']}:{spec['line']}) "
                        f"has no linked tests."
                    )
                results[tag_str] = "untested"
                continue

            cmd = self.build_command_for_targets(targets)

            if dry_run:
                print(f"{tag_str}:")
                for target in targets:
                    print(f"  : {target}")
                print("  Command:", " ".join(shlex.quote(p) for p in cmd))
                continue

            print(f"Running tests for {tag_str} ...")
            res = subprocess.run(cmd, capture_output=True, text=True)
            results[tag_str] = {
                "result": "",
                "test_count": len(targets),
                "output": "",
                "error": "",
            }
            if res.returncode == 0:
                results[tag_str]["result"] = "passed"
            else:
                results[tag_str]["result"] = "failed"
                if res.stdout and self.verbose:
                    results[tag_str]["output"] = res.stdout
                    print(res.stdout)
                if res.stderr and self.verbose:
                    results[tag_str]["error"] = res.stderr
                    print(res.stderr)

        if dry_run:
            return 0

        # Summary: the traceability report.
        print("\n===== Spec tag results =====")
        failed = 0
        for tag_str, outcome in results.items():
            if outcome["result"] == "failed":
                failed += 1
                print(
                    f"  {tag_str}: ",
                    "\033[91m {}\033[00m".format(outcome["result"].upper()),
                    f" Test Count: {outcome['test_count']}",
                )
            elif outcome["result"] == "passed":
                print(
                    f"  {tag_str}: ",
                    "\033[92m {}\033[00m".format(outcome["result"].upper()),
                    f" Test Count: {outcome['test_count']}",
                )
            elif outcome["result"] == "untested":
                print(
                    f"  {tag_str}: ",
                    "\033[93m {}\033[00m".format(outcome["result"].upper()),
                    f" Test Count: {outcome['test_count']}",
                )
        print(results)
        return results

