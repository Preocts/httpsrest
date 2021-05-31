"""Tests for sample"""
import httpsrest
import pytest


def test_main() -> None:
    """Main test"""
    assert httpsrest.main()


@pytest.mark.parametrize(
    ("value_in", "expected"),
    (
        (2, 4),
        (4, 16),
        (16, 256),
    ),
)
def test_squared(value_in: int, expected: int) -> None:
    assert httpsrest.squared(value_in) == expected
