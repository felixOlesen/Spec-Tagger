from spec_tagger.tag_test.spec_test_crawler import SpecCrawler, TestCrawler
from spec_tagger.tag_test.test_runner import Runner


def tag_id(tag_type, name, revision):
    return f"{tag_type}~{name}~{revision}"


# feat~spec_crawling~1
def test_spec_runs_successfully():
    crawler = SpecCrawler(verbose=False, spec_dir="test_data/spec")
    try:
        tag_data = crawler.run()
        assert True
    except:
        assert False


# story~spec_crawl_directory~1
def test_find_all_spec_files_in_directory():
    crawler = SpecCrawler(verbose=False, spec_dir="test_data/spec")
    tag_data = crawler.run()
    files = crawler.files

    assert len(files) > 0


# story~spec_crawl_file_list~1
def test_find_all_spec_files_in_list():
    file_list = [
        "test_data/spec/example_spec.feature",
        "test_data/spec/example_spec_2.md",
    ]
    crawler = SpecCrawler(verbose=False, spec_dir=file_list)
    tag_data = crawler.run()
    files = crawler.files

    assert len(files) == len(file_list)


# story~spec_crawl_file~1
def test_finds_spec_file():
    single_file = "test_data/spec/example_spec.feature"
    crawler = SpecCrawler(verbose=False, spec_dir=single_file)
    tag_data = crawler.run()
    files = crawler.files

    assert files[0] == single_file


# story~identify_function_name~1
def test_finds_correct_function_name():
    dir = "test_data/tests/"
    crawler = TestCrawler(verbose=False, test_dir=dir, framework="python.pytest")
    tag_data = crawler.run()
    tag = tag_data.get_tag(tag_id("feat", "example_tag", 1))
    print(tag)
    assert tag["test_function"] == "test_example_function"


TEST_CLASS_FIXTURE = "test_data/tests/example_class_test.py"


# feat~pytest_class_support~1
def test_pytest_class_method_resolves_to_class_qualified_name():
    crawler = TestCrawler(
        verbose=False, test_dir="test_data/tests", framework="python.pytest"
    )
    tag_data = crawler.run()

    tags = tag_data.file_to_tag[TEST_CLASS_FIXTURE]
    resolved = {tag["full_tag"]: tag["test_function"] for tag in tags}

    assert (
        resolved[tag_id("feat", "example_class_tag", "1")]
        == "TestExampleClass::test_class_method"
    )
    assert (
        resolved[tag_id("feat", "example_nested_class_tag", "1")]
        == "TestExampleClass::TestNestedClass::test_nested_method"
    )


# feat~pytest_class_support~1
def test_pytest_class_method_builds_correct_command():
    crawler = TestCrawler(
        verbose=False, test_dir="test_data/tests", framework="python.pytest"
    )
    tag_data = crawler.run()
    tag = tag_data.get_tag(tag_id("feat", "example_class_tag", "1"))

    runner = Runner(
        test_run_command="pytest {tests}",
        test_format="{file}::{name}",
        test_join=None,
        linked_tags=None,
        one_by_one=False,
        test_coverage_location="",
        coverage_library=None,
        verbose=False,
    )
    target = runner.format_target(tag)

    assert target == f"{TEST_CLASS_FIXTURE}::TestExampleClass::test_class_method"
