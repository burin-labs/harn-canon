# HTML Seed Predicate Pack

This pack covers plain HTML markup before framework-specific packs (React, Vue, Astro, server-side templating engines) layer tighter rules on top. It targets high-signal accessibility and security defaults that survive direct inspection of changed HTML files: image alternative text, document language, inline event handlers, inline styles, semantic landmarks, safe new-window anchors, accessible form controls, and accessible link purpose.

## Stack Assumptions

- Source checks target files ending in `.html` or `.htm`. Templating dialects with non-HTML syntax (`.hbs`, `.ejs`, `.liquid`, `.pug`, framework-specific single-file components) are out of scope until per-framework packs land.
- Build, dependency, and report directories are excluded: `node_modules/`, `dist/`, `build/`, `out/`, `coverage/`, `vendor/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `.cache/`, `target/`, and `test-results/`.
- Predicates that require a full document (`documents_specify_lang`) only fire on files that contain a root `<html>` element, so HTML fragments and partials remain quiet.
- Deterministic predicates are regex-driven scans of changed source text. They are intentionally tolerant of whitespace and case, but they do not parse HTML, so attribute order and quoting style matter.
- Semantic predicates make one cheap judge call over changed HTML files and use only evidence captured at authoring time. They block only when the judge can cite a concrete changed span.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `images_have_alt_text` | deterministic | Block | Every `<img>` must carry an `alt` attribute (`alt=""` is acceptable for decorative images). |
| `documents_specify_lang` | deterministic | Block | Full HTML documents must declare a primary language on `<html>`. |
| `no_inline_event_handlers` | deterministic | Block | Inline `on*=` event-handler attributes must move to scripts so a strict CSP can apply. |
| `no_inline_styles` | deterministic | Warn | Inline `style="…"` declarations should move to stylesheets or scoped classes. |
| `prefer_semantic_landmarks` | deterministic | Warn | `<div>`s named after landmark roles should usually be `<nav>`, `<header>`, `<main>`, `<footer>`, `<aside>`, or `<article>`. |
| `target_blank_uses_rel_noopener` | deterministic | Block | Anchors with `target="_blank"` must include `rel="noopener"` (or `rel="noreferrer"`) to prevent reverse-tabnabbing. |
| `form_controls_have_accessible_names` | semantic | Block | Form controls require an accessible name from `<label>`, `aria-label`, `aria-labelledby`, or `title`. |
| `link_purpose_is_clear` | semantic | Block | Generic placeholder anchor text must be replaced or contextualized so the destination is clear. |

## Evidence

Evidence scanned on 2026-05-09.

- MDN Web Docs: `<img>` element, `<a>` element, `lang` global attribute, `style` global attribute, event handler attribute reference, `rel="noopener"`, and Content Security Policy.
- WHATWG HTML Living Standard: sections module for the `<nav>`, `<header>`, `<main>`, `<footer>`, `<aside>`, and `<article>` semantics.
- W3C WAI tutorials: image-alt decision tree and form-label patterns.
- W3C WCAG 2.2 Understanding documents: Language of Page (3.1.1), Labels or Instructions (3.3.2), and Link Purpose (In Context) (2.4.4).
- web.dev guides: strict CSP and external-anchors-use-rel-noopener.

## Known False Positives

- Regex predicates do not parse HTML. Comments, embedded `<script>` or `<style>` blocks, conditional comments, and unusually formatted multi-line tags can confuse deterministic checks.
- `images_have_alt_text` ignores `<img>` tags that *contain* an `alt` attribute regardless of value. It does not detect placeholder alt text such as the file name; the semantic judge can still flag those when `link_purpose_is_clear` and follow-up accessibility predicates land.
- `documents_specify_lang` only fires on files that include a `<html>` element, so server-rendered partials and component fragments are silent. It accepts `lang=` and `xml:lang=`, including templated values like `lang="{{ locale }}"`.
- `no_inline_event_handlers` is keyword-shaped and ignores any attribute that does not begin with `on` followed by lowercase letters. SVG-specific or vendor-prefixed handlers may need an explicit allow once suppressions ship.
- `prefer_semantic_landmarks` matches landmark-shaped tokens inside any class or id value, so a div with `class="my-nav-bar"` will warn even when it is not a navigation region. The verdict is intentionally `Warn` for this reason.
- `target_blank_uses_rel_noopener` accepts any `rel` value containing `noopener` or `noreferrer`. It does not enforce explicit ordering, so `rel="external noopener"` is allowed.
- The semantic predicates depend on the judge recognizing concrete changed spans. They should stay high-threshold and cite specific control or anchor changes before blocking.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "public/index.html", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "public/index.html", "text": "..."}]}
  ]
}
```
