# C# Seed Predicate Pack

This pack covers plain C# and .NET library or application code before framework-specific packs such as ASP.NET Core, MAUI, Unity, or Orleans add tighter local rules. It focuses on high-signal defaults for nullable safety, async correctness, analyzer hygiene, exception diagnostics, and security-sensitive data handling.

## Stack Assumptions

- Files use `.cs`; project checks target `.csproj`, `Directory.Build.props`, and `Directory.Build.targets`.
- Projects use SDK-style .NET builds with nullable reference types enabled centrally or in each changed project file.
- Deterministic predicates operate over changed source text until Flow exposes stable Roslyn symbols, analyzer configuration, and effective MSBuild property queries.
- Semantic predicates may block only when the judge can cite a concrete changed span and the issue is not reliably expressible with simple syntax checks.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `nullable_reference_types_enabled` | deterministic | Block | Changed C# project defaults must enable nullable reference types. |
| `async_method_naming` | deterministic | Warn | Async Task-returning methods should use an `Async` suffix unless a fixed contract prevents it. |
| `no_task_wait` | deterministic | Block | Production C# paths must not synchronously block on `Task` completion. |
| `configure_await_false_in_libraries` | deterministic | Warn | Library-looking code should make continuation capture explicit with `ConfigureAwait`. |
| `no_unused_privates` | deterministic | Block | Changed analyzer configuration must not disable IDE0051 unused-private-member diagnostics. |
| `no_throw_ex_resets_stack` | deterministic | Block | Catch blocks should use bare `throw;` instead of `throw ex;`. |
| `no_valuetask_reuse` | deterministic | Warn | `ValueTask` instances should not be consumed more than once. |
| `no_console_write_in_prod_path` | deterministic | Warn | Production code should use structured logging instead of ad hoc `Console` writes. |
| `sql_commands_use_parameters` | semantic | Block | SQL commands must bind untrusted values instead of interpolating them into command text. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, tokens, private keys, and production connection strings must not live in source or config. |
| `no_sensitive_data_in_logs` | semantic | Block | Logs and exception messages must not expose secrets or sensitive user data. |

## Evidence

Evidence scanned on 2026-05-08.

- Microsoft Learn C# nullable reference type docs, nullable reference type reference, and exception-handling statement docs.
- Microsoft Learn .NET analyzer docs for CA1849, CA2007, CA2012, CA2100, CA2200, IDE0051, code-style naming rules, and reliability rule indexes.
- Microsoft Learn .NET logging guidance for structured `ILogger` usage and production log-level considerations.
- OWASP cheat sheets for SQL injection prevention, logging, and secrets management.
- GitHub secret scanning docs for hardcoded credential risk and remediation context.

## Known False Positives

- Regex predicates are intentionally conservative and file-scoped. A file containing both an offending pattern and an allowed pattern may be allowed until Roslyn-level matching lands.
- `nullable_reference_types_enabled` only inspects changed project/default files. The intended runtime form should resolve the effective nullable context for each touched C# file.
- `async_method_naming` warns on interface implementations and framework overrides when source text alone cannot see the inherited contract.
- `configure_await_false_in_libraries` treats non-test files under `/src/` as library-looking unless their path suggests UI or MVC surface area.
- `no_unused_privates` guards analyzer configuration rather than trying to identify unused private members from text alone.
- `no_valuetask_reuse` only catches obvious repeated local consumption and should become a Roslyn dataflow predicate later.
- The semantic predicates must cite concrete changed spans and should stay high-threshold to avoid blocking on speculative security concerns.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape is deliberately simple until the Flow replay harness lands:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/File.cs", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/File.cs", "text": "..."}]}
  ]
}
```
