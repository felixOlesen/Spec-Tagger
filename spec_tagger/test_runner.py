import subprocess
import shlex

class Runner:
    def __init__(self, test_run_command, test_format, test_join, linked_tags, verbose):
        self.test_run_command = test_run_command
        self.test_format = test_format
        self.linked_tags = linked_tags
        self.test_join = test_join
        self.verbose = verbose

    def format_target(self, tag):
        if 'test_function' not in tag:
            return tag['filename']
        return self.test_format.format(file=tag['filename'], name=tag['test_function'])

    def build_targets_for_link(self, link):
        # Dedupe and prune within this one spec tag's tests.
        targets = []
        seen = set()
        file_level = set()

        for test_tag in link['test_tags']:
            if test_tag.get('test_function') is None:
                file_level.add(test_tag['filename'])

        for test_tag in link['test_tags']:
            target = self.format_target(test_tag)
            file_part = target.split('::')[0]
            if target not in file_level and file_part in file_level:
                continue                      # whole file already runs, skip
            if target not in seen:
                seen.add(target)
                targets.append(target)

        if self.test_join is not None and targets:
            targets = [self.test_join.join(targets)]
        return targets
    
    def build_command_for_targets(self, targets):
        cmd = []
        for part in shlex.split(self.test_run_command):
            if part == '{tests}' or part == '{files}':
                for target in targets:
                    cmd.append(target)
            else:
                cmd.append(part)
        return cmd

    def report_coverage(self):
        untested = []
        for tag_str, link in self.linked_tags.items():
            if len(link['test_tags']) == 0:
                untested.append(tag_str)
                spec = link['spec_tag']
                if self.verbose:
                    print(f"Warning: {tag_str} ({spec['file']}:{spec['line']}) "
                        f"has no linked tests.")
        return untested

    def run_tests(self, dry_run=False):
        results = {}          # tag_str -> 'passed' | 'failed' | 'untested'

        for tag_str, link in self.linked_tags.items():
            targets = self.build_targets_for_link(link)

            if not targets:
                spec = link['spec_tag']
                if self.verbose:
                    print(f"Warning: {tag_str} ({spec['file']}:{spec['line']}) "
                        f"has no linked tests.")
                results[tag_str] = 'untested'
                continue

            cmd = self.build_command_for_targets(targets)

            if dry_run:
                print(f"{tag_str}:")
                for target in targets:
                    print(f"  → {target}")
                print("  Command:", ' '.join(shlex.quote(p) for p in cmd))
                continue

            print(f"Running tests for {tag_str} ...")
            res = subprocess.run(cmd, capture_output=True, text=True)

            if res.returncode == 0:
                results[tag_str] = 'passed'
            else:
                results[tag_str] = 'failed'
                if res.stdout and self.verbose:
                    print(res.stdout)
                if res.stderr and self.verbose:
                    print(res.stderr)

        if dry_run:
            return 0

        # Summary: the traceability report.
        print("\n===== Spec tag results =====")
        failed = 0
        for tag_str, outcome in results.items():
            print(f"  {tag_str}: {outcome.upper()}")
            if outcome == 'failed':
                failed += 1

        return 1 if failed else 0