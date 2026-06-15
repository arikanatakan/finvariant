"""Run finvariant against the cases in validation_cases.json: a hand-built
consistent model, Apple's real FY2024 statements, and one isolated breakage per
invariant.
"""

import json
from pathlib import Path

import pytest

import finvariant as fv

CASES = json.loads((Path(__file__).parent / "validation_cases.json").read_text())["cases"]


def _build(case):
    return fv.Statements(
        periods=case["periods"],
        income_statement=case.get("income_statement", {}),
        balance_sheet=case.get("balance_sheet", {}),
        cash_flow=case.get("cash_flow", {}),
    )


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case(case):
    report = fv.check(_build(case))
    assert report.ok is case["expect_ok"]
    failed = {o.rule_id for o in report.findings}
    assert failed == set(case["expect_failed_rules"])
