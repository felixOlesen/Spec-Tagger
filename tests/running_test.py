from spec_tagger.tag_test.spec_test_crawler import SpecCrawler, TestCrawler
from spec_tagger.tag_test.spec_test_linker import Linker
from spec_tagger.tag_test.test_runner import Runner
from tests.crawler_test import tag_id


# feat~running_a_test_successfully~1
def test_run_successfully():
    spec_dir = "test_data/spec/test_running/test_feature.md"
    spec_crawler = SpecCrawler(verbose=False, spec_dir=spec_dir)
    spec_tag_data = spec_crawler.run()

    test_crawler = TestCrawler(
        verbose=False, test_dir="test_data/tests", framework="python.pytest"
    )
    test_tag_data = test_crawler.run()

    linker = Linker(spec_tag_data, test_tag_data, None, False, False)
    linked_tags, invalid_tags = linker.link_data()

    runner = Runner(
        test_run_command="pytest {tests}",
        test_format="{file}::{name}",
        test_join=None,
        linked_tags=linked_tags,
        one_by_one=False,
        test_coverage_location="",
        coverage_library=None,
        verbose=False,
    )

    results = runner.run_tests()
    result = results[tag_id("feat", "example_running_tag", "1")]["results"][0][
        "outcome"
    ]

    assert result == "passed"
