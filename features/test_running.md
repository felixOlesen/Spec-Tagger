# feat~no_func~2

Spec item example

# feat~dead_func~1

# feat~pytest_class_support~1

Test tags on a `def test_...` declared inside a `pytest` test class (including
nested classes) must resolve to the class-qualified node id
(`OuterClass::InnerClass::test_name`), so the constructed `pytest` command
addresses the correct test rather than a bare, ambiguous function name.
