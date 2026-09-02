## What changed

<!--
Three to five sentences. Say what you changed and why, in plain language.

Example:
The Python pack accepted `except Exception: pass` because the predicate only
matched a bare `except:`. It now also matches a broad `except Exception`
whose body is a single `pass`, which is the form that actually shows up in
review. Two fixtures cover it: one slice that must block and one that swallows
a specific exception on purpose and must stay allowed. Evidence is the CPython
tutorial section on handling exceptions, refreshed to a current source date.
-->

## Pack and scope

<!-- Which language or stack pack this touches. One pack per pull request. -->

## Evidence

<!--
For a new or changed predicate:
- The `_EVIDENCE_*` constant it cites, with at least two independent URLs no
  older than 18 months.
- The `confidence` value and what it is calibrated against.
- The `source_date` you scanned on.
-->

## Validation

<!-- Paste what you ran and what it reported. -->

- [ ] `harn run scripts/validate-canon.harn -- --today $(date -u +%F)`
- [ ] `harn run scripts/execute-fixtures.harn`
- [ ] `harn check --strict-types . && harn lint --strict .`

## Checklist

- [ ] The title follows `[Area] Sentence case summary`.
- [ ] Every new predicate has a fixture it blocks and one it allows.
- [ ] The pack README has a row for every predicate.
- [ ] No predicate calls a side-effect builtin. See the trust model in
      [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] Routing selectors, if any, are in `canon-packs.json` and nowhere else.
