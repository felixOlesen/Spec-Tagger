feat~spec_crawling~1
Feature: Crawling through the Specification

    The Spec Crawler is a program that allows for tags in specification 
    file/s to be identified for later linking and running against tests.

    story~spec_crawl_directory~1
    Scenario: Crawler walks through a directory
        Given the spec is a directory of various allowed files
        And all user-provided arguments are valid
        When the crawler runs
        Then all of the files should be identified
    
    story~spec_crawl_file_list~1
    Scenario: Crawler walks through a list of files
        Given the spec is a list files
        And all user-provided arguments are valid
        When the crawler runs
        Then all of the files should be identified

    story~spec_crawl_file~1
    Scenario: Crawler walks to a specific file
        Given the spec is a single file
        And all user-provided arguments are valid
        When the crawler runs
        Then the one file should be identified

Feature: Crawling through the Tests
    
    The Test Crawler is a program that allows for tags in test file/s to 
    be identified for later linking with the tagged specifications.
    
    story~identify_function_name~1
    Scenario: Name of tagged function is correctly found
        Given that there is at least one test file
        And that the file has at least one tag
        And the tagged function is declared within 20 lines after the tag
        And there are no other functions declared between the tag and the correct function
        When the crawler runs
        Then every tag with a function should have the correct function name attached

