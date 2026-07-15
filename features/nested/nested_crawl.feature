feature: Nested crawl
  As a user of SpecTagger
  I want to be able to crawl through nested directories
  So that I can find all spec files in a directory structure

    feat~test~1
    scenario: Nested crawl
        Given a directory structure with nested directories and spec files
        When the SpecCrawler is run on the root directory 
        Then it should find all spec files in the nested directories 
