import sys
sys.path.append("..")
from spec_tagger.main import example_function
import pytest

@pytest.mark.parametrize("input_value, expected_output", [
    (1, 2),
    (-1, 0),
    (0, 1),
])
def test_example_function(input_value, expected_output):
    assert example_function(input_value) == expected_output