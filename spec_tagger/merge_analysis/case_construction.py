import subprocess
from pathlib import Path
from datetime import datetime, timezone
import time


class CaseConstructor:
    def __init__(
        self,
        complete_matrices,
        case_dir_path,
        repo_abs_path,
        spec_prefix,
        test_prefix,
        src_prefix,
        commit_times,
    ) -> None:
        self.complete_matrices = complete_matrices
        self.case_dir_path = Path(case_dir_path)
        self.repo_abs_path = Path(repo_abs_path)
        self.spec_prefix = Path(spec_prefix)
        self.test_prefix = Path(test_prefix)
        self.src_prefix = Path(src_prefix)
        self.commit_times = commit_times

    def run(self):
        # Complete Cases Construction
        self._complete_case_construction()

    def _complete_case_construction(self):
        if not self.complete_matrices:
            return
        # for merge_sha, complete_commits in self.complete_matrices.items():
        sorted_cases = self._sort_complete_cases_by_similarity(self.complete_matrices)
        self._generate_diff_files(sorted_cases)

    def _sort_complete_cases_by_similarity(self, complete_matrix):
        from statistics import mean

        cutoff = time.time() - (5 * 365 * 24 * 3600)
        flat = [
            (merge_sha, commit_sha, scores)
            for merge_sha, commits in complete_matrix.items()
            for commit_sha, scores in commits.items()
        ]
        # Sorts the entries by viable times based on a cutoff (last 5 years)
        # This prevents encountering difficult-to-set-up development environments
        viable = [
            (merge_sha, commit_sha, scores)
            for merge_sha, commit_sha, scores in flat
            if self.commit_times.get(commit_sha) >= cutoff
        ]

        best = sorted(viable, key=lambda t: mean(t[2].values()), reverse=True)
        print(f"flat={len(flat)}  viable={len(viable)}  times={len(self.commit_times)}")
        print("sample key:", next(iter(self.commit_times.items()), None))
        for _, commit_sha, _ in flat:
            print(commit_sha, "->", self.commit_times.get(commit_sha, "MISSING"))
        print("cutoff:", cutoff, datetime.fromtimestamp(cutoff, tz=timezone.utc))
        for merge_sha, commit_sha, scores in best:
            pairs = "  ".join(f"{k}={v:.3f}" for k, v in sorted(scores.items()))
            print(f"{commit_sha[:8]}  {pairs}")
        return best

    def _generate_diff_files(self, sorted_cases):
        for i, (merge_sha, commit_sha, scores) in enumerate(sorted_cases[:10], 1):
            path = self._capture_case(merge_sha, commit_sha, f"case-{i:02d}")
            print(f"case-{i:02d}  {commit_sha[:8]}  ->  {path}")

    def _capture_case(self, merge_sha: str, commit_sha: str, case_id: str) -> Path:
        """Save per-artifact diffs plus metadata for one candidate commit."""
        ARTIFACTS = {
            "spec": self.spec_prefix,
            "test": self.test_prefix,
            "src": self.src_prefix,
        }
        output_dir = self.case_dir_path / case_id
        output_dir.mkdir(parents=True, exist_ok=True)

        def git(*args) -> str:
            return subprocess.run(
                ["git", "-C", self.repo_abs_path, *args],
                capture_output=True,
                text=True,
                errors="replace",
                check=True,
            ).stdout

        parent = git("rev-parse", f"{commit_sha}^").strip()

        for name, prefix in ARTIFACTS.items():
            diff = git("diff", parent, commit_sha, "--", prefix)
            if diff.strip():
                (output_dir / f"{name}.diff").write_text(diff, encoding="utf-8")
        timestamp = self.commit_times.get(commit_sha)
        date_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
            "%Y-%m-%d UTC"
        )
        (output_dir / "meta.txt").write_text(
            f"case_id:    {case_id}\n"
            f"merge:      {merge_sha}\n"
            f"commit:     {commit_sha}\n"
            f"parent:     {parent}\n\n"
            f"time:     {date_str}\n\n"
            f"--- message ---\n{git('log', '-1', '--format=%s%n%n%b', commit_sha)}\n"
            f"--- files ---\n{git('show', '--stat', '--format=', commit_sha)}\n",
            encoding="utf-8",
        )
        return output_dir
