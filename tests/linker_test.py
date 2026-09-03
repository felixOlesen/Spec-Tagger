import pytest

from spec_tagger.tag_test.spec_test_crawler import SpecCrawler, TestCrawler
from spec_tagger.tag_test.spec_test_data import SpecTagData, TestTagData, Invalidities
from spec_tagger.tag_test.spec_test_linker import Linker


def add_spec_tag(
    spec_data, name, revision, tag_type="feat", filename="spec.feature", line=1
):
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
    return f"{tag_type}~{name}~{revision}"


# feat~succesful_linking~1
def test_successful_linking():
    test_data = TestTagData()
    spec_data = SpecTagData()

    add_test_tag(test_data=test_data, name="success_tag", revision=1)
    add_spec_tag(spec_data=spec_data, name="success_tag", revision=1)

    linker = Linker(
        spec_data=spec_data, test_data=test_data, target_tag=None, verbose=False
    )
    linked_tags, _ = linker.link_data()
    assert linked_tags["feat~success_tag"]["spec_tag"]["full_tag"] == tag_id(
        "feat", "success_tag", "1"
    )
    assert len(linked_tags["feat~success_tag"]["test_tags"]) == 1
    assert linked_tags["feat~success_tag"]["test_tags"][0]["full_tag"] == tag_id(
        "feat", "success_tag", "1"
    )


# feat~invalid_tags_found~1
def test_invalid_tags():
    test_data = TestTagData()
    spec_data = SpecTagData()

    add_test_tag(test_data=test_data, name="orphaned_test_tag", revision=1)
    add_spec_tag(spec_data=spec_data, name="orphaned_spec_tag", revision=1)

    add_spec_tag(spec_data=spec_data, name="duplicate_spec_tag", revision=1)
    add_spec_tag(spec_data=spec_data, name="duplicate_spec_tag", revision=1)

    add_spec_tag(spec_data=spec_data, name="missing_test_func", revision=1)
    add_test_tag(
        test_data=test_data, name="missing_test_func", revision=1, test_function=None
    )

    add_test_tag(test_data=test_data, name="revision_mismatch", revision=2)
    add_spec_tag(spec_data=spec_data, name="revision_mismatch", revision=5)

    linker = Linker(
        spec_data=spec_data, test_data=test_data, target_tag=None, verbose=False
    )
    linked_tags, invalid_tags = linker.link_data()

    assert len(invalid_tags) == 8
    assert len(linked_tags.keys()) == 3
