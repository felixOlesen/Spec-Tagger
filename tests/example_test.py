# feat~no_func~1
def test_find_all_spec_files():
    from spec_tagger.spec_test_crawler import SpecCrawler
    spec_crawler = SpecCrawler(False, "features/", enabled_extensions={'.spec', '.feature', '.md', '.txt', '.allium'})
    spec_crawler.crawl_files()
    assert len(spec_crawler.files) > 0, "No spec files found in the 'features/' directory."

# step~step_test~1
def test_find_all_test_files():
    from spec_tagger.spec_test_crawler import TestCrawler
    test_crawler = TestCrawler(False, "tests/", enabled_extensions={'.py', '.js', '.java', '.cpp', '.cs', '.rb', '.go', '.ts', '.php', '.swift', '.kt', '.m', '.scala', '.sh', '.pl', '.r', '.lua', '.hs', '.erl', '.ex', '.exs'})
    test_crawler.crawl_files()
    assert len(test_crawler.files) > 0, "No test files found in the 'tests/' directory."

# feat~test~1 feat~test_2~1 
def test_spec_crawler_extract_tags():
    from spec_tagger.spec_test_crawler import SpecCrawler
    spec_crawler = SpecCrawler(False, "features/", enabled_extensions={'.spec', '.feature', '.md', '.txt', '.allium'})
    spec_crawler.crawl_files()
    spec_crawler.extract_tags()
    assert -1 > 0, "No tags extracted from the spec files."