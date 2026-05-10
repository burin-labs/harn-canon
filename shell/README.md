# Shell Seed Predicate Pack

This pack covers POSIX shell, Bash, and other Bourne-family scripts that ship inside repositories: build helpers, deploy scripts, CI glue, and one-off operational tools. It targets the small set of high-signal mistakes that turn shell scripts into latent reliability and security incidents — missing strict-mode flags, parsing `ls`, dynamic `eval`, missing tempfile cleanup, blanket `shellcheck` disables, hardcoded secrets, and leaking sensitive data into logs.

## Stack Assumptions

- Files are detected by extension (`.sh`, `.bash`, `.zsh`, `.ksh`, `.dash`) or by a Bourne-family shebang on line 1 (`sh`, `bash`, `zsh`, `ksh`, `dash`, `ash`).
- Strict-mode enforcement targets *executable* scripts (those with a shebang). Files without a shebang are assumed to be sourced libraries where `set -e`/`set -u` semantics may be inappropriate.
- Deterministic predicates run over changed source text until Flow exposes a stable shell AST query API; rules with meaningful false-positive risk warn rather than block.
- Semantic predicates make one cheap judge call over the changed shell files and rely on the rubric to cite concrete spans before blocking.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `set_euo_pipefail` | deterministic | Block | Executable shell scripts must enable `errexit`, `nounset`, and `pipefail`. |
| `no_parsing_ls` | deterministic | Block | Capturing `ls` output for iteration is unsafe with whitespace, newlines, and globbing. |
| `no_eval_dynamic_input` | deterministic | Block | `eval` on interpolated variables or command substitutions is shell injection. |
| `trap_cleanup_on_tempfile` | deterministic | Warn | Scripts that create tempfiles via `mktemp` should remove them with an `EXIT` trap. |
| `no_blanket_shellcheck_disable` | deterministic | Warn | `# shellcheck disable=all` hides every diagnostic; prefer narrowly scoped SC codes. |
| `shellcheck_clean` | semantic | Block | Changed shell scripts should pass ShellCheck under its default configuration. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, tokens, and private keys must not live in shell source. |
| `no_sensitive_data_in_logs` | semantic | Block | `echo`/`printf`/log lines must not emit credentials or sensitive request data. |

## Evidence

Evidence scanned on 2026-05-09.

- GNU Bash reference manual: `set` builtin (errexit, nounset, pipefail) and `trap` builtin.
- Google Shell Style Guide: shell selection, strict-mode guidance, and `eval` usage.
- ShellCheck wiki: SC2086 (quote expansions), SC2045 (parsing `ls`), SC2294 (`eval` on arrays/variables), SC2064 (single-quote `trap` arguments), and the `Directive`/`Ignore` pages for `# shellcheck disable=` syntax.
- Greg's Wiki (`mywiki.wooledge.org`): `ParsingLs`, `BashFAQ/048` (eval pitfalls), and `SignalTrap`.
- OWASP cheat sheets: Secrets Management and Logging guidance; GitHub secret-scanning documentation for the hardcoded-credential surface area.

## Known False Positives

- Regex predicates do not parse shell. Heredocs, single-quoted literals, and string interpolation can fool them until a real shell AST is wired in.
- `set_euo_pipefail` only inspects files with a Bourne-family shebang. Sourced libraries (no shebang) are skipped because they typically inherit the caller's options.
- `no_parsing_ls` blocks all `$(ls …)` and backtick `ls …` capture, including the rare cases where the output is intentionally formatted for human display. Reroute through `find -print0` or array globbing, or suppress with a justification once `# harn` directives land.
- `no_eval_dynamic_input` blocks `eval` lines that contain `$` or backticks anywhere on the line. Fully literal `eval` (rare) is allowed; in-string `$` literals (e.g. inside single quotes) may trigger a false positive.
- `trap_cleanup_on_tempfile` is conservative at file granularity. Multi-script pipelines that delegate cleanup to a parent script will warn until suppressions land.
- `no_blanket_shellcheck_disable` only flags `disable=all`; narrower disables and missing-justification cases are left to code review.
- Semantic predicates depend on the judge recognizing concrete changed spans. They should stay high-threshold until Flow exposes structured shell data-flow signals.

## Fixtures

Each fixture in `fixtures/` contains at least one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "scripts/deploy.sh", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "scripts/deploy.sh", "text": "..."}]}
  ]
}
```
