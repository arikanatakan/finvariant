"""The public entry point: ``check()`` runs the applicable invariants over a set
of statements and returns an :class:`AuditReport`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ._result import AuditReport, data_hash, utcnow
from ._version import __version__
from .model import Statements
from .rules import run_rules


def _jsonable(table: Mapping) -> dict:
    return {period: dict(values) for period, values in table.items()}


def check(statements: Statements, *, abs_tol: float = 0.5, rel_tol: float = 1e-4,
          rules: Iterable[str] | None = None) -> AuditReport:
    """Check ``statements`` against the accounting invariants.

    Parameters
    ----------
    statements:
        A :class:`Statements` instance in the canonical schema.
    abs_tol, rel_tol:
        A check passes when the discrepancy is within
        ``max(abs_tol, rel_tol * abs(expected))``. The defaults absorb the
        rounding found in statements reported in whole millions.
    rules:
        Optional set of rule ids to restrict the report to.
    """
    if not isinstance(statements, Statements):
        raise TypeError("check() expects a Statements instance")

    outcomes = run_rules(statements, abs_tol, rel_tol)
    if rules is not None:
        wanted = set(rules)
        outcomes = [o for o in outcomes if o.rule_id in wanted]

    meta = {
        "computed_at": utcnow(),
        "version": __version__,
        "periods": list(statements.periods),
        "abs_tol": abs_tol,
        "rel_tol": rel_tol,
        "input_hash": data_hash({
            "periods": list(statements.periods),
            "is": _jsonable(statements.income_statement),
            "bs": _jsonable(statements.balance_sheet),
            "cf": _jsonable(statements.cash_flow),
        }),
    }
    return AuditReport(tuple(outcomes), meta)
