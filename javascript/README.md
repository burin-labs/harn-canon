# JavaScript Seed Predicate Pack

This pack covers plain JavaScript before framework-specific packs such as React, Node services, browser extensions, or build tooling add narrower rules. It focuses on high-signal defaults for async correctness, dynamic-code hazards, production logging, global scope hygiene, and untrusted data handling.

## Stack Assumptions

- Files use `.js`, `.jsx`, `.mjs`, or `.cjs`.
- Projects use modern JavaScript, strict mode or modules where practical, and linting compatible with current ESLint rule guidance.
- Deterministic predicates operate over changed source text until Flow exposes stable JavaScript AST and module-resolution queries.
- Semantic predicates may block only when the judge can cite a concrete changed span and the issue is not reliably expressible with simple syntax checks.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_floating_promises` | deterministic | Block | Obvious Promise-returning calls must be awaited, returned, explicitly void-marked, or handled with `.catch()`. |
| `no_eval` | deterministic | Block | Direct `eval` use is blocked because it executes source text dynamically. |
| `no_implied_eval` | deterministic | Block | Timer APIs must receive functions instead of strings of JavaScript source. |
| `strict_equality` | deterministic | Block | Loose equality and inequality are blocked in favor of `===` and `!==`. |
| `no_var_keyword` | deterministic | Block | `var` declarations are blocked in favor of block-scoped `let` or `const`. |
| `no_console_in_prod_path` | deterministic | Block | Production JavaScript paths must not ship `console.log`, `debug`, `trace`, or `info`. |
| `no_with_statement` | deterministic | Block | `with` statements are blocked because they are incompatible with strict mode and obscure name resolution. |
| `no_implicit_globals` | deterministic | Warn | Browser-script-style top-level declarations should not leak names onto the global object. |
| `runtime_validate_external_data` | semantic | Block | External data must be runtime-validated before being trusted as domain data. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, tokens, private keys, and production connection strings must not live in source. |
| `no_sensitive_data_in_logs` | semantic | Block | Logs and error messages must not expose secrets or sensitive user data. |

## Evidence

Evidence scanned on 2026-05-08.

- ESLint rules: `no-eval`, `no-implied-eval`, `eqeqeq`, `no-var`, `no-console`, `no-with`, and `no-implicit-globals`.
- MDN JavaScript and Web API docs: `eval`, `Promise.prototype.catch`, `fetch`, `JSON.parse`, strict equality, strict mode, and `var`.
- OWASP cheat sheets for input validation, logging, and secrets management.
- GitHub secret scanning docs for hardcoded credential risk and remediation context.

## Known False Positives

- Regex predicates are intentionally conservative and file-scoped. A file containing both an offending pattern and an allowed pattern may be allowed until AST-level matching lands.
- `no_floating_promises` only blocks obvious async surfaces such as `fetch`, `Promise.*`, `new Promise`, or `*Async` calls until promise-aware JavaScript analysis is available.
- `strict_equality` is source-text based and does not inspect comments, strings, or project-specific `== null` conventions.
- `no_implicit_globals` warns on top-level function declarations even inside CommonJS modules because source text alone cannot reliably distinguish browser script execution from module execution.
- `no_console_in_prod_path` allows tests and CLI paths but does not yet understand custom generated-code or storybook directories.
- The semantic predicates must cite concrete changed spans and should stay high-threshold to avoid blocking on speculative security concerns.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape is deliberately simple until the Flow replay harness lands:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/file.js", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/file.js", "text": "..."}]}
  ]
}
```
