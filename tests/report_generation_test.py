import json

import pytest

from spec_tagger.tag_test.report_generation import Generator


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
