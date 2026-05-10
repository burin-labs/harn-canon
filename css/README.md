# CSS Seed Predicate Pack

This pack covers vanilla CSS plus the common preprocessor dialects (Sass `.scss`/`.sass`, Less `.less`). It targets review issues that changed stylesheet slices can catch cheaply: cascade hygiene (`!important`, id selectors), internationalization (logical properties), unit hygiene (zero values, absolute font sizes), and accessibility (focus indicators, reduced-motion respect).

## Stack Assumptions

- Source files end in `.css`, `.scss`, `.sass`, or `.less`. CSS-in-JS, styled-components, and tagged-template stylesheets are out of scope until Harn Flow exposes a stable embedded-CSS extractor.
- Vendor and build artifacts under `node_modules/`, `vendor/`, `dist/`, `build/`, or matching `*.min.css`/`*.min.scss`/`*.min.less` are skipped.
- Test stylesheets under `__tests__/`, `test/`, `tests/`, or matching `*.test.css`/`*.spec.scss` are skipped by deterministic source predicates.
- Deterministic predicates use file-text scans until Harn Flow exposes a stable CSS AST query API. They will accept some false positives in rare grammar shapes; see the list below.
- Semantic predicates make one cheap judge call over changed stylesheets and use only evidence captured at authoring time.
- Advisory rules return `Warn` when stylistic exceptions are common (vendor-driven id usage, intentionally physical layouts, decorative micro-transitions). Blocking rules are reserved for `!important` without justification, suppressed focus indicators, and motion that ignores `prefers-reduced-motion`.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_important_without_comment` | deterministic | Block | `!important` overrides need an inline comment so reviewers can see the override is intentional and bounded. |
| `no_id_selectors` | deterministic | Warn | Id selectors spike specificity (0,1,0,0) and break component composition; classes and attributes scale better. |
| `prefer_logical_properties` | deterministic | Warn | Physical-direction properties (`margin-left`, `text-align: right`, …) break in RTL locales; logical equivalents mirror automatically. |
| `no_zero_with_unit` | deterministic | Warn | Zero-length values are unitless by definition; `0px` adds bytes and minor noise without changing meaning. |
| `font_size_uses_relative_units` | deterministic | Warn | Absolute font sizes (`px`, `pt`) ignore the user's browser font-size preference and fail WCAG 1.4.4 resize-text. |
| `accessible_focus_indicator` | semantic | Block | Suppressing focus outlines without a visible replacement breaks keyboard navigation (WCAG 2.4.7). |
| `respect_prefers_reduced_motion` | semantic | Block | Non-trivial animations and transitions need a `prefers-reduced-motion` escape hatch (WCAG 2.3.3). |

## Evidence

Evidence scanned on 2026-05-09.

- MDN Web Docs: `!important`, specificity, ID selectors, logical properties and values, length units, `font-size`, `:focus-visible`, `outline`, and `@media (prefers-reduced-motion)`.
- W3C / CSSWG: CSS Logical Properties Level 1 editor's draft.
- W3C WAI / WCAG 2.2: Understanding Focus Visible (2.4.7), Resize Text (1.4.4), Animation from Interactions (2.3.3).
- web.dev: logical-properties learn module, font-size guidance, reduced-motion article.
- Stylelint docs: `declaration-no-important`, `selector-max-id`, `length-zero-no-unit` rule references for cross-tool calibration of common style issues.

## Known False Positives

- Regex predicates do not parse CSS. Comments, multi-line declarations, Sass interpolation, nested rules, and `@supports` blocks can confuse deterministic checks.
- `no_important_without_comment` accepts the file as soon as one `!important` is paired with a nearby comment; multiple unjustified overrides in the same file will not all be flagged independently. It also cannot tell whether a comment actually explains the override versus being unrelated.
- `no_id_selectors` flags any `#name` selector form. Sass interpolation `#{$var}` is excluded, but `#main` rules deliberately used to style ids written by a CMS will need a local suppression once the predicate runtime supports them.
- `prefer_logical_properties` flags only the most common physical properties (`margin/padding/border-left|right`, `text-align|float|clear: left|right`). Vertical-axis properties and `*-top`/`*-bottom` are intentionally not flagged because the inline-axis cases drive most RTL bugs.
- `no_zero_with_unit` excludes time (`0s`, `0ms`) and angle units (`0deg`) because their unit can carry intent in animation/transform contexts. Decimal lengths like `0.5px` are not flagged.
- `font_size_uses_relative_units` flags only `px` and `pt`. Container queries with `cqw` font-size and clamp expressions that contain a `px` term may produce false positives.
- Semantic predicates depend on the judge recognizing concrete changed spans. They should stay high-threshold and cite the exact selector or media query before blocking.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape matches the current harn-canon convention:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "components/card.css", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "components/card.css", "text": "..."}]}
  ]
}
```
