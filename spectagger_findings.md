## Spec review

### Uncovered behavioural changes (1)

**Returns whether a specific line number in a given file is considered covered, based on the filtered coverage data (a line is covered if it appears in the file's covered_lines set and is not present in the filtered missing_lines set after overlap removal).** · confidence 92
`spec_tagger/spec_review/coverage_filter.py` — uncovered

Suggested spec item:

> Given a file path and line number, the CoverageFilter.is_line_covered method returns True if the line is within the set of covered lines for that file after filtering out overlapping missing lines, and False otherwise.

<details><summary>Evidence</summary>

```
+    def is_line_covered(self, file: str, line: int):
+        pass
```

</details>
