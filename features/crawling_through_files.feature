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


Feature: Crawling through files for tags

    The base crawler is a program that focuses entirely on filtering through
    text to identify and collect tags.

    Scenario: Tag is successfully extracted
        Given that the crawler has identified at least one file
        And the file has at least one tag of the correct format
        Then the crawler will identify the tag
        And append it to the correct group

    Scenario: Multiple tags on a single line are successfully extracted
        Given that the crawler has identified at least one file
        And the file has multiple correctly-formatted tags on one line
        Then crawler will correclty identify each tag
        And append them to the correct group

Feature: Crawling through the Tests
    
    The Test Crawler is a program that allows for tags in test file/s to 
    be identified for later linking with the tagged specifications.

    Scenario: Name of tagged function is correctly found
        Given that there is at least one test file
        And that the file has at least one tag
        And the tagged function is declared within 20 lines after the tag
        And there are no other functions declared between the tag and the correct function
        When the crawler runs
        Then every tag with a function should have the correct function name attached