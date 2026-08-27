from functools import lru_cache
from pathlib import Path
import subprocess
import os
from spec_tagger.merge_analysis.symbol_extraction import SymbolExtractor
from spec_tagger.merge_analysis.language_support import EXT_TO_LANG
import re
from itertools import combinations
from spec_tagger.merge_analysis.clustering import (
    build_groups,
    analyse_group,
    rank_candidates,
    report,
)


class ChangeSearch:
    def __init__(self, spec_prefix, test_prefix, src_prefix) -> None:
        self.src_prefix = src_prefix
        self.spec_prefix = spec_prefix
        self.test_prefix = test_prefix
        self.threshold = 0.2

        self.base = os.environ.get("GITHUB_BASE_REF") or "origin/main"
        self.head = os.environ.get("GITHUB_SHA") or "HEAD"
        self.diff_range = f"{self.base}...{self.head}"

        self.symbol_extractor = SymbolExtractor()

    def run(self):
        # Initial Scan of git logs
        scanned_entries = self._initial_scan()

        # Translate logs into ranked items based on internal jaccard similarity of respective bags of words
        complete_matrices = {}
        incomplete_matrices = {}
        for merge_sha, pr_content in scanned_entries.items():
            complete_matrix = self._make_complete_relatedness_matrix(pr_content)
            if complete_matrix:
                print(f"\n{merge_sha}: COMPLETE CHANGE FOUND")
                complete_matrices[merge_sha] = complete_matrix
                print(complete_matrices[merge_sha])

            incomplete_matrix = self._incomplete_relatedness_matrix(pr_content)
            if incomplete_matrix:
                print(f"\n{merge_sha}: INCOMPLETE CHANGE FOUND")
                incomplete_matrices[merge_sha] = incomplete_matrix
                print(incomplete_matrices[merge_sha])

        # Report on the incomplete commits found to judge which ones are right for testing
        for merge_sha, matrix in incomplete_matrices.items():
            all_commits = [sha for sha, _ in scanned_entries[merge_sha]["all_changes"]]
            change_types_by_commit = dict(scanned_entries[merge_sha]["all_changes"])
            chronological = self._git(
                "rev-list", "--reverse", f"{merge_sha}^1..{merge_sha}"
            ).splitlines()
            groups = [
                analyse_group(g, change_types_by_commit, chronological)
                for g in build_groups(matrix, all_commits, self.threshold)
            ]
            print(report(groups))

        commit_times = self._get_commit_times()
        return incomplete_matrices, complete_matrices, commit_times

    def _get_commit_times(self):
        out = self._git("log", "--format=%H %ct", "--all")
        return {
            line.split()[0]: int(line.split()[1]) for line in out.splitlines() if line
        }

    @lru_cache(maxsize=None)
    def _git(self, *args: str) -> str:
        """Run a git command, returning the stdout of the command. Empty string returned on failure."""
        try:
            return subprocess.run(
                ["git", *args],
                capture_output=True,
                text=True,
                errors="replace",
                check=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def _initial_scan(self):
        # First, scan through the merge signatures and hashmap them
        # Then, Scan through the commits between merges, identifying sole implementation,
        # test, or spec changes that may be updated later
        # Print them out in a nice way to figure out promising candidates
        merge_list = self._git(
            "log",
            "--format=COMMIT %H",
            "--name-only",
            "--merges",
            "-m",
            "--first-parent",
        ).splitlines()
        merge_hashes = {}
        for merge in merge_list:
            if merge.startswith("COMMIT"):
                hash = merge.split(" ")[1]
                merge_hashes[hash] = self._git(
                    "rev-list", f"{hash}^1..{hash}", "--reverse"
                ).splitlines()

        per_pr = {}
        for merge_sha, commits in merge_hashes.items():
            per_commit = {}
            for sha in commits:
                files = self._git("show", "--name-only", "--format=", sha).splitlines()
                per_commit[sha] = self._classify_commit(files)
            kinds_in_pr = set().union(*per_commit.values())
            isolated = {}
            incomplete_mixed = {}
            complete_mixed = {}
            all_changes = []
            for s, k in per_commit.items():
                if len(k) == 1:
                    isolated[s] = k
                elif len(k) == 2:
                    incomplete_mixed[s] = k
                elif len(k) == 3:
                    complete_mixed[s] = k
                all_changes.append((s, k))
            if incomplete_mixed or isolated or complete_mixed:
                per_pr[merge_sha] = {}

            if merge_sha in per_pr:
                if kinds_in_pr:
                    per_pr[merge_sha]["change_types"] = kinds_in_pr

                if isolated:
                    per_pr[merge_sha]["isolated_changes"] = isolated

                if incomplete_mixed:
                    per_pr[merge_sha]["incomplete_mixed_changes"] = incomplete_mixed

                if complete_mixed:
                    per_pr[merge_sha]["complete_mixed_changes"] = complete_mixed
                per_pr[merge_sha]["all_changes"] = all_changes
        return per_pr

    def _make_complete_relatedness_matrix(self, pr_content) -> None | dict:
        complete_matrix = {}
        for sha, change_types in pr_content["all_changes"]:
            if len(change_types) == 3:
                spec_diff = self._git(
                    "diff", "-U0", f"{sha}^1..{sha}", "--", f"{self.spec_prefix}"
                )
                test_diff = self._git(
                    "diff", "-U0", f"{sha}^1..{sha}", "--", f"{self.test_prefix}"
                )
                src_diff = self._git(
                    "diff", "-U0", f"{sha}^1..{sha}", "--", f"{self.src_prefix}"
                )
                test_changed_lines = self._changed_lines(test_diff)
                test_symbols = self._get_symbols_from_changed_lines(
                    sha, test_changed_lines
                )

                src_changed_lines = self._changed_lines(src_diff)
                src_symbols = self._get_symbols_from_changed_lines(
                    sha, src_changed_lines
                )
                spec_vs_test = self.symbol_extractor.relatedness_spec_to_code(
                    spec_diff, test_symbols
                )
                spec_vs_src = self.symbol_extractor.relatedness_spec_to_code(
                    spec_diff, src_symbols
                )

                test_vs_src = self.symbol_extractor.relatedness_code_to_code(
                    test_symbols, src_symbols
                )
                if sha not in complete_matrix and (
                    spec_vs_test > self.threshold
                    or spec_vs_src > self.threshold
                    or test_vs_src > self.threshold
                ):
                    complete_matrix[sha] = {}
                if any(
                    s > self.threshold for s in (spec_vs_test, spec_vs_src, test_vs_src)
                ):
                    complete_matrix[sha]["spec_test"] = spec_vs_test
                    complete_matrix[sha]["spec_src"] = spec_vs_src
                    complete_matrix[sha]["test_src"] = test_vs_src
        return complete_matrix

    def _diff(self, sha: str, prefix: str) -> str:
        return self._git(
            "diff",
            "-U0",
            f"{sha}^1..{sha}",
            "--",
            f"{prefix}",
        )

    def _get_symbols_from_changed_lines(self, sha, changed_line_dict):
        symbols = set()
        for path, lines in changed_line_dict.items():
            lang = EXT_TO_LANG.get(Path(path).suffix)
            if not lang or not lines:
                continue
            source = self._git("show", f"{sha}:{path}")
            symbols |= self.symbol_extractor.tree_sitter_code_symbols(
                source, lines, lang
            )
        return symbols

    def _incomplete_relatedness_matrix(self, pr_content):
        CHANGE_TYPES = (
            ("spec", self.spec_prefix),
            ("test", self.test_prefix),
            ("src", self.src_prefix),
        )
        cache: dict[str, dict[str, set]] = {}
        for sha, change_types in pr_content["all_changes"]:
            entry = {}
            for change_type, prefix in CHANGE_TYPES:
                if change_type not in change_types:
                    continue
                diff = self._diff(sha, prefix)
                if not diff:
                    continue
                if change_type == "spec":
                    entry[change_type] = self.symbol_extractor._prose_words(diff)
                else:
                    entry[change_type] = self._get_symbols_from_changed_lines(
                        sha, self._changed_lines(diff)
                    )
            if entry:
                cache[sha] = entry

        matrix: dict[tuple[str, str], dict[str, float]] = {}
        for a, b in combinations(cache, 2):
            scores = {
                f"{ka}->{kb}": self.jaccard(va, vb)
                for ka, va in cache[a].items()
                for kb, vb in cache[b].items()
            }
            if any(s >= self.threshold for s in scores.values()):
                matrix[(a, b)] = scores
        return matrix

    def jaccard(self, a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def _classify_commit(self, commit_files: list[str]) -> set[str]:
        result = set()
        for filename in commit_files:
            if filename.startswith(self.spec_prefix):
                result.add("spec")
            elif filename.startswith(self.src_prefix):
                result.add("src")
            elif filename.startswith(self.test_prefix):
                result.add("test")
        return result

    def _changed_lines(self, diff_text: str) -> dict[str, set[int]]:
        HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
        out: dict[str, set[int]] = {}
        current, new_line = None, 0

        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current = line[6:]
                out.setdefault(current, set())
            elif line.startswith("+++ /dev/null"):
                current = None
            elif m := HUNK.match(line):
                new_line = int(m.group(1))
            elif current and line.startswith("+"):
                out[current].add(new_line)
                new_line += 1
            elif current and not line.startswith("-"):
                new_line += 1

        return out
