# Regex sanitizer bypass evidence (empirically verified)

All inputs below were passed through a regex-based sanitizer (DangerousTagRegex + EventAttributeRegex + JavascriptProtocolRegex) and came out **unchanged** — i.e. the browser would decode/execute them. Verified by running the sanitizer against a test harness in a throwaway console project.

| Input | Sanitizer output | Browser behavior |
|---|---|---|
| `<a href="jav&#x61;script:alert(1)">` | kept as-is | entity-decodes to `javascript:` → executes on click |
| `<a href="java&#115;cript:...">` | kept | same |
| `<a href="javascript&#x3a;...">` | kept | entity-decoded colon → `javascript:` |
| `<a href="&#x6a;avascript:...">` | kept | entity-decoded `j` → `javascript:` |
| `<a href="java\tscript:...">` | kept | URL parser strips tab → `javascript:` |
| `<svg><a xlink:href="javascript:...">` | kept | regex requires whitespace before `href`; `xlink:href` never matches; SVG `<a>` navigates |
| `<svg><a href="jav&#x61;script:...">` | kept | SVG + entity combo |
| `<a href="vbscript:msgbox(1)">` | kept | legacy IE vector (not in `javascript:` regex) |
| `<img src="jav&#x61;script:...">` | kept | entity bypass on `src` |

What the regexes DID correctly strip (regression baseline): literal `javascript:`, mixed-case `JaVaScRiPt:`, `onerror`/`onclick`/`onload` attributes, `<script>/<iframe>/<object>` literal tags, `![x](javascript:...)` markdown syntax (Markdig neutralizes it itself), `<scr&#x69;pt>` (Markdig entity-escapes unknown tag text before the sanitizer sees it — tag-name entity encoding is NOT a browser vector, attribute values are).

## Why regex blacklists fail

1. HTML **character references are decoded in attribute values** during tokenization — the sanitizer must decode before checking schemes.
2. The URL parser strips ASCII tabs/newlines **before scheme detection** — `java\tscript:` is `javascript:`.
3. Attribute-name matching misses namespaced forms (`xlink:href`) and non-standard attributes (`srcdoc`, `style`).
4. Blacklists enumerate what's known today; a parser re-serializing from a DOM allowlist has no enumeration gap.

## The fix that works

Parser-level allowlist via `Ganss.XSS.HtmlSanitizer` (AngleSharp DOM):

```csharp
var sanitizer = new HtmlSanitizer();
sanitizer.AllowedTags.Clear();
foreach (var t in new[] { "p","h1","h2","h3","h4","h5","h6","a","img","ul","ol","li",
    "blockquote","pre","code","table","thead","tbody","tr","th","td",
    "strong","em","del","br","hr","span","figure","figcaption" })
    sanitizer.AllowedTags.Add(t);
sanitizer.AllowedAttributes.Clear();
foreach (var a in new[] { "href","src","alt","title","class","lang" })
    sanitizer.AllowedAttributes.Add(a);
sanitizer.AllowedSchemes.Clear();
foreach (var s in new[] { "http","https","mailto" })
    sanitizer.AllowedSchemes.Add(s);
sanitizer.AllowedCssProperties.Clear(); // strip style
var safe = sanitizer.Sanitize(html);
```

Keep `class` for Markdig code-block language annotations (`language-csharp`). One static configured instance is thread-safe.

## Regression test set

Cover every row above (entity variants, whitespace, xlink:href) plus: legitimate `https://` links preserved, relative links preserved, tables/code/images survive, `style=` gone, `onerror` gone.
