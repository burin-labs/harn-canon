# TypeScript Seed Predicate Pack

This pack covers plain TypeScript and TSX code before framework-specific packs such as React, Next.js, or Node services add tighter local rules. It focuses on high-signal defaults for type safety, async correctness, production logging, and untrusted boundary handling.

## Stack Assumptions

- Files use `.ts`, `.tsx`, `.mts`, or `.cts`; config checks target `tsconfig.json`.
- Projects use TypeScript strict mode and type-aware linting where practical.
- Deterministic predicates operate over changed source text until Flow exposes stable TypeScript AST and tsconfig-resolution queries.
- Semantic predicates may block only when the judge can cite a concrete changed span and the issue is not reliably expressible with simple syntax checks.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_floating_promises` | deterministic | Block | Obvious Promise-returning calls must be awaited, returned, explicitly void-marked, or handled with `.catch()`. |
| `no_any_without_comment` | deterministic | Block | Explicit `any` requires a targeted `no-explicit-any` disable comment with a reason. |
| `strict_null_checks_required` | deterministic | Block | Changed tsconfig files must not disable `strict` or `strictNullChecks`. |
| `no_console_in_prod_path` | deterministic | Block | Production TypeScript paths must not ship `console.log`, `debug`, `trace`, or `info`. |
| `exhaustive_switch` | deterministic | Warn | Switches should include explicit exhaustiveness handling. |
| `ts_comment_suppressions_have_description` | deterministic | Block | TypeScript suppression comments need a meaningful reason, and `@ts-nocheck` is blocked. |
| `no_non_null_assertion_in_prod_path` | deterministic | Warn | Production code should narrow nullable values instead of using postfix `!`. |
| `no_inline_type_only_imports` | deterministic | Warn | Inline-only type imports should use top-level `import type`. |
| `runtime_validate_external_data` | semantic | Block | External data must be runtime-validated before being trusted as a domain type. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, tokens, private keys, and production connection strings must not live in source. |
| `no_sensitive_data_in_logs` | semantic | Block | Logs and error messages must not expose secrets or sensitive user data. |

## Evidence

Evidence scanned on 2026-04-26.

- typescript-eslint rules: `no-floating-promises`, `no-explicit-any`, `switch-exhaustiveness-check`, `ban-ts-comment`, `no-non-null-assertion`, `no-import-type-side-effects`, and `no-unsafe-assignment`.
- TypeScript docs: `strict`, `strictNullChecks`, `unknown`, exhaustiveness checking with `never`, and `verbatimModuleSyntax`.
- ESLint `no-console` rule and MDN Promise `.catch()` documentation.
- OWASP cheat sheets for input validation, logging, and secrets management.
- GitHub secret scanning docs for hardcoded credential risk and remediation context.

## Known False Positives

- Regex predicates are intentionally conservative and file-scoped. A file containing both an offending pattern and an allowed pattern may be allowed until AST-level matching lands.
- `no_floating_promises` only blocks obvious async surfaces such as `fetch`, `Promise.*`, `new Promise`, or `*Async` calls until TypeScript type information is available.
- `strict_null_checks_required` currently blocks changed `tsconfig.json` files that turn strictness off. The intended runtime form should resolve the effective tsconfig for each touched TypeScript file.
- `exhaustive_switch` warns on non-union switches because source text alone cannot distinguish union/enumeration switches from scalar switches.
- `no_inline_type_only_imports` warns on all inline type imports, including mixed value/type imports; projects that prefer inline style can downgrade this predicate locally.
- The semantic predicates must cite concrete changed spans and should stay high-threshold to avoid blocking on speculative security concerns.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape is deliberately simple until the Flow replay harness lands:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/file.ts", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/file.ts", "text": "..."}]}
  ]
}
```
