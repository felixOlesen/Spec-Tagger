import json

import pytest

from spec_tagger.tag_test.report_generation import Generator


def tag_id(tag_type, name, revision):
    # This file lives under tests/, the project's own default test_dir, so
    # the spectagger crawler regex-matches any literal "type~name~revision"
    # substring on any line - including inside fixture strings, not just
    # comments. Building tag strings at runtime avoids fixture data being
    # picked up as real (and orphaned) test tags when this project audits
    # its own spec. See tests/linker_test.py for the same pattern.
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


# confidence: 90
# feat~report_generation~1 story~report_merges_link_data_into_results~1
def test_construct_report_merges_link_data_into_test_results(tmp_path):
    tag = tag_id("feat", "example", 1)
    links = {
        "feat~example": make_link(
            tag, test_tags=[{"filename": "t.py", "test_function": "test_example"}]
        )
    }
    test_output = {tag: make_test_result(test_count=1, pass_count=1)}

    generator = make_generator(
        tmp_path, successful_links=links, test_output=test_output
    )
    generator._construct_report_object()

    result = generator.output_object["test_results"][tag]
    assert result["spec_tag"]["full_tag"] == tag
    assert result["test_tags"][0]["test_function"] == "test_example"


# confidence: 90
# story~report_construction_requires_successful_links~1
def test_construct_report_skips_when_no_successful_links(tmp_path, capsys):
    generator = make_generator(
        tmp_path, successful_links=None, test_output={"anything": True}
    )
    generator._construct_report_object()

    assert generator.output_object == {}
    assert "Warning tag links found to be null" in capsys.readouterr().out


# confidence: 90
# story~report_construction_requires_test_output~1
def test_construct_report_skips_when_no_test_output(tmp_path, capsys):
    generator = make_generator(
        tmp_path, successful_links={"anything": True}, test_output=None
    )
    generator._construct_report_object()

    assert generator.output_object == {}
    assert "Warning test_output found to be null" in capsys.readouterr().out


# confidence: 90
# story~report_carries_tag_coverage_and_test_coverage~1
def test_construct_report_always_carries_coverage_data(tmp_path):
    tag = tag_id("feat", "example", 1)
    links = {"feat~example": make_link(tag)}
    test_output = {tag: make_test_result(test_count=0, pass_count=0)}
    tag_coverage = {"files": ["untagged.py"], "tests": {}}

    generator = make_generator(
        tmp_path,
        successful_links=links,
        test_output=test_output,
        tag_coverage_data=tag_coverage,
    )
    generator._construct_report_object()

    coverage = generator.output_object["coverage_data"]
    assert coverage["tag_coverage"] == tag_coverage
    assert coverage["test_coverage"] is None


# confidence: 85
# story~python_coverage_reports_are_parsed_per_tag~1
def test_python_coverage_reports_are_parsed_per_tag(tmp_path):
    coverage_dir = tmp_path / "coverage"
    coverage_dir.mkdir()
    tag = tag_id("feat", "example", 1)

    coverage_report = {
        "files": {
            "src/example.py": {
                "executed_lines": [1, 2, 3],
                "missing_lines": [4],
                "summary": {"percent_covered": 75.0},
            }
        }
    }
    (coverage_dir / f"{tag}_cov.json").write_text(json.dumps(coverage_report))

    links = {"feat~example": make_link(tag)}
    test_output = {tag: make_test_result(test_count=1, pass_count=1)}

    generator = make_generator(
        tmp_path,
        successful_links=links,
        test_output=test_output,
        test_coverage_location=str(coverage_dir),
        test_coverage_library="python.coverage",
    )
    generator._construct_report_object()

    file_coverage = generator.output_object["coverage_data"]["test_coverage"][tag][
        "src/example.py"
    ]
    assert file_coverage["coverage"] == 75.0
    assert file_coverage["covered_lines"] == [1, 2, 3]
    assert file_coverage["missing_lines"] == [4]


# confidence: 90
# story~json_report_written_to_disk~1
def test_json_report_written_to_disk(tmp_path):
    tag = tag_id("feat", "example", 1)
    links = {"feat~example": make_link(tag)}
    test_output = {tag: make_test_result(test_count=1, pass_count=1)}

    generator = make_generator(
        tmp_path,
        report_type="json",
        successful_links=links,
        test_output=test_output,
    )
    generator.generate_report()

    written = json.loads((tmp_path / "report.json").read_text())
    assert written["test_results"][tag]["spec_tag"]["full_tag"] == tag


# confidence: 85
# story~html_report_written_to_disk~1
def test_html_report_written_to_disk(tmp_path):
    tag = tag_id("feat", "example", 1)
    links = {"feat~example": make_link(tag)}
    test_output = {tag: make_test_result(test_count=1, pass_count=1)}
    report_dir = tmp_path / "report"

    generator = make_generator(
        tmp_path,
        report_output_dir=str(report_dir),
        report_type="html",
        successful_links=links,
        test_output=test_output,
    )
    generator.generate_report()

    assert report_dir.is_dir()
    data_js = (report_dir / "data.js").read_text()
    assert data_js.startswith("window.REPORT_DATA = ")
    assert tag in data_js
    for template in ("index.html", "style.css", "script.js"):
        assert (report_dir / template).read_text()


# confidence: 85
# story~stdout_report_prints_status_per_tag~1
def test_stdout_report_classifies_tag_status(tmp_path, capsys):
    untested_tag = tag_id("feat", "untested", 1)
    passed_tag = tag_id("feat", "passed", 1)
    failed_tag = tag_id("feat", "failed", 1)

    links = {
        "feat~untested": make_link(untested_tag),
        "feat~passed": make_link(passed_tag),
        "feat~failed": make_link(failed_tag),
    }
    test_output = {
        untested_tag: make_test_result(test_count=0, pass_count=0),
        passed_tag: make_test_result(test_count=2, pass_count=2),
        failed_tag: make_test_result(test_count=2, pass_count=1, fail_count=1),
    }

    generator = make_generator(
        tmp_path,
        report_type="stdout",
        successful_links=links,
        test_output=test_output,
    )
    generator.generate_report()

    out = capsys.readouterr().out
    sections = {
        untested_tag: out.split(untested_tag, 1)[1],
        passed_tag: out.split(passed_tag, 1)[1],
        failed_tag: out.split(failed_tag, 1)[1],
    }
    assert "UNTESTED" in sections[untested_tag][:100]
    assert "PASSED" in sections[passed_tag][:100]
    assert "FAILED" in sections[failed_tag][:100]


# confidence: 80
# story~stdout_prints_coverage_and_invalid_tags~1
def test_stdout_prints_coverage_and_invalid_tags(tmp_path, capsys):
    coverage_dir = tmp_path / "coverage"
    coverage_dir.mkdir()
    tag = tag_id("feat", "example", 1)

    coverage_report = {
        "files": {
            "src/example.py": {
                "executed_lines": [1],
                "missing_lines": [],
                "summary": {"percent_covered": 100.0},
            }
        }
    }
    (coverage_dir / f"{tag}_cov.json").write_text(json.dumps(coverage_report))

    orphan_tag = tag_id("feat", "orphan", 1)
    links = {"feat~example": make_link(tag)}
    test_output = {tag: make_test_result(test_count=1, pass_count=1)}
    invalid_tags = [
        {
            "full_tag": orphan_tag,
            "validity": {"reasons": ["No corresponding spec tag found."]},
        }
    ]

    generator = make_generator(
        tmp_path,
        report_type="stdout",
        successful_links=links,
        test_output=test_output,
        invalid_tags=invalid_tags,
        test_coverage_location=str(coverage_dir),
        test_coverage_library="python.coverage",
    )
    generator.generate_report()

    out = capsys.readouterr().out
    assert f"Coverage for Tag {tag}" in out
    assert "src/example.py" in out
    assert orphan_tag in out
    assert "No corresponding spec tag found." in out


# confidence: 90
# story~invalid_report_type_is_rejected~1
def test_invalid_report_type_generates_nothing(tmp_path, capsys):
    tag = tag_id("feat", "example", 1)
    links = {"feat~example": make_link(tag)}
    test_output = {tag: make_test_result(test_count=1, pass_count=1)}

    generator = make_generator(
        tmp_path,
        report_type="not_a_real_type",
        successful_links=links,
        test_output=test_output,
    )
    generator.generate_report()

    assert "Invalid report type given." in capsys.readouterr().out
    assert not (tmp_path / "report.json").exists()
