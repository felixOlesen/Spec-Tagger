import json
from _pytest.tmpdir import tmp_path
from spec_tagger.tag_test.report_generation import Generator
from spec_tagger.spec_review.context_aggregator import ContextAggregator


def tag_id(tag_type, name, revision):
    return f"{tag_type}~{name}~{revision}"


def make_link(full_tag, filename="spec.feature", line=1, test_tags=None):
    return {
        "spec_tag": {"full_tag": full_tag, "filename": filename, "line": line},
        "test_tags": test_tags if test_tags is not None else [],
    }


def make_test_result(test_count, pass_count, fail_count=0, results=None):
    return {
        "test_date": "2026-01-01 00:00:00",
        "results": results if results is not None else [],
        "test_count": test_count,
        "exec_time": "0.000000 Seconds",
        "pass_count": pass_count,
        "fail_count": fail_count,
    }


def make_generator(tmp_path, **overrides):
    defaults = dict(
        report_output_dir=str(tmp_path),
        report_type="json",
        test_output=None,
        invalid_tags=[],
        successful_links=None,
        one_by_one=False,
        tag_coverage_data={"files": [], "tests": {}},
        test_coverage_location=None,
        test_coverage_library=None,
        verbose=False,
    )
    defaults.update(overrides)
    return Generator(**defaults)


def test_valid_report_parsed_correctly(tmp_path):
    tag_link = {"feat~example": make_link(tag_id("feat", "example", 1))}
    test_result = {
        tag_id("feat", "example", 1): make_test_result(test_count=1, pass_count=1)
    }

    generator = make_generator(
        tmp_path,
        report_type="json",
        successful_links=tag_link,
        test_output=test_result,
    )
    generator.generate_report()
    aggregator = ContextAggregator((tmp_path / "report.json"), "HEAD~1", "HEAD")
    total_context = aggregator.get_all_context()

    outputted_json = json.loads((tmp_path / "report.json").read_text())
    assert outputted_json["test_results"][tag_id("feat", "example", 1)]["spec_tag"][
        "full_tag"
    ] == tag_id("feat", "example", 1)
