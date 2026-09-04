# Language and Coverage Support

## Python.Pytest

story~pytest_test_identified~1
Pytest tests need to be identifiable and runnable through the test crawling and test runner functionality

story~pytest_class_identified~1
Pytest classes also need to be identifiable and runnable through the test crawling and test runner functionality

feat~uncovered_test_collection~1

## Uncovered test collection

Uncovered tests and test files are also collected in the crawler functionality to take into account tests that have not been linked with the spec yet.

story~uncovered_file_collection~1

### Uncovered File Collection

A sub-functionality of this is that the crawler can identify files with no tags in them at all, allowing for tag coverage to be understood as well.
