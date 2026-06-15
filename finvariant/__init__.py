"""finvariant - deterministic integrity checks for financial statements.

Give it income statement, balance sheet and cash flow data in a canonical
schema; it verifies the accounting invariants - the balance sheet balances,
the cash flow ties to the balance sheet, subtotals foot, and the three
statements articulate - and returns a structured, auditable report.

    import finvariant as fv

    s = fv.Statements(periods=["FY2024"],
                      income_statement={"FY2024": {...}},
                      balance_sheet={"FY2024": {...}},
                      cash_flow={"FY2024": {...}})

    r = fv.check(s)
    r.ok            # do the statements tie out?
    r.summary()     # plain-language verdict with every failed check
    r.to_dict()     # JSON-safe payload with provenance

It verifies; it does not parse, fetch or build statements.
"""

from ._result import AuditReport, RuleOutcome
from ._version import __version__
from .check import check
from .model import Statements

__all__ = ["check", "Statements", "AuditReport", "RuleOutcome", "__version__"]
