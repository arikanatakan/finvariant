"""Run finvariant against every case in tests/cases/.

Each case is its own JSON file: a hand-built consistent model, six real
companies (each illustrating a different angle), and one isolated breakage per
invariant. Each file documents what it demonstrates in its "description".
"""

import json
from pathlib import Path

import pytest

import finvariant as fv

CASE_FILES = sorted((Path(__file__).parent / "cases").glob("*.json"))


def _build(case):
    return fv.Statements(
        periods=case["periods"],
        income_statement=case.get("income_statement", {}),
        balance_sheet=case.get("balance_sheet", {}),
        cash_flow=case.get("cash_flow", {}),
    )


@pytest.mark.parametrize("path", CASE_FILES, ids=[p.stem for p in CASE_FILES])
def test_case(path):
    case = json.loads(path.read_text())
    report = fv.check(_build(case))

    assert report.ok is case["expect_ok"]

    failed = {o.rule_id for o in report.findings}
    assert failed == set(case["expect_failed_rules"])

    skipped = {o.rule_id for o in report.outcomes if o.status == "skip"}
    for rule_id in case.get("expect_skipped_rules", []):
        assert rule_id in skipped


def test_cases_exist():
    assert len(CASE_FILES) >= 13
