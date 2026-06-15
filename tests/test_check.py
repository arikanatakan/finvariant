import json

import pytest

import finvariant as fv


def _balanced(assets=100, liabilities=60, equity=40):
    return fv.Statements(
        periods=["FY2024"],
        balance_sheet={"FY2024": {
            "total_assets": assets, "total_liabilities": liabilities,
            "total_equity": equity,
        }},
    )


def test_equation_passes():
    r = fv.check(_balanced())
    assert r.ok
    assert r.n_failed == 0
    assert any(o.rule_id == "EQ.accounting_equation" and o.status == "pass"
               for o in r.outcomes)


def test_equation_fails_with_numbers():
    r = fv.check(_balanced(assets=101))
    assert not r.ok
    assert len(r.findings) == 1
    f = r.findings[0]
    assert f.rule_id == "EQ.accounting_equation"
    assert f.expected == 100 and f.actual == 101 and f.difference == 1


def test_relative_tolerance_absorbs_rounding():
    s = _balanced(assets=1000050, liabilities=1000000, equity=0)
    assert fv.check(s).ok                    # 50 is within 0.01% of 1,000,000
    assert not fv.check(s, rel_tol=0.0).ok   # demanded exact, so it fails


def test_rules_filter():
    r = fv.check(_balanced(), rules=["EQ.accounting_equation"])
    assert {o.rule_id for o in r.outcomes} == {"EQ.accounting_equation"}


def test_subtotal_without_items_skips():
    s = fv.Statements(periods=["FY2024"],
                      balance_sheet={"FY2024": {"total_current_assets": 100}})
    r = fv.check(s)
    assert any(o.rule_id == "FOOT.bs.total_current_assets" and o.status == "skip"
               for o in r.outcomes)
    assert r.ok  # a skip never fails the report


def test_to_dict_is_json_serializable():
    d = fv.check(_balanced()).to_dict()
    json.dumps(d)
    assert d["schema"] == 1
    assert d["ok"] is True
    assert "input_hash" in d["meta"]


def test_summary_is_plain_text():
    t = fv.check(_balanced()).summary()
    assert "finvariant" in t
    assert "Verdict" in t
    assert "—" not in t  # no em dash


def test_provenance_changes_with_input():
    a = fv.check(_balanced()).meta["input_hash"]
    b = fv.check(_balanced(assets=200, liabilities=100, equity=100)).meta["input_hash"]
    assert a != b


def test_typeerror_on_non_statements():
    with pytest.raises(TypeError):
        fv.check({"periods": ["FY2024"]})
