# TOML Seed Predicate Pack

This pack covers TOML configuration documents — Cargo manifests, `pyproject.toml`, tool configs, and any other `.toml` file. TOML has a small surface area, so this v0 focuses on rules drawn directly from the TOML 1.0 specification plus the dominant package-metadata conventions used by the largest TOML ecosystems.

## Stack Assumptions

- TOML files use the `.toml` extension (covers `Cargo.toml`, `pyproject.toml`, `taplo.toml`, `deny.toml`, and the long tail of tool configs).
- Predicates run on changed slices and use file-text scans — no separate TOML parser is invoked, so syntactic edge cases that a parser would catch (e.g. unterminated strings) are out of scope here and remain the parser's job.
- Advisory rules return `Warn` when a project's existing convention may legitimately diverge. Blocking rules are reserved for spec violations and security-sensitive issues.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_duplicate_table_headers` | deterministic | Block | TOML 1.0 forbids defining the same standard table more than once. |
| `no_trailing_comma_in_inline_table` | deterministic | Block | TOML 1.0 inline tables disallow a terminating comma after the last pair. |
| `boolean_literals_are_lowercase` | deterministic | Block | TOML boolean literals are case-sensitive and must be lowercase `true` or `false`. |
| `key_naming_convention` | deterministic | Warn | Bare keys with uppercase letters drift from the lowercase snake/kebab convention used by Cargo and PEP 621. |
| `datetime_includes_offset` | deterministic | Warn | Datetime values without an offset are local-date-times and resolve differently across machines. |
| `secrets_not_hardcoded_in_toml` | semantic | Block | Credentials and signing secrets belong in env vars or a secret manager, not committed config. |
| `package_metadata_declares_license` | semantic | Warn | Publishable Cargo and Python package metadata should declare license information. |

## Evidence

Evidence scanned on 2026-05-09 and refreshed on 2026-05-15 for new predicates.

- TOML 1.0 specification (canonical reference for table, inline-table, key, and datetime grammar): the `toml.io` rendered spec and the `toml-lang/toml` 1.0.0 source.
- Cargo manifest reference and PEP 621 `pyproject.toml` specification (lowercase / kebab-case key conventions adopted by the two largest TOML ecosystems).
- Cargo manifest reference and PyPA project metadata specification for package license fields.
- RFC 3339 (datetime grammar that TOML inherits, including the meaning of an absent offset).
- OWASP Secrets Management Cheat Sheet, GitHub secret-scanning docs, and CWE-798 (hardcoded credentials).

## Known False Positives

- Regex predicates do not parse TOML. Unusual whitespace, comments inside complex values, or inline tables split across (technically invalid) lines may confuse the deterministic checks.
- `no_duplicate_table_headers` relies on a regex backreference and is intentionally narrow: it catches `[a.b]` repeated verbatim but does not catch the harder case of a dotted key (e.g. `a.b.c = 1`) implicitly redefining a table established with `[a.b]`. Implicit-redefinition detection needs a real parser and is left for a future revision.
- `no_trailing_comma_in_inline_table` only inspects single-line inline tables (the only shape TOML 1.0 permits). Inline tables that have been illegally split across lines will not be flagged here — the parser will reject them first.
- `boolean_literals_are_lowercase` inspects direct values after `=`. Boolean-looking strings inside quoted values or arrays are ignored.
- `key_naming_convention` flags any bare key containing an uppercase ASCII letter. Projects that intentionally use mixed case (Hugo's `[Params]` style is one example) can suppress per-finding once the predicate runtime exposes suppressions.
- `datetime_includes_offset` only inspects datetime literals that appear directly on the right-hand side of `=`. Datetime values nested inside arrays or inline tables on separate lines are not flagged in v0.
- `secrets_not_hardcoded_in_toml` depends on the judge recognizing concrete credential-shaped strings. It should remain high-threshold and cite exact lines before blocking; placeholders, env-var references, and clearly fake fixtures must allow.
- `package_metadata_declares_license` is intentionally Warn-level because private workspaces, unpublished examples, and inherited workspace metadata can be legitimate.

## Future Predicates

These were considered for v0 and deferred until the Harn Flow runtime exposes the needed primitives:

- `stable_top_level_table_order` — warn when top-level table headers are reordered relative to `repo_at_base`. Useful for diff hygiene but requires base-state file lookup that no current pack exercises.
- `no_implicit_table_redefinition` — block dotted keys that implicitly redefine an explicitly opened table. Requires a real TOML parser to avoid heavy false-positive rates.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "Cargo.toml", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "Cargo.toml", "text": "..."}]}
  ]
}
```
