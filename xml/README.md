# XML Seed Predicate Pack

This pack covers raw XML payloads, schemas (XSD), stylesheets (XSLT), and related XML-shaped formats (WSDL, SVG, RSS, Atom). XML has a smaller surface area than a full programming language, so the pack focuses on the few defaults that consistently catch real shipping incidents: external entity injection, encoding ambiguity, namespace discipline, schema hygiene, stylesheet resource loading, and credential leaks in config files.

## Stack Assumptions

- Source checks target `.xml`, `.xsd`, `.xsl`, `.xslt`, `.wsdl`, `.svg`, `.rss`, and `.atom` files.
- Payload-only checks (DOCTYPE block) exclude `.xsd`, `.xsl`, and `.xslt` because schemas and stylesheets routinely declare types the parser never needs to expand.
- Deterministic predicates operate on changed source text. Until Flow exposes an XML AST and parser-configuration query, parser-side defenses (`FEATURE_SECURE_PROCESSING`, `XMLConstants.ACCESS_EXTERNAL_DTD`, `defusedxml`, etc.) live in language packs rather than this format pack.
- Semantic predicates may block only when the judge can cite a concrete changed span and the issue is not reliably expressible with simple syntax checks.

## Predicate Coverage

| Predicate | Mode | Verdict | Purpose |
|---|---|---|---|
| `no_inline_doctype` | deterministic | Block | XML payloads must not declare an inline DOCTYPE; the entity subset is the primary XXE vector. |
| `no_external_entity_references` | deterministic | Block | `<!ENTITY ... SYSTEM>` and `<!ENTITY ... PUBLIC>` declarations must not appear in any XML file. |
| `xml_declares_utf8` | deterministic | Warn | XML files should pin `encoding="UTF-8"` in the XML declaration for stable interop. |
| `xml_namespace_prefixes_declared` | deterministic | Warn | Files that use namespace-prefixed elements must declare at least one `xmlns:prefix=` binding. |
| `xsd_has_target_namespace` | deterministic | Warn | XSD schemas should declare a `targetNamespace` so consumers can disambiguate types. |
| `xslt_no_external_documents` | deterministic | Block | XSLT `xsl:include`, `xsl:import`, and `document()` must not load absolute `http(s)`, `ftp`, or `file` URIs. |
| `no_hardcoded_secrets` | semantic | Block | XML config and payload files must not embed credentials, tokens, or production connection strings. |
| `xsd_constrains_user_input` | semantic | Block | Schema changes must not weaken validation on attacker-reachable fields. |

## Evidence

Evidence scanned on 2026-05-09.

- W3C XML 1.0 specification (encoding declaration, DOCTYPE definition, external entity rules) and W3C Namespaces in XML 1.0.
- W3C XML Schema 1.1 Structures specification and XML Schema Primer for `targetNamespace` semantics.
- W3C XSLT 3.0 specification for stable URI collection rules around `document()`, `xsl:include`, and `xsl:import`.
- IETF RFC 7303 (XML Media Types) for default encoding and charset behavior.
- OWASP cheat sheets: XML External Entity Prevention, XML Security, and Secrets Management.
- OWASP community page on XSLT Injection for stylesheet resource-loading risk.
- MITRE CWE-611 (Improper Restriction of XML External Entity Reference) and CWE-776 (Recursive Entity Expansion).
- GitHub secret scanning documentation for hardcoded credential risk and remediation context.

## Known False Positives

- Regex predicates are intentionally conservative and file-scoped. Files containing both an offending pattern and an allowed one may be allowed or warned imprecisely until AST-level matching lands.
- `no_inline_doctype` blocks every DOCTYPE in payload files, including legitimate uses such as XHTML documents that intentionally reference a public DTD. Move to an external schema or a XHTML-specific override pack if needed.
- `no_external_entity_references` blocks all SYSTEM/PUBLIC entity declarations, including ones whose targets the project controls; the safe path is still to load such fragments through application code.
- `xml_declares_utf8` only inspects the literal XML declaration. Files relying on a UTF-8 BOM with no declaration will warn.
- `xml_namespace_prefixes_declared` warns at file granularity when any prefix appears without a corresponding `xmlns:` binding in the same document, even when the binding is inherited from an enclosing document at runtime.
- `xsd_has_target_namespace` does not detect chameleon schemas that intentionally omit `targetNamespace` to be re-included.
- `xslt_no_external_documents` only catches absolute URIs in literal `href` and `document()` arguments; computed URIs slip through and should be reviewed at the call site.
- The semantic predicates must cite concrete changed spans and should stay high-threshold to avoid blocking on speculative concerns.

## Fixtures

Each fixture in `fixtures/` contains one blocked or warned example and one allowed example for the corresponding predicate. The fixture shape mirrors the existing seed packs:

```json
{
  "predicate": "name",
  "cases": [
    {"expect": "Block", "files": [{"path": "config/app.xml", "text": "..."}]},
    {"expect": "Allow", "files": [{"path": "config/app.xml", "text": "..."}]}
  ]
}
```
