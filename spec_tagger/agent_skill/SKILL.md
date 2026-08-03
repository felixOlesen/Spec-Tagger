---
name: spectagger
description: Audit and maintain spec traceability for a project using the spectagger CLI — links specification items to the tests that verify them via revision-numbered tags, runs those tests, and reports where the spec, tests, and code have diverged. Use this skill whenever the user mentions spec drift, traceability, spec tags or tag revisions, or asks why a requirement shows as untested, which tests cover a spec item, whether the specs are still accurate, or asks to tag a project, fix broken or stale spec links, or check that the spec matches the implementation — even if they don't name spectagger. Also use it when working in a repo containing tags like [feat~name~1], [story~name~1], and/or [step~name~1]. 
---
# SpecTagger

[instructions]

## Running The Spec Tagger Tool

Only `--test_command` is genuinely required — everything else has a default. Run
`spectagger --help` for the full, current list; the flags below are the ones that
change behaviour most.

### Start with the cheapest checks

Two flags let you validate the tag graph before spending time on tests:

- `--tag_check` stops after identifying invalid tags and never runs the suite.
  Use it first when tagging a project or diagnosing broken links — it isolates
  tag problems from test problems.
- `--dry_run` resolves the spec-to-test links and shows what would run, without
  executing anything. This catches wrong framework detection, malformed test
  targets, and tags that resolve to nothing in seconds rather than after a slow
  failing suite.

Read the dry-run output before proceeding: check that each spec tag lists the
tests you expect and that no tag reports zero targets unexpectedly.

### Pointing it at the right files

- `--target_spec` (default `features`) — the spec directory, file, or
  comma-separated list of files to read. Every path listed must exist.
- `--test_dir` (default `tests`) — root directory containing the test files to
  crawl. Must exist.
- `--target_tag` — restrict the run to a single tag. Invaluable for
  investigating one spec item rather than auditing everything. Must match
  `feat|story|step~name~revision`.
- `--spec_file_extensions` / `--test_extensions` — comma-separated extension
  allow-lists, when the defaults pick up the wrong files.

### Running the tests

- `--test_command` (**required**) — how the suite is invoked, e.g.
  `pytest {tests}`. `{tests}` is replaced with the resolved targets.
- `--test_format` (default `{file}::{name}`) — how a *single* test is addressed.
  `{file}` is the test file path, `{name}` the test function name. The default
  is pytest-style; other frameworks need different forms (minitest wants
  `{file} -n /^{name}$/`, RSpec `{file}:{line}`). Getting this wrong is the most
  common cause of the tool running the wrong tests — or the whole suite — while
  appearing to work. See `references/frameworks.md`.
- `--test_framework` — skip detection by naming the framework. Worth setting
  when detection is ambiguous: the test command cannot distinguish classic
  minitest from minitest-spec, or pytest-style from unittest-style, because the
  invocation is identical. Without a framework, the tool falls back to
  file-level testing rather than targeting individual tests.
- `--test_join` — join all targets into one argument with this separator instead
  of passing them separately (e.g. `|` for `go test -run`). Use when the runner
  expects a single alternation pattern rather than a list.
- `--one_by_one` — run each test in its own subprocess. Significantly slower, so
  reach for it only when you need per-test attribution: knowing *which* linked
  test failed, rather than that the group did.

### Reporting

`--report` enables report generation and requires `--report_output` to be an
**existing** directory — create it first, or the run fails validation.
`--report_type` accepts `json`, `html`, or `stdout` (default `json`).

Add `--verbose` when diagnosing: it surfaces undetected files and unresolved
tags that are otherwise silent.

### Example

```bash
# 1. validate the tag graph only
spectagger --target_spec features --test_dir tests --tag_check \
           --test_command "pytest {tests}"

# 2. see what would run
spectagger --target_spec features --test_dir tests --dry_run \
           --test_command "pytest {tests}"

# 3. run, with a report
mkdir -p report
spectagger --target_spec features --test_dir tests \
           --test_command "pytest {tests}" \
           --report --report_type html --report_output report
```

To investigate one spec item:

```bash
spectagger --target_tag story~adding_two_valid_nums~1 \
           --test_command "pytest {tests}" --one_by_one --verbose
```

## Responding to Tool Results

The tool reports facts; deciding what those facts mean is your job. Work in this
order — diagnose the kind of drift, gather the evidence that discriminates
between its possible causes, then act only within the tier that finding allows.

Two rules govern everything below. **Diagnose before acting**: the same symptom
has several possible causes, and the right response differs completely between
them. **Never resolve a judgement silently**: where intent is involved, present
the evidence and let the user decide.

---

### The four kinds of drift

Name the drift before choosing an action — each kind has a different fix and a
different level of certainty.

| Kind | What it means | How it surfaces | Detectable by |
|---|---|---|---|
| **Link drift** | The connection between spec and test is broken or stale | Invalid tag; unresolved reference; revision mismatch | Deterministic — the tool is right |
| **Coverage drift** | The spec is accurate but nothing verifies it any more | Spec item reports `untested` | Deterministic |
| **Prose drift** | The spec describes behaviour the code no longer has | Linked test fails; or passes while the prose says otherwise | Partly — needs judgement |
| **Semantic drift** | Tag resolves, test passes, but the test no longer verifies what the prose claims | *Nothing* — everything looks intact | Judgement only |

Semantic drift is the dangerous one precisely because the tool cannot see it. A
green run is not evidence the spec is accurate. When reviewing a spec item, read
the prose against what the linked tests actually assert — do not infer
correctness from a passing result.

---

### Responding to `untested`

Ambiguous, and the ambiguity is the whole problem. Establish which case applies
before reporting anything, because they range from "expected" to "serious".

1. **Never covered.** A new spec item that has not been tagged onto any test.
   Expected; report as an open coverage gap, not an error. Propose candidate
   tests, or propose writing one.
2. **Coverage regressed.** Tags existed previously and no longer do — a test was
   deleted, renamed, or moved. This is a genuine loss of verification and should
   be reported prominently. Distinguishing this from case 1 needs history: check
   whether the tag appears in earlier revisions of the test files.
3. **Tag misplaced.** The tag exists but the crawler could not bind it. Check
   placement first: the tag must sit within 10 lines above its test with no
   other test definition in between. Report the tag's location and what was
   found instead — this is a fixable authoring mistake, not missing coverage.
4. **Framework undetected.** The test file's framework was never identified, so
   its tests were never crawled and every tag in it reports untested. Re-run with
   `--verbose` to list undetected files. Suspect this whenever *several* items in
   the same file report untested at once.

Before concluding coverage is missing, rule out 3 and 4 — they are tooling
problems that masquerade as coverage problems, and reporting them as missing
coverage sends the user to fix the wrong thing.

---

### Responding to invalid tags

Diagnose the cause; the corrections are opposites.

- **References a non-existent ID.** Usually a typo or a renamed spec item.
  Propose the correction, suggesting the closest existing ID. Never create a
  spec item to make a tag resolve.
- **References a stale revision.** The spec moved to `~2`; the tag still claims
  `~1`. This is the designed signal, not a fault: it means the test has not been
  re-verified against the new meaning. Resolution requires a human confirming
  the test still covers the new prose. Propose; do not auto-bump.
- **Orphaned by a deleted spec item.** Propose repointing or removing the tag.
  Never delete test code to clear the warning.
- **Malformed.** Propose the corrected `type~name~revision` form.

---

### Responding to `failed`

The strongest drift signal available, and the one most often mishandled. Exactly
one of three things has happened.

First, confirm the failure is attributable: a test failing at head that was
already failing at base is not evidence of drift from this change.

Then gather the evidence that discriminates:

- what the diff actually changed;
- what the commit messages and PR description *claim* the change does;
- what the spec prose says the behaviour should be;
- what the failing assertion expected versus received.

| Cause | Indicators | Action |
|---|---|---|
| **The code is wrong** | Nothing in the messages claims a behaviour change; the diff looks like a refactor or fix; spec and test agree with each other | Report as a probable regression. The tool just caught a real bug — this is the highest-value outcome |
| **The test is wrong** | Messages describe a deliberate behaviour change; the spec already reflects it; only the test lags | Propose the test update; check whether the spec also needs a revision bump |
| **The spec is wrong** | Messages describe a deliberate change; the code and test agree; the prose describes older intent | Propose the prose change and a revision bump, then re-verify every linked test |

State which cause the evidence favours and why, then let the user confirm. The
cost of guessing wrong runs both ways: treating a regression as "the spec needs
updating" enshrines a bug as intended behaviour, while treating a deliberate
change as a regression blocks legitimate work.

Where several tests share a tag, note the pattern — all failing suggests the
behaviour changed; one failing among several suggests that specific test is
wrong. Re-run with `--one_by_one` if you need per-test attribution.

---

### Responding to `passed`

A pass means only that nothing the linked tests assert on broke. It does not
mean behaviour is unchanged; it can equally mean behaviour changed and the tests
were too weak to notice.

So do not report a clean run as evidence the spec is accurate. If the user is
asking whether the spec still matches reality, a green result is a necessary but
insufficient answer — read the prose against what the tests actually assert, and
say plainly which spec items you checked that way and which you did not.

A pass combined with a materially changed implementation is worth flagging:
either the change was behaviour-preserving, or it changed behaviour nothing
verifies. Both are worth a sentence in the report.

---

### Choosing what you may do about it

Every finding falls into one of three tiers, and the tier — not your confidence
— determines what action is permitted.

**Auto.** Reversible, mechanical, unambiguous. Only two members: forward tag
propagation to an already-decided revision where the lagging test is confirmed
consistent, and re-anchoring a tag after a pure rename or move. Apply as a
clearly labelled, revertible change; never silently.

**Propose.** Anything requiring a judgement about whether a change was material,
or a new revision number whose correct value is not obvious. Suggest the edit;
do not apply it.

**Never auto.** Revision *decrements* or rollbacks; any edit to spec prose or
test logic; merge collisions. A revision bump with no matching content change
looks like a mistake, but may be a deliberate signal to force re-review —
rolling it back destroys intent the tool cannot see. Explain what you observed
and ask.

When judging whether a change is material enough to warrant a revision bump,
apply two filters in order. First mechanically: ignore whitespace, formatting,
comment-only edits, and pure renames — if nothing survives, no bump is needed.
Only then ask the real question: *does this change what the spec describes, or
what the test verifies?* Bias toward material unless clearly cosmetic —
over-flagging costs a moment of review, under-flagging lets drift through
silently, which is the failure this tool exists to prevent.

---

### Reporting

Lead with drift findings, grouped by tier. A list of passing tags is far less
interesting than one genuine contradiction, and burying a finding beneath a
coverage summary defeats the point of the run.

For each finding, state: which spec item, what was observed, which kind of drift
it indicates, what the evidence suggests, and what you propose. Where confidence
is low, say so — a flagged uncertainty is useful; a confident wrong diagnosis is
expensive.

---

## Tagging

### Tag anatomy

A tag has three parts: `type~name~revision`.

```
story~adding_two_valid_nums~1
│     │                     └── revision: bump when the MEANING changes
│     └── name: snake_case, describes the behaviour, stable across revisions
└── type: feat | story | step | req — the kind of spec element
```

The revision is what makes drift detectable. Bumping it invalidates every test
tag still claiming the old revision, so a meaning change automatically flags
exactly the tests that need re-verifying. Never renumber a revision to make a
mismatch disappear — the mismatch is the signal.

---

### Placing tags in the specification

Granularity is your choice: a feature, a scenario, or an individual step may
each carry its own tag. Tag at the level the behaviour is actually verifiable —
a step-level tag is only worth adding if a test can meaningfully target that
step alone.

Placement differs by element type, and the crawler relies on it:

- **Feature or story tags** go on the line **directly above** the element they
  describe.
- **Step tags** go on the **same line** as the step, separated by at least one
  space.

```gherkin
# story~adding_two_valid_nums~1
Scenario: Adding two valid numbers
    Given the calculator is open
    When I add 2 and 3          # step~sum_two_operands~1
    Then the result is 5
```

---

### Assigning spec tags to tests

Work through the spec first, then the tests. For each tagged spec element, find
the test functions whose behaviour corresponds to it and copy the tag onto them.

The relationship is many-to-many, and both directions are legitimate:

- **One spec tag → many tests.** Fine whenever it makes behavioural sense — a
  single story is often covered by a unit test, an integration test, and an
  end-to-end test. Tag all of them.
- **One test → many spec tags.** Also fine. Put the tags on the same line,
  separated by spaces.

Placement in test files:

- Ideally on the line **directly above** the test function declaration.
- At most **10 lines above** it.
- **No other test definition may appear between a tag and the test it belongs
  to** — the crawler binds a tag to the next test it encounters, so an
  intervening definition silently steals the tag.

```python
# story~adding_two_valid_nums~1 story~result_is_displayed~1
def test_adds_two_positive_integers():
    ...
```

Match on **behaviour, not vocabulary**. A test named `test_sum` that verifies
the addition story is a match; a test that merely mentions the same words but
verifies something else is not. If no test covers a tagged spec element, leave
it untagged and report it — an uncovered spec item is a real finding, and
inventing a link to suppress the warning destroys the signal the tool exists to
produce.

---

### Recording assignment confidence

Every spec-to-test assignment is a judgement, and some are far less certain than
others. Record that uncertainty rather than hiding it: above each tag line in a
test file, add a comment with a confidence score out of 100 for that assignment.

```python
# confidence: 95
# story~adding_two_valid_nums~1
def test_adds_two_positive_integers():
    ...
```

Where a test carries several tags with differing confidence, note each:

```python
# confidence: story~adding_two_valid_nums~1=90 story~result_is_displayed~1=55
```

Scores are for the human reviewing the work — they direct attention to the
assignments most likely to be wrong. A low score is useful information, not a
failure, so report it honestly rather than inflating it. Treat anything below
roughly 70 as needing explicit review, and say so when presenting results.

---

### Asking before assuming

Ask clarifying questions rather than guessing when:

- the appropriate tagging granularity is unclear (feature vs scenario vs step);
- a spec element has no plausible test, or a test matches no spec element;
- an existing tag's revision disagrees with the spec's, since resolving that is
  a drift decision, not a tagging one;
- the type prefix to use for a new element is ambiguous.

A wrong tag is worse than a missing one: a missing tag surfaces as an uncovered
spec item, which is visible and correct. A wrong tag reports coverage that does
not exist.

---  
