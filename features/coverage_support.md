# Coverage Support

## Features

feat~uncovered_test_collection~1

### Un-Covered Test Function Collection

story~all_tests_are_collected~1
The test crawler needs to be able to run collect the names of test functions that are connected to tags AND not connected to any tags.
This needs to be the case for both Describe/it tests and regular tests. step~describe_it_and_regular~1

feat~coverage_support~1

### Coverage Library Support

Coverage libraries need to be supported to allow for the CI pipeline to get enough information, to make value judgements on semantic drift when the implementation code changes but the spec and test code haven't changed.

Currently these libraries need to be supported:

- Coverage (Python) step~python_coverage_support~1
- Coverage (Ruby/SimpleCov) step~ruby_simplecov_support~1
