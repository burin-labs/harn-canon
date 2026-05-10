# PHP Seed Predicate Pack

This pack covers general-purpose PHP application and library code targeting modern PHP (8.1+) before framework-specific packs (Laravel, Symfony, WordPress) layer in tighter defaults. It targets review-slice issues with clear correctness, maintenance, or security impact: missing strict-types declarations, legacy syntax that depends on ini settings, removed extensions, code-injection sinks, register-globals revivals via `extract()`, untyped class state, debug leakage, SQL injection, hardcoded secrets, and PHP object injection through `unserialize()`.

## Stack Assumptions

- Source files use the `.php` extension; templates additionally use `.phtml`. Strict-types and typed-property checks scope to `.php` only because templates frequently open with HTML.
- Production paths exclude any path under `/tests/`, `/Tests/`, `/test/`, `/spec/`, `/bin/`, `/scripts/`, `/script/`, and any file ending in `Test.php`, `TestCase.php`, or `_test.php`. Vendored paths under `/vendor/`, `/node_modules/`, `/build/`, and `/dist/` are excluded everywhere.
- Projects target PHP 8.0+ where typed properties, constructor property promotion, `match`, and named arguments are standard, and where `create_function()` and the `ext/mysql` extension are gone.
- Deterministic predicates run regex over changed source text until Flow exposes a stable PHP AST query API. Rules with meaningful false-positive risk warn rather than block.
- Semantic predicates make a single judge call over changed PHP files; they should only block when they can cite concrete changed spans.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `declare_strict_types_enforced` | deterministic | Block | Production class files should opt into strict scalar coercion so type errors surface at the boundary. |
| `no_short_open_tags` | deterministic | Block | `<?` short open tags depend on the `short_open_tag` ini directive and are non-portable; PSR-1 forbids them. |
| `no_deprecated_mysql_ext` | deterministic | Block | The `ext/mysql` extension was removed in PHP 7.0; new code must use PDO or mysqli. |
| `no_create_function` | deterministic | Block | `create_function()` evaluates a string body and was removed in PHP 8.0; closures replace it. |
| `no_eval` | deterministic | Block | `eval()` is the canonical PHP code-injection sink. |
| `no_extract_from_request` | deterministic | Block | `extract($_GET/$_POST/...)` recreates the register_globals injection pattern. |
| `typed_properties` | deterministic | Warn | Untyped class properties skip the runtime invariant that typed properties enforce on every write. |
| `no_debug_dump_in_prod` | deterministic | Warn | `var_dump`/`print_r`/`var_export` write directly to output and leak internal state in production paths. |
| `prepared_statements_only` | semantic | Block | SQL built by interpolating user-controlled values is the leading vector for SQL injection. |
| `no_hardcoded_secrets` | semantic | Block | Credentials and tokens should come from `getenv`/`$_ENV` or a secret manager, not literals or `define()`. |
| `unserialize_input_is_trusted` | semantic | Block | Calling `unserialize()` on untrusted input enables PHP object injection (POP-chain) attacks. |

## Evidence

Evidence scanned on 2026-05-10.

- PHP manual: language type declarations and `strict_types`, basic syntax PHP tags, `mysqlinfo.api.choosing`, `function.create-function`, `function.eval`, `function.extract`, `function.var-dump`, `function.print-r`, `function.unserialize`, `function.getenv`, `language.oop5.properties`, PDO prepared statements, mysqli quickstart prepared statements, `migration70.removed-exts-sapis`, the PHP 8.0 migration overview, and `security.variables`.
- PHP RFCs: `scalar_type_hints_v5`, `mysql_deprecation`, `deprecations_php_7_2` (which deprecated `create_function`), `typed_properties_v2`.
- PHP-FIG: PSR-1 (basic coding standard) for PHP tag and side-effect rules; PSR-3 (logger interface) as the alternative to ad-hoc dumping.
- PHP The Right Way: `strict_types` recommendation.
- OWASP cheat sheets and project pages: SQL Injection Prevention, Secrets Management, Deserialization, Code Injection, PHP Object Injection, PHP File Inclusion, CICD-SEC-06 Insufficient Credential Hygiene.
- CWE: CWE-95 (eval injection).

## Known False Positives

- Regex predicates do not parse PHP. String literals, heredocs, and comments containing keywords can fool deterministic checks until AST-backed matching lands.
- `declare_strict_types_enforced` only inspects `.php` files that begin with `<?php` (after an optional UTF-8 BOM). Files that open with HTML or other content are intentionally skipped because strict-types must be the first statement of the file. Expect false negatives on files with leading whitespace beyond a BOM.
- `no_short_open_tags` flags `<?` followed by anything other than `php`, `=`, or `xml`, including escapes inside strings or HTML embedded in heredocs.
- `no_deprecated_mysql_ext` matches `mysql_<name>(` at word boundaries. Project-defined helpers named `mysql_helper_*` would be flagged; rename them.
- `no_create_function`, `no_eval`, `no_extract_from_request`, and `no_debug_dump_in_prod` allow method calls (`$obj->eval(`) by excluding `>` from the leading character class. Function calls inside docblock examples will still flag.
- `typed_properties` matches property declarations on a line of their own. Inline constructor property promotion such as `function __construct(public $name, public $age)` is missed; multi-line promotion (each parameter on its own line) is caught.
- `no_debug_dump_in_prod` only inspects production paths. Calls in `/bin/`, `/scripts/`, or test directories are intentionally allowed.
- Semantic predicates depend on a cheap judge call and should stay high-threshold until Flow exposes structured PHP data-flow analysis.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape mirrors the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/Service.php", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/Service.php", "text": "..."}]}
  ]
}
```
