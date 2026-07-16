# feat~no_test~1
def test_find_no_spec_files():
    from spec_tagger.spec_test_crawler import SpecCrawler
    spec_crawler = SpecCrawler(False, "features/", enabled_extensions={'.spec', '.feature', '.md', '.txt', '.allium'})
    spec_crawler.crawl_files()
    assert len(spec_crawler.files) > 0, "No spec files found in the 'features/' directory."