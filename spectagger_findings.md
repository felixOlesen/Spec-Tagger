## Spec review

### Uncovered behavioural changes (3)

**An unrecognized report_type generates no report file and prints an invalid report type message.** · confidence 95
`features/report_generation.feature` — spec only

Suggested spec item:

> > If report_type is not one of the recognized types (json, html, stdout), the generation is aborted, an invalid type message is printed, and no report file is written to disk.

<details><summary>Evidence</summary>

```
Given report_type is not one of `json`, `html`, or `stdout`
When the report is generated
Then a message is printed saying the report type is invalid
And no report file is written
```

</details>

**Report construction is skipped when successful_links is empty, printing a warning and omitting test results, coverage data, and invalid tags from the report object.** · confidence 95
`features/report_generation.feature` — spec only

**The `spec-review` sub-command invokes `create_prompt()` which returns `Please tag the specification with new information` to prompt the user for tagging the specification.** · confidence 95
`spec_tagger/spec_review/system_prompt_creation.py` — uncovered
