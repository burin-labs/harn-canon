# Terraform Seed Predicate Pack

This pack covers Terraform configurations (`.tf` files) for AWS, Azure, GCP, and other providers. Terraform's surface area is small enough that a v0 pack can target the highest-signal review issues directly: tagging hygiene, variable typing, remote state, version pinning, sensitive output handling, hardcoded secrets, and over-broad IAM grants.

## Stack Assumptions

- Source checks target HCL `.tf` files; `.tf.json`, `.tfvars`, override files, and `.terraform.lock.hcl` are out of scope for v0.
- Production paths exclude `examples/`, `test/`, `tests/`, `testdata/`, and `.terraform/` working directories.
- Projects target Terraform 1.x (or OpenTofu 1.x), so the modern `terraform { required_providers { ... = { source, version } } }` form is assumed; legacy bare-string provider declarations are not recognized.
- Child modules conventionally live under a `modules/` path. The backend predicate uses that convention to scope itself to root-module files.
- Deterministic predicates operate over changed source text until Flow exposes a stable HCL AST query API. Regex-based matching is intentionally conservative.
- Semantic predicates may block only when the judge can cite a concrete changed span and the issue is not reliably expressible as a syntactic check.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `required_tags_on_resources` | deterministic | Warn | Cloud resources should carry `Owner`, `Env` (or `Environment`), and `CostCenter` tags via the resource tag map or provider `default_tags`. |
| `variable_type_constraints_explicit` | deterministic | Warn | Every `variable` block should declare an explicit `type` constraint. |
| `remote_state_backend_configured` | deterministic | Warn | Root-module files that declare `required_providers` should also configure a remote state backend. |
| `module_registry_version_pinned` | deterministic | Block | Registry-sourced modules must pin a `version` constraint. |
| `provider_versions_pinned` | deterministic | Block | Every `required_providers` entry must declare an explicit `version` constraint. |
| `outputs_with_secret_names_marked_sensitive` | deterministic | Block | Outputs whose names suggest secrets, tokens, keys, or credentials must set `sensitive = true`. |
| `no_hardcoded_secrets` | semantic | Block | Credentials, API keys, tokens, private keys, and production connection strings must not live in source. |
| `iam_policies_avoid_wildcard_grants` | semantic | Block | IAM policy documents must not grant `Action = "*"` or `Resource = "*"` in unrestricted Allow statements. |

## Evidence

Evidence scanned on 2026-05-09.

- HashiCorp Terraform language docs: input variables, type constraints, backends, remote state, module syntax and sources, expression version constraints, provider requirements, outputs, sensitive data in state, and provider configuration (including AWS `default_tags`).
- HashiCorp Terraform Cloud recommended practices for shared remote state and version pinning.
- AWS tagging best-practices whitepaper for `Owner` / `Env` / `CostCenter` style operational tag schemes.
- Microsoft Azure Cloud Adoption Framework resource-tagging guidance.
- Google Cloud Resource Manager tags overview.
- OWASP Secrets Management Cheat Sheet and GitHub secret scanning documentation for hardcoded-credential risk.
- AWS IAM, Microsoft Entra, and Google Cloud IAM least-privilege guidance for wildcard-grant avoidance.

## Known False Positives

- Regex predicates do not parse HCL. Multi-block files where some blocks satisfy a check and others do not may slip past file-scoped predicates until AST-level matching lands.
- `required_tags_on_resources` is a Warn-level word-boundary check. Files that mention "owner", "env", or "costcenter" outside of tags (variable names, comments, locals) will silence the warning. Orgs with different tag standards should override this predicate locally.
- `variable_type_constraints_explicit` warns at file granularity. A file with one untyped variable alongside several typed ones will not warn.
- `remote_state_backend_configured` skips files under `/modules/` paths but cannot fully distinguish root from child modules in unconventional layouts. Configurations that split `terraform { required_providers }` and `terraform { backend }` across sibling files will warn on the providers file when it is changed alone.
- `module_registry_version_pinned` recognizes the canonical registry source shape (`<NAMESPACE>/<NAME>/<PROVIDER>` or `<HOST>/<NAMESPACE>/<NAME>/<PROVIDER>`). Files that mix registry and local sources can mask a missing pin on the registry module.
- `provider_versions_pinned` assumes the modern source/version map syntax. Legacy bare-string provider declarations (`aws = "~> 4.0"`) are not recognized.
- `outputs_with_secret_names_marked_sensitive` is keyword-driven on output names. An output named neutrally that nonetheless leaks a secret is not caught here — the semantic `no_hardcoded_secrets` predicate complements this case.
- The semantic predicates depend on a cheap judge. They should stay high-threshold and cite concrete changed spans before blocking.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "main.tf", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "main.tf", "text": "..."}]}
  ]
}
```
