def test_find_all_spec_files():
    from spec_tagger.spec_test_crawler import SpecCrawler
    spec_crawler = SpecCrawler("features/", enabledExtensions={'.spec', '.feature', '.md', '.txt', '.allium'})
    spec_crawler.crawlFiles()
    assert len(spec_crawler.files) > 0, "No spec files found in the 'features/' directory."

def test_find_all_test_files():
    from spec_tagger.spec_test_crawler import TestCrawler
    test_crawler = TestCrawler("tests/", enabledExtensions={'.py', '.js', '.java', '.cpp', '.cs', '.rb', '.go', '.ts', '.php', '.swift', '.kt', '.m', '.scala', '.sh', '.pl', '.r', '.lua', '.hs', '.erl', '.ex', '.exs'})
    test_crawler.crawlFiles()
    assert len(test_crawler.files) > 0, "No test files found in the 'tests/' directory."

# feat~test~1
def test_spec_crawler_extract_tags():
    from spec_tagger.spec_test_crawler import SpecCrawler
    spec_crawler = SpecCrawler("features/", enabledExtensions={'.spec', '.feature', '.md', '.txt', '.allium'})
    spec_crawler.crawlFiles()
    spec_crawler.extractTags()
    assert len(spec_crawler.tagData) > 0, "No tags extracted from the spec files."