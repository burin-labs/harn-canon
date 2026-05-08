# Java Seed Predicate Pack

This pack covers plain Java application and library code before framework-specific packs such as Spring, Android, or Maven/Gradle policy packs add tighter rules. It focuses on high-signal defaults for generic type safety, nullness contracts, exception handling, logging, immutable data modeling, and untrusted input boundaries.

## Stack Assumptions

- Source checks target `.java` files; production checks exclude common test paths and `*Test.java`, `*Tests.java`, and `*IT.java`.
- Projects are assumed to target Java 17 or newer, so records are available for simple immutable data carriers.
- Projects may use JSpecify, NullAway, Checker Framework, SpotBugs, JetBrains, Jakarta, or project-level nullness defaults; the nullness predicate accepts common annotations and package defaults.
- Deterministic predicates operate over changed source text until Flow exposes stable Java AST and build-tool queries.
- Semantic predicates may block only when the judge can cite a concrete changed span and the issue is not reliably expressible with simple syntax checks.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_raw_collection_types` | deterministic | Block | Common generic containers such as `List`, `Map`, `Set`, and `Optional` must be parameterized. |
| `null_safety_annotations` | deterministic | Warn | Public reference-returning APIs should have package-level or explicit nullness annotations. |
| `immutable_value_objects` | deterministic | Warn | Simple final-field data carriers should usually be records on Java 17+. |
| `no_swallowed_exceptions` | deterministic | Block | Empty production `catch` blocks must handle, log, rethrow, or explain ignored exceptions. |
| `prefer_stream_over_loop` | deterministic | Warn | Index-based loops over collection `size()`/`get(i)` pairs should use enhanced loops or streams. |
| `no_print_stack_trace` | deterministic | Block | Production code should log exceptions with context or rethrow rather than calling `printStackTrace()`. |
| `no_system_out_in_prod` | deterministic | Warn | Production code should use the project logger instead of direct stdout/stderr writes. |
| `optional_returns_are_not_null` | deterministic | Block | Methods returning `Optional<T>` must return an `Optional`, not `null`. |
| `jdbc_queries_use_parameters` | semantic | Block | SQL values must be bound with parameters or safe query builders. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, tokens, private keys, and production connection strings must not live in source. |

## Evidence

Evidence scanned on 2026-05-08.

- Oracle docs for Java SE 25 records, raw types in the Java Language Specification and Generics tutorial, `Collection.stream()`, `Stream`, `Optional`, `PreparedStatement`, and `java.util.logging.Logger`.
- OpenJDK JEP 395 for record rationale and data-carrier semantics.
- Error Prone bug patterns for empty catch blocks, catch-and-print-stack-trace handling, and null Optional use.
- Checkstyle `EmptyCatchBlock` guidance.
- JSpecify and NullAway nullness annotation documentation.
- OWASP cheat sheets for logging, secrets management, and SQL injection prevention.
- GitHub secret scanning documentation for hardcoded credential risk and remediation context.

## Known False Positives

- Regex predicates are intentionally conservative and file-scoped. A file containing both an offending pattern and a separate allowed pattern may be allowed or warned imprecisely until AST-level matching lands.
- `no_raw_collection_types` focuses on common collection-like APIs and does not attempt full generic type parsing.
- `null_safety_annotations` warns at file granularity when a public reference-returning method appears without a recognized nullness annotation or package default in the same changed file.
- `immutable_value_objects` warns on simple final-field classes even when framework constraints, inheritance, serialization, or identity semantics make a class the right choice.
- `prefer_stream_over_loop` only identifies the common `for (int i = 0; i < xs.size(); i++) { xs.get(i) }` shape and may miss equivalent loops.
- The semantic predicates must cite concrete changed spans and should stay high-threshold to avoid blocking on speculative security concerns.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape is deliberately simple until the Flow replay harness lands:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/main/java/App.java", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/main/java/App.java", "text": "..."}]}
  ]
}
```
