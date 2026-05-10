# Markdown Seed Predicate Pack

This pack covers prose Markdown files used for documentation, READMEs, and design notes. Markdown has a smaller surface area than full programming languages, so the pack stays narrow and focuses on review-slice checks with clear correctness, accessibility, or safety impact: untagged code fences, heading-level discipline, single document title, image alt text, dangerous raw HTML, broken internal links, and link-style consistency.

## Stack Assumptions

- Files use `.md` or `.markdown`. MDX (`.mdx`) is intentionally excluded for v0 because its JSX layer needs separate parsing rules.
- Documents target CommonMark with GitHub Flavored Markdown extensions; predicates do not assume Pandoc-only or Liquid-templated dialects.
- Production-path checks exclude `node_modules/`, `vendor/`, `third_party/`, `target/`, `dist/`, `build/`, `out/`, `.git/`, and obvious `fixtures/`, `testdata/`, `test/`, and `tests/` paths so vendored docs and intentionally malformed test fixtures do not get flagged.
- Deterministic predicates run regex scans on changed source text until Harn Flow exposes a Markdown AST query API. Rules with meaningful false-positive risk warn rather than block.
- Semantic predicates make one cheap judge call and only act when they can cite concrete changed spans.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `code_fence_language_specified` | deterministic | Warn | Fenced code blocks should declare a language so highlighters and assistive tech can render them well. |
| `heading_level_discipline` | deterministic | Warn | Heading levels should not jump (h1 → h3) — accessibility tools depend on monotonic structure. |
| `single_h1_per_doc` | deterministic | Warn | A document should have one H1 acting as its title, not several. |
| `image_alt_text_present` | deterministic | Block | Every meaningful image needs alt text; decorative images need an explicit empty alt. |
| `no_dangerous_inline_html` | deterministic | Block | Raw `<script>`, `<iframe>`, `javascript:` URLs, and inline event handlers are XSS sinks when Markdown renders to HTML. |
| `no_broken_internal_links` | semantic | Block | Relative links and anchors must resolve to a file or heading that exists in the slice or repo. |
| `consistent_link_format` | semantic | Warn | A single document should not freely mix inline, reference, and bare-URL link styles. |

## Evidence

Evidence scanned on 2026-05-09.

- CommonMark 0.31.2 specification: fenced code blocks, raw HTML, links.
- GitHub Flavored Markdown (GFM) specification: fenced code blocks and the disallowed raw HTML extension.
- markdownlint rule docs: MD040 (fenced-code-language), MD001 (heading-increment), MD025 (single-h1), MD045 (no-alt-text), MD051 (link-fragments), MD054 (link-image-style).
- W3C WAI tutorials and WCAG 2.2 understanding pages: page structure / headings, images alt text, non-text content (1.1.1), info and relationships (1.3.1), link purpose in context (2.4.4).
- OWASP Cross-Site Scripting Prevention Cheat Sheet: HTML and URL contexts that motivate the dangerous-HTML predicate.
- GitHub docs: basic writing and formatting syntax, used as the de-facto rendering reference for repository-hosted docs.

## Known False Positives

- Regex predicates do not parse Markdown. Code samples that demonstrate Markdown syntax can be misread; HTML inside fenced code blocks is treated as regular content.
- `code_fence_language_specified` flags only when a complete bare opener / bare closer pair is detected; a file with all tagged blocks is allowed even if their closers are bare. It does not yet recognize tilde (`~~~`) fences.
- `heading_level_discipline` is a file-level approximation: it flags when a level appears without its parent level present in the same document. It will miss intra-document skips (h2 → h4 → h2 → h4) where every parent level appears somewhere, and miss skips inside ATX-only setext-mixed documents.
- `single_h1_per_doc` flags two ATX-style top-level headings; setext (`===`) H1s are not yet detected.
- `image_alt_text_present` blocks `![](url)` only. Markdown reference-image syntax (`![][ref]`) is not yet inspected; HTML `<img>` tags without `alt` attributes are also outside the v0 check.
- `no_dangerous_inline_html` is keyword-based and case-insensitive. It will catch tags that are inside fenced code blocks intended as documentation; once the predicate runtime exposes structured slices, prefer a local suppression over relaxing the rule.
- `no_broken_internal_links` and `consistent_link_format` depend on the semantic judge recognizing concrete changed spans. They should stay high-threshold and cite exact link spans before acting.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Warn", "files": [{"path": "docs/install.md", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "docs/install.md", "text": "..."}]}
  ]
}
```
