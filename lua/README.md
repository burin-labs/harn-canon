# Lua Seed Predicate Pack

This pack covers general-purpose Lua application and library code targeting modern Lua (5.2+, including LuaJIT). It focuses on review-slice checks with clear correctness, maintenance, or security impact: implicit globals, dynamic source loading, removed-API usage (`setfenv`/`getfenv`), shell-execution hygiene, module-return convention, `require` binding style, tail-call recursion, metatable-boundary documentation, and hardcoded secrets.

## Stack Assumptions

- Files use the `.lua` extension. LuaRocks `.rockspec` files are intentionally excluded — they are written as bare-name globals (a Lua-as-DSL pattern) and would trip the implicit-globals heuristic.
- Projects target Lua 5.2 or newer (or LuaJIT) — `setfenv` and `getfenv` were removed in Lua 5.2 and `loadstring` was folded into `load`. Code that needs Lua 5.1 compatibility should suppress the affected predicates locally.
- Production-path checks exclude obvious `spec/`, `test/`, `tests/`, `bin/`, `script/`, `scripts/`, `examples/` paths and files ending in `_spec.lua` or `_test.lua`.
- `module_returns_value` further excludes files that begin with a `#!` shebang, treating those as scripts rather than modules.
- Deterministic predicates run over changed source text until Flow exposes a stable Lua AST query API. Rules with meaningful false-positive risk (`no_implicit_globals`, `module_returns_value`, `require_assigned_to_local`) warn rather than block.
- Semantic predicates use one cheap judge call and should block only when they can cite concrete changed spans.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_global_function_definition` | deterministic | Block | Top-level `function name(...)` creates an implicit global; modules should declare `local function` or attach to a module table. |
| `no_implicit_globals` | deterministic | Warn | Top-level bare-name assignments leak through `_G`; they should be `local` or written through `_G.` to make intent explicit. |
| `no_loadstring_or_loadfile` | deterministic | Block | Compiling caller-supplied Lua source is the equivalent of `eval` and is the leading injection vector in scripted hosts. |
| `no_setfenv_or_getfenv` | deterministic | Block | Both functions were removed in Lua 5.2 and are unavailable on modern runtimes; use the `_ENV` upvalue instead. |
| `no_unsafe_os_command` | deterministic | Block | `os.execute` and `io.popen` invoke a shell; non-literal arguments are command-injection risks. |
| `module_returns_value` | deterministic | Warn | Lua modules should end with `return M` so `require` consumers receive the module table. |
| `require_assigned_to_local` | deterministic | Warn | `require` results should be bound to a local; bare top-level `require` calls only side-effect through `package.loaded`. |
| `tail_call_recursion` | semantic | Warn | Recursive functions should keep the recursive call in tail position to avoid unbounded stack growth. |
| `metatable_boundary_documented` | semantic | Block | Mutating metatable fields changes table behavior in a non-local way; the change should explain the new contract. |
| `no_hardcoded_secrets` | semantic | Block | Credentials and tokens should come from a secret manager or scoped environment, not embedded literals. |

## Evidence

Evidence scanned on 2026-05-10.

- Lua 5.4 reference manual: assignments (§3.3.3), function definitions (§3.4.11), proper tail calls (§3.4.10), metatables (§2.4), modules (§6.3), and the `load`, `loadfile`, `dofile`, `require`, `os.execute`, and `io.popen` standard library entries.
- Lua 5.2 reference manual incompatibilities (§8.1) — `setfenv`/`getfenv` removal.
- Programming in Lua (Lua.org): chapters on local variables and blocks (6.2), tail calls (6.3), metatables (13), modules and packages (15), and `require` (15.1).
- Luacheck documentation: warning catalogue for non-local globals and unused values.
- Lua-users wiki tutorials: `ScopeTutorial`, `ModulesTutorial`, `MetatablesTutorial`, and the Lua 5.2 migration page.
- OWASP cheat sheets and GitHub secret scanning documentation: code injection, OS command injection, secrets management, and hardcoded credential risk.

## Known False Positives

- Regex predicates are source-text checks. Comments, string literals, multiline strings (`[[ ... ]]`), and metaprogramming can fool them until AST-backed matching lands.
- `no_global_function_definition` flags any `function name(` at the start of a line; the column-zero heuristic misses functions defined inside a `do ... end` block (false negative) and may flag `function name(` lines inside long-strings (false positive).
- `no_implicit_globals` matches column-zero bare-name assignments (`foo = ...` or `foo, bar = ...`) and cannot tell a deliberate `_ENV` reassignment apart from a forgotten `local`. Indented assignments inside functions are not inspected — the rule is about top-level binding hygiene.
- `no_loadstring_or_loadfile` and `no_unsafe_os_command` allow literal-string arguments and block dynamic ones; if a single file mixes both, only the block triggers (file-global heuristic). They cannot prove a variable is trusted.
- `no_setfenv_or_getfenv` will flag the legitimate Lua 5.1 compatibility shim `local setfenv = setfenv or function(...) ... end`. Projects that genuinely target 5.1 should suppress the rule for that file.
- `module_returns_value` checks only that a column-zero `return` statement appears anywhere in the file, so files that early-return inside a guarded `if` block but never reach a final `return` will still pass. The rule excludes test, script, and example paths and files starting with a `#!` shebang. Side-effect-only modules (e.g., a strict-mode patch loaded for its registration) should add a trailing `return true` to silence it.
- `require_assigned_to_local` flags any top-level `require` not preceded by `local NAME =`. Side-effect-only `require` calls (e.g., loading a logger that registers itself) trigger the warn until they are wrapped in `local _ = require(...)`.
- Semantic predicates depend on a cheap judge and should stay high-threshold until Flow exposes structured Lua data-flow.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape mirrors the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "src/server.lua", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "src/server.lua", "text": "..."}]}
  ]
}
```
