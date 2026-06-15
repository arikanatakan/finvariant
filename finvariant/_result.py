"""The result contract: one ``AuditReport`` for every check, with provenance
and a JSON-safe payload, so a verification can be reproduced and audited later.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

SCHEMA = 1

PASS = "pass"
FAIL = "fail"
SKIP = "skip"
ERROR = "error"
WARNING = "warning"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def data_hash(obj: object) -> str:
    payload = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()[:16]


@dataclass(frozen=True)
class RuleOutcome:
    """The result of one rule on one period."""

    rule_id: str
    description: str
    statement: str
    period: str
    status: str            # pass | fail | skip
    severity: str          # error | warning
    expected: float | None = None
    actual: float | None = None
    difference: float | None = None
    message: str = ""

    def __str__(self) -> str:
        tag = self.severity.upper() if self.status == FAIL else self.status.upper()
        head = f"[{tag}] {self.rule_id} {self.description} ({self.period})"
        if self.status == FAIL and self.expected is not None:
            return (f"{head}: expected {self.expected:g}, got {self.actual:g}, "
                    f"off by {self.difference:g}")
        return head if not self.message else f"{head}: {self.message}"


@dataclass(frozen=True)
class AuditReport:
    """Outcome of checking a set of statements against the accounting invariants."""

    outcomes: tuple[RuleOutcome, ...]
    meta: dict

    @property
    def findings(self) -> tuple[RuleOutcome, ...]:
        """The rules that failed."""
        return tuple(o for o in self.outcomes if o.status == FAIL)

    @property
    def ok(self) -> bool:
        """True when no error-severity rule failed."""
        return not any(o.status == FAIL and o.severity == ERROR for o in self.outcomes)

    @property
    def n_passed(self) -> int:
        return sum(1 for o in self.outcomes if o.status == PASS)

    @property
    def n_failed(self) -> int:
        return sum(1 for o in self.outcomes if o.status == FAIL)

    @property
    def n_skipped(self) -> int:
        return sum(1 for o in self.outcomes if o.status == SKIP)

    def _verdict(self) -> str:
        if not self.ok:
            return "FAIL - statements do not tie out"
        warnings = any(o.status == FAIL and o.severity == WARNING for o in self.outcomes)
        return "PASS (with warnings)" if warnings else "PASS - statements tie out"

    def summary(self) -> str:
        run = self.n_passed + self.n_failed
        lines = [
            f"finvariant audit - {self.meta.get('computed_at', '')}",
            f"  {run} checks run, {self.n_passed} passed, {self.n_failed} failed, "
            f"{self.n_skipped} skipped",
        ]
        for finding in self.findings:
            lines.append("  " + str(finding))
        lines.append(f"Verdict: {self._verdict()}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "ok": self.ok,
            "verdict": self._verdict(),
            "counts": {
                "passed": self.n_passed,
                "failed": self.n_failed,
                "skipped": self.n_skipped,
            },
            "findings": [
                {
                    "rule_id": o.rule_id,
                    "description": o.description,
                    "statement": o.statement,
                    "period": o.period,
                    "severity": o.severity,
                    "expected": o.expected,
                    "actual": o.actual,
                    "difference": o.difference,
                    "message": o.message,
                }
                for o in self.findings
            ],
            "meta": self.meta,
        }
