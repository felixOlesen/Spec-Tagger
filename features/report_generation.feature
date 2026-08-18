feat~report_generation~1
Feature: Generating a report from a spec tagger run

    The Report Generator takes everything a spec tagger run has produced -
    the linker's successful links and invalid tags, the test runner's
    per-tag results, and the crawler's tag coverage data - and turns it
    into a single report: written as JSON, rendered as a static HTML
    dashboard, or printed straight to the terminal.

    story~report_merges_link_data_into_results~1
    Scenario: Test results are enriched with their linked spec and test tags
        Given the test runner has produced results keyed by full spec tag
        And the linker has produced successful links for those same tags
        When the report object is constructed
        Then each test result gains the spec_tag and test_tags from its matching link

    story~report_construction_requires_successful_links~1
    Scenario: Report construction is skipped when there are no successful links
        Given successful_links is empty or null
        When the report object is constructed
        Then a warning is printed
        And no test results, coverage data, or invalid tags are added to the report

    story~report_construction_requires_test_output~1
    Scenario: Report construction is skipped when there is no test output
        Given test_output is empty or null
        When the report object is constructed
        Then a warning is printed
        And no test results, coverage data, or invalid tags are added to the report

    story~report_carries_tag_coverage_and_test_coverage~1
    Scenario: The report always carries both kinds of coverage data
        Given successful_links and test_output are present
        When the report object is constructed
        Then coverage_data.tag_coverage holds the crawler's tagless-file and untagged-test data
        And coverage_data.test_coverage holds the parsed test coverage report, or null if none was configured

    story~python_coverage_reports_are_parsed_per_tag~1
    Scenario: Coverage.py JSON reports are aggregated per spec tag
        Given a coverage report directory containing one "<tag>_cov.json" file per tag
        And test_coverage_library is "python.coverage"
        When the report object is constructed
        Then each tag's entry lists, per covered file, its percent covered, covered lines, and missing lines

    story~json_report_written_to_disk~1
    Scenario: The json report type writes the report object to a file
        Given report_type is "json"
        When the report is generated
        Then a "report.json" file containing the report object is written to report_output_dir

    story~html_report_written_to_disk~1
    Scenario: The html report type writes a self-contained static report
        Given report_type is "html"
        When the report is generated
        Then report_output_dir is created if it doesn't already exist
        And a "data.js" file assigning the report object to window.REPORT_DATA is written
        And the index.html, style.css, and script.js template files are copied alongside it

    story~stdout_report_prints_status_per_tag~1
    Scenario: The stdout report type classifies each spec tag's status
        Given report_type is "stdout"
        When the report is generated
        Then a tag with zero linked test executions is printed as UNTESTED
        And a tag whose pass_count equals its test_count is printed as PASSED
        And any other tag is printed as FAILED

    Scenario: One-by-one runs are judged as a single test regardless of target count
        Given one_by_one is true
        And report_type is "stdout"
        When the report is generated
        Then each tag's status is judged using a test_count of 1

    story~stdout_prints_coverage_and_invalid_tags~1
    Scenario: The stdout report also summarizes coverage and invalid tags
        Given report_type is "stdout"
        When the report is generated
        Then the parsed test coverage is printed per tag and per covered file
        And each invalid tag is printed with its recorded reasons

    story~invalid_report_type_is_rejected~1
    Scenario: An unrecognized report_type generates nothing
        Given report_type is not one of "json", "html", or "stdout"
        When the report is generated
        Then a message is printed saying the report type is invalid
        And no report file is written
