## Spec review

### Uncovered behavioural changes (1)

**CoverageFilter._filter_missing_and_covered_lines updates per-file covered and missing line sets and removes any missing lines that are also covered, so that file_to_missing_lines only contains lines that are genuinely uncovered.** · confidence 95
`spec_tagger/spec_review/coverage_filter.py` — uncovered

Suggested spec item:

> Given a coverage dictionary, CoverageFilter maintains file-to-covered-lines and file-to-missing-lines sets, and filters missing lines by removing those present in the covered set, ensuring missing lines are truly uncovered.

<details><summary>Evidence</summary>

```
if len(missing_lines) == 0 and len(covered_lines) == 0: continue
self.file_to_missing_lines[file] -= self.file_to_covered_lines[file]
```

</details>
