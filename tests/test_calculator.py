"""Tests for the safe arithmetic calculator."""

import pytest

from researchmind.tools.calculator import calculate


def test_calculate_basic_expression() -> None:
    assert calculate("2 + 3 * 4") == 14.0


def test_calculate_parentheses() -> None:
    assert calculate("(10 - 4) / 2") == 3.0


def test_calculate_power() -> None:
    assert calculate("2 ** 3") == 8.0


def test_calculate_unary_operator() -> None:
    assert calculate("-5 + 8") == 3.0


def test_division_by_zero_is_rejected() -> None:
    with pytest.raises(ValueError, match="Division by zero"):
        calculate("10 / 0")


def test_function_calls_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported operation"):
        calculate("__import__('os')")


def test_attribute_access_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported operation"):
        calculate("x.real")


def test_excessive_exponent_is_rejected() -> None:
    with pytest.raises(ValueError, match="Exponent"):
        calculate("2 ** 101")


def test_empty_expression_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        calculate("   ")


def test_expression_length_is_limited() -> None:
    with pytest.raises(ValueError, match="too long"):
        calculate("1" * 201)
