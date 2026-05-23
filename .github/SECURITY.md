# Security policy

## Reporting a vulnerability

Email **security@burinlabs.com** with the details. Encrypt with our public key
if the report contains exploit material (key available on request).

Please include:

- a clear description of the issue and the impact (e.g. a malicious
  predicate that survived review and ships in a pack, a CI bypass, a
  validator gap that lets an unsafe predicate land)
- a minimal reproduction (offending Harn snippet, PR that should have been
  rejected, etc.)
- any affected pack or predicate
- whether the issue has been disclosed publicly or to other parties

## Response window

We aim to:

- acknowledge new reports within **2 business days**
- triage and confirm (or dispute) within **5 business days**
- ship a fix or mitigation within **30 days** for confirmed issues, faster
  for actively-exploited supply-chain bugs (e.g. a malicious predicate in a
  shipped pack)

## Scope

In scope:

- every `invariants.harn` predicate pack and its fixtures
- the validator (`scripts/validate_canon.py`)
- CI gates that enforce the trust model (see `CONTRIBUTING.md`)
- the side-effect builtin ban and any way to bypass it

Out of scope (report upstream):

- vulnerabilities in `harn` itself ->
  https://github.com/burin-labs/harn/security/policy
- predicate false positives or false negatives that don't violate the trust
  model -- file these as regular issues

## Trust model recap

Predicate packs are **trusted code** that runs on consumer machines when
`harn lint` evaluates them. PRs are reviewed accordingly; predicates may
not call side-effect builtins. See `CONTRIBUTING.md` for the full list.

## Coordinated disclosure

We support coordinated disclosure. Please give us the response window above
before publishing details. We will credit reporters in the release notes for
the fix unless asked otherwise.
