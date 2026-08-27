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

   For `describe`/`it`-style frameworks (RSpec, Jest) there's no unique function name to tag, so the tag goes above the block instead — see [Language support](#language-support) for how these resolve to a specific example.

3. **Run `spectagger`.** It crawls both trees, links spec tags to test tags by `type~name`, detects your test framework from `--test_command` (or trusts `--test_framework` if you pass it), and runs the matching tests through your own test command — reporting pass/fail per spec tag, not just per test.

A tag has three parts: `type~name~revision`.

- `type` is one of `feat`, `story`, or `step` (feature / user story / step — use whichever granularity fits, they're otherwise equivalent).
- `name` is an identifier (`[A-Za-z0-9_]+`).
- `revision` is an integer, bumped when the spec's behavior changes meaningfully. If a test's revision doesn't match the highest revision seen for that tag, it's flagged as stale instead of silently passing.

## Installation

Spec Tagger has zero runtime dependencies — it's pure standard library. Requires Python 3.10+.

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
| `--test_format`          | `{file}::{name}`                  | How a single test target is addressed on the CLI. `{file}` = test file path, `{name}` = resolved test name, `{line}` = the line the test/example starts at |
| `--test_framework`       | _(auto-detected)_                 | Name a registered framework (e.g. `python.pytest`, `ruby.rspec`) to skip auto-detection from `--test_command`            |
| `--one_by_one`           | off                                | Run each resolved test target as its own subprocess call instead of one command per spec tag — needed for runners that can't take multiple targets in a single invocation. Slower: one subprocess per target. |
| `--test_join`            | _(none)_                          | If set, join all resolved targets into **one** CLI argument with this separator                                          |
| `--dry_run`              | off                               | Print the resolved targets and command per spec tag without actually running tests                                       |
| `--verbose`              | off                               | Print crawler/linker internals: found files, extracted tags, and link resolution                                         |
| `--report`               | off                               | Generate a traceability report _(see [Report generation](#report-generation) below)_                                     |
| `--report_output`        | `report`                          | Directory to write the report to — must already exist                                                                    |
| `--report_type`          | `json`                            | `json`, `html`, or `stdout`                                                                                              |

### Test framework detection

Spec Tagger keeps a small registry of known frameworks in [`language_patterns.py`](spec_tagger/language_patterns.py) (`FRAMEWORKS`), each entry naming its file extensions, how it recognizes a test declaration, and a set of regexes used to spot it in a `--test_command` string. On every run, `detect_framework` scans `--test_command` against those regexes and picks the first match; pass `--test_framework` explicitly (e.g. `ruby.rspec`) to skip detection entirely, so long as it's a registered name (`framework_support_check`). If nothing matches, Spec Tagger falls back to file-level test granularity — see [Language support](#language-support).

Currently registered:

| Framework       | Extensions                  | Resolves to                             | Detected from                   |
| --------------- | ---------------------------- | ---------------------------------------- | --------------------------------- |
| `python.pytest` | `.py`                        | function name (`test...`), class-qualified when nested in a `class` (`Class::test...`) | `pytest` in the command            |
| `ruby.minitest` | `.rb`                         | function name (`test_...`)               | `ruby ... -Itest` / `minitest`     |
| `ruby.rspec`    | `.rb`                         | `describe`/`it` description path         | `rspec` in the command             |
| `js.jest`       | `.js`, `.ts`, `.jsx`, `.tsx`  | `describe`/`it`/`test` description path  | `jest` in the command              |

### Example: matching your test framework

`--test_format` and `--test_join` exist to adapt Spec Tagger's tag-to-target resolution to how _your_ test runner addresses individual tests. Framework auto-detection picks the right strategy for finding the target, but you still need to tell it how your runner expects that target on the CLI:

```bash
# pytest: file::function_name targets, passed as separate args
spectagger --test_command "pytest {tests}" \
           --test_format "{file}::{name}" # Works out to: 'pytest example_test_file::test_func_name'

# Jest: describe/it descriptions resolve to a name, matched with -t
spectagger --test_dir src --test_extensions .test.js \
           --test_command "npx jest {tests}" \
           --test_format '{file} -t "{name}"'

# RSpec: describe/it blocks resolve by line number instead of name
spectagger --test_dir spec --test_extensions .rb \
           --test_command "rspec {tests}" \
           --test_format "{file}:{line}"

# Go: one -run regex joined with '|', matched against the whole target list
spectagger --test_dir . --test_extensions .go \
           --test_command "go test -run '{tests}' ./..." \
           --test_format "{name}" --test_join "|"
```

### One-by-one test running

By default Spec Tagger builds a single command per spec tag, passing every linked test target to it at once. Some runners don't support that trivially (or you want isolated pass/fail per target rather than one combined result). Pass `--one_by_one` to run each resolved target as its own subprocess call instead:

```bash
spectagger --test_command "pytest {tests}" --one_by_one
```

This is slower — one subprocess invocation per target instead of one per spec tag — but gives per-target results in the report rather than one merged outcome.

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
  feat~checkout_flow~1:  PASSED
 Test Count: 1
 Overall: 1/1 passed.

  story~apply_discount_code~1:  FAILED
 Test Count: 1
 Overall: 0/1 passed.
```

Spec tags with no linked tests print as `UNTESTED`. Spec tags with no linked tests at all, and test tags with no matching spec (or a revision mismatch), are surfaced as invalid tags — run with `--verbose` to see the full breakdown of crawled tags, links, and invalid-tag reasons, or use `--report` for a structured version of the same information.

> **Note:** `Runner.run_tests` returns a structured results dict (used to build reports), but `main.py` never turns that into the process exit code — so `spectagger` itself always exits `0` regardless of test outcomes. If you're wiring this into CI, check the printed summary, parse the `--report` output, or grep stdout rather than relying on the exit code until this is addressed.

### Report generation

`--report` builds a traceability report combining the run's pass/fail results, the successful spec↔test links, and the invalid-tag list, written to `--report_output` (must already exist beforehand) as `--report_type`:

- **`json`** — dumps the full report object to `report.json`: one entry per spec tag with its test results, execution time, linked spec/test tag data, plus a top-level `invalid_tags` list.
- **`html`** — writes the same object to `data.js` (`window.REPORT_DATA = {...}`) and copies the static viewer (`index.html`, `style.css`, `script.js`) from [`spec_tagger/templates/`](spec_tagger/templates/) into `--report_output`, giving you a self-contained report you can open directly in a browser.
- **`stdout`** — prints an ANSI-colored summary (per spec tag: status, spec location, execution time, linked tests, and any failure output) followed by the invalid-tags list, straight to the terminal — handy for CI logs or piping into an LLM.

```bash
spectagger --test_command "pytest {tests}" --report --report_type html --report_output report
```

`--report` is ignored under `--dry_run` (nothing runs, so there's nothing to report on).

### Coverage libraries

Pass `--coverage_library` (`python.coverage` or `ruby.simplecov`) alongside `--coverage_report_path` (a directory that must already exist) to have `Runner` capture per-tag line coverage, which `Generator` then folds into the report's `coverage_data.test_coverage` under each spec tag.

For each spec tag, `Runner` resets the coverage tool, runs that tag's linked tests, and writes the result to `<coverage_report_path>/<tag>_cov.json`. `Generator` then reads every `*_cov.json` in that directory and derives `coverage` / `covered_lines` / `missing_lines` per file.

- **`python.coverage`** — works out of the box: `Runner` shells out to `coverage erase` / `coverage json -o ...` directly, so your `--test_command` just needs to run under `coverage run` (e.g. `coverage run -m pytest {tests}`).
- **`ruby.simplecov`** — SimpleCov has no CLI equivalent for erase/output-to-path, so it needs a one-time snippet in your test suite's boot file (`spec_helper.rb` / `rails_helper.rb`), and `Runner` union-merges each individual test invocation's result itself rather than relying on SimpleCov's own timeout-based merging (more robust for `--one_by_one` runs of unknown duration):

  ```ruby
  require 'simplecov'
  SimpleCov.use_merging false
  SimpleCov.start
  ```

  With `use_merging` disabled, SimpleCov overwrites its result file on every run instead of merging across runs — `Runner` reads that file after each individual test invocation within a tag and unions the covered/missing line sets in Python before moving to the next tag.

## Language support

Spec Tagger separates two concerns that are supported independently:

**1. Which files get crawled for tags** (any language, no configuration needed)

Tag extraction is pure text/regex matching, so tags are recognized in _any_ file whose extension is enabled — there's no language-specific parsing at the crawl stage. Spec files default to `.spec`, `.feature`, `.md`, `.txt`; test files default to a broad set covering most mainstream languages (`.py`, `.js`, `.ts`, `.java`, `.go`, `.rb`, `.cpp`, `.cs`, `.php`, `.swift`, `.kt`, `.m`, `.scala`, `.sh`, `.pl`, `.r`, `.lua`, `.hs`, `.erl`, `.ex`, `.exs`). Both lists are extendable via `--spec_file_extensions` / `--test_extensions` for anything not covered.

**2. Which frameworks resolve tags down to a specific test target** (currently `python.pytest`, `ruby.minitest`, `ruby.rspec`, `js.jest` — see the table under [Test framework detection](#test-framework-detection))

After finding a tag in a test file, the `TestCrawler` looks at the following lines (up to 20, `LINE_STOP_CONDITION`) to identify which test the tag belongs to, skipping blank lines and lines matching the framework's `skip_prefixes` (comments/decorators). How it resolves depends on the framework's style, both defined per-entry in `FRAMEWORKS` (in [`spec_tagger/language_patterns.py`](spec_tagger/language_patterns.py)):

- **Function-name frameworks** (`python.pytest`, `ruby.minitest`) — a `func` regex matches the test's `def`, capturing its name directly.
- **Block/description frameworks** (`ruby.rspec`, `js.jest`) — there's no unique function name, so a `describe`/`example` pair of regexes is used instead: the crawler finds the enclosing `it`/`test`/`example` line below the tag, then walks upward through enclosing `describe` blocks using indentation as the nesting signal, joining their descriptions together (e.g. `"Cart > Discounts > applies percentage off"`).

For extensions not covered by the detected (or overridden) framework — or when no framework is detected at all — every tag in that file resolves to the whole file as the test target, rather than a specific function or example, i.e. file-level granularity.

To add a new framework, add an entry to `FRAMEWORKS` with `extensions`, `skip_prefixes`, either a `func` pattern (function-name languages) or a `describe`/`example` pair (block/description languages), and a `detection.command_signals` list of regexes so `detect_framework` can recognize it from a `--test_command` string. (Entries also carry `address_mode`, `block_style`, and a suggested `test_format` as descriptive metadata — these aren't consumed anywhere yet, so `--test_format` still needs to be passed explicitly, as in the examples above.)

## Project architecture

```
spec_tagger/
├── main.py               CLI entry point: argument parsing and orchestration
├── spec_test_data.py     Tag storage/validity model (TagData, SpecTagData, TestTagData)
├── spec_test_crawler.py  Crawls files and extracts tags (Crawler, SpecCrawler, TestCrawler)
├── spec_test_linker.py   Links spec tags to test tags, validates revisions (Linker)
├── test_runner.py        Builds test targets/commands and executes them (Runner)
├── report_generation.py  Builds and writes json/html/stdout reports (Generator)
├── language_patterns.py  Per-framework regexes and detection signals (FRAMEWORKS)
└── templates/            Static assets for the HTML report (index.html, style.css, script.js)
```

### [`main.py`](spec_tagger/main.py)

Defines the `spectagger` CLI via `argparse`, validates the parsed arguments (`validate_args`), and wires the pipeline together in order: `SpecCrawler` → framework detection (`detect_framework`/`framework_support_check`) → `TestCrawler` → `Linker` → `Runner` → (if `--report`) `Generator`. This is the only place that knows about all the components — each is otherwise independent and testable in isolation.

### [`spec_test_data.py`](spec_tagger/spec_test_data.py)

`TagData` is the shared storage/validity model used by both crawlers. Tags are stored both per-type (`features`, `stories`, `steps`) and per-file (`file_to_tag`), alongside `tag_revisions` — a `type~name` → set-of-revisions map used to spot revision drift. `add_tag` builds each tag as a dict (`filename`, `line`, `closing_line`, `type`, `name`, `revision`, `full_tag`, `tag_partial`, `content`, `item_start_line`, and a `validity: {valid, reasons}` block) and immediately flags a tag invalid if more than one revision has been seen for its `type~name`. Validity lives on the tag dict itself now, rather than a separate parallel list.

`SpecTagData` adds `identify_duplicates` (flags exact duplicate spec tags — wired into `Linker.link_data`) and `update_spec_item_closing_lines`; `TagData.update_closing_line` and `get_most_recent_revision` are available on any `TagData`. None of those last three are currently called from the crawl/link pipeline — they're reserved for future use (e.g. surfacing the actual spec/test snippet in a report). `TestTagData` doesn't add anything beyond the base class yet.

### [`spec_test_crawler.py`](spec_tagger/spec_test_crawler.py)

The base `Crawler` class does two things: walk a directory (or file/list of files) collecting paths with enabled extensions (`crawl_files`), then scan each file line-by-line for tags matching the tag regex (`extract_tags`). The tag regex uses lookbehind/lookahead assertions to avoid partial matches inside longer tag-like strings, and a single line can contain multiple tags.

Two subclasses specialize this:

- **`SpecCrawler`** — crawls spec files. `directory_or_files` can be a directory (walked recursively), a list of explicit file paths, or a single file path; `crawl_files` is overridden to handle all three cases and warns about any explicitly-listed files that weren't found or don't have an enabled extension.
- **`TestCrawler`** — crawls test files, then (given a detected or overridden `framework`) does one extra pass (`extract_and_assign_test_declarations`) to resolve each tag to a specific test target, as described in [Language support](#language-support) above. For files whose extension isn't covered by that framework, tags are left without a `test_function` key entirely, which `Runner` later treats as a file-level target. A tag that's in a covered file but still fails to resolve gets `test_function = None`, which the `Linker` treats as invalid (as opposed to file-level).

### [`spec_test_linker.py`](spec_tagger/spec_test_linker.py)

The `Linker` takes the crawled spec tags and test tags and reconciles them into `linked_tags`: a dict keyed by `type~name`, each entry holding one `spec_tag` and a list of matching `test_tags`. `link_data` first calls `spec_data.identify_duplicates()` and `check_revisions()` (which merges the spec and test `tag_revisions` maps and flags any tag whose revision isn't the highest seen for its `type~name`, whether the spec or the test is the one that's behind), then links valid spec tags to valid test tags, and finally drops any spec entry left with no linked tests. Invalid tags encountered anywhere in the process are recorded via `register_invalid_tag` (which flips the tag's own `validity.valid` to `False` and appends a reason) and swept up at the end into a flat `invalid_tags` list (`invalid_tag_sweep`). Reasons currently flagged:

- **Duplicate tags** — the same exact tag (including revision) appears more than once.
- **Outdated revision** — a tag's revision isn't the highest seen for that `type~name`, regardless of whether it's the spec or the test that's behind.
- **Test tag with no matching spec tag** — an orphaned test.
- **Test tag whose function/example couldn't be resolved** (`test_function is None`) — treated as invalid rather than silently linked.
- **Spec tag with no matching test tag at all** — uncovered spec.

`display_data()` is a verbose-mode dump of everything crawled, linked, and flagged.

### [`test_runner.py`](spec_tagger/test_runner.py)

The `Runner` turns `linked_tags` into actual subprocess invocations, one per spec tag (or one per target under `--one_by_one`):

1. `build_targets_for_link` — for each spec tag's test tags, formats each into a CLI-addressable target string via `test_format` (`{file}`/`{name}`/`{line}` placeholders). It also dedupes and prunes redundant targets: if a whole file is already a target (no resolved test — the file-level fallback case), individual targets within that same file are skipped, since running the file covers them. If `test_join` is set, all targets collapse into a single joined string (for runners like `go test -run` that take one regex rather than a target list).
2. `build_command_for_targets` — tokenizes `test_command` with `shlex.split` and substitutes the `{tests}`/`{files}` placeholder token with the resolved target(s), so arbitrary shell-style commands can be built safely without a literal shell.
3. `run_tests` — for each spec tag, runs the built command(s) via `subprocess.run` (or just prints them, under `--dry_run`), and records a structured result: `test_date`, a `results` list (`outcome`/`output`/`error`/`cmd` per subprocess call), `test_count`, `exec_time`, `pass_count`, and `fail_count`. This structured dict is what `report_generation.py` consumes. It also prints a colored (`\033[92m`/`\033[91m`) per-spec-tag summary at the end, but the dict itself — not a 0/1 status — is what's returned; `main.py` doesn't use it to set the process exit code (see note above).

### [`report_generation.py`](spec_tagger/report_generation.py)

The `Generator` merges `Runner`'s per-spec-tag results with `Linker`'s successful links and invalid-tag list into one report object (`_construct_report_object`), then writes it out per `report_type`:

- `_generate_json` — dumps the report object to `report.json`.
- `_generate_html` — writes `data.js` (`window.REPORT_DATA = {...}`) and copies `index.html`/`style.css`/`script.js` out of [`spec_tagger/templates/`](spec_tagger/templates/) into `--report_output`, via `importlib.resources` so it works from an installed package, not just a checkout.
- `_generate_stdout` — prints an ANSI-colored summary directly to the terminal instead of writing files.

### [`language_patterns.py`](spec_tagger/language_patterns.py)

`FRAMEWORKS`, keyed by `"language.framework"` (`python.pytest`, `ruby.minitest`, `ruby.rspec`, `js.jest`). Each entry carries `extensions`, `skip_prefixes`, either a `func` pattern (function-name languages) or a `describe`/`example` pair (block/description languages), and `detection.command_signals` — regexes `detect_framework` matches against `--test_command` to guess the framework in use. `framework_support_check` validates a user-supplied `--test_framework` name against this registry. See [Language support](#language-support) for how these get used.

## Testing

Spec Tagger tests itself using its own tag format — see [`features/`](features/) for the specs and [`tests/crawler_test.py`](tests/crawler_test.py) for the linked pytest tests, plus [`test_data/`](test_data/) for example tests and specs to run the code against. Run the suite directly with pytest:

```bash
pytest
```

or, to exercise the traceability loop against its own specs:

```bash
spectagger --target_spec features --test_dir tests --test_command "pytest {tests}" --test_format "{file}::{name}"
```
