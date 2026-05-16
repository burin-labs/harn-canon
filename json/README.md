# JSON Seed Predicate Pack

This pack covers strict JSON content quality before format-specific packs (npm `package.json` rules, JSON Schema authoring, OpenAPI documents, etc.) layer narrower checks on top. It focuses on RFC 8259 conformance, encoding hygiene, and untrusted-data hazards that show up across most JSON files a repo ships.

## Stack Assumptions

- Files use `.json`, `.jsonc`, or `.json5`. Strict-conformance predicates apply only to `.json`; `.jsonc` and `.json5` are exempt because their parsers accept comments and trailing commas by design.
- Files matching `tsconfig*.json`, `jsconfig*.json`, or paths under `.vscode/` and `.devcontainer/` are treated as JSONC-by-convention and exempt from the strict checks; the toolchains that read them allow comments and trailing commas.
- Deterministic predicates work on changed source text until Flow exposes a stable JSON AST and value-tree query API.
- Semantic predicates may block only when the judge can cite a concrete changed value or property and the issue is not reliably expressible with simple syntax checks.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_trailing_commas` | deterministic | Block | Strict `.json` must follow RFC 8259, which forbids trailing commas. |
| `no_comments_in_json` | deterministic | Block | Strict `.json` must not contain `//` or `/*` comment markers; rename to `.jsonc` or `.json5` if comments are required. |
| `strings_use_double_quotes` | deterministic | Block | Strict `.json` object keys and string values must use double quotation marks, not single quotes. |
| `no_bom_prefix` | deterministic | Warn | JSON files must not begin with a UTF-8 byte order mark. |
| `no_nan_or_infinity_literals` | deterministic | Block | `NaN`, `Infinity`, and `-Infinity` are not valid JSON numbers. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, tokens, private keys, and production connection strings must not live in committed JSON values. |
| `respects_declared_schema` | semantic | Block | When a JSON file declares a `$schema` reference, changed values must satisfy it. |
| `stable_key_ordering` | semantic | Warn | Config-shaped JSON edits should not reorder unrelated keys and create diff noise. |

## Evidence

Evidence scanned on 2026-05-09 and refreshed on 2026-05-15 for new predicates.

- IETF RFC 8259 — JSON grammar (numbers, objects, strings), the explicit "no comments" stance, and the byte-order-mark prohibition.
- json.org canonical syntax reference.
- VS Code JSON-with-comments documentation describing the `.jsonc` convention.
- MDN `JSON.stringify` documentation showing how `NaN` and `Infinity` are serialized to `null`.
- OWASP Secrets Management cheat sheet and GitHub secret-scanning documentation.
- JSON Schema specification and the JSON Schema "getting started" guide.
- npm `package.json` configuration reference describing the conventional ordering authors expect tooling to preserve.

## Known False Positives

- Regex predicates are intentionally conservative and file-scoped. A literal `,]`, `//`, `/*`, `NaN`, or `Infinity` substring inside a JSON string value can trip the corresponding predicate until value-aware matching lands.
- `strings_use_double_quotes` may flag a string value that itself contains a JSON-looking snippet with single quotes, because v0 scans raw file text rather than parsed string boundaries.
- `no_trailing_commas` and `no_comments_in_json` apply only to `.json`; `.jsonc`, `.json5`, and the JSONC-by-convention paths listed above are exempt. Project-specific JSONC formats not on that list (for example, `tslint.json`) will need an explicit allowlist later.
- `no_bom_prefix` triggers any time the file's first three bytes are the UTF-8 BOM, even when downstream tooling silently strips it. The verdict is `Warn` because the file usually still works but eventually breaks a parser somewhere.
- `respects_declared_schema` only fires when a `$schema` reference is present and the violation is concretely visible in the slice; it is not a full JSON Schema validator.
- `stable_key_ordering` is intentionally narrow and should stay out of changes that touch the reordered region for substantive reasons; it is biased toward warning rather than blocking to avoid fighting alphabetizing formatters.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the other packs in this repo:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "config/app.json", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "config/app.json", "text": "..."}]}
  ]
}
```
