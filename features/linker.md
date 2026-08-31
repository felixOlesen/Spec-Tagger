feat~spec_test_linking~1

# Linking specs to tests

Once the spec crawler and test crawler have each produced their own set of
tags, the Linker's job is to reconcile the two: it walks every spec tag and
every test tag, matches them up by identifier (`type~name`), and decides
whether each pairing is healthy. The result is a map of linked spec/test
pairs, and a separate list of tags that couldn't be resolved cleanly, each
carrying a human-readable reason.

story~linker_matches_tag_and_revision~1

## A clean match

The simplest case is also the most common one: a spec tag and a test tag
declare the same identifier and the same revision number. When that
happens, the linker treats them as verified — the spec tag is recorded as
linked to that test, and neither tag shows up anywhere in the invalid list.
This is the state every other scenario below is ultimately trying to reach
or explain a deviation from.

story~linker_flags_untested_spec~1

## A spec item nobody tests

Sometimes a spec tag exists with no test anywhere claiming to cover it.
The linker still records the spec tag, but marks it invalid with the
reason "Spec tag has no corresponding valid test tag," and its slot in the
linked-tags map is left with no test tags attached rather than an empty
placeholder. This is the case most people actually run spectagger to catch
— specification drifting ahead of the code that's supposed to prove it.

story~linker_flags_orphan_test~1

## A test with no spec behind it

The mirror image of the above: a test declares a tag, but no spec item
anywhere shares that identifier. The linker reports the test tag as
invalid, with the reason "Test tag has no corresponding valid spec tag,"
and it never makes it into a linked pair. In practice this usually means a
spec item was renamed or removed and the test's tag was never updated to
match.

story~linker_flags_revision_mismatch~1

## Revisions drifting apart

A spec tag and a test tag can share an identifier but disagree on revision
number — this is how the linker catches a spec that changed without its
test being updated, or vice versa. Whichever side holds the lower revision
number is the one considered stale: it's marked invalid as outdated
compared to other tags sharing its identifier. Because the outdated tag is
excluded from linking, the *other*, newer side ends up reported as having
no valid counterpart at all — a spec with a newer revision than its test
looks exactly like an untested spec item, and a test with a newer revision
than its spec looks exactly like an orphaned test. The underlying reason
recorded on the stale tag is what distinguishes a genuine revision drift
from a simple missing counterpart.

story~linker_flags_duplicate_spec_tags~1

## The same spec tag declared twice

If the same tag identifier and revision appear more than once across the
spec files, that's treated as an authoring mistake rather than something
to link: every copy is marked invalid as a duplicate, and none of them are
linked to a matching test, even if a perfectly good test exists for that
identifier. Ambiguity in the spec itself has to be resolved before linking
is meaningful.

story~linker_flags_missing_test_function~1

## A tag with nothing underneath it

A test tag can be well-formed and revision-matched, and still fail to
link if the crawler couldn't find an actual test function following it in
the source file. The linker reports this as invalid with the reason "No
test function was found following the tag," and — just as with an
entirely absent test — the spec tag on the other end is reported as having
no valid test tag to point to.

story~linker_partial_spec_coverage~1

## Partial coverage across many tags

None of the above cases are mutually exclusive within a single run: a spec
file might declare several tags, only some of which have matching tests.
The linker evaluates every tag independently, so the covered ones link
successfully while the uncovered ones are reported as invalid — a single
run can produce a mix of healthy links and outstanding gaps side by side.

story~linker_target_tag_filtering~1

## Narrowing the run to one tag

The linker can be scoped to a single spec item by passing a target tag.
When that happens, every tag that doesn't match the target's identifier is
marked to be ignored before linking even begins, so it never appears in
either the linked results or the invalid list — it's as if those tags were
never crawled at all. This is what lets a targeted re-check of one spec
item avoid surfacing unrelated noise from the rest of the project.

story~linker_empty_data_guards~1

## When there's nothing to link

Two degenerate cases are worth calling out on their own. If no spec tags
were crawled at all, the linker prints a warning and exits without
attempting to link anything. If spec tags exist but no test tags were
crawled at all, the linker also prints a warning and exits early — but
because this check happens after the spec tags have already been recorded,
those spec tags are left sitting in the linked-tags map without being
flagged as invalid. Neither case raises an error; both are treated as
"there was nothing meaningful to do here" rather than a failure.

story~linker_display_methods~1

## Reading the results back

Once a run has finished, the linker can print its own results: the linked
spec/test pairs, and separately, the invalid tags together with the
reasons they were rejected. These are convenience views over the same data
returned by the run itself, meant for a human skimming a terminal rather
than for anything downstream that needs to consume the results
programmatically.

## Confirming it end-to-end

The scenarios above are about the linker's own logic, given tag data
handed to it directly. It's worth separately confirming that the same
behavior holds when the tag data comes from actually crawling real files
on disk — that the spec crawler, test crawler, and linker all agree with
each other.

story~linker_links_real_crawled_files~1

A spec file and test file sharing a tag and revision should link cleanly
when both are produced by the real crawlers, with the pairing appearing in
the linked results and nothing about it showing up in the invalid list —
sourced from real filesystem paths and line numbers rather than
hand-constructed tag dictionaries.

story~linker_flags_revision_mismatch_in_real_crawled_files~1
A spec file and test file sharing an identifier but disagreeing on
revision should produce exactly the outdated/no-valid-counterpart pairing
described above, again this time sourced from real crawled files rather
than hand-built tag data — confirming the crawlers and the linker agree on
what "the same tag" means.

## A known gap

One case isn't yet handled the way the rest of this document describes.
When a test tag has no matching spec tag at all, and the run is using the
default settings, the linker's revision check currently raises an
unhandled `KeyError` instead of reaching the "orphaned test tag" handling
described above — because that check indexes into a revision map that was
never populated for a tag with no spec-side counterpart. This is tracked
but not yet fixed; see the skipped test
`test_orphan_test_tag_raises_keyerror_without_spec_subset` in
`tests/linker_test.py` for a reproduction.
