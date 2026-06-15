import pytest

from finvariant import Statements


def test_unknown_field_raises():
    with pytest.raises(ValueError):
        Statements(periods=["FY2024"], balance_sheet={"FY2024": {"frobnicate": 1}})


def test_non_finite_raises():
    with pytest.raises(ValueError):
        Statements(periods=["FY2024"], balance_sheet={"FY2024": {"cash": float("nan")}})


def test_bool_rejected():
    with pytest.raises(ValueError):
        Statements(periods=["FY2024"], balance_sheet={"FY2024": {"cash": True}})


def test_empty_periods_raises():
    with pytest.raises(ValueError):
        Statements(periods=[])


def test_duplicate_periods_raise():
    with pytest.raises(ValueError):
        Statements(periods=["FY2024", "FY2024"])


def test_period_not_declared_raises():
    with pytest.raises(ValueError):
        Statements(periods=["FY2024"], balance_sheet={"FY2025": {"cash": 1}})


def test_at_returns_three_statements():
    s = Statements(periods=["FY2024"], balance_sheet={"FY2024": {"cash": 10}})
    at = s.at("FY2024")
    assert set(at) == {"is", "bs", "cf"}
    assert at["bs"]["cash"] == 10
    assert at["is"] == {}
