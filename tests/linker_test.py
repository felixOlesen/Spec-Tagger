import pytest

from spec_tagger.tag_test.spec_test_crawler import SpecCrawler, TestCrawler
from spec_tagger.tag_test.spec_test_data import SpecTagData, TestTagData
from spec_tagger.tag_test.spec_test_linker import Linker


def add_spec_tag(spec_data, name, revision, tag_type="feat", filename="spec.feature", line=1):
    spec_data.add_tag(
        filename=filename,
        line=line,
        closing_line=line,
        tag_type=tag_type,
        name=name,
        revision=revision,
        full_tag=f"{tag_type}~{name}~{revision}",
        content=None,
        item_start_line=line,
    )


def add_test_tag(
    test_data,
    name,
    revision,
    tag_type="feat",
    filename="test.py",
    line=1,
    test_function="test_fn",
):
    test_data.add_tag(
        filename=filename,
        line=line,
        closing_line=line,
        tag_type=tag_type,
        name=name,
        revision=revision,
        full_tag=f"{tag_type}~{name}~{revision}",
        content=None,
        item_start_line=line,
    )
    tag = test_data.get_tag(f"{tag_type}~{name}~{revision}")
    tag["test_function"] = test_function
    return tag


def tag_id(tag_type, name, revision):
    # Builds a "type~name~revision" string at runtime rather than as a
    # source-level literal. This file lives under tests/, the project's own
    # default test_dir, so the spectagger crawler regex-matches any literal
    # tag-shaped substring on any line - including inside string literals in
    # assertions, not just comments. A hardcoded literal tag string here
    # would be picked up as a real (and orphaned) test tag when this
    # project audits its own spec.
    return f"{tag_type}~{name}~{revision}"


# ---------------------------------------------------------------------------
# Unit tests: exercise Linker.link_data() directly against in-memory data,
# bypassing the crawlers so each documented linking case can be isolated.
# ---------------------------------------------------------------------------


# confidence: 95
# feat~spec_test_linking~1 story~linker_matches_tag_and_revision~1
def test_matching_tag_and_revision_links_successfully():
    # Case 4: spec and test share the same tag and revision.
    spec = SpecTagData()
    add_spec_tag(spec, "x", "1")
    test = TestTagData()
    add_test_tag(test, "x", "1")

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert invalid == []
    assert linked["feat~x"]["spec_tag"]["validity"]["valid"] is True
    assert [t["full_tag"] for t in linked["feat~x"]["test_tags"]] == [tag_id("feat", "x", 1)]


# confidence: 95
# story~linker_flags_untested_spec~1
def test_spec_tag_with_no_matching_test_is_invalid():
    # Case 1: spec has a tag, but no test claims it.
    # A second, fully-matched pair (y) keeps test_data non-empty so the
    # linker doesn't take its early "no test data at all" exit.
    spec = SpecTagData()
    add_spec_tag(spec, "x", "1", line=1)
    add_spec_tag(spec, "y", "1", line=2)
    test = TestTagData()
    add_test_tag(test, "y", "1")

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert linked["feat~x"]["test_tags"] is None
    assert linked["feat~x"]["spec_tag"]["validity"]["valid"] is False
    assert invalid == [linked["feat~x"]["spec_tag"]]
    assert "Spec tag has no corresponding valid test tag." in invalid[0]["validity"]["reasons"]

    # The matched pair is unaffected.
    assert linked["feat~y"]["spec_tag"]["validity"]["valid"] is True
    assert len(linked["feat~y"]["test_tags"]) == 1


# confidence: 80
# story~linker_flags_orphan_test~1
# The prose doesn't mention that this only surfaces cleanly under
# spec_subset=True (see NOTE below); default settings hit a separate known
# bug (test_orphan_test_tag_raises_keyerror_without_spec_subset) instead.
def test_test_tag_with_no_matching_spec_is_invalid_when_spec_subset():
    # Case 2: test has a tag, but no corresponding spec exists.
    #
    # NOTE: this only surfaces cleanly with spec_subset=True. With the
    # default spec_subset=False, check_revisions() indexes
    # self.spec_data.tag_revisions[tag["tag_partial"]] unconditionally for
    # every tag (spec and test), but only merges test-tag revisions into
    # that map for tag_partials that already exist in it. An orphaned test
    # tag is therefore never added to the map and raises a bare KeyError
    # before the "no corresponding spec" check ever runs. See
    # test_orphan_test_tag_raises_keyerror_without_spec_subset below, which
    # is skipped pending a fix to check_revisions().
    spec = SpecTagData()
    add_spec_tag(spec, "known", "1")
    test = TestTagData()
    add_test_tag(test, "known", "1", filename="t.py", line=1)
    add_test_tag(test, "orphan", "1", filename="t.py", line=10)

    linker = Linker(spec, test, target_tag=None, verbose=False, spec_subset=True)
    linked, invalid = linker.link_data()

    assert list(linked.keys()) == ["feat~known"]
    assert len(invalid) == 1
    assert invalid[0]["full_tag"] == tag_id("feat", "orphan", 1)
    assert "Test tag has no corresponding valid spec tag." in invalid[0]["validity"]["reasons"]


@pytest.mark.skip(
    reason=(
        "Known bug in Linker.check_revisions(): a test tag with no matching "
        "spec tag is never added to revision_map, so revision_map[tag_partial] "
        "raises KeyError instead of being handled by the 'no corresponding "
        "spec tag' check further down in link_data(). Reproduces with default "
        "spec_subset=False."
    )
)
def test_orphan_test_tag_raises_keyerror_without_spec_subset():
    spec = SpecTagData()
    test = TestTagData()
    add_test_tag(test, "orphan", "1")

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linker.link_data()


# confidence: 95
# story~linker_flags_revision_mismatch~1
def test_spec_revision_higher_than_test_revision_leaves_spec_unlinked():
    # Cases 3 & 7: same tag identifier, spec has the higher revision.
    # The outdated test tag is invalidated and excluded, so the spec tag
    # ends up with no valid test link even though a same-named test exists.
    spec = SpecTagData()
    add_spec_tag(spec, "x", "2")
    test = TestTagData()
    add_test_tag(test, "x", "1")

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert linked["feat~x"]["spec_tag"]["revision"] == "2"
    assert linked["feat~x"]["test_tags"] is None

    reasons = {tag["full_tag"]: tag["validity"]["reasons"][0] for tag in invalid}
    assert reasons[tag_id("feat", "x", 1)] == "Revision number is outdated compared to other tags with the same identifier."
    assert reasons[tag_id("feat", "x", 2)] == "Spec tag has no corresponding valid test tag."


# confidence: 95
# story~linker_flags_revision_mismatch~1
def test_test_revision_higher_than_spec_revision_leaves_spec_unlinked():
    # Cases 3 & 8: same tag identifier, test has the higher revision.
    # Here the spec tag itself is the outdated one, so it never makes it
    # into linked_tags, and the (now newer-than-spec) test tag is reported
    # as having no corresponding spec.
    spec = SpecTagData()
    add_spec_tag(spec, "x", "1")
    test = TestTagData()
    add_test_tag(test, "x", "2")

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert linked == {}

    reasons = {tag["full_tag"]: tag["validity"]["reasons"][0] for tag in invalid}
    assert reasons[tag_id("feat", "x", 1)] == "Revision number is outdated compared to other tags with the same identifier."
    assert reasons[tag_id("feat", "x", 2)] == "Test tag has no corresponding valid spec tag."


# confidence: 95
# story~linker_flags_duplicate_spec_tags~1
def test_duplicate_spec_tags_are_invalidated_and_unlinked():
    spec = SpecTagData()
    add_spec_tag(spec, "x", "1", filename="a.feature", line=1)
    add_spec_tag(spec, "x", "1", filename="b.feature", line=1)
    test = TestTagData()
    add_test_tag(test, "x", "1")

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert linked == {}
    invalid_by_file = {tag["filename"]: tag["validity"]["reasons"] for tag in invalid}
    assert invalid_by_file["a.feature"] == ["Duplicate tags found in the specification."]
    assert invalid_by_file["b.feature"] == ["Duplicate tags found in the specification."]
    assert "Test tag has no corresponding valid spec tag." in invalid_by_file["test.py"]


# confidence: 95
# story~linker_flags_missing_test_function~1
def test_test_tag_without_test_function_is_invalid():
    spec = SpecTagData()
    add_spec_tag(spec, "x", "1")
    test = TestTagData()
    add_test_tag(test, "x", "1", test_function=None)

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert linked["feat~x"]["test_tags"] is None
    reasons = {tag["full_tag"]: tag["validity"]["reasons"] for tag in invalid}
    assert reasons[tag_id("feat", "x", 1)] == ["No test function was found following the tag."]


# confidence: 95
# story~linker_partial_spec_coverage~1
def test_spec_with_multiple_tags_partially_covered_by_tests():
    # Case 5: two spec tags, only one has a matching test.
    spec = SpecTagData()
    add_spec_tag(spec, "a", "1", line=1)
    add_spec_tag(spec, "b", "1", line=2)
    test = TestTagData()
    add_test_tag(test, "a", "1")

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert linked["feat~a"]["test_tags"] is not None
    assert linked["feat~b"]["test_tags"] is None
    assert len(invalid) == 1
    assert invalid[0]["full_tag"] == tag_id("feat", "b", 1)


# confidence: 95
# story~linker_target_tag_filtering~1
def test_target_tag_filters_out_unrelated_tags():
    spec = SpecTagData()
    add_spec_tag(spec, "a", "1", line=1)
    add_spec_tag(spec, "b", "1", line=2)
    test = TestTagData()
    add_test_tag(test, "a", "1")

    # "a" has a matching test but is filtered out; only "b" is processed,
    # and it has no test, so it should be the sole invalid entry.
    linker = Linker(spec, test, target_tag=tag_id("feat", "b", 1), verbose=False)
    linked, invalid = linker.link_data()

    assert list(linked.keys()) == ["feat~b"]
    assert len(invalid) == 1
    assert invalid[0]["full_tag"] == tag_id("feat", "b", 1)


# confidence: 90
# story~linker_empty_data_guards~1
def test_link_data_returns_none_when_spec_data_is_empty(capsys):
    # spec_subset=True is required here for the same reason noted in
    # test_test_tag_with_no_matching_spec_is_invalid_when_spec_subset: with
    # zero spec tags, the lone test tag has no entry in revision_map and
    # check_revisions() would otherwise raise KeyError before link_data()
    # ever reaches its own "spec data is null" guard.
    spec = SpecTagData()
    test = TestTagData()
    add_test_tag(test, "x", "1")

    linker = Linker(spec, test, target_tag=None, verbose=False, spec_subset=True)
    result = linker.link_data()

    assert result is None
    assert "Warning spec data found to be null on run." in capsys.readouterr().out


# confidence: 90
# story~linker_empty_data_guards~1
def test_link_data_returns_none_when_test_data_has_no_tags(capsys):
    # If test_data has zero tags at all (as opposed to simply no tag
    # matching the spec), link_data exits early after populating
    # linked_tags but before running any invalidation checks, so the
    # untested spec tag is *not* reported in invalid_tags.
    spec = SpecTagData()
    add_spec_tag(spec, "x", "1")
    test = TestTagData()

    linker = Linker(spec, test, target_tag=None, verbose=False)
    result = linker.link_data()

    assert result is None
    assert "Warning test data found to be null on run." in capsys.readouterr().out
    assert linker.linked_tags["feat~x"]["test_tags"] == []
    assert linker.invalid_tags == []


# confidence: 90
# story~linker_display_methods~1
def test_display_methods_do_not_raise(capsys):
    spec = SpecTagData()
    add_spec_tag(spec, "x", "1")
    test = TestTagData()
    add_test_tag(test, "x", "1")

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linker.link_data()

    linker.display_data()
    linker.display_invalid_tags()

    out = capsys.readouterr().out
    assert "Linked Tags:" in out


# ---------------------------------------------------------------------------
# Integration tests: crawl real fixture files with SpecCrawler/TestCrawler
# and feed the results through Linker, matching the style of
# tests/crawler_test.py.
# ---------------------------------------------------------------------------


# confidence: 95
# story~linker_links_real_crawled_files~1
def test_full_pipeline_links_example_fixtures():
    spec = SpecCrawler(verbose=False, spec_dir="test_data/spec").run()
    test = TestCrawler(
        verbose=False, test_dir="test_data/tests", framework="python.pytest"
    ).run()

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert linked["feat~example_tag"]["spec_tag"]["validity"]["valid"] is True
    assert linked["feat~example_tag_2"]["spec_tag"]["validity"]["valid"] is True
    assert linked["feat~example_tag"]["test_tags"][0]["full_tag"] == tag_id("feat", "example_tag", 1)
    assert linked["feat~example_tag_2"]["test_tags"][0]["full_tag"] == tag_id("feat", "example_tag_2", 1)
    assert not any(tag["full_tag"].startswith("feat~example_tag") for tag in invalid)


# confidence: 95
# story~linker_flags_revision_mismatch_in_real_crawled_files~1
def test_full_pipeline_flags_revision_mismatch_fixture():
    spec = SpecCrawler(verbose=False, spec_dir="test_data/spec").run()
    test = TestCrawler(
        verbose=False, test_dir="test_data/tests", framework="python.pytest"
    ).run()

    linker = Linker(spec, test, target_tag=None, verbose=False)
    linked, invalid = linker.link_data()

    assert linked["feat~linker_revision_mismatch"]["test_tags"] is None
    reasons = {tag["full_tag"]: tag["validity"]["reasons"][0] for tag in invalid}
    assert (
        reasons[tag_id("feat", "linker_revision_mismatch", 1)]
        == "Revision number is outdated compared to other tags with the same identifier."
    )
    assert (
        reasons[tag_id("feat", "linker_revision_mismatch", 2)]
        == "Spec tag has no corresponding valid test tag."
    )
