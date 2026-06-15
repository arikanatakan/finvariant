"""Canonical financial-statement schema and the ``Statements`` container.

Sign convention (the checks assume it; finvariant does not parse or convert):

- Income statement: revenue positive; expenses (``cogs``, ``operating_expenses``,
  ``interest_expense``, ``tax``) entered as positive magnitudes, so
  ``net_income = ((revenue - cogs) - operating_expenses + other_income
  - interest_expense) - tax``.
- Balance sheet: every line positive as normally presented. ``treasury_stock``
  and an accumulated deficit may be negative.
- Cash flow: every line signed by its effect on cash (inflows positive,
  outflows negative). So ``capex``, ``debt_repaid``, ``share_buybacks`` and
  ``dividends_paid`` are negative, and
  ``net_change_in_cash = cfo + cfi + cff + fx_effect``.

Provide only the fields you have. A check whose inputs are missing is reported
as skipped, never failed. To check that a subtotal foots, provide its line
items as well as the subtotal; partial line items are reported as not footing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping

# Income statement: (subtotal, plus_terms, minus_terms). A subtotal must equal
# the sum of the plus terms minus the sum of the minus terms.
IS_RELATIONS: list[tuple[str, list[str], list[str]]] = [
    ("gross_profit", ["revenue"], ["cogs"]),
    ("operating_income", ["gross_profit"], ["operating_expenses"]),
    ("pretax_income", ["operating_income", "other_income"], ["interest_expense"]),
    ("net_income", ["pretax_income"], ["tax"]),
]
IS_FIELDS: set[str] = {
    "revenue", "cogs", "gross_profit", "operating_expenses", "operating_income",
    "other_income", "interest_expense", "pretax_income", "tax", "net_income",
    "depreciation_amortization",
}

# Balance sheet sections: subtotal -> line items that should sum to it.
BS_SECTIONS: dict[str, list[str]] = {
    "total_current_assets": [
        "cash", "short_term_investments", "accounts_receivable", "inventory",
        "prepaid_expenses", "other_current_assets",
    ],
    "total_non_current_assets": [
        "ppe_net", "goodwill", "intangible_assets", "long_term_investments",
        "deferred_tax_assets", "other_non_current_assets",
    ],
    "total_current_liabilities": [
        "accounts_payable", "short_term_debt", "accrued_liabilities",
        "deferred_revenue", "current_portion_long_term_debt",
        "other_current_liabilities",
    ],
    "total_non_current_liabilities": [
        "long_term_debt", "deferred_tax_liabilities", "pension_liabilities",
        "other_non_current_liabilities",
    ],
    "total_equity": [
        "common_stock", "additional_paid_in_capital", "retained_earnings",
        "treasury_stock", "accumulated_oci", "minority_interest", "other_equity",
    ],
}
# Higher-level balance-sheet sums.
BS_TOTALS: dict[str, list[str]] = {
    "total_assets": ["total_current_assets", "total_non_current_assets"],
    "total_liabilities": ["total_current_liabilities", "total_non_current_liabilities"],
}
BS_FIELDS: set[str] = (
    {item for items in BS_SECTIONS.values() for item in items}
    | set(BS_SECTIONS) | set(BS_TOTALS)
)

# Cash flow sections: subtotal -> line items that should sum to it.
CF_SECTIONS: dict[str, list[str]] = {
    "cfo": [
        "net_income", "depreciation_amortization", "stock_based_compensation",
        "deferred_taxes", "change_in_accounts_receivable", "change_in_inventory",
        "change_in_accounts_payable", "change_in_working_capital", "other_operating",
    ],
    "cfi": [
        "capex", "acquisitions", "divestitures", "purchases_of_investments",
        "sales_of_investments", "other_investing",
    ],
    "cff": [
        "debt_issued", "debt_repaid", "equity_issued", "share_buybacks",
        "dividends_paid", "other_financing",
    ],
}
CF_OTHER: list[str] = ["fx_effect", "net_change_in_cash", "beginning_cash", "ending_cash"]
CF_FIELDS: set[str] = (
    {item for items in CF_SECTIONS.values() for item in items}
    | set(CF_SECTIONS) | set(CF_OTHER)
)


def _validate_period(name: str, period: str, values: Mapping[str, float],
                     valid: set[str]) -> None:
    unknown = sorted(set(values) - valid)
    if unknown:
        raise ValueError(
            f"{name} for period {period!r} has unknown fields: {unknown}. "
            f"Map them to a canonical role or an 'other_*' line."
        )
    for key, value in values.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{name}[{period!r}][{key!r}] must be a number")
        if not math.isfinite(float(value)):
            raise ValueError(f"{name}[{period!r}][{key!r}] must be finite")


@dataclass
class Statements:
    """A set of financial statements, by period, in the canonical schema."""

    periods: list[str]
    income_statement: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    balance_sheet: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    cash_flow: Mapping[str, Mapping[str, float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.periods or not all(isinstance(p, str) for p in self.periods):
            raise ValueError("periods must be a non-empty list of period labels")
        if len(set(self.periods)) != len(self.periods):
            raise ValueError("periods must be unique")
        known = set(self.periods)
        for name, table, valid in (
            ("income_statement", self.income_statement, IS_FIELDS),
            ("balance_sheet", self.balance_sheet, BS_FIELDS),
            ("cash_flow", self.cash_flow, CF_FIELDS),
        ):
            extra = set(table) - known
            if extra:
                raise ValueError(f"{name} has periods not in 'periods': {sorted(extra)}")
            for period, values in table.items():
                _validate_period(name, period, values, valid)

    def at(self, period: str) -> dict[str, dict[str, float]]:
        """The three statements for one period as plain dicts (missing -> empty)."""
        return {
            "is": dict(self.income_statement.get(period, {})),
            "bs": dict(self.balance_sheet.get(period, {})),
            "cf": dict(self.cash_flow.get(period, {})),
        }
