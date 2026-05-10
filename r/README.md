# R Seed Predicate Pack

This pack covers the R-specific footguns that an Archivist can catch cheaply on a changed slice: search-path pollution, non-reproducible session state, brittle logical literals, ambiguous assignment direction, off-by-one iteration over empty inputs, code injection through `eval(parse(...))`, mutating package-install side effects, and the classic "loop where a vectorized op would do." Two of the three semantic predicates target reproducibility and namespace discipline — both judgement-heavy enough that a single judge call earns its keep over regex.

## Stack Assumptions

- R source files use `.R`, `.r`, `.Rmd`, `.rmd`, `.qmd`, or `.Rnw` extensions. R Markdown and Quarto files mix prose with code chunks, but the regex predicates fire on full-text matches, so a hit inside a code chunk is treated the same as a hit in a `.R` script.
- Production paths exclude any path under `tests/`, `testthat/`, `test/`, `inst/extdata/`, `man-roxygen/`, `data-raw/`, or `dev/`.
- Package source paths are detected by an `R/` directory segment (the canonical layout for an installable R package per *R Packages 2e* and *Writing R Extensions*). The `package_namespace_discipline` predicate restricts itself to those paths because `library()` and unqualified non-base symbols are only a problem in package code; analysis scripts use them routinely.
- Analysis scripts are R files outside `R/` and outside test directories. The `reproducible_random_seed` predicate scopes there because `set.seed()` inside package source would clobber the caller's RNG state.
- Deterministic predicates use file-text regex scans because Harn Flow does not yet expose a stable R AST query API; semantic predicates make a single judge call over changed R files.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_attach` | deterministic | Block | `attach()` splices a database into the search path, shadowing variables and hiding load order from the reader. |
| `no_setwd_in_scripts` | deterministic | Block | `setwd()` hardcodes a path that breaks on any other contributor's machine and on CI. |
| `no_rm_list_ls` | deterministic | Block | `rm(list = ls())` only clears user objects from the calling environment; it gives a false sense of reproducibility while leaving loaded packages, options, and graphics state intact. |
| `use_logical_constants` | deterministic | Warn | `T` and `F` are ordinary symbols that any caller can rebind, silently flipping branches. `TRUE`/`FALSE` are reserved. |
| `no_right_assign` | deterministic | Warn | `->` and `->>` put the binding target on the right, hiding it from a reader scanning the left margin. |
| `seq_along_over_one_to_length` | deterministic | Warn | `1:length(x)` evaluates to `c(1, 0)` when `x` is empty, looping twice with invalid indices instead of zero times. |
| `no_install_or_update_packages` | deterministic | Block | `install.packages()` and `update.packages()` mutate the user's library on import. Pin via `renv` or `DESCRIPTION` instead. |
| `no_eval_parse_text` | deterministic | Block | `eval(parse(text = ...))` evaluates arbitrary text as code and skips static checks; it is the canonical R injection sink. |
| `vectorize_over_loops` | semantic | Warn | Element-wise loops in R are typically 10–100× slower than the equivalent vectorized expression and harder to read. |
| `reproducible_random_seed` | semantic | Warn | Analysis scripts that sample or simulate without `set.seed()` produce a different answer on every run. |
| `package_namespace_discipline` | semantic | Warn | `library()` inside `R/` mutates the user's search path on package load; unqualified non-base symbols dodge the `DESCRIPTION` Imports declaration and break under `R CMD check`. |

## Evidence

Evidence scanned on 2026-05-10.

- *R Manuals* (CRAN, R Foundation): `attach`, `getwd`/`setwd`, `rm`, `seq`, `eval`, `Random`, `install.packages`, `lapply`, `assignOps`, `logical` reference pages.
- *Writing R Extensions* (CRAN): namespace and dependency declaration semantics for installable packages.
- *R Packages, 2e* (Wickham & Bryan, r-pkgs.org): code, dependency mindset, namespace, dependencies-in-practice chapters.
- *Advanced R, 2e* (Wickham, adv-r.hadley.nz): environments, expressions, control-flow, performance-improve chapters.
- *R for Data Science, 2e* (Wickham, Çetinkaya-Rundel, Grolemund, r4ds.hadley.nz): iteration, workflow-scripts, and Quarto chapters; workflow-vs-script post on tidyverse.org.
- *tidyverse style guide* (style.tidyverse.org): syntax — assignment operator, `TRUE`/`FALSE` over `T`/`F`.
- *Google R style guide* (google.github.io/styleguide/Rguide.html): assignment operator and logical-constant guidance.
- *here* (here.r-lib.org), *renv* (rstudio.github.io/renv), and *rlang* (rlang.r-lib.org): canonical alternatives to `setwd()`, `install.packages()`, and `eval(parse(text = ...))`.

## Known False Positives

- Regex predicates do not parse R. Strings, comments, and roxygen blocks containing the matched tokens (e.g. an `attach(` literal in a docstring) will trip the deterministic checks. Suppress locally once the predicate runtime supports it.
- `use_logical_constants` matches `T` and `F` only when they appear in a logical-literal context (after `=`, `,`, `(`, `<-`, `==`, `&&`, `||`, etc.). It still flags `T`/`F` used as user-defined symbols in those contexts; the canon's stance is that single-letter `T`/`F` as a variable name is itself worth flagging. Conversely, `T` inside a string or comment slips through, which is fine.
- `no_right_assign` looks for `->` followed by an identifier and not preceded by `<` (to avoid `<-`). Right-assigns into chained subscripts (`x[i] -> y`) are caught; `->` inside a string or `#` comment is a residual FP.
- `seq_along_over_one_to_length` matches the literal `1:length(x)` family. Loops written `seq.int(1, length(x))` or `1L:length(x)` slip through; the rule targets the most common idiom by design.
- `no_install_or_update_packages` flags any `install.packages(` / `update.packages(` call site, including `renv::install()` wrappers that legitimately call `install.packages` internally — those wrappers should not appear in committed source either, so the FP rate is low in practice.
- `no_eval_parse_text` only matches `eval(parse(text = ...))`. Equivalent `do.call("eval", list(parse(text = ...)))` rewrites are not caught; they are rare enough that catching them with regex is not worth the brittleness.
- The semantic predicates restrict their scan to a path-scoped subset (analysis scripts for `reproducible_random_seed`, package source for `package_namespace_discipline`). A repo with no R files in those scopes will allow trivially.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and at least one allowed example for the corresponding predicate. The fixture shape matches the harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "scripts/load.R", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "scripts/load.R", "text": "..."}]}
  ]
}
```
