class TestExampleClass:
    # feat~example_class_tag~1
    def test_class_method(self):
        assert 1 == 1

    class TestNestedClass:
        # feat~example_nested_class_tag~1
        def test_nested_method(self):
            assert 1 == 1
