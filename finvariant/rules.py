"""The accounting-invariant catalogue.

Each rule reads only the fields it needs. A rule whose inputs are absent emits
nothing; a subtotal given without its line items emits a ``skip``; an applicable
rule emits ``pass`` or ``fail``.
"""

from __future__ import annotations

from ._result import ERROR, FAIL, PASS, SKIP, WARNING, RuleOutcome
from .model import BS_SECTIONS, BS_TOTALS, CF_SECTIONS, IS_RELATIONS, Statements

IS_DESC = {
    "gross_profit": "gross profit = revenue - cogs",
    "operating_income": "operating income = gross profit - operating expenses",
    "pretax_income": "pretax income = operating income + other income - interest",
    "net_income": "net income = pretax income - tax",
}
BS_SECTION_DESC = {
    "total_current_assets": "current assets foot",
    "total_non_current_assets": "non-current assets foot",
    "total_current_liabilities": "current liabilities foot",
    "total_non_current_liabilities": "non-current liabilities foot",
    "total_equity": "equity foots",
}
BS_TOTAL_DESC = {
    "total_assets": "total assets = current + non-current assets",
    "total_liabilities": "total liabilities = current + non-current liabilities",
}
CF_SECTION_DESC = {
    "cfo": "operating cash flow foots",
    "cfi": "investing cash flow foots",
    "cff": "financing cash flow foots",
}


def _present(d: dict, keys: list[str]) -> list[str]:
    return [k for k in keys if k in d]


def _sum(d: dict, keys: list[str]) -> float:
    return sum(d[k] for k in keys if k in d)


def _close(expected: float, actual: float, abs_tol: float, rel_tol: float) -> bool:
    return abs(actual - expected) <= max(abs_tol, rel_tol * abs(expected))


def _check(rule_id, desc, statement, period, severity,
           expected, actual, abs_tol, rel_tol) -> RuleOutcome:
    status = PASS if _close(expected, actual, abs_tol, rel_tol) else FAIL
    return RuleOutcome(rule_id, desc, statement, period, status, severity,
                       round(float(expected), 6), round(float(actual), 6),
                       round(float(actual) - float(expected), 6))


def _skip(rule_id, desc, statement, period, severity, message) -> RuleOutcome:
    return RuleOutcome(rule_id, desc, statement, period, SKIP, severity,
                       message=message)


def _income_relations(out, cur, period, at, rt) -> None:
    isd = cur["is"]
    for target, plus, minus in IS_RELATIONS:
        if target not in isd:
            continue
        if plus[0] not in isd:
            out.append(_skip(f"FOOT.is.{target}", IS_DESC[target], "IS", period,
                             ERROR, f"{plus[0]} not provided"))
            continue
        expected = _sum(isd, plus) - _sum(isd, minus)
        out.append(_check(f"FOOT.is.{target}", IS_DESC[target], "IS", period,
                          ERROR, expected, isd[target], at, rt))


def _bs_sections(out, cur, period, at, rt) -> None:
    bs = cur["bs"]
    for subtotal, items in BS_SECTIONS.items():
        if subtotal not in bs:
            continue
        present = _present(bs, items)
        if not present:
            out.append(_skip(f"FOOT.bs.{subtotal}", BS_SECTION_DESC[subtotal], "BS",
                             period, ERROR, "no line items provided"))
            continue
        out.append(_check(f"FOOT.bs.{subtotal}", BS_SECTION_DESC[subtotal], "BS",
                          period, ERROR, _sum(bs, present), bs[subtotal], at, rt))


def _bs_totals(out, cur, period, at, rt) -> None:
    bs = cur["bs"]
    for total, parts in BS_TOTALS.items():
        if total not in bs or not all(p in bs for p in parts):
            continue
        out.append(_check(f"FOOT.bs.{total}", BS_TOTAL_DESC[total], "BS", period,
                          ERROR, _sum(bs, parts), bs[total], at, rt))


def _accounting_equation(out, cur, period, at, rt) -> None:
    bs = cur["bs"]
    if not all(k in bs for k in ("total_assets", "total_liabilities", "total_equity")):
        return
    out.append(_check("EQ.accounting_equation",
                      "assets = liabilities + equity", "BS", period, ERROR,
                      bs["total_liabilities"] + bs["total_equity"],
                      bs["total_assets"], at, rt))


def _cf_sections(out, cur, period, at, rt) -> None:
    cf = cur["cf"]
    for subtotal, items in CF_SECTIONS.items():
        if subtotal not in cf:
            continue
        present = _present(cf, items)
        if not present:
            out.append(_skip(f"FOOT.cf.{subtotal}", CF_SECTION_DESC[subtotal], "CF",
                             period, ERROR, "no line items provided"))
            continue
        out.append(_check(f"FOOT.cf.{subtotal}", CF_SECTION_DESC[subtotal], "CF",
                          period, ERROR, _sum(cf, present), cf[subtotal], at, rt))


def _cf_net_change(out, cur, period, at, rt) -> None:
    cf = cur["cf"]
    if not all(k in cf for k in ("cfo", "cfi", "cff", "net_change_in_cash")):
        return
    expected = cf["cfo"] + cf["cfi"] + cf["cff"] + cf.get("fx_effect", 0.0)
    out.append(_check("FOOT.cf.net_change",
                      "net change in cash = cfo + cfi + cff", "CF", period, ERROR,
                      expected, cf["net_change_in_cash"], at, rt))


def _cash_ties(out, cur, prev, period, at, rt) -> None:
    cf, bs = cur["cf"], cur["bs"]
    if all(k in cf for k in ("net_change_in_cash", "beginning_cash", "ending_cash")):
        out.append(_check("CASH.net_change_ties",
                          "net change = ending cash - beginning cash", "CF", period,
                          ERROR, cf["ending_cash"] - cf["beginning_cash"],
                          cf["net_change_in_cash"], at, rt))
    if "ending_cash" in cf and "cash" in bs:
        out.append(_check("CASH.ending_ties",
                          "cash flow ending cash = balance sheet cash", "BS/CF",
                          period, ERROR, bs["cash"], cf["ending_cash"], at, rt))
    if prev is not None and "beginning_cash" in cf and "cash" in prev["bs"]:
        out.append(_check("CASH.beginning_ties",
                          "beginning cash = prior period balance sheet cash", "BS/CF",
                          period, ERROR, prev["bs"]["cash"], cf["beginning_cash"],
                          at, rt))


def _articulation(out, cur, prev, period, at, rt) -> None:
    isd, bs, cf = cur["is"], cur["bs"], cur["cf"]

    if "net_income" in isd and "net_income" in cf:
        out.append(_check("ART.net_income",
                          "net income agrees between income statement and cash flow",
                          "IS/CF", period, ERROR, isd["net_income"], cf["net_income"],
                          at, rt))

    ni = isd.get("net_income", cf.get("net_income"))
    if (prev is not None and "retained_earnings" in bs
            and "retained_earnings" in prev["bs"] and ni is not None):
        # dividends_paid follows the cash-flow sign convention (an outflow is
        # negative), so it is added, not subtracted: a negative value reduces RE.
        dividends = cf.get("dividends_paid", 0.0)
        expected = prev["bs"]["retained_earnings"] + ni + dividends
        out.append(_check("ART.retained_earnings",
                          "retained earnings = prior + net income - dividends", "BS",
                          period, ERROR, expected, bs["retained_earnings"], at, rt))

    if "depreciation_amortization" in cf and "depreciation_amortization" in isd:
        out.append(_check("ART.depreciation",
                          "depreciation agrees between income statement and cash flow",
                          "IS/CF", period, WARNING, isd["depreciation_amortization"],
                          cf["depreciation_amortization"], at, rt))


def run_rules(s: Statements, abs_tol: float, rel_tol: float) -> list[RuleOutcome]:
    out: list[RuleOutcome] = []
    for i, period in enumerate(s.periods):
        cur = s.at(period)
        prev = s.at(s.periods[i - 1]) if i > 0 else None
        _income_relations(out, cur, period, abs_tol, rel_tol)
        _bs_sections(out, cur, period, abs_tol, rel_tol)
        _bs_totals(out, cur, period, abs_tol, rel_tol)
        _accounting_equation(out, cur, period, abs_tol, rel_tol)
        _cf_sections(out, cur, period, abs_tol, rel_tol)
        _cf_net_change(out, cur, period, abs_tol, rel_tol)
        _cash_ties(out, cur, prev, period, abs_tol, rel_tol)
        _articulation(out, cur, prev, period, abs_tol, rel_tol)
    return out
