## Spec review

### Uncovered behavioural changes (3)

**is_line_covered method body is empty (pass), so it does not return whether a line is covered; callers always receive None and cannot determine coverage status.** · confidence 92
`spec_tagger/spec_review/coverage_filter.py` — uncovered

Suggested spec item:

> is_line_covered(file: str, line: int) -> bool: returns True if the line is within the filtered covered_lines set for the given file after _filter_missing_and_covered_lines has been executed, False if the line is within the filtered missing_lines set, and raises KeyError if the file has no coverage data.

**Reports the set of lines changed in git that are not covered by tests for each changed source file that has test coverage, enabling identification of partially uncovered lines.** · confidence 85
`spec_tagger/spec_review/result_triage.py` — uncovered

Suggested spec item:

> When a changed file within the source directory has associated test coverage, the triage logic should compute and report the lines changed in git that are not covered by those tests, so that partial coverage gaps are identifiable.

**The function changed_lines_from_diff now accepts two git refs (base, head) instead of pre-computed diff text, internally fetches the unified diff via _git('diff', '-U0', base...head), and returns a dict mapping file paths to sets of added line numbers.** · confidence 90
`spec_tagger/spec_review/git_context.py` — uncovered

Suggested spec item:

> When called with base and head git refs, changed_lines_from_diff retrieves the unified diff between them and returns a dictionary of file paths to sets of line numbers that were added in the new diff, correctly parsing unified diff hunk headers and line numbers.
