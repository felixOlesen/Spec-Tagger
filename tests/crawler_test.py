from spec_tagger.spec_test_crawler import SpecCrawler, TestCrawler
# feat~spec_crawling~1
def test_spec_runs_successfully():
    crawler = SpecCrawler(verbose=False, spec_dir='test_data/spec')
    try:
        tag_data = crawler.run()        
        assert(True)
    except:
        assert(False)

# story~spec_crawl_directory~1
def test_find_all_spec_files_in_directory():
    crawler = SpecCrawler(verbose=False, spec_dir='test_data/spec')
    tag_data = crawler.run()
    files  = crawler.files

    assert(len(files) > 0)


# story~spec_crawl_file_list~1
def test_find_all_spec_files_in_list():
    file_list = ['test_data/spec/example_spec.feature', 'test_data/spec/example_spec_2.md']
    crawler = SpecCrawler(verbose=False, spec_dir=file_list)
    tag_data = crawler.run()
    files  = crawler.files

    assert(len(files) == len(file_list))

# story~spec_crawl_file~1
def test_finds_spec_file():
    single_file = 'test_data/spec/example_spec.feature'
    crawler = SpecCrawler(verbose=False, spec_dir=single_file)
    tag_data = crawler.run()
    files  = crawler.files

    assert(files[0] == single_file)

# feat~no_func~1
def test_example():
    assert(True)

# feat~no_func~1
def test_example_2():
    assert(True)
