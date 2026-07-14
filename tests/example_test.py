# step~find_all_spec_files~4 feat~find_all_spec_files~4
def test_find_all_spec_files():
    from spec_tagger.spec_test_crawler import SpecCrawler
    spec_crawler = SpecCrawler("features/", enabledExtensions={'.spec', '.feature', '.md', '.txt', '.allium'})
    spec_crawler.crawlFiles()
    assert len(spec_crawler.files) > 0, "No spec files found in the 'features/' directory."