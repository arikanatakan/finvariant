# Contributing

Thanks for your interest in finvariant.

## Development setup

```
git clone https://github.com/arikanatakan/finvariant
cd finvariant
python -m pip install -e ".[dev]"
```

## Before opening a pull request

```
ruff check .
pytest
```

Both must pass. A new invariant should come with cases in `tests/cases/` (one
JSON file per case): a consistent example that passes and an isolated breakage
that the new rule, and only that rule, catches. Each file should explain what it
demonstrates in its "description". Reference numbers taken from real statements
must cite their source (filing and fiscal year).

## Scope

finvariant verifies the internal consistency of financial statements. It does
not parse, fetch, build or forecast them. New rules are welcome when they encode
a genuine accounting invariant and are checked from its definition.

## Conventions

- Keep the `Statements` and `AuditReport` contracts append-only: add fields, do
  not rename or remove.
- A rule whose inputs are absent emits nothing or a skip, never a failure.
- Rule ids are stable, readable identifiers (for example `EQ.accounting_equation`).
