# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[semantic versioning](https://semver.org/).

## [0.1.0] - 2026-06-15

First release.

### Added

- `Statements` - a canonical, validated schema for income statement, balance
  sheet and cash flow data across one or more periods.
- `check()` - verifies the accounting invariants and returns an `AuditReport`:
  - footing: every subtotal equals the sum of its line items, in all three
    statements;
  - the accounting equation: assets = liabilities + equity;
  - cash: net change = cfo + cfi + cff, ending cash ties to the balance sheet,
    beginning cash ties to the prior period;
  - articulation: net income agrees across statements, retained earnings roll
    forward by net income less dividends.
- `AuditReport` - `ok`, per-rule findings (expected vs actual, difference,
  severity), counts, `summary()` and a JSON-safe `to_dict()` with provenance.
- Configurable absolute and relative tolerances for rounded statements.
- Validation suite: a hand-built consistent model, the real published
  statements of Apple (FY2024), Tesla (FY2024) and NVIDIA (FY2025), and one
  isolated breakage per invariant.
