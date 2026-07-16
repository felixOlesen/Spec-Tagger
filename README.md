# Spec Tagger

Tag-based spec-to-test traceability and test runner.

Spec Tagger links behavioral specifications (feature files, markdown, plain text) to the tests that verify them, using lightweight inline tags like `feat~checkout_flow~1`. It then runs only the linked tests for you, reports which spec tags are covered, and flags drift — untested specs, orphaned tests, and mismatched revisions — as part of your test loop.

Spec Tagger is designed to be as framework and language agnostic as possible. Point it at a directory of specs and a directory of tests, tell it how to invoke your test runner, and it does the crawling, linking, and invoking.

## How it works

1. **Tag your specs.** Drop a tag on any line above the requirement it describes:

   ```
   feat~checkout_flow~1
   Feature: Checkout

       story~apply_discount_code~1
       Scenario: A valid discount code reduces the total
           ...
   ```

2. **Tag your tests** the same way, as a comment above the test:

   ```python
   # story~apply_discount_code~1
   def test_discount_code_applies_percentage_off():
       ...
   ```

3. **Run `spectagger`.** It crawls both trees, links spec tags to test tags by `type~name`, and runs the matching tests through your own test command — reporting pass/fail per spec tag, not just per test.

A tag has three parts: `type~name~revision`.v

- `type` is one of `feat`, `story`, or `step` (feature / user story / step — use whichever granularity fits, they're otherwise equivalent).
- `name` is an identifier (`[A-Za-z0-9_]+`).
- `revision` is an integer, bumped when the spec's behavior changes meaningfully. If a test's revision doesn't match its spec's revision, the test is flagged as stale instead of silently passing.

## Installation

Spec Tagger has zero runtime dependencies — it's pure standard library. Requires Python 3.9+.

```bash
git clone git@github.com:felixOlesen/Spec-Tagger.git
cd Spec-Tagger
pip install -e .
```

This installs the `spectagger` CLI command via the entry point declared in [pyproject.toml](pyproject.toml).

> **Note:** [requirements.txt](requirements.txt) is a `conda list --explicit`-style export of a development environment, not a pip dependency list. It's only relevant if you're contributing to Spec Tagger itself and want to reproduce that conda environment — it is not needed to install or run the tool.

## Usage

The only required argument is `--test_command`: the shell command used to invoke your test runner, with `{tests}` as a placeholder for the resolved test targets.

```bash
spectagger --test_command "pytest {tests}"
```

By default this crawls `features/` for specs and `tests/` for tests. Both are configurable:

```bash
spectagger \
  --target_spec specs/ \
  --test_dir tests/ \
  --test_command "pytest {tests}"
```

### Key options

| Flag                     | Default                           | Description                                                                                                              |
| ------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `--target_spec`          | `features`                        | Directory, single file, or list of files to crawl for spec tags                                                          |
| `--spec_file_extensions` | `.spec,.feature,.md,.txt`         | Comma-separated extra extensions to treat as spec files                                                                  |
| `--test_dir`             | `tests`                           | Root directory to crawl for test tags                                                                                    |
| `--test_extensions`      | _(broad default set — see below)_ | Comma-separated extensions to treat as test files                                                                        |
| `--test_command`         | _(required)_                      | Shell command to run tests, e.g. `"pytest {tests}"`                                                                      |
| `--test_format`          | `{file}::{name}`                  | How a single test target is addressed on the CLI. `{file}` = test file path, `{name}` = test function name               |
| `--test_join`            | _(none)_                          | If set, join all resolved targets into **one** CLI argument with this separator                                          |
| `--dry_run`              | off                               | Print the resolved targets and command per spec tag without actually running tests                                       |
| `--verbose`              | off                               | Print crawler/linker internals: found files, extracted tags, and link resolution                                         |
| `--report`               | off                               | Generate a traceability report _(see [Report generation](#report-generation-work-in-progress) below — not yet wired up)_ |
| `--report_output`        | `.`                               | Directory to write the report to                                                                                         |
| `--report_type`          | `json`                            | `json`, `html`, or `stdout`                                                                                              |

### Example: matching your test framework

`--test_format` and `--test_join` exist to adapt Spec Tagger's tag-to-target resolution to how _your_ test runner addresses individual tests. A few examples:

```bash
# pytest: file::function_name targets, passed as separate args
spectagger --test_command "pytest {tests}" \
           --test_format "{file}::{name}" # Works out to: 'pytest example_test_file::test_func_name'

# Jest: run whole files (Jest tags don't resolve to a function name — see Language support)
spectagger --test_dir src --test_extensions .test.js \
           --test_command "npx jest {tests}" \
           --test_format "{file}"

# Go: one -run regex joined with '|', matched against the whole target list
spectagger --test_dir . --test_extensions .go \
           --test_command "go test -run '{tests}' ./..." \
           --test_format "{name}" --test_join "|"
```

### Dry-running before wiring into CI

Use `--dry_run` to sanity-check that your tags resolve to the targets and command you expect, without executing anything:

```bash
spectagger --test_command "pytest {tests}" --dry_run
```

```
feat~checkout_flow~1:
  : tests/test_checkout.py::test_totals_include_tax
  Command: pytest tests/test_checkout.py::test_totals_include_tax

story~apply_discount_code~1:
  : tests/test_checkout.py::test_discount_code_applies_percentage_off
  Command: pytest tests/test_checkout.py::test_discount_code_applies_percentage_off
```

### Reading the output

A normal run prints a pass/fail summary keyed by **spec tag**, not by individual test — this is the traceability payoff: you see coverage at the requirement level.

```
===== Spec tag results =====
  feat~checkout_flow~1:   PASSED  Test Count: 1
  story~apply_discount_code~1:   FAILED  Test Count: 1
```

Spec tags with no linked tests, and test tags with no matching spec (or a revision mismatch), are surfaced as invalid tags — run with `--verbose` to see the full breakdown of crawled tags, links, and invalid-tag reasons.

> **Note:** `Runner.run_tests` computes a pass/fail status (1 if anything failed), but `main.py` currently discards that return value rather than using it as the process exit code — so `spectagger` itself always exits `0` regardless of test outcomes. If you're wiring this into CI, check the printed summary rather than the exit code until this is addressed.

### Report generation (work in progress)

`--report` / `--report_output` / `--report_type` are accepted and validated by the CLI, but [`report_generation.py`](spec_tagger/report_generation.py) is currently a stub — the `Generator` class isn't yet wired into the run loop. Treat these flags as reserved for now.

## Language support

Spec Tagger separates two concerns that are supported independently:

**1. Which files get crawled for tags** (any language, no configuration needed)

Tag extraction is pure text/regex matching, so tags are recognized in _any_ file whose extension is enabled — there's no language-specific parsing at the crawl stage. Spec files default to `.spec`, `.feature`, `.md`, `.txt`; test files default to a broad set covering most mainstream languages (`.py`, `.js`, `.ts`, `.java`, `.go`, `.rb`, `.cpp`, `.cs`, `.php`, `.swift`, `.kt`, `.m`, `.scala`, `.sh`, `.pl`, `.r`, `.lua`, `.hs`, `.erl`, `.ex`, `.exs`). Both lists are extendable via `--spec_file_extensions` / `--test_extensions` for anything not covered.

**2. Which languages resolve tags down to a specific function name** (currently Python and Ruby)

After finding a tag in a test file, Spec Tagger looks at the following lines to identify which function the tag belongs to, so it can target that one test instead of the whole file. This requires a language-aware pattern, defined in [`spec_tagger/language_patterns.py`](spec_tagger/language_patterns.py):

```python
FUNC_PATTERNS = {
    '.py': re.compile(r'^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)'),
    '.rb': re.compile(r'^\s*def\s+(?:self\.)?([A-Za-z_]\w*[?!]?)'),
}
```

For extensions **not** in `FUNC_PATTERNS`, Spec Tagger falls back to **file-level granularity**: every tag in that file resolves to the whole file as the test target, rather than an individual function. Some frameworks (notably Jest and other `describe`/`it` description-based frameworks) don't always have unique function names to resolve to, so file-level targeting is used instead until `describe`/`it` can be supported.

To add function-name resolution for another language (e.g. JavaScript function declarations, Go's `func Test...`), add an entry to `FUNC_PATTERNS` with a regex whose first capturing group is the function name, plus a matching entry in `SKIP_PREFIXES` for that language's comment/decorator syntax (lines the crawler should skip over while searching for the function, such as `#` comments or `@decorator` lines in Python).

## Project architecture

```
spec_tagger/
├── main.py               CLI entry point: argument parsing and orchestration
├── spec_test_crawler.py  Crawls files and extracts tags (Crawler, SpecCrawler, TestCrawler)
├── spec_test_linker.py   Links spec tags to test tags, validates revisions (Linker)
├── test_runner.py        Builds test targets/commands and executes them (Runner)
├── report_generation.py  Report output (Generator) — stub, not yet implemented
└── language_patterns.py  Per-language regexes for function-signature resolution
```

### [`main.py`](spec_tagger/main.py)

Defines the `spectagger` CLI via `argparse`, validates the parsed arguments (`validate_args`), and wires the pipeline together in order: `SpecCrawler` → `TestCrawler` → `Linker` → `Runner`. This is the only place that knows about all four components — each of them is otherwise independent and testable in isolation.

### [`spec_test_crawler.py`](spec_tagger/spec_test_crawler.py)

The base `Crawler` class does two things: walk a directory (or file/list of files) collecting paths with enabled extensions (`crawl_files`), then scan each file line-by-line for tags matching the tag regex (`extract_tags`). The tag regex uses lookbehind/lookahead assertions to avoid partial matches inside longer tag-like strings, and a single line can contain multiple tags.

Two subclasses specialize this:

- **`SpecCrawler`** — crawls spec files. `directory_or_files` can be a directory (walked recursively), a list of explicit file paths, or a single file path; `crawl_files` is overridden to handle all three cases and warns about any explicitly-listed files that weren't found or don't have an enabled extension.
- **`TestCrawler`** — crawls test files, then does one extra pass (`extract_and_assign_test_declarations`) to resolve each tag to a specific test function name, as described in [Language support](#language-support) above. It scans up to 20 lines (`LINE_STOP_CONDITION`) past each tag, skipping over blank lines and lines matching that language's `SKIP_PREFIXES` (comments/decorators), and stops at the first line matching `FUNC_PATTERNS` — or the first non-skippable, non-matching line, whichever comes first. A tag that fails to resolve to a function gets `test_function = None`, which the `Linker` later treats as invalid.

### [`spec_test_linker.py`](spec_tagger/spec_test_linker.py)

The `Linker` takes the crawled spec tags and test tags and reconciles them into `linked_tags`: a dict keyed by `type~name`, each entry holding one `spec_tag` and a list of matching `test_tags`. Along the way it flags problems into `invalid_tags`, each with a reason:

- **Duplicate tags** — the same exact tag (including revision) appears more than once.
- **Multiple revisions of the same `type~name`** — e.g. `feat~x~1` and `feat~x~2` both present; the older revision is flagged and the highest revision wins as canonical.
- **Test tag with no matching spec tag** — an orphaned test.
- **Test tag whose function couldn't be resolved** (`test_function is None`) — treated as invalid rather than silently linked.
- **Spec tag with no matching test tag at all** — uncovered spec.
- **Revision mismatch** between an otherwise-matching spec tag and test tag — the test is excluded from that link (stale test).

Entries that end up with zero valid test tags are dropped from `linked_tags` entirely, so `Runner` only ever sees fully-resolved, valid links. `display_data()` is a verbose-mode dump of everything crawled, linked, and flagged.

### [`test_runner.py`](spec_tagger/test_runner.py)

The `Runner` turns `linked_tags` into actual subprocess invocations, one per spec tag:

1. `build_targets_for_link` — for each spec tag's test tags, formats each into a CLI-addressable target string via `test_format` (`{file}`/`{name}` placeholders). It also dedupes and prunes redundant targets: if a whole file is already a target (no resolved function — the file-level fallback case), individual function-level targets within that same file are skipped, since running the file covers them. If `test_join` is set, all targets collapse into a single joined string (for runners like `go test -run` that take one regex rather than a target list).
2. `build_command_for_targets` — tokenizes `test_command` with `shlex.split` and substitutes the `{tests}`/`{files}` placeholder token with the resolved target(s), so arbitrary shell-style commands can be built safely without a literal shell.
3. `run_tests` — for each spec tag, runs the built command via `subprocess.run` (or just prints it, under `--dry_run`), classifies the result as `passed`/`failed`/`untested`, and prints a colored (`\033[92m`/`\033[91m`) per-spec-tag summary at the end. It returns `1` if anything failed and `0` otherwise, though `main.py` doesn't currently propagate that value to the process exit code (see note above).

### [`report_generation.py`](spec_tagger/report_generation.py)

Currently an empty stub (`Generator` with just `__init__`). The CLI already validates `--report`/`--report_output`/`--report_type` in `main.py`, but nothing calls into `Generator` yet — this is the natural extension point for turning `Runner`'s results and `Linker`'s invalid-tag list into a persisted JSON/HTML/stdout traceability report.

### [`language_patterns.py`](spec_tagger/language_patterns.py)

Pure data: `FUNC_PATTERNS` (extension → regex for extracting a function name) and `SKIP_PREFIXES` (extension → tuple of line prefixes the crawler should skip past, such as comments and decorators) as described under [Language support](#language-support).

## Testing

Spec Tagger tests itself using its own tag format — see [`features/`](features/) for the specs and [`tests/crawler_test.py`](tests/crawler_test.py) for the linked pytest tests, plus [`test_data/`](test_data/) for example tests and specs to run the code against. Run the suite directly with pytest:

```bash
pytest
```

or, to exercise the traceability loop against its own specs:

```bash
spectagger --target_spec features --test_dir tests --test_command "pytest {tests}" --test_format "{file}::{name}"
```
