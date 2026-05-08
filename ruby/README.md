# Ruby Seed Predicate Pack

This pack covers general-purpose Ruby application and library code before framework-specific packs such as Rails add tighter defaults. It focuses on review-slice checks with clear correctness, maintenance, or security impact: explicit string literal mutability, global mutation, risky core-class changes, legacy options hashes, dynamic evaluation, unsafe deserialization, superclass initialization, RuboCop policy drift, hardcoded secrets, and sensitive logging.

## Stack Assumptions

- Files use `.rb`, `.rake`, `.gemspec`, `Gemfile`, or `Rakefile` Ruby source conventions.
- Projects target modern Ruby with keyword arguments, Psych safe-loading APIs, and RuboCop available as the local style authority.
- Deterministic predicates run over changed source text until Flow exposes a stable Ruby AST query API. Rules with meaningful false-positive risk warn rather than block.
- Production-path checks exclude obvious `spec/`, `test/`, `tests/`, `bin/`, `script/`, `scripts/`, `Rakefile`, and `.rake` paths.
- Semantic predicates use one cheap judge call and should block only when they can cite concrete changed spans.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `frozen_string_literal_magic_comment` | deterministic | Warn | Production Ruby files should opt into frozen string literals explicitly. |
| `no_monkey_patch_stdlib` | deterministic | Block | Application code should not reopen high-risk Ruby core classes globally. |
| `no_global_variables` | deterministic | Block | Application-defined `$globals` leak mutable state across the process. |
| `no_class_variable_state` | deterministic | Block | Class variables are shared through inheritance and make state ownership unclear. |
| `prefer_keyword_args` | deterministic | Warn | Modern Ruby APIs should prefer explicit keyword arguments over `options = {}`. |
| `no_dynamic_eval` | deterministic | Block | Dynamic `eval`-style execution is hard to reason about and can become injection. |
| `no_unsafe_deserialization` | deterministic | Block | YAML/Psych/Marshal object loading should use safe, explicit deserialization paths. |
| `initialize_calls_super` | deterministic | Warn | Subclass constructors should call `super` unless skipping parent setup is intentional. |
| `rubocop_style_compliance` | semantic | Block | Ruby changes should honor the repo's RuboCop configuration or justify narrow disables. |
| `no_hardcoded_secrets` | semantic | Block | Credentials and tokens should come from secret managers or scoped environment. |
| `no_sensitive_data_in_logs` | semantic | Block | Logs, telemetry, and raised messages should not expose secrets or sensitive user data. |

## Evidence

Evidence scanned on 2026-05-08.

- Ruby 3.4 documentation and RubyGuides: magic comments, global variables, class variables, keyword arguments, `Kernel#eval`, inheritance, refinements, modules/classes, open classes, and `Psych.safe_load`.
- RuboCop documentation: `Style/FrozenStringLiteralComment`, `Style/GlobalVars`, `Style/ClassVars`, `Style/OptionHash`, `Security/Eval`, `Security/YAMLLoad`, `Lint/MissingSuper`, configuration, and the RuboCop project overview.
- OWASP cheat sheets and GitHub secret scanning documentation: deserialization, secrets management, logging, and hardcoded credential risk.

## Known False Positives

- Regex predicates are source-text checks. Comments, string literals, metaprogramming, and multiline formatting can fool them until AST-backed matching lands.
- `frozen_string_literal_magic_comment` warns on production Ruby files that intentionally rely on mutable string literals.
- `no_monkey_patch_stdlib` blocks direct reopening of selected core classes even when a project intentionally centralizes compatibility patches. Prefer refinements or an explicit patch module.
- `no_global_variables` only targets lowercase application globals; special Ruby globals and uppercase builtin globals are left alone.
- `no_dynamic_eval` allows literal-string eval calls but blocks dynamic arguments. It cannot prove whether a variable is trusted.
- `no_unsafe_deserialization` blocks all `Marshal.load` and direct YAML/Psych load calls because source text cannot prove trust boundaries.
- `initialize_calls_super` is conservative at the file level and may warn when `super` appears outside the target constructor or when a parent constructor is intentionally skipped.
- Semantic predicates depend on a cheap judge and should stay high-threshold until Flow exposes structured Ruby data-flow and RuboCop results.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape mirrors the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "app/service.rb", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "app/service.rb", "text": "..."}]}
  ]
}
```
