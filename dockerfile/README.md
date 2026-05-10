# Dockerfile Seed Predicate Pack

This pack covers `Dockerfile` and `Containerfile` build recipes. It targets high-signal review issues that changed Dockerfile slices can catch cheaply: floating base-image tags, noisy or leaky `apt-get` invocations, `ADD` misuse, supply-chain-unsafe `curl | sh` installs, missing non-root user, secret-shaped values baked into image layers, shell-form `CMD`/`ENTRYPOINT`, single-stage builds that ship build toolchains, and unnecessary layer fragmentation.

## Stack Assumptions

- Build recipes are named `Dockerfile`, `Dockerfile.<variant>`, `<name>.Dockerfile`, or `Containerfile` (Podman/Buildah convention).
- Dockerfiles are linted as build-system source, so every changed file flows through this pack regardless of subdirectory.
- Deterministic predicates use file-text scans until Harn Flow exposes a stable Dockerfile parser; Hadolint-style AST queries can replace the regex layer later without changing predicate semantics.
- Semantic predicates make one cheap judge call over changed Dockerfiles and use only evidence captured at authoring time.
- Advisory rules return `Warn` when idiomatic exceptions are common (slim base images that already drop privileges, `apt-get`-free distros, single-stage debug images). Blocking rules are reserved for floating base-image tags, `curl | sh` installs, and secrets baked into `ENV`/`ARG`.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_latest_or_unpinned_base_image` | deterministic | Block | `FROM` must pin a tag (preferably a digest); bare images and `:latest` make rebuilds non-reproducible. |
| `apt_get_no_install_recommends` | deterministic | Warn | `apt-get install` should pass `--no-install-recommends` to avoid pulling optional dependencies into the image. |
| `apt_get_clean_lists` | deterministic | Warn | The same `RUN` that installs packages should `rm -rf /var/lib/apt/lists/*` so caches do not bloat the layer. |
| `prefer_copy_over_add` | deterministic | Warn | Local file copies should use `COPY`; `ADD` is reserved for remote URLs and auto-extracted archives. |
| `no_curl_pipe_shell` | deterministic | Block | Piping `curl`/`wget` directly into a shell skips checksum and signature verification. |
| `non_root_user_set` | deterministic | Warn | Containers should drop to a non-root account via an explicit `USER` directive. |
| `no_secrets_in_env_or_arg` | deterministic | Block | Credentials, tokens, and private keys must not be baked into image layers via `ENV` or `ARG` defaults. |
| `use_exec_form_for_cmd_entrypoint` | deterministic | Warn | `CMD` and `ENTRYPOINT` should use the JSON exec form so the process receives signals directly. |
| `multi_stage_build_preferred` | semantic | Block | Single-stage builds that ship compilers, package managers, or dev dependencies should split into build and runtime stages. |
| `minimize_layer_count` | semantic | Warn | Consecutive related `RUN` steps that leak intermediate artifacts across layers should be merged. |

## Evidence

Evidence scanned on 2026-05-09.

- Docker Build best practices: `FROM` pinning, `apt-get` patterns, `ADD` vs `COPY`, `USER`, `RUN` layering, multi-stage builds, layer minimization.
- Docker Reference: directives `FROM`, `ADD`, `COPY`, `USER`, `ARG`, `CMD`, `ENTRYPOINT`.
- Docker Build secrets: BuildKit `--mount=type=secret` for build-time credentials.
- OWASP Docker Security Cheat Sheet and Code Injection guidance for `curl | sh` and non-root recommendations.
- OWASP Secrets Management Cheat Sheet for hardcoded credential risk.
- Debian `apt-get` manpage for `--no-install-recommends` semantics.

## Known False Positives

- Regex predicates do not parse Dockerfiles. Inline comments, `\` line continuations across many lines, heredocs, and multi-stage `FROM ... AS build` aliases can confuse deterministic checks.
- `no_latest_or_unpinned_base_image` allows digest pins (`@sha256:...`) and any explicit non-`latest` tag, and exempts `FROM scratch`. It does not catch `FROM --platform=$BUILDPLATFORM image` (no tag) because the leading `--platform` flag suppresses the unpinned match. Pin freshness still belongs in dependency management.
- `apt_get_no_install_recommends` requires the `--no-install-recommends` flag on the same physical line as `apt-get install`; multi-line `RUN` blocks that put the flag on a continuation line will warn until a Dockerfile parser lands.
- `apt_get_no_install_recommends` and `apt_get_clean_lists` are file-scoped and Debian/Ubuntu-specific. Alpine (`apk`), Red Hat (`dnf`/`microdnf`), and distroless images are not flagged; future packs should add per-distro predicates.
- `prefer_copy_over_add` warns on every local-path `ADD`, including the legitimate "auto-extract local tarball" case. It does not warn on `ADD --chown=...` style flag forms because the leading `--` suppresses the match. Treat the warning as a prompt to confirm extraction is intended.
- `non_root_user_set` cannot read base-image metadata, so it warns even when the base image (e.g., `node:*-alpine`, `nginxinc/nginx-unprivileged`) already sets a non-root `USER`. Multi-stage builds whose final stage drops privileges in a later `USER` directive are correctly allowed because the file as a whole contains a non-root `USER`. A repo-level allow can suppress this once the predicate runtime supports suppressions.
- `no_secrets_in_env_or_arg` is keyword-based. `ARG` declarations without a default value (e.g., `ARG NPM_TOKEN`) and `ENV` values that reference shell or BuildKit substitutions (e.g., `ENV PASSWORD=$BUILD_PASSWORD`) are intentionally allowed because they expect runtime injection.
- `use_exec_form_for_cmd_entrypoint` warns on the shell form across the file, including stages where shell expansion is genuinely required. Prefer wrapping the command in an explicit `bash -lc` exec-form invocation.
- Semantic predicates depend on the judge recognizing concrete changed spans. They should stay high-threshold and cite the specific stage and instructions before blocking or warning.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "Dockerfile", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "Dockerfile", "text": "..."}]}
  ]
}
```
